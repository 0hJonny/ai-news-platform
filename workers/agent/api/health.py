# api/health.py
import asyncio
import logging

from chromadb import HttpClient
from fastapi import APIRouter, HTTPException
from psycopg import AsyncConnection

from core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


async def check_postgres():
    """Check Postgres with a timeout."""
    try:
        async with asyncio.timeout(3.0):  # Wait at most 3 seconds
            async with await AsyncConnection.connect(settings.postgres_uri) as conn:
                async with conn.cursor() as cur:
                    await cur.execute("SELECT 1")
    except Exception as e:
        logger.error(f"PostgreSQL health check failed: {e}")
        raise HTTPException(status_code=503, detail="PostgreSQL unavailable") from e


async def check_chroma():
    """Check ChromaDB (asynchronously via a thread)."""
    try:

        def _ping():
            client = HttpClient(host=settings.chroma_host, port=settings.chroma_port)
            client.heartbeat()

        async with asyncio.timeout(3.0):
            await asyncio.to_thread(_ping)
    except Exception as e:
        logger.error(f"Chroma health check failed: {e}")
        raise HTTPException(status_code=503, detail="Chroma unavailable") from e


@router.get("/health")
async def health_check():
    # Run the checks in parallel
    await asyncio.gather(check_postgres(), check_chroma())
    return {"status": "ok", "postgres": "connected", "chroma": "connected"}
