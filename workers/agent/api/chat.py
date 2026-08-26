import json
import logging
import asyncio
import uuid
from fastapi import APIRouter, HTTPException, Request, Depends
from sse_starlette.sse import EventSourceResponse
from langgraph.graph.state import CompiledStateGraph

from api.schemas import ChatRequest, ChatEvent, FinalAnswer
from api.dependencies import get_graph, get_current_user
from core.config import settings
from core.langfuse_handler import get_langfuse_handler
from repositories.chat_repo import ChatRepository 

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/stream")
async def stream_chat(
    payload: ChatRequest, 
    request: Request,
    graph: CompiledStateGraph = Depends(get_graph),
    user_id: str = Depends(get_current_user)
):
    # 1. Strict validation of the user UUID
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID is required")
        
    try:
        valid_user_id = str(uuid.UUID(str(user_id)))
    except ValueError:
        raise HTTPException(status_code=400, detail="User ID must be a valid UUID")

    # Check that the frontend passed session_id
    if not payload.session_id:
        raise HTTPException(status_code=400, detail="session_id is required. Create a chat in Go first.")

    model_name = settings.ollama_model if settings.llm_provider == "ollama" else settings.lmstudio_model
    repo = ChatRepository(settings.go_chat_service)
    
    # 2. SAVE THE QUESTION RIGHT AWAY (no need to create a session, the frontend already got it from Go)
    try:
        await repo.save_message(
            user_id=valid_user_id,
            session_id=str(payload.session_id),
            role="user",
            content=payload.question
        )
    except Exception as e:
        logger.error(f"Failed to save user message in Go: {e}")
        # If Go responds with 500 (e.g. due to an invalid session_id), we fail here
        raise HTTPException(status_code=500, detail="Failed to save message. Does this session exist?")

    initial_state = {
        "session_id": str(payload.session_id),
        "question": payload.question,
        "current_query": "",
        "intent": "",
        "draft_answer": "",
        "critique": "",
        "final_answer": "",
        "current_step_message": "Инициализация...",
        "error": None,
        "search_count": 0,
        "revision_count": 0,
        "max_results": 3,
        "is_sufficient": False,
        "is_consistent": False,
        "internal_context": [],
        "web_context": []
    }

    config = {"configurable": {"thread_id": str(payload.session_id)}}

    langfuse_handler = get_langfuse_handler()
    if langfuse_handler:
        langfuse_handler.session_id = str(payload.session_id)
        langfuse_handler.user_id = valid_user_id
        config["callbacks"] = [langfuse_handler]

    async def event_generator():
        try:
            yield {"event": "status", "data": ChatEvent(node="start", message="init", model=model_name).model_dump_json()}

            # 1. Set trace_id before the loop so we can capture it on the fly
            trace_id = None

            async for event in graph.astream_events(initial_state, config=config, version="v2"):
                
                # 2. Capture trace_id from the very first event
                if trace_id is None and event["event"] == "on_chain_start":
                    trace_id = event["run_id"]
                    logger.info(f"[{payload.session_id}] Captured Langfuse trace_id: {trace_id}")

                if await request.is_disconnected():
                    logger.info(f"[{payload.session_id}] Client disconnected, stopping stream.")
                    break

                kind = event["event"]

                if kind == "on_chat_model_stream" and "draft_generation" in event.get("tags", []):
                    chunk = event["data"]["chunk"].content
                    if chunk:
                        yield {"event": "token", "data": json.dumps({"text": chunk})}

                elif kind == "on_chain_end":
                    metadata = event.get("metadata", {})
                    if "langgraph_node" in metadata:
                        node_name = event["name"]
                        state_update = event["data"].get("output", {})

                        if isinstance(state_update, dict):
                            if "error" in state_update and state_update["error"]:
                                yield {"event": "error", "data": json.dumps({"detail": state_update["error"]})}
                                return
                            
                            if "current_step_message" in state_update:
                                step_msg = state_update.get("current_step_message", "")
                                chat_event = ChatEvent(node=node_name, message=step_msg, model=model_name)
                                yield {"event": "node_update", "data": chat_event.model_dump_json()}

            if not await request.is_disconnected():
                final_state = await graph.aget_state(config)
                final_text = final_state.values.get("final_answer", "Не удалось сформировать ответ.")
                
                # 4. SAVE TO GO AND GET THE message_id
                message_id = None
                try:
                    # Make sure to pass valid_user_id from Depends
                    saved_msg = await repo.save_message(
                        user_id=valid_user_id,
                        session_id=str(payload.session_id),
                        role="assistant",
                        content=final_text,
                        trace_id=trace_id,
                        meta_data={"model": model_name}
                    )
                    # Extract the created message's ID from the Go response
                    if saved_msg:
                        message_id = saved_msg.get("id")
                except Exception as e:
                    logger.error(f"Failed to save AI message in Go: {e}")

                # 5. RETURN THE FINAL ANSWER WITH message_id AND trace_id
                final_answer = FinalAnswer(
                    session_id=payload.session_id, 
                    answer=final_text, 
                    trace_id=trace_id,
                    message_id=message_id # Make sure this field is added to the FinalAnswer schema!
                )
                yield {"event": "final", "data": final_answer.model_dump_json()}

        except asyncio.CancelledError:
            logger.info(f"[{payload.session_id}] Stream cancelled by client.")
        except Exception as e:
            logger.exception(f"[{payload.session_id}] Stream error")
            # Return the real error so the frontend and logs can see what failed
            yield {"event": "error", "data": json.dumps({"detail": str(e)})} 
        finally:
            if langfuse_handler and settings.langfuse_public_key:
                from langfuse import get_client
                get_client().flush()

    return EventSourceResponse(event_generator())