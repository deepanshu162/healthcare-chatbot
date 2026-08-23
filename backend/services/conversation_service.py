import re
import uuid
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.db.mongodb import db_manager
from backend.models.conversation_models import (
    ConversationDetail,
    ConversationSummary,
    MessageRecord,
)

logger = logging.getLogger("healthai.conversation_service")


class ConversationService:
    """
    Persistent MongoDB conversation management for HealthAI v0.3 / Milestone 3.
    Includes in-memory cache layer for low latency and multi-turn context retention.
    """

    def __init__(self, max_history_turns: int = 12):
        self._max_history_turns = max_history_turns
        # In-memory sliding window cache: conversation_id -> list of turn dicts
        self._memory_cache: Dict[str, List[Dict[str, str]]] = {}

    def _generate_title_from_text(self, text: str) -> str:
        """Create a clean, human-readable conversation title from user's first input."""
        cleaned = text.strip().replace("\n", " ")
        cleaned = re.sub(r"\s+", " ", cleaned)
        if len(cleaned) <= 38:
            return cleaned.rstrip(".!?,")
        return cleaned[:35].rstrip(".!?,") + "..."

    async def get_or_create_id(
        self,
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        initial_title: Optional[str] = None
    ) -> str:
        """Retrieve existing conversation session ID or initialize a new persistent session."""
        now_iso = datetime.utcnow().isoformat()

        if conversation_id and conversation_id.strip():
            cid = conversation_id.strip()
            # If MongoDB is connected, ensure conversation document exists or associate user_id
            if db_manager.is_connected() and db_manager.conversations is not None:
                existing = await db_manager.conversations.find_one({"id": cid})
                if existing:
                    # Update user_id if newly authenticated
                    if user_id and not existing.get("user_id"):
                        await db_manager.conversations.update_one(
                            {"id": cid},
                            {"$set": {"user_id": user_id, "updated_at": now_iso}}
                        )
                    return cid
                else:
                    # Insert record for existing ID
                    title = initial_title or "New Assessment"
                    await db_manager.conversations.insert_one({
                        "id": cid,
                        "user_id": user_id,
                        "title": title,
                        "message_count": 0,
                        "last_risk_hint": "unknown",
                        "created_at": now_iso,
                        "updated_at": now_iso
                    })
                    return cid
            return cid

        # Generate fresh conversation ID
        new_id = f"conv_{uuid.uuid4().hex[:12]}"
        title = initial_title or "New Assessment"

        if db_manager.is_connected() and db_manager.conversations is not None:
            try:
                await db_manager.conversations.insert_one({
                    "id": new_id,
                    "user_id": user_id,
                    "title": title,
                    "message_count": 0,
                    "last_risk_hint": "unknown",
                    "created_at": now_iso,
                    "updated_at": now_iso
                })
            except Exception as exc:
                logger.warning(f"Failed to persist new conversation {new_id}: {exc}")

        self._memory_cache[new_id] = []
        return new_id

    async def get_history(self, conversation_id: str) -> List[Dict[str, str]]:
        """
        Retrieve formatted conversation history for Gemini AI context window.
        Returns list of dicts: [{"role": "user"|"assistant", "content": "..."}]
        """
        # If cached in memory, return sliding window
        if conversation_id in self._memory_cache and self._memory_cache[conversation_id]:
            return self._memory_cache[conversation_id].copy()

        # If not in cache but DB is available, retrieve from messages collection
        if db_manager.is_connected() and db_manager.messages is not None:
            try:
                cursor = db_manager.messages.find(
                    {"conversation_id": conversation_id}
                ).sort("created_at", 1)
                
                messages = await cursor.to_list(length=100)
                history = [{"role": m["role"], "content": m["content"]} for m in messages]
                
                # Apply sliding window
                sliding = history[-self._max_history_turns:] if len(history) > self._max_history_turns else history
                self._memory_cache[conversation_id] = sliding
                return sliding.copy()
            except Exception as exc:
                logger.warning(f"Error loading history from MongoDB for {conversation_id}: {exc}")

        return self._memory_cache.get(conversation_id, []).copy()

    async def add_turn(
        self,
        conversation_id: str,
        role: str,
        content: str,
        response_type: Optional[str] = None,
        questions: Optional[List[Any]] = None,
        risk_hint: Optional[str] = None,
        clinical_note: Optional[Any] = None,
        user_id: Optional[str] = None
    ) -> None:
        """
        Persist a conversation turn to MongoDB and update cache sliding window.
        """
        now_iso = datetime.utcnow().isoformat()
        msg_id = f"msg_{uuid.uuid4().hex[:12]}"

        # 1. Update in-memory sliding window cache
        if conversation_id not in self._memory_cache:
            self._memory_cache[conversation_id] = []

        self._memory_cache[conversation_id].append({
            "role": role,
            "content": content.strip()
        })

        if len(self._memory_cache[conversation_id]) > self._max_history_turns:
            self._memory_cache[conversation_id] = self._memory_cache[conversation_id][-self._max_history_turns:]

        # 2. Persist to MongoDB
        if db_manager.is_connected() and db_manager.messages is not None and db_manager.conversations is not None:
            try:
                # Prepare message document
                questions_data = []
                if questions:
                    for q in questions:
                        if hasattr(q, "model_dump"):
                            questions_data.append(q.model_dump())
                        elif isinstance(q, dict):
                            questions_data.append(q)
                        elif isinstance(q, str):
                            questions_data.append({"question": q, "options": []})

                clinical_note_data = None
                if clinical_note:
                    if hasattr(clinical_note, "model_dump"):
                        clinical_note_data = clinical_note.model_dump()
                    elif isinstance(clinical_note, dict):
                        clinical_note_data = clinical_note

                msg_doc = {
                    "id": msg_id,
                    "conversation_id": conversation_id,
                    "role": role,
                    "content": content.strip(),
                    "response_type": response_type,
                    "questions": questions_data,
                    "risk_hint": risk_hint or "unknown",
                    "clinical_note": clinical_note_data,
                    "created_at": now_iso
                }
                await db_manager.messages.insert_one(msg_doc)

                # Update conversation document
                conv = await db_manager.conversations.find_one({"id": conversation_id})
                update_fields: Dict[str, Any] = {
                    "updated_at": now_iso,
                    "last_risk_hint": risk_hint or (conv.get("last_risk_hint") if conv else "unknown")
                }
                if clinical_note_data:
                    update_fields["last_clinical_note"] = clinical_note_data
                if user_id:
                    update_fields["user_id"] = user_id

                # If first user message, generate title
                if conv and (conv.get("title") == "New Assessment" or not conv.get("title")) and role == "user":
                    update_fields["title"] = self._generate_title_from_text(content)

                await db_manager.conversations.update_one(
                    {"id": conversation_id},
                    {
                        "$set": update_fields,
                        "$inc": {"message_count": 1}
                    },
                    upsert=True
                )
            except Exception as exc:
                logger.warning(f"Error persisting turn for {conversation_id} in MongoDB: {exc}")

    async def list_user_conversations(self, user_id: Optional[str]) -> List[ConversationSummary]:
        """Fetch all conversation sessions for a user or anonymous sessions."""
        if not db_manager.is_connected() or db_manager.conversations is None:
            return []

        query = {"user_id": user_id} if user_id else {"user_id": None}
        try:
            cursor = db_manager.conversations.find(query).sort("updated_at", -1)
            docs = await cursor.to_list(length=100)
            
            results = []
            for d in docs:
                results.append(ConversationSummary(
                    id=d["id"],
                    user_id=d.get("user_id"),
                    title=d.get("title", "Assessment"),
                    message_count=d.get("message_count", 0),
                    last_risk_hint=d.get("last_risk_hint", "unknown"),
                    created_at=d.get("created_at", datetime.utcnow().isoformat()),
                    updated_at=d.get("updated_at", datetime.utcnow().isoformat())
                ))
            return results
        except Exception as exc:
            logger.warning(f"Error listing user conversations: {exc}")
            return []

    async def get_conversation_detail(self, conversation_id: str, user_id: Optional[str] = None) -> Optional[ConversationDetail]:
        """Retrieve complete conversation with all associated messages and clinical summary."""
        if not db_manager.is_connected() or db_manager.conversations is None or db_manager.messages is None:
            # Fallback from memory if not in DB
            if conversation_id in self._memory_cache:
                msgs = [
                    MessageRecord(
                        conversation_id=conversation_id,
                        role=m["role"],
                        content=m["content"],
                        created_at=datetime.utcnow().isoformat()
                    )
                    for m in self._memory_cache[conversation_id]
                ]
                return ConversationDetail(
                    id=conversation_id,
                    user_id=user_id,
                    title="Assessment",
                    created_at=datetime.utcnow().isoformat(),
                    updated_at=datetime.utcnow().isoformat(),
                    messages=msgs
                )
            return None

        conv_doc = await db_manager.conversations.find_one({"id": conversation_id})
        if not conv_doc:
            return None

        # Check authorization if session belongs to another user
        if conv_doc.get("user_id") and user_id and conv_doc.get("user_id") != user_id:
            return None

        # Fetch messages
        cursor = db_manager.messages.find({"conversation_id": conversation_id}).sort("created_at", 1)
        msg_docs = await cursor.to_list(length=200)

        message_records = []
        last_note = conv_doc.get("last_clinical_note")

        for m in msg_docs:
            note = m.get("clinical_note")
            if note:
                last_note = note
            message_records.append(MessageRecord(
                id=m.get("id"),
                conversation_id=m["conversation_id"],
                role=m["role"],
                content=m["content"],
                response_type=m.get("response_type"),
                questions=m.get("questions", []),
                risk_hint=m.get("risk_hint"),
                clinical_note=note,
                created_at=m.get("created_at", datetime.utcnow().isoformat())
            ))

        return ConversationDetail(
            id=conv_doc["id"],
            user_id=conv_doc.get("user_id"),
            title=conv_doc.get("title", "Assessment"),
            last_clinical_note=last_note,
            created_at=conv_doc.get("created_at", datetime.utcnow().isoformat()),
            updated_at=conv_doc.get("updated_at", datetime.utcnow().isoformat()),
            messages=message_records
        )

    async def delete_conversation(self, conversation_id: str, user_id: Optional[str] = None) -> bool:
        """Delete a conversation session and all its messages."""
        if conversation_id in self._memory_cache:
            del self._memory_cache[conversation_id]

        if not db_manager.is_connected() or db_manager.conversations is None:
            return True

        query: Dict[str, Any] = {"id": conversation_id}
        if user_id:
            query["user_id"] = user_id

        result = await db_manager.conversations.delete_one(query)
        if result.deleted_count > 0 and db_manager.messages is not None:
            await db_manager.messages.delete_many({"conversation_id": conversation_id})
            return True
        return False

    async def clear_all_user_conversations(self, user_id: str) -> int:
        """Delete all conversations belonging to a user."""
        if not db_manager.is_connected() or db_manager.conversations is None:
            return 0

        # Find user conversations
        cursor = db_manager.conversations.find({"user_id": user_id}, {"id": 1})
        convs = await cursor.to_list(length=500)
        cids = [c["id"] for c in convs]

        for cid in cids:
            if cid in self._memory_cache:
                del self._memory_cache[cid]

        del_result = await db_manager.conversations.delete_many({"user_id": user_id})
        if cids and db_manager.messages is not None:
            await db_manager.messages.delete_many({"conversation_id": {"$in": cids}})

        return del_result.deleted_count


# Global singleton instance
conversation_service = ConversationService()
