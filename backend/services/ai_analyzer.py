from typing import Dict, Optional, List, Tuple
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain.memory import ConversationBufferMemory

from config.settings import settings
from services.knowledge_base import _get_vs

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

    Interpretación del indicador Liquidez corriente:
    ≥ 1.5 → buena liquidez (en general, puede pagar deudas de corto plazo sin problema).
    1.0 a 1.5 → aceptable, pero con poco margen.
    < 1.0 → alerta: no tiene suficientes activos líquidos para cubrir pasivos corrientes.

    Interpretación indicador deuda a patrimonio
    < 1.0 → bajo apalancamiento, la empresa usa más capital propio que deuda.
    1.0 a 2.0 → apalancamiento moderado, habitual en muchas empresas.
    > 2.0 → alto apalancamiento, mayor riesgo financiero.
""".strip()

# Prompt con memoria + 2 variables de entrada: input y context
chat_prompt = ChatPromptTemplate.from_messages([
    ("system", RSP_CONTEXT),
    MessagesPlaceholder(variable_name="history"),
    ("human", "CONTEXTO (si hay):\n{context}\n\nPregunta:\n{input}")
])

# Estado por sesión
_session_llm: Dict[str, ChatOpenAI] = {}
_session_memory: Dict[str, ConversationBufferMemory] = {}

def _get_llm(session_id: str) -> ChatOpenAI:
    if session_id not in _session_llm:
        _session_llm[session_id] = ChatOpenAI(
            model=settings.MODEL_NAME,
            openai_api_key=settings.OPENAI_API_KEY,
            temperature=settings.TEMPERATURE,
        )
    return _session_llm[session_id]

def _get_memory(session_id: str) -> ConversationBufferMemory:
    if session_id not in _session_memory:
        _session_memory[session_id] = ConversationBufferMemory(
            memory_key="history",
            return_messages=True
        )
    return _session_memory[session_id]

def _retrieve_with_scores(question: str, collection: str, k: int):
    vs = _get_vs(collection)
    try:
        results = vs.similarity_search_with_relevance_scores(question, k=k)
        docs_scores = [(doc, float(score)) for (doc, score) in results]
    except Exception:
        docs = vs.similarity_search(question, k=k)
        docs_scores = [(d, 0.0) for d in docs]

    parts, sources = [], []
    best = 0.0
    for i, (d, score) in enumerate(docs_scores, start=1):
        src = d.metadata.get("source", f"doc_{i}")
        preview = d.page_content[:900] + ("..." if len(d.page_content) > 900 else "")
        parts.append(f"[Fuente: {src} | score={round(score,3)}]\n{preview}")
        sources.append({"source": src, "metadata": {k:v for k,v in d.metadata.items() if k!='source'}, "preview": preview, "score": score})
        best = max(best, score)
    return "\n\n".join(parts), sources, best

DEFAULT_THRESHOLD = 0.75

def chat(
    session_id: str,
    message: Optional[str] = None,
    context_override: Optional[str] = None,   # reservado por si luego quieres override
    use_kb: Optional[bool] = None,            # None=AUTO; True/False para forzar
    collection: str = "cursos",
    k: int = 3,
    threshold: float = DEFAULT_THRESHOLD
):
    llm = _get_llm(session_id)
    memory = _get_memory(session_id)

    # Construimos la “cadena” con LCEL (passthroughs para input/context)
    def get_history(_: dict):
        return memory.load_memory_variables({})["history"]

    chain = (
        {
            "history": get_history,          # obtiene historial desde memory
            "input": RunnablePassthrough(),  # pasa tal cual lo que invoquemos
            "context": RunnablePassthrough()
        }
        | chat_prompt
        | llm
        | StrOutputParser()
    )

    context_block = ""
    sources = None
    rationale = "no_kb"

    if use_kb is None or use_kb is True:
        ctx, srcs, best = _retrieve_with_scores(message or "", collection, k)
        if use_kb is True or (srcs and best >= threshold):
            context_block, sources = ctx, srcs
            rationale = f"kb_used (best_score={round(best,3)} >= {threshold})"
        else:
            rationale = f"kb_skipped (best_score={round(best,3)} < {threshold})"

    # 👉 Ahora sí: invocamos con DOS variables sin error
    answer = chain.invoke({"input": message or "", "context": context_block})

    # Guardar en memoria
    memory.save_context({"input": message or ""}, {"output": answer})

    return {
        "answer": answer,
        "sources": sources,
        "mode": ("auto" if use_kb is None else ("forced_kb" if use_kb else "no_kb")),
        "rationale": rationale
    }

def reset_session(session_id: str) -> None:
    _session_llm.pop(session_id, None)
    _session_memory.pop(session_id, None)

def sessions_count() -> int:
    return len(_session_memory)
