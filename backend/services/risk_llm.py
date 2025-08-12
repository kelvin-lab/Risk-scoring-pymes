# services/risk_llm.py
import json, re
from typing import Dict, Any, Optional
from services.ai_analyzer import chat as chat_with_kb

_JSON = re.compile(r"\{[\s\S]*\}", re.MULTILINE)

def llm_assessment_with_ai_analyzer(
    *,
    empresa: Dict[str, Any],
    finanzas,                   # pydantic FinanceMetrics
    scoring: Dict[str, Any],
    signals: Optional[Dict[str, Any]],
    use_kb: bool,
    collection: Optional[str],
    k: int,
    session_id: str
) -> Dict[str, Any]:
    sig = signals or {}
    ms = scoring.get("monto_sugerido", {})
    prompt = f"""
        Eres un analista de crédito. Devuelve SOLO JSON válido con este formato:
        {{
        "top_5": ["<razon 1>", "<razon 2>", "<razon 3>", "<razon 4>", "<razon 5>"],
        "resumen": {{
            "parrafo_1": "<máx ~120 palabras>",
            "parrafo_2": "<máx ~120 palabras>"
        }}
        }}

        Base de análisis (estructura):
        - Empresa: {empresa.get('razon_social')} / {empresa.get('nombre_comercial')}
        - Ventas anuales: {finanzas.ventas_anuales}
        - Margen bruto: {finanzas.margen_bruto}
        - Razón corriente: {finanzas.razon_corriente}
        - Deuda/Activos: {finanzas.deuda_total_activos}
        - Flujo de caja operativo: {finanzas.flujo_caja_operativo}
        - Rating digital (0..5): {sig.get('digital_rating')}
        - Score interno: {scoring.get('score')} ({scoring.get('riesgo')})
        - Monto sugerido (máx): {ms.get('max')}

        Instrucciones:
        1) Prioriza razones cuantitativas y de riesgo crediticio real.
        2) Nada de texto fuera del JSON.
        """.strip()

    res = chat_with_kb(
        session_id=session_id,
        message=prompt,
        use_kb=use_kb,                # si True, usará la KB y fuentes
        collection=collection or "empresas",
        k=k
    )
    content = res.get("answer", "")

    m = _JSON.search(content)
    if not m:
        return {"top_5": [], "resumen": {"parrafo_1": "", "parrafo_2": ""}}

    try:
        data = json.loads(m.group(0))
        top_5 = list(data.get("top_5", []))[:5]
        resumen = data.get("resumen", {}) or {}
        return {
            "top_5": top_5,
            "resumen": {
                "parrafo_1": (resumen.get("parrafo_1") or "")[:1200],
                "parrafo_2": (resumen.get("parrafo_2") or "")[:1200],
            }
        }
    except Exception:
        return {"top_5": [], "resumen": {"parrafo_1": "", "parrafo_2": ""}}
