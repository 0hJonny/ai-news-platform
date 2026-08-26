import logging
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from agent.workflow import build_agent_workflow

logger = logging.getLogger(__name__)

async def init_agent_app(checkpointer: AsyncPostgresSaver):
    """
    Infrastructure function: takes the agent's business logic and wraps
    it with state-persistence mechanisms (checkpointer) for FastAPI.
    """
    logger.info("Initializing and compiling the LangGraph agent...")

    # Get the plain graph
    workflow = build_agent_workflow()

    # Compile it with the checkpointer
    app = workflow.compile(checkpointer=checkpointer)

    logger.info("Agent compiled successfully and ready to serve.")
    return app