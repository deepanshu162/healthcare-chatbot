import json
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_sample_endpoint():
    print("Testing GET /api/prescription/sample...")
    response = client.get("/api/prescription/sample")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    print("Sample response received successfully!")
    print("Diagnosis problem:", data["diagnosis"]["problem"])
    print("Medicines count:", len(data["medicines"]))
    print("Unclear items count:", len(data["unclear_items"]))
    assert " Amoxicillin" in data["medicines"][0]["medicine_name"] or "Amoxicillin" in data["medicines"][0]["medicine_name"]
    print("Sample test PASSED!\n")


def test_explain_validation():
    print("Testing POST /api/prescription/explain invalid file type...")
    response = client.post(
        "/api/prescription/explain",
        files={"file": ("test.txt", b"some plain text content", "text/plain")}
    )
    assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    print("Validation test PASSED!\n")


if __name__ == "__main__":
    test_sample_endpoint()
    test_explain_validation()
    print("ALL API TESTS PASSED SUCCESSFULLY!")
