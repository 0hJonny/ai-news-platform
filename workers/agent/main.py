from contextlib import asynccontextmanager
import asyncio
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.router import api_v1_router 
from api.health import router as health_router
from utils.logging_config import setup_logging
from storage.postgres_saver import create_postgres_checkpointer
from storage.chroma_client import get_chroma_vectorstore
from core.graph import init_agent_app
from core.config import settings
from core.postgres import db_pool

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Starting application...")

    # Lazy Chroma check
    try:
        await asyncio.to_thread(get_chroma_vectorstore)
        logger.info("Chroma is available.")
    except Exception as e:
        logger.error(f"Failed to connect to Chroma: {e}")
        raise

    # 1. Open the global PostgreSQL pool
    await db_pool.open()
    logger.info("Global PostgreSQL pool opened.")

    try:
        # 2. Pass the pool into the checkpointer and the graph
        async with create_postgres_checkpointer() as checkpointer:
            app.state.graph = await init_agent_app(checkpointer)
            logger.info("Graph and DB ready to serve.")
            yield
    finally:
        # 3. Close the pool when the server shuts down
        await db_pool.close()
        logger.info("Shutting down, pools closed.")

app = FastAPI(lifespan=lifespan)

# origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

app.include_router(health_router)
app.include_router(api_v1_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8082, reload=True)