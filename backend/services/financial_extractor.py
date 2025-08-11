# services/financial_extractor.py
from typing import Optional, Tuple, Dict, Any
import re

from services.scoring_service import FinanceMetrics

_NUM = r"[-+]?\d{1,3}(?:[\.\s]\d{3})*(?:,\d+)?|[-+]?\d+(?:\.\d+)?"

def _to_float(s: Optional[str]) -> Optional[float]:
    if not s:
        return None
    t = s.strip()
    if re.search(r",\d{1,3}$", t):
        t = t.replace(".", "").replace(",", ".")
    else:
        t = t.replace(",", "")
    try:
        return float(t)
    except:
        return None

def _rx(label: str) -> re.Pattern:
    return re.compile(rf"{label}\s*[:\-]?\s*({_NUM})", re.IGNORECASE)

def _search_first(text: str, patterns) -> Optional[float]:
    if isinstance(patterns, (list, tuple)):
        for p in patterns:
            m = p.search(text)
            if m:
                return _to_float(m.group(1))
        return None
    m = patterns.search(text)
    return _to_float(m.group(1)) if m else None

def extract_financial_metrics_from_text(text: str) -> Tuple[FinanceMetrics, Dict[str, Any]]:
    tx = re.sub(r"\u00A0", " ", text)

    # --------- ESTADO DE RESULTADOS ---------
    rx_ingresos = [
        _rx(r"INGRESOS\s+DE\s+ACTIVIDADES\s+ORDINARIAS"),
        _rx(r"\b401\b.*?INGRESOS.*?ORDINARIAS"),
        _rx(r"VENTAS\s+NETAS"),
    ]
    ventas = _search_first(tx, rx_ingresos)

    rx_ganancia_bruta = [
        _rx(r"GANANCIA\s+BRUTA"),
        _rx(r"\b402\b.*?GANANCIA\s+BRUTA"),
    ]
    ganancia_bruta = _search_first(tx, rx_ganancia_bruta)

    # --------- BALANCE ---------
    rx_activo_corriente = [_rx(r"\bACTIVO\s+CORRIENTE\b"), _rx(r"\b101\s*ACTIVO\s+CORRIENTE\b")]
    rx_pasivo_corriente = [_rx(r"\bPASIVO\s+CORRIENTE\b"), _rx(r"\b201\s*PASIVO\s+CORRIENTE\b")]
    rx_total_activo = [_rx(r"^\s*1\s*ACTIVO\s+("+_NUM+")"), _rx(r"\bTOTAL\s+ACTIVO\b")]
    rx_total_pasivo = [_rx(r"^\s*2\s*PASIVO\s+("+_NUM+")"), _rx(r"\bTOTAL\s+PASIVO\b")]

    act_corr = _search_first(tx, rx_activo_corriente)
    pas_corr = _search_first(tx, rx_pasivo_corriente)
    tot_act  = _search_first(tx, rx_total_activo)
    tot_pas  = _search_first(tx, rx_total_pasivo)

    # --------- FLUJOS ---------
    rx_fco = [
        _rx(r"FLUJOS\s+DE\s+EFECTIVO.*?ACTIVIDADES\s+DE\s+OPERACI[ÓO]N"),
        _rx(r"\b9501\b\s*FLUJOS\s+DE\s+EFECTIVO.*OPERACI[ÓO]N"),
        _rx(r"FLUJO\s+DE\s+CAJA\s+OPERATIVO"),
    ]
    fco = _search_first(tx, rx_fco)

    # --------- CÁLCULOS ---------
    margen_bruto = None
    if ventas and ventas != 0 and ganancia_bruta is not None:
        margen_bruto = max(0.0, min(1.0, ganancia_bruta / ventas))

    razon_corriente = None
    if act_corr and pas_corr and pas_corr != 0:
        razon_corriente = act_corr / pas_corr

    deuda_total_activos = None
    if tot_act and tot_act != 0 and tot_pas is not None:
        deuda_total_activos = tot_pas / tot_act

    metrics = FinanceMetrics(
        ventas_anuales=ventas or 0.0,
        margen_bruto=margen_bruto if margen_bruto is not None else 0.22,
        razon_corriente=razon_corriente if razon_corriente is not None else 1.2,
        deuda_total_activos=deuda_total_activos if deuda_total_activos is not None else 0.6,
        flujo_caja_operativo=fco or 0.0,
        # estos campos extra NO están en el modelo de scoring;
        # si los quieres, añádelos allí, o no los devuelvas.
    )

    debug = {
        "confidence": _confidence(metrics, act_corr, pas_corr, tot_act, tot_pas),
        "raw_values": {
            "ingresos": ventas,
            "ganancia_bruta": ganancia_bruta,
            "activo_corriente": act_corr,
            "pasivo_corriente": pas_corr,
            "total_activo": tot_act,
            "total_pasivo": tot_pas,
            "fco": fco,
        },
        "log": {
            "margen_bruto_calc": f"{ganancia_bruta} / {ventas}" if (ganancia_bruta and ventas) else None,
            "razon_corriente_calc": f"{act_corr} / {pas_corr}" if (act_corr and pas_corr) else None,
            "apalancamiento_calc": f"{tot_pas} / {tot_act}" if (tot_act and tot_pas is not None) else None,
        },
        "notes": "Regex ES (401/402/9501 + corrientes + totales). Convierte coma decimal."
    }
    return metrics, debug

def _confidence(m: FinanceMetrics, act_corr, pas_corr, tot_act, tot_pas) -> float:
    score = 0
    if m.ventas_anuales > 0: score += 0.25
    if m.margen_bruto not in (None, 0.22): score += 0.2
    if act_corr and pas_corr: score += 0.25
    if tot_act and tot_pas is not None: score += 0.2
    if m.flujo_caja_operativo != 0: score += 0.1
    return round(score, 2)
