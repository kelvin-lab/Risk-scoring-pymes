# backend/services/scoring_service.py
from typing import List, Optional
from pydantic import BaseModel

# ---------- Modelos ----------
class Reference(BaseModel):
    nombre: str
    tipo: str                  # "cliente" | "proveedor"
    antiguedad_meses: int
    pago_prom_dias: int        # promedio de atraso en días (<=0 si paga anticipado)
    monto_prom_mensual: float

class FinanceMetrics(BaseModel):
    ventas_anuales: float                  # USD
    margen_bruto: float                    # 0..1
    razon_corriente: float                 # Activo Corriente / Pasivo Corriente
    deuda_total_activos: float             # 0..1 (apalancamiento)
    flujo_caja_operativo: float            # USD (anual o último periodo)

class ScorePayload(BaseModel):
    sector: str
    antiguedad_meses: int
    digital_rating: Optional[float] = None # 0..5 (si no hay redes, None)
    referencias: Optional[List[Reference]] = None
    finanzas: FinanceMetrics

class SimulationPayload(BaseModel):
    ventas_delta_pct: float = 0.0
    reputacion_delta: float = 0.0
    atraso_pago_max_dias: int = 5

def compute_score(p: ScorePayload) -> dict:
    """
    Combina señales financieras + digitales + referencias en un score 0..1.
    Heurística simple para demo; ajusta pesos y tramos según tu apetito de riesgo.
    Además, calcula el monto sugerido considerando ventas, FCO, liquidez y apalancamiento.
    """
    score = 0.0
    factores = []

    # Liquidez
    rc = p.finanzas.razon_corriente or 0.0
    if rc >= 2.0:
        score += 0.30; factores.append(("Liquidez (RC≥2.0)", "+"))
    elif rc >= 1.5:
        score += 0.22; factores.append(("Liquidez (RC 1.5-2.0)", "+"))
    elif rc >= 1.0:
        score += 0.12; factores.append(("Liquidez (RC 1.0-1.5)", "±"))
    else:
        score += 0.04; factores.append(("Liquidez (RC<1.0)", "-"))

    # Margen
    mg = p.finanzas.margen_bruto or 0.0
    if mg >= 0.35:
        score += 0.18; factores.append(("Margen bruto (≥35%)", "+"))
    elif mg >= 0.25:
        score += 0.12; factores.append(("Margen bruto (25-35%)", "+"))
    elif mg >= 0.15:
        score += 0.07; factores.append(("Margen bruto (15-25%)", "±"))
    else:
        score += 0.03; factores.append(("Margen bruto (<15%)", "-"))

    # Apalancamiento
    dta = p.finanzas.deuda_total_activos or 0.0
    if dta <= 0.40:
        score += 0.15; factores.append(("Apalancamiento (≤40%)", "+"))
    elif dta <= 0.60:
        score += 0.08; factores.append(("Apalancamiento (40-60%)", "±"))
    else:
        score += 0.03; factores.append(("Apalancamiento (>60%)", "-"))

    # Flujo operativo
    fco = p.finanzas.flujo_caja_operativo or 0.0
    if fco > 0:
        score += 0.12; factores.append(("Flujo operativo (+)", "+"))
    else:
        score += 0.04; factores.append(("Flujo operativo (−)", "-"))

    # Reputación digital (0..5 → 0..0.10)
    if p.digital_rating is not None:
        score += max(0.0, min(p.digital_rating / 5.0 * 0.10, 0.10))  # escala clara
        factores.append(("Reputación digital", "+" if p.digital_rating >= 4.0 else "±"))

    # Antigüedad (máx 0.10 a 10 años)
    score += min((p.antiguedad_meses or 0) / 120.0, 0.10)
    factores.append(("Antigüedad", "+" if (p.antiguedad_meses or 0) >= 24 else "±"))

    # Referencias (disciplina de pago)
    if p.referencias:
        prom_atraso = sum(r.pago_prom_dias for r in p.referencias) / len(p.referencias)
        if prom_atraso <= 5:
            score += 0.08; factores.append(("Disciplina de pago (≤5 días)", "+"))
        elif prom_atraso <= 15:
            score += 0.04; factores.append(("Disciplina de pago (6-15 días)", "±"))
        else:
            score += 0.01; factores.append(("Disciplina de pago (>15 días)", "-"))

    score = round(min(score, 0.99), 2)
    riesgo = "Bajo" if score >= 0.75 else "Medio" if score >= 0.55 else "Alto"

    # ========= Monto sugerido (nuevo) =========
    ventas = max(0.0, p.finanzas.ventas_anuales or 0.0)

    # base por ventas: 10% si RC<1.0, 20% si RC>=1.0
    base_por_ventas = (0.10 if rc < 1.0 else 0.20) * ventas

    # tope por flujo: no dar más del 40% del FCO anual
    tope_por_fco = 0.40 * max(0.0, fco)

    # si no hay FCO, sé conservador (mitad de la base por ventas)
    monto_bruto = min(base_por_ventas, tope_por_fco) if tope_por_fco > 0 else base_por_ventas * 0.50

    # penalizaciones
    penal = 1.0
    if dta > 0.80:        # apalancamiento muy alto
        penal *= 0.60
    elif dta > 0.65:
        penal *= 0.80
    if rc < 1.0:          # liquidez tensa
        penal *= 0.90

    monto_max = max(0.0, monto_bruto * penal)
    monto_min = 0.25 * monto_max

    def _round_money(x: float) -> int:
        # redondeo a centenas para que sea “bonito”
        return int(round(x, -2)) if x else 0

    rango = {"min": _round_money(monto_min), "max": _round_money(monto_max)}

    return {
        "score": score,
        "riesgo": riesgo,
        "monto_sugerido": rango,
        "factores": factores
    }


def simulate(p: ScorePayload, s: SimulationPayload) -> dict:
    """Aplica cambios simples y recalcula."""
    adj = p.model_copy(deep=True)
    adj.finanzas.ventas_anuales *= (1 + s.ventas_delta_pct / 100.0)
    if adj.digital_rating is not None:
        adj.digital_rating = max(0.0, min(5.0, adj.digital_rating + s.reputacion_delta))
    if adj.referencias:
        for r in adj.referencias:
            r.pago_prom_dias = min(r.pago_prom_dias, s.atraso_pago_max_dias)
    return compute_score(adj)
