import logging
import uuid
from fastapi import APIRouter, HTTPException, Depends
from api.schemas import FeedbackRequest
from api.dependencies import get_current_user
from core.config import settings
from langfuse import get_client
from repositories.chat_repo import ChatRepository 

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/feedback")
async def submit_feedback(
    feedback: FeedbackRequest,
    user_id: str = Depends(get_current_user)
):
    # 1. Validate the user
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID is required")
        
    try:
        valid_user_id = str(uuid.UUID(str(user_id)))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid User ID format")

    # 2. Send to LangFuse (if enabled and trace_id is present)
    if settings.langfuse_public_key and feedback.trace_id:
        try:
            client = get_client()
            client.create_score(
                trace_id=str(feedback.trace_id),
                name="user_feedback",
                value=1.0 if feedback.rating == "like" else 0.0,
                data_type="NUMERIC",
                comment=feedback.comment,
            )
            # Force-flush the data to Langfuse
            client.flush()
        except Exception as e:
            # Log it, but don't fail the request if Langfuse is unavailable
            logger.error(f"Langfuse scoring failed: {e}")

    # 3. Save to PostgreSQL via the Go microservice
    try:
        # Pass the Go service URL, not db_pool!
        repo = ChatRepository(settings.go_chat_service) 
        
        await repo.set_feedback(
            user_id=valid_user_id,
            message_id=str(feedback.message_id),
            rating=feedback.rating,
            comment=feedback.comment
        )
        
        logger.info(f"Feedback saved in Go DB: message={feedback.message_id} rating={feedback.rating}")
        return {"status": "ok", "message": "Feedback recorded"}
        
    except Exception as e:
        logger.error(f"Failed to save feedback in Go backend: {e}")
        raise HTTPException(status_code=500, detail="Failed to store feedback in database")