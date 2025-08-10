import base64

from typing import Dict, Optional
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage

from config.settings import settings

RSP_CONTEXT = """
Eres un asistente virtual llamado "AlfaTech", especializado en apoyar el análisis de riesgo financiero
de pequeñas y medianas empresas (PYMEs) en Ecuador, utilizando datos no tradicionales como comportamiento digital,
referencias comerciales y actividad en redes sociales.

Reglas y comportamiento:
1. Mantén un tono formal, claro y empático, transmitiendo confianza y profesionalismo.
2. Utiliza un lenguaje accesible para personas que no son expertas en finanzas, pero sin perder rigor técnico.
3. Guía al usuario paso a paso para recopilar la información necesaria: estados financieros, redes sociales, referencias comerciales.
4. Puedes hacer preguntas aclaratorias para obtener datos más precisos.
5. No respondas consultas fuera del alcance del análisis de riesgo para PYMEs.
6. Explica brevemente cómo cada dato será usado en la evaluación de riesgo.
7. Ofrece siempre un resumen de próximos pasos y estado de la solicitud.
8. Usa ocasionalmente emojis relacionados con finanzas 📊💼💡 para humanizar la interacción.
""".strip()


chat_prompt = ChatPromptTemplate.from_messages([
    ("system", RSP_CONTEXT),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}")
])

#sesiones
_session_storage: Dict[str, LLMChain] = {}

def get_chain(session_id: str) -> LLMChain:
    if session_id in _session_storage:
        return _session_storage[session_id]

    llm = ChatOpenAI(
        model=settings.MODEL_NAME,
        openai_api_key=settings.OPENAI_API_KEY,
        temperature=settings.TEMPERATURE,
    )

    memory = ConversationBufferMemory(
        memory_key="history",
        return_messages=True
    )

    chain = LLMChain(
        llm=llm,
        prompt=chat_prompt,
        memory=memory,
        verbose=False
    )
    _session_storage[session_id] = chain
    return chain

def chat(session_id: str, message: Optional[str] = None) -> str:
    chain = get_chain(session_id)
    return chain.predict(input=message or "")

def reset_session(session_id: str) -> None:
    _session_storage.pop(session_id, None)

def sessions_count() -> int:
    return len(_session_storage)


def _encode_image_to_b64(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")

def analyze_image_bytes(image_bytes: bytes, prompt: str) -> str:
    """
    Analiza una imagen (bytes) con un modelo vision de OpenAI usando LangChain.
    Retorna el texto de respuesta del modelo.
    """
    b64 = _encode_image_to_b64(image_bytes)

    mensaje = HumanMessage(
        content=[
            {"type": "text", "text": prompt},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
            },
        ]
    )

    vision_model = getattr(settings, "MODEL_NAME_VISION", settings.MODEL_NAME)
    llm = ChatOpenAI(
        model=vision_model,                      
        openai_api_key=settings.OPENAI_API_KEY,
        temperature=0.2,
    )

    resp = llm.invoke([mensaje])
    return resp.content

def analyze_image_path(image_path: str, prompt: str) -> str:
    with open(image_path, "rb") as f:
        return analyze_image_bytes(f.read(), prompt)
