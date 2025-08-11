from typing import Dict, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config.settings import settings
from services.knowledge_base import _get_vs  # usamos tu mismo acceso a Chroma

# Memoria simple por sesión (historial breve para el RAG)
_rag_history: Dict[str, List] = {}

# Limitamos el contexto para no exceder tokens
_CTX_SPLITTER = RecursiveCharacterTextSplitter(
    chunk_size=1200, chunk_overlap=100, separators=["\n\n", "\n", ". ", " ", ""]
)

SYSTEM_PROMPT = """Eres "AlfaTech", asistente para análisis de riesgo de PYMEs en Ecuador.
Responde con tono formal, claro y empático. Usa SOLO el contexto proporcionado.
Si la respuesta no está en el contexto, di: "No encuentro esa información en la base de conocimiento."
Cuando corresponda, incluye un breve "Próximos pasos". Evita inventar datos."""

def _format_context(docs) -> str:
    # Une los top-k fragmentos y (opcional) recorta si son muy largos
    parts = []
    for i, d in enumerate(docs, start=1):
        txt = d.page_content
        # “sanitizar” largo
        chunks = _CTX_SPLITTER.split_text(txt)
        merged = "\n".join(chunks[:2])  # 2 sub-chunks por doc como tope suave
        src = d.metadata.get("source", f"doc_{i}")
        parts.append(f"[Fuente: {src}]\n{merged}")
    return "\n\n".join(parts)

def rag_answer(
    session_id: str,
    question: str,
    collection: str = "cursos",
    k: int = 3,
) -> dict:
    """
    Recupera top-k del VS, construye prompt con contexto + historial corto y responde.
    Devuelve la respuesta y las fuentes.
    """
    # 1) Recuperación
    vs = _get_vs(collection)
    docs = vs.similarity_search(question, k=k)

    context = _format_context(docs) if docs else ""

    # 2) Modelo de chat
    llm = ChatOpenAI(
        model=settings.MODEL_NAME,
        openai_api_key=settings.OPENAI_API_KEY,
        temperature=settings.TEMPERATURE,
    )

    # 3) Historial por sesión (opcional, breve)
    history = _rag_history.get(session_id, [])[-6:]  # últimos 6 mensajes

    # 4) Construcción de mensajes
    messages = [SystemMessage(content=SYSTEM_PROMPT)]

    # Inyecta historial
    messages.extend(history)

    # Inyecta pregunta con contexto
    human_text = (
        f"Pregunta: {question}\n\n"
        f"=== CONTEXTO ===\n{context if context else '(sin resultados)'}\n"
        f"=== FIN CONTEXTO ===\n\n"
        f"Instrucción: responde SOLO basándote en el contexto. Si el contexto no contiene la respuesta, dilo."
    )
    messages.append(HumanMessage(content=human_text))

    # 5) Invocación
    ai = llm.invoke(messages)

    # 6) Actualiza historial
    history = _rag_history.get(session_id, [])
    history.append(HumanMessage(content=question))
    history.append(AIMessage(content=ai.content))
    _rag_history[session_id] = history

    # 7) Empaqueta fuentes
    sources = []
    for d in docs:
        sources.append({
            "source": d.metadata.get("source"),
            "meta": {k: v for k, v in d.metadata.items() if k != "source"},
            "preview": d.page_content[:300] + ("..." if len(d.page_content) > 300 else "")
        })

    return {
        "answer": ai.content,
        "sources": sources,
        "collection": collection,
        "k": k
    }

def rag_reset(session_id: str) -> None:
    _rag_history.pop(session_id, None)
