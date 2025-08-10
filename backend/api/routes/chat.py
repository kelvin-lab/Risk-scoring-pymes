from fastapi import APIRouter, HTTPException
from models.schemas import ChatRequest, ChatResponse, ResetRequest, StatusResponse
from services.ai_analyzer import chat, reset_session, sessions_count

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    try:
        answer = chat(req.session_id, req.message)
        return ChatResponse(session_id=req.session_id, answer=answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reset")
def reset(req: ResetRequest):
    reset_session(req.session_id)
    return {"status": "reset", "session_id": req.session_id}

@router.get("/status", response_model=StatusResponse)
def status():
    return StatusResponse(sessions=sessions_count())