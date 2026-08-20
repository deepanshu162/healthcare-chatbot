import uuid
import logging
from typing import Dict, List, Optional

logger = logging.getLogger("healthai.conversation_service")


class ConversationService:
    """
    In-memory conversation context management for HealthAI v0.2.
    
    NOTE: In-memory storage is temporary for Milestone 2.
    In a future milestone (Milestone 3), this will be replaced with persistent MongoDB storage.
    """

    def __init__(self, max_history_turns: int = 12):
        # In-memory dictionary: conversation_id -> list of message dictionaries
        self._conversations: Dict[str, List[Dict[str, str]]] = {}
        self._max_history_turns = max_history_turns

    def get_or_create_id(self, conversation_id: Optional[str] = None) -> str:
        """Retrieve existing valid conversation ID or generate a new unique ID."""
        if conversation_id and conversation_id.strip():
            cid = conversation_id.strip()
            if cid not in self._conversations:
                self._conversations[cid] = []
            return cid

        new_id = f"conv_{uuid.uuid4().hex[:12]}"
        self._conversations[new_id] = []
        return new_id

    def get_history(self, conversation_id: str) -> List[Dict[str, str]]:
        """Retrieve conversation history for a given session."""
        return self._conversations.get(conversation_id, []).copy()

    def add_turn(self, conversation_id: str, role: str, content: str) -> None:
        """
        Append a turn (user or assistant) to the conversation history.
        Maintains sliding window to prevent unbounded context growth.
        """
        if conversation_id not in self._conversations:
            self._conversations[conversation_id] = []

        self._conversations[conversation_id].append({
            "role": role,
            "content": content.strip()
        })

        # Apply sliding window pruning
        if len(self._conversations[conversation_id]) > self._max_history_turns:
            self._conversations[conversation_id] = self._conversations[conversation_id][-self._max_history_turns:]

    def clear_conversation(self, conversation_id: str) -> None:
        """Reset or remove a conversation session."""
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]


# Global singleton instance
conversation_service = ConversationService()
