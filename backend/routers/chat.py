"""Chat route with local RAG context and session memory."""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from services.ai_client import AIClient

router = APIRouter()


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    session_id: str | None = None
    top_k: int = Field(default=4, ge=1, le=10)


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    context_sources: list[str]


def _trim_history(history: list[dict[str, str]], max_messages: int = 12) -> list[dict[str, str]]:
    return history[-max_messages:]


@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, request: Request) -> ChatResponse:
    rag = request.app.state.rag_service
    sessions: dict[str, list[dict[str, str]]] = request.app.state.chat_sessions

    session_id = payload.session_id or str(uuid4())
    history = sessions.get(session_id, [])

    chunks = rag.retrieve(payload.message, top_k=payload.top_k)
    sources = sorted({chunk.source for chunk in chunks})
    context_text = "\n\n".join([f"[{c.source}]\n{c.text}" for c in chunks]) or "No local context found."

    system_prompt = (
        "You are Synthera World assistant. Use retrieved context when relevant. "
        "If context is missing, be explicit and give practical next steps."
    )

    messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
    if history:
        messages.extend(_trim_history(history))
    messages.append(
        {
            "role": "user",
            "content": (
                f"Retrieved context:\n{context_text}\n\n"
                f"User question:\n{payload.message}"
            ),
        }
    )

    client = AIClient()
    try:
        result = await client.complete(messages)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    answer = result.get("content", "").strip()
    if not answer:
        raise HTTPException(status_code=502, detail="Empty chat response from model.")

    new_history = history + [{"role": "user", "content": payload.message}, {"role": "assistant", "content": answer}]
    sessions[session_id] = _trim_history(new_history, max_messages=20)

    return ChatResponse(session_id=session_id, answer=answer, context_sources=sources)
