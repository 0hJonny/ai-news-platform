from fastapi import Request, Header
from langgraph.graph.state import CompiledStateGraph

def get_graph(request: Request) -> CompiledStateGraph:
    """Extracts the compiled graph from the application state."""
    return request.app.state.graph

def get_current_user(x_user_id: str | None = Header(default=None, alias="X-User-Id")) -> str:
    """
    Extracts the user ID from the header.
    """
    return x_user_id or "anonymous"