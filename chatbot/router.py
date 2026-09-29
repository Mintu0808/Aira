from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

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


@router.post("/api/chat", response_model=ChatResponse)
async def chat(http_request: Request, payload: ChatRequest) -> ChatResponse:
    session_id = payload.session_id or str(uuid4())
    user_id = payload.user_id or session_id
    agent_app = http_request.app.state.agent_app

    try:
        result = await run_in_threadpool(
            agent_app.invoke,
            {
                "messages": [HumanMessage(content=payload.message.strip())],
                "user_id": user_id,
            },
            {"configurable": {"thread_id": session_id}},
        )
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"Agent request failed: {error}") from error

    response = result["messages"][-1]
    reply = response.content if isinstance(response.content, str) else str(response.content)
    return ChatResponse(reply=reply, session_id=session_id)
