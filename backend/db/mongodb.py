import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from backend.config import settings

logger = logging.getLogger("healthai.db")


class MongoDBManager:
    """Manages asynchronous MongoDB connection lifecycle, collections, and indexes."""

    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self._is_connected: bool = False

    async def connect(self) -> bool:
        """Establish async connection to MongoDB and ensure indexes."""
        uri = settings.MONGODB_URI
        db_name = settings.MONGODB_DB_NAME

        try:
            logger.info(f"Connecting to MongoDB at {uri[:20]}... (DB: {db_name})")
            self.client = AsyncIOMotorClient(
                uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000
            )
            self.db = self.client[db_name]
            
            # Verify connectivity with ping command
            await self.client.admin.command("ping")
            self._is_connected = True
            logger.info("Successfully connected to MongoDB.")

            # Create essential indexes
            await self._init_indexes()
            return True
        except Exception as exc:
            self._is_connected = False
            logger.warning(f"MongoDB connection failed: {exc}. Database persistence will be disabled or fallback mode.")
            return False

    async def close(self) -> None:
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            self._is_connected = False
            logger.info("MongoDB connection closed.")

    async def _init_indexes(self) -> None:
        """Ensure collection indexes exist for optimal query performance."""
        if self.db is None:
            return

        try:
            # Users collection: unique email
            await self.db.users.create_index("email", unique=True)

            # Conversations collection: indexed by user_id and updated_at desc, plus unique id
            await self.db.conversations.create_index("id", unique=True)
            await self.db.conversations.create_index([("user_id", 1), ("updated_at", -1)])

            # Messages collection: indexed by conversation_id and created_at asc
            await self.db.messages.create_index([("conversation_id", 1), ("created_at", 1)])
            logger.info("MongoDB indexes verified/created successfully.")
        except Exception as exc:
            logger.warning(f"Failed to create MongoDB indexes: {exc}")

    def is_connected(self) -> bool:
        """Check if currently connected to MongoDB."""
        return self._is_connected

    def get_database(self) -> Optional[AsyncIOMotorDatabase]:
        """Return active MongoDB database instance."""
        return self.db if self._is_connected else None

    @property
    def users(self):
        return self.db.users if self.db is not None else None

    @property
    def conversations(self):
        return self.db.conversations if self.db is not None else None

    @property
    def messages(self):
        return self.db.messages if self.db is not None else None


db_manager = MongoDBManager()


def get_db() -> Optional[AsyncIOMotorDatabase]:
    """Dependency helper to get active database instance."""
    return db_manager.get_database()
