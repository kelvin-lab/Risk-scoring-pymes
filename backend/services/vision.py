# backend/services/vision.py
import base64
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from config.settings import settings

def _encode_image_to_b64(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")

def analyze_image_bytes(image_bytes: bytes, prompt: str) -> str:
    b64 = _encode_image_to_b64(image_bytes)
    mensaje = HumanMessage(
        content=[
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
        ]
    )
    llm = ChatOpenAI(
        model=getattr(settings, "MODEL_NAME_VISION", settings.MODEL_NAME),
        openai_api_key=settings.OPENAI_API_KEY,
        temperature=0.2,
    )
    resp = llm.invoke([mensaje])
    return resp.content

def analyze_image_path(image_path: str, prompt: str) -> str:
    with open(image_path, "rb") as f:
        return analyze_image_bytes(f.read(), prompt)
