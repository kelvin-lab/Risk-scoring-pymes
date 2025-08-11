from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

# Chat
class ChatRequest(BaseModel):
    session_id: str = Field(..., examples=["demo1"])
    message: str = Field(..., examples=["¿Tienen curso de IA en AWS?"])
    context_override: Optional[str] = Field(None, description="(Opcional) Sobrescribe el prompt de sistema")
    # AUTO‑RAG: None=auto (umbral), True=forzar usar KB, False=sin KB
    use_kb: Optional[bool] = Field(None, description="None=auto, True=forzar KB, False=sin KB")
    collection: str = Field("cursos", description="Colección de Chroma")
    k: int = Field(3, ge=1, le=10, description="Top‑k para retrieval")
class ChatResponse(BaseModel):
    session_id: str
    answer: str
    sources: Optional[List[Dict[str, Any]]] = Field(
        None, description="Fuentes recuperadas cuando se usó KB"
    )
class ResetRequest(BaseModel):
    session_id: str

class StatusResponse(BaseModel):
    sessions: int
