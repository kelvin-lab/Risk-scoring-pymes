from pydantic import BaseModel, Field
from typing import List, Optional

# Chat
class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=3)
    message: str
class ChatResponse(BaseModel):
    session_id: str
    answer: str

class ResetRequest(BaseModel):
    session_id: str

class StatusResponse(BaseModel):
    sessions: int
