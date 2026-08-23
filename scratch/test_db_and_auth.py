import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncio
import httpx
from mongomock_motor import AsyncMongoMockClient
from backend.main import app
from backend.db.mongodb import db_manager


async def run_tests():
    print("==================================================")
    print("HealthAI v0.3 - Database & Auth Verification Suite")
    print("==================================================")
    
    # If no live MongoDB instance is reachable, plug in AsyncMongoMockClient for test environment
    if not db_manager.is_connected():
        print("  -> Initializing AsyncMongoMockClient for test suite validation...")
        mock_client = AsyncMongoMockClient()
        db_manager.client = mock_client
        db_manager.db = mock_client["healthai_test"]
        db_manager._is_connected = True
        await db_manager._init_indexes()
        print("  -> AsyncMongoMockClient initialized successfully.")

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        
        # 1. Health check
        print("\n[1] Testing GET /health...")
        res = await client.get("/health")
        print(f"Status: {res.status_code}")
        health_data = res.json()
        print(f"Health Data: {health_data}")
        assert res.status_code == 200
        assert health_data["status"] == "running"
        assert health_data["database_connected"] is True
        print("  [OK] Health check passed.")

        # 2. User Registration
        test_email = f"doctor_{int(asyncio.get_event_loop().time() * 1000)}@example.com"
        test_pass = "SecurePass123!"
        test_name = "Dr. Jane Smith"
        
        print(f"\n[2] Testing POST /api/auth/register with email: {test_email}...")
        res = await client.post("/api/auth/register", json={
            "name": test_name,
            "email": test_email,
            "password": test_pass
        })
        print(f"Status: {res.status_code}")
        assert res.status_code == 201
        reg_data = res.json()
        token = reg_data["access_token"]
        user_id = reg_data["user"]["id"]
        print(f"  [OK] User registered. User ID: {user_id}, Token: {token[:20]}...")

        # 3. Duplicate Registration Prevention
        print("\n[3] Testing duplicate email registration prevention...")
        res = await client.post("/api/auth/register", json={
            "name": test_name,
            "email": test_email,
            "password": test_pass
        })
        print(f"Status: {res.status_code}")
        assert res.status_code == 409
        print("  [OK] Duplicate email correctly rejected with 409 Conflict.")

        # 4. User Login
        print("\n[4] Testing POST /api/auth/login...")
        res = await client.post("/api/auth/login", json={
            "email": test_email,
            "password": test_pass
        })
        assert res.status_code == 200
        login_data = res.json()
        auth_token = login_data["access_token"]
        print("  [OK] Login succeeded. JWT access token received.")

        # 5. Invalid Password Login
        print("\n[5] Testing login with wrong password...")
        res = await client.post("/api/auth/login", json={
            "email": test_email,
            "password": "WrongPassword!"
        })
        assert res.status_code == 401
        print("  [OK] Invalid password rejected with 401 Unauthorized.")

        # 6. Profile /api/auth/me
        print("\n[6] Testing GET /api/auth/me with Bearer token...")
        auth_headers = {"Authorization": f"Bearer {auth_token}"}
        res = await client.get("/api/auth/me", headers=auth_headers)
        assert res.status_code == 200
        me_data = res.json()
        assert me_data["email"] == test_email
        print(f"  [OK] Profile retrieved: {me_data['name']} ({me_data['email']})")

        # 7. List conversations initially
        print("\n[7] Testing GET /api/conversations (empty)...")
        res = await client.get("/api/conversations", headers=auth_headers)
        assert res.status_code == 200
        conv_list = res.json()
        print(f"  [OK] Conversations count: {conv_list['total']}")

        # 8. Chat with Conversation Persistence
        print("\n[8] Testing POST /api/chat with user authentication...")
        res = await client.post("/api/chat", json={
            "message": "I have had a throbbing pain in my right temple for two days."
        }, headers=auth_headers)
        print(f"Status: {res.status_code}")
        assert res.status_code == 200
        chat_data = res.json()
        cid = chat_data["conversation_id"]
        print(f"  [OK] Chat response received. Session ID: {cid}, Response Type: {chat_data['response_type']}")

        # 9. Verify Conversation listed in history
        print("\n[9] Testing GET /api/conversations (persisted session)...")
        res = await client.get("/api/conversations", headers=auth_headers)
        assert res.status_code == 200
        convs = res.json()["conversations"]
        assert len(convs) >= 1
        matched = next((c for c in convs if c["id"] == cid), None)
        assert matched is not None
        print(f"  [OK] Found conversation in history: '{matched['title']}' (messages: {matched['message_count']}, risk: {matched['last_risk_hint']})")

        # 10. Load Conversation Details
        print(f"\n[10] Testing GET /api/conversations/{cid}...")
        res = await client.get(f"/api/conversations/{cid}", headers=auth_headers)
        assert res.status_code == 200
        detail = res.json()
        assert detail["id"] == cid
        assert len(detail["messages"]) >= 2
        print(f"  [OK] Loaded conversation detail with {len(detail['messages'])} messages.")

        # 11. Delete Conversation
        print(f"\n[11] Testing DELETE /api/conversations/{cid}...")
        res = await client.delete(f"/api/conversations/{cid}", headers=auth_headers)
        assert res.status_code == 200
        print("  [OK] Conversation successfully deleted.")

        # Verify deletion in list
        res = await client.get("/api/conversations", headers=auth_headers)
        assert res.status_code == 200
        remaining = res.json()["conversations"]
        assert not any(c["id"] == cid for c in remaining)
        print("  [OK] Verified conversation is no longer in list.")

    print("\n==================================================")
    print("ALL DATABASE & AUTHENTICATION TESTS PASSED!")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(run_tests())
