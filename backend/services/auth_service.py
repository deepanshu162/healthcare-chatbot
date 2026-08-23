import uuid
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from backend.config import settings
from backend.db.mongodb import db_manager

logger = logging.getLogger("healthai.auth")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


class AuthService:
    """Handles authentication, password hashing, JWT tokens, and user persistence."""

    def hash_password(self, password: str) -> str:
        """Hash a plaintext password with bcrypt salt."""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify plaintext password against bcrypt hash."""
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"),
                hashed_password.encode("utf-8")
            )
        except Exception:
            return False

    def create_access_token(self, user_id: str, email: str) -> str:
        """Create signed JWT access token with expiration."""
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {
            "sub": user_id,
            "email": email,
            "exp": expire,
            "iat": datetime.utcnow()
        }
        encoded_jwt = jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt

    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Decode and validate a JWT access token."""
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            return payload
        except jwt.PyJWTError as exc:
            logger.debug(f"JWT decode error: {exc}")
            return None

    async def register_user(self, name: str, email: str, password: str) -> Dict[str, Any]:
        """Register a new user account in MongoDB."""
        if not db_manager.is_connected() or db_manager.users is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database is not available. Please ensure MongoDB is running."
            )

        # Check for existing email
        normalized_email = email.strip().lower()
        existing = await db_manager.users.find_one({"email": normalized_email})
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email address already exists."
            )

        user_id = f"usr_{uuid.uuid4().hex[:12]}"
        password_hash = self.hash_password(password)
        now_iso = datetime.utcnow().isoformat()

        user_doc = {
            "id": user_id,
            "name": name.strip(),
            "email": normalized_email,
            "password_hash": password_hash,
            "created_at": now_iso,
            "updated_at": now_iso
        }

        await db_manager.users.insert_one(user_doc)
        logger.info(f"Registered new user {user_id} ({normalized_email})")

        return {
            "id": user_id,
            "name": user_doc["name"],
            "email": normalized_email,
            "created_at": now_iso
        }

    async def authenticate_user(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate user credentials and return user info."""
        if not db_manager.is_connected() or db_manager.users is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database is not available. Please ensure MongoDB is running."
            )

        normalized_email = email.strip().lower()
        user_doc = await db_manager.users.find_one({"email": normalized_email})
        if not user_doc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password."
            )

        if not self.verify_password(password, user_doc.get("password_hash", "")):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password."
            )

        return {
            "id": user_doc["id"],
            "name": user_doc.get("name", "User"),
            "email": user_doc["email"],
            "created_at": user_doc.get("created_at")
        }

    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve user profile by ID."""
        if not db_manager.is_connected() or db_manager.users is None:
            return None

        user_doc = await db_manager.users.find_one({"id": user_id})
        if not user_doc:
            return None

        return {
            "id": user_doc["id"],
            "name": user_doc.get("name", "User"),
            "email": user_doc["email"],
            "created_at": user_doc.get("created_at")
        }


auth_service = AuthService()


async def get_optional_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[Dict[str, Any]]:
    """FastAPI dependency to optionally authenticate user from Authorization Bearer header."""
    if not token:
        return None

    payload = auth_service.decode_token(token)
    if not payload:
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    user = await auth_service.get_user_by_id(user_id)
    return user


async def get_current_user(user: Optional[Dict[str, Any]] = Depends(get_optional_current_user)) -> Dict[str, Any]:
    """FastAPI dependency requiring valid authenticated user."""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided or are invalid.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user
