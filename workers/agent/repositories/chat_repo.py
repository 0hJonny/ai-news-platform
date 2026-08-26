import httpx
from typing import Optional, Dict, Any

class ChatRepository:
    def __init__(self, go_backend_url: str):
        self.base_url = go_backend_url.rstrip("/")
        self.timeout = httpx.Timeout(10.0, connect=5.0)

    async def ensure_session(self, session_id: str, user_id: str):
        """
        Creates the session in Go (or makes sure it already exists).
        user_id must be a valid UUID that already exists in auth.users.
        """
        headers = {"X-User-ID": user_id}
        payload = {
            "session_id": session_id,
            # title is optional, the DB defaults to 'New chat'
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/chats/sessions", 
                json=payload, 
                headers=headers
            )
            response.raise_for_status()
            return response.json()

    async def save_message(
        self,
        user_id: str,
        session_id: str,
        role: str, # strictly: 'user', 'assistant', or 'system'
        content: str,
        parent_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        meta_data: Optional[Dict[str, Any]] = None
    ) -> dict:
        
        headers = {"X-User-ID": user_id}
        payload = {
            "session_id": session_id,
            "role": role,
            "content": content,
            "parent_id": parent_id,
            "trace_id": trace_id,
            "meta_data": meta_data or {}
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/chats/messages", 
                json=payload, 
                headers=headers
            )
            response.raise_for_status()
            return response.json()
    
    async def set_feedback(
        self,
        user_id: str,
        message_id: str,
        rating: str,
        comment: Optional[str] = None
    ) -> dict:
        """
        Sends feedback (like/dislike) for an AI message.

        Arguments:
        - user_id: The user's strict UUID (for authorization).
        - message_id: UUID of the message being rated.
        - rating: Strictly 'like' or 'dislike' (matches the DB ENUM).
        - comment: Optional text comment from the user.
        """
        if rating not in ("like", "dislike"):
            raise ValueError("Rating must be exactly 'like' or 'dislike'")

        headers = {"X-User-ID": user_id}
        payload = {
            "message_id": message_id,
            "rating": rating,
            "comment": comment
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # Pay attention to the URL.
            # Make sure this exact route is registered in Go
            response = await client.post(
                f"{self.base_url}/chats/feedback", 
                json=payload, 
                headers=headers
            )
            
            response.raise_for_status()
            return response.json()