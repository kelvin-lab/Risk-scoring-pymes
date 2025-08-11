from fastapi import APIRouter, HTTPException
from models.schemas import ChatRequest, ChatResponse, ResetRequest, StatusResponse
from services.ai_analyzer import chat, reset_session, sessions_count

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("", response_model=ChatResponse, summary="Enviar mensaje al asistente (auto-RAG)")
def chat_endpoint(req: ChatRequest):
    try:
        result = chat(
            session_id=req.session_id,
            message=req.message,
            context_override=req.context_override,
            use_kb=req.use_kb,          
            collection=req.collection,
            k=req.k
        )
        return ChatResponse(
            session_id=req.session_id,
            answer=result["answer"],
            sources=result["sources"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/reset",
    summary="Reiniciar memoria de una sesión",
    description="Elimina la memoria asociada al `session_id`.",
)
def reset(req: ResetRequest):
    reset_session(req.session_id)
    return {"status": "reset", "session_id": req.session_id}

@router.get(
    "/status",
    response_model=StatusResponse,
    summary="Ver sesiones activas en memoria",
    description="Devuelve el número de sesiones actualmente almacenadas en el servidor.",
)
def status():
    return StatusResponse(sessions=sessions_count())