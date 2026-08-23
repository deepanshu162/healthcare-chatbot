import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncio
from backend.config import settings
from backend.db.mongodb import db_manager

async def test_live_connection():
    print("==================================================")
    print("Testing Live MongoDB Atlas Cloud Connection...")
    print("==================================================")
    print(f"Connecting to URI: {settings.MONGODB_URI[:35]}...")
    print(f"Database: {settings.MONGODB_DB_NAME}")
    
    success = await db_manager.connect()
    
    if success:
        print("\n[SUCCESS] Successfully connected to MongoDB Atlas!")
        print("  - Ping command returned OK")
        print("  - Collections & Indexes verified on Atlas")
        
        # Test inserting and reading a quick verification ping doc
        test_col = db_manager.db["_connection_test"]
        await test_col.insert_one({"status": "healthy", "timestamp": "now"})
        doc = await test_col.find_one({"status": "healthy"})
        print(f"  - Atlas Read/Write Test: {doc['status']}")
        await test_col.delete_many({})
        print("  - Atlas Cleanup: Completed")
        print("\n==================================================")
        print("Your MongoDB Atlas database is 100% LIVE and ready!")
        print("==================================================")
    else:
        print("\n[ERROR] Connection could not be established.")
        print("Please verify that Network Access in Atlas allows access from anywhere (0.0.0.0/0).")
    
    await db_manager.close()

if __name__ == "__main__":
    asyncio.run(test_live_connection())
