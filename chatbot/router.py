from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import FileResponse
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from .database import get_chat_history, list_chat_conversations, log_message_to_db

BASE_DIR = Path(__file__).resolve().parent.parent
router = APIRouter()


class ChatRequest(BaseModel):
    message: Annotated[str, Field(min_length=1, max_length=4000)]
    session_id: str | None = None
    user_id: str | None = None


class ChatResponse(BaseModel):
    reply: str
    session_id: str


@router.get("/", include_in_schema=False)
async def home() -> FileResponse:
    return FileResponse(BASE_DIR / "static" / "index.html")


@router.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/api/conversations")
async def conversations(
    user_id: Annotated[str, Query(min_length=1, max_length=255)],
) -> list[dict[str, str]]:
    return await run_in_threadpool(list_chat_conversations, user_id)


@router.get("/api/conversations/{session_id}/messages")
async def conversation_messages(
    session_id: str,
    user_id: Annotated[str, Query(min_length=1, max_length=255)],
) -> dict[str, object]:
    history = await run_in_threadpool(get_chat_history, user_id, session_id)
    if not history:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return {"session_id": session_id, "messages": history}


@router.post("/api/chat", response_model=ChatResponse)
async def chat(http_request: Request, payload: ChatRequest) -> ChatResponse:
    session_id = payload.session_id or str(uuid4())
    user_id = payload.user_id or session_id
    message = payload.message.strip()
    agent_app = http_request.app.state.agent_app

    await run_in_threadpool(log_message_to_db, session_id, user_id, "user", message)

    try:
        result = await run_in_threadpool(
            agent_app.invoke,
            {
                "messages": [HumanMessage(content=message)],
                "user_id": user_id,
                "thread_id": session_id,
            },
            {"configurable": {"thread_id": session_id}},
        )
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"Agent request failed: {error}") from error

    response = result["messages"][-1]
    reply = response.content if isinstance(response.content, str) else str(response.content)
    return ChatResponse(reply=reply, session_id=session_id)
