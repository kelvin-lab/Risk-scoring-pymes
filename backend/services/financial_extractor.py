# services/financial_extractor.py
from typing import Optional, Tuple, Dict, Any
import re

from services.scoring_service import FinanceMetrics

_NUM = r"[-+]?\d+(?:[\.,]\d+)?(?:\.\d+)?|[-+]?\d{1,3}(?:[\.,]\d{3})*(?:[\.,]\d+)?"

def _to_float(s: Optional[str]) -> Optional[float]:
    if not s:
        return None
    
    original = s
    t = s.strip()
    
    # Eliminar espacios entre dígitos si existen
    t = re.sub(r'\s+(?=\d)', '', t)
    
    # Verificar si el número tiene formato con punto como separador de miles y coma decimal
    # Ejemplo: 19.308.186,80
    if re.search(r'\d{1,3}(\.\d{3})+,\d+$', t):
        # Reemplazar puntos (separadores de miles) por nada y coma por punto
        t = t.replace(".", "").replace(",", ".")
    
    # Verificar si el número tiene formato con coma como separador de miles y punto decimal
    # Ejemplo: 19,308,186.80
    elif re.search(r'\d{1,3}(,\d{3})+\.\d+$', t):
        # Reemplazar comas (separadores de miles) por nada
        t = t.replace(",", "")
    
    # Verificar si el número solo tiene coma como decimal sin separadores de miles
    # Ejemplo: 19308186,80
    elif re.search(r'\d+,\d+$', t):
        # Reemplazar coma por punto
        t = t.replace(",", ".")
    
    # Verificar si el número solo tiene separadores de miles sin decimales
    # Ejemplo: 19.308.186 o 19,308,186
    elif re.search(r'\d{1,3}([\.,]\d{3})+$', t):
        # Eliminar todos los separadores
        t = t.replace(".", "").replace(",", "")
    
    # Si es un número simple sin separadores, dejarlo como está
    
    print(f"[LOG] Convirtiendo valor: '{original}' -> '{t}'")
    try:
        return float(t)
    except Exception as e:
        print(f"[LOG] Error al convertir '{original}' a float: {str(e)}")
        return None

def _rx(label: str) -> re.Pattern:
    return re.compile(rf"{label}\s*[:\-]?\s*({_NUM})", re.IGNORECASE)

def _search_first(text: str, patterns, field_name="") -> Optional[float]:
    if isinstance(patterns, (list, tuple)):
        for i, p in enumerate(patterns):
            m = p.search(text)
            if m:
                value = _to_float(m.group(1))
                print(f"[LOG] Campo encontrado: {field_name} - Patrón #{i+1} - Valor extraído: {value} - Texto: {m.group(0)}")
                return value
        print(f"[LOG] Campo NO encontrado: {field_name} - Se probaron {len(patterns)} patrones")
        return None
    m = patterns.search(text)
    if m:
        value = _to_float(m.group(1))
        print(f"[LOG] Campo encontrado: {field_name} - Valor extraído: {value} - Texto: {m.group(0)}")
        return value
    print(f"[LOG] Campo NO encontrado: {field_name}")
    return None

def extract_financial_metrics_from_text(text: str) -> Tuple[FinanceMetrics, Dict[str, Any]]:
    tx = re.sub(r"\u00A0", " ", text)

    print("\n[LOG] Iniciando extracción de métricas financieras...")
    
    # --------- ESTADO DE RESULTADOS ---------
    # Patrones mejorados para capturar ingresos/ventas
    rx_ingresos = [
        re.compile(rf"401\s*INGRESOS\s+DE\s+ACTIVIDADES\s+ORDINARIAS\s*[:\-]?\s*({_NUM})", re.IGNORECASE),
        re.compile(rf"\b401\b\s*[:\-]?\s*({_NUM})", re.IGNORECASE),
        re.compile(rf"INGRESOS\s+DE\s+ACTIVIDADES\s+ORDINARIAS\s*[:\-]?\s*({_NUM})", re.IGNORECASE),
        _rx(r"VENTAS\s+NETAS"),
        _rx(r"INGRESOS\s+NETOS"),
        _rx(r"INGRESOS\s+TOTALES"),
        _rx(r"TOTAL\s+INGRESOS"),
        _rx(r"VENTAS\s+TOTALES"),
        _rx(r"TOTAL\s+VENTAS"),
        re.compile(rf"401[\s\w]*?[:\-]?\s*({_NUM})", re.IGNORECASE),
        re.compile(rf"INGRESOS[\s\w]*?[:\-]?\s*({_NUM})", re.IGNORECASE),
        re.compile(rf"VENTAS[\s\w]*?[:\-]?\s*({_NUM})", re.IGNORECASE),
    ]
    print("\n[LOG] Buscando ingresos/ventas...")
    ventas = _search_first(tx, rx_ingresos, "ingresos/ventas")

    # Patrones mejorados para capturar ganancia bruta
    rx_ganancia_bruta = [
        re.compile(rf"402\s*GANANCIA\s+BRUTA\s*[:\-]?\s*({_NUM})", re.IGNORECASE),
        re.compile(rf"\b402\b\s*[:\-]?\s*({_NUM})", re.IGNORECASE),
        re.compile(rf"GANANCIA\s+BRUTA\s*[:\-]?\s*({_NUM})", re.IGNORECASE),
        re.compile(rf"UTILIDAD\s+BRUTA\s*[:\-]?\s*({_NUM})", re.IGNORECASE),
        re.compile(rf"MARGEN\s+BRUTO\s*[:\-]?\s*({_NUM})", re.IGNORECASE),
        re.compile(rf"402[\s\w]*?[:\-]?\s*({_NUM})", re.IGNORECASE),
        re.compile(rf"GANANCIA\s+BRUTA[\s\w]*?[:\-]?\s*({_NUM})", re.IGNORECASE),
        re.compile(rf"UTILIDAD\s+BRUTA[\s\w]*?[:\-]?\s*({_NUM})", re.IGNORECASE),
    ]
    print("\n[LOG] Buscando ganancia bruta...")
    ganancia_bruta = _search_first(tx, rx_ganancia_bruta, "ganancia_bruta")

    # --------- BALANCE ---------
    # Patrones mejorados para capturar activo corriente
    rx_activo_corriente = [
        re.compile(rf"101\s*ACTIVO\s+CORRIENTE\s*[:\-]?\s*({_NUM})", re.IGNORECASE),
        re.compile(rf"\b101\b\s*[:\-]?\s*({_NUM})", re.IGNORECASE),
        re.compile(rf"ACTIVO\s+CORRIENTE\s*[:\-]?\s*({_NUM})", re.IGNORECASE),
        re.compile(rf"ACTIVOS\s+CORRIENTES\s*[:\-]?\s*({_NUM})", re.IGNORECASE),
        re.compile(rf"101[\s\w]*?[:\-]?\s*({_NUM})", re.IGNORECASE),
        re.compile(rf"ACTIVO\s+CORRIENTE[\s\w]*?[:\-]?\s*({_NUM})", re.IGNORECASE),
    ]

    # Patrones mejorados para capturar pasivo corriente
    rx_pasivo_corriente = [
        re.compile(rf"201\s*PASIVO\s+CORRIENTE\s*[:\-]?\s*({_NUM})", re.IGNORECASE),
        re.compile(rf"\b201\b\s*[:\-]?\s*({_NUM})", re.IGNORECASE),
        re.compile(rf"PASIVO\s+CORRIENTE\s*[:\-]?\s*({_NUM})", re.IGNORECASE),
        re.compile(rf"PASIVOS\s+CORRIENTES\s*[:\-]?\s*({_NUM})", re.IGNORECASE),
        re.compile(rf"201[\s\w]*?[:\-]?\s*({_NUM})", re.IGNORECASE),
        re.compile(rf"PASIVO\s+CORRIENTE[\s\w]*?[:\-]?\s*({_NUM})", re.IGNORECASE),
    ]

    # Patrones mejorados para capturar total activo
    rx_total_activo = [
        re.compile(rf"1\s*ACTIVO\s*[:\-]?\s*({_NUM})", re.IGNORECASE),
        re.compile(rf"\b1\b\s*ACTIVO\s*[:\-]?\s*({_NUM})", re.IGNORECASE),
        re.compile(rf"\bTOTAL\s+ACTIVO\b\s*[:\-]?\s*({_NUM})", re.IGNORECASE),
        re.compile(rf"ACTIVOS\s+TOTALES\s*[:\-]?\s*({_NUM})", re.IGNORECASE),
        re.compile(rf"TOTAL\s+DE\s+ACTIVOS\s*[:\-]?\s*({_NUM})", re.IGNORECASE),
        re.compile(rf"1[\s\w]*?ACTIVO[\s\w]*?[:\-]?\s*({_NUM})", re.IGNORECASE),
        re.compile(rf"TOTAL\s+ACTIVO[\s\w]*?[:\-]?\s*({_NUM})", re.IGNORECASE),
    ]

    # Patrones mejorados para capturar total pasivo
    rx_total_pasivo = [
        re.compile(rf"2\s*PASIVO\s*[:\-]?\s*({_NUM})", re.IGNORECASE),
        re.compile(rf"\b2\b\s*PASIVO\s*[:\-]?\s*({_NUM})", re.IGNORECASE),
        re.compile(rf"\bTOTAL\s+PASIVO\b\s*[:\-]?\s*({_NUM})", re.IGNORECASE),
        re.compile(rf"PASIVOS\s+TOTALES\s*[:\-]?\s*({_NUM})", re.IGNORECASE),
        re.compile(rf"TOTAL\s+DE\s+PASIVOS\s*[:\-]?\s*({_NUM})", re.IGNORECASE),
        re.compile(rf"2[\s\w]*?PASIVO[\s\w]*?[:\-]?\s*({_NUM})", re.IGNORECASE),
        re.compile(rf"TOTAL\s+PASIVO[\s\w]*?[:\-]?\s*({_NUM})", re.IGNORECASE),
    ]

    print("\n[LOG] Buscando activo corriente...")
    act_corr = _search_first(tx, rx_activo_corriente, "activo_corriente")
    print("\n[LOG] Buscando pasivo corriente...")
    pas_corr = _search_first(tx, rx_pasivo_corriente, "pasivo_corriente")
    print("\n[LOG] Buscando total activo...")
    tot_act  = _search_first(tx, rx_total_activo, "total_activo")
    print("\n[LOG] Buscando total pasivo...")
    tot_pas  = _search_first(tx, rx_total_pasivo, "total_pasivo")

    # --------- FLUJOS ---------
    # Patrones mejorados para capturar flujo de caja operativo
    rx_fco = [
        re.compile(rf"9501\s*FLUJOS\s+DE\s+EFECTIVO.*?ACTIVIDADES\s+DE\s+OPERACI[ÓO]N\s*[:\-]?\s*({_NUM})", re.IGNORECASE),
        re.compile(rf"\b9501\b\s*[:\-]?\s*({_NUM})", re.IGNORECASE),
        re.compile(rf"FLUJOS\s+DE\s+EFECTIVO.*?ACTIVIDADES\s+DE\s+OPERACI[ÓO]N\s*[:\-]?\s*({_NUM})", re.IGNORECASE),
        re.compile(rf"FLUJO\s+DE\s+CAJA\s+OPERATIVO\s*[:\-]?\s*({_NUM})", re.IGNORECASE),
        re.compile(rf"FLUJO\s+OPERATIVO\s*[:\-]?\s*({_NUM})", re.IGNORECASE),
        re.compile(rf"EFECTIVO\s+GENERADO\s+POR\s+OPERACIONES\s*[:\-]?\s*({_NUM})", re.IGNORECASE),
        re.compile(rf"9501[\s\w]*?[:\-]?\s*({_NUM})", re.IGNORECASE),
        re.compile(rf"FLUJO\s+DE\s+CAJA\s+OPERATIVO[\s\w]*?[:\-]?\s*({_NUM})", re.IGNORECASE),
    ]
    print("\n[LOG] Buscando flujo operativo...")
    fco = _search_first(tx, rx_fco, "flujo_operativo")

    # --------- CÁLCULOS ---------
    print("\n[LOG] Realizando cálculos financieros...")
    margen_bruto = None
    if ventas and ventas != 0 and ganancia_bruta is not None:
        margen_bruto = max(0.0, min(1.0, ganancia_bruta / ventas))
        print(f"[LOG] Cálculo margen bruto: {ganancia_bruta} / {ventas} = {margen_bruto}")
    else:
        print(f"[LOG] No se pudo calcular margen bruto. Ventas: {ventas}, Ganancia bruta: {ganancia_bruta}")

    razon_corriente = None
    if act_corr and pas_corr and pas_corr != 0:
        razon_corriente = act_corr / pas_corr
        print(f"[LOG] Cálculo razón corriente: {act_corr} / {pas_corr} = {razon_corriente}")
    else:
        print(f"[LOG] No se pudo calcular razón corriente. Activo corriente: {act_corr}, Pasivo corriente: {pas_corr}")

    deuda_total_activos = None
    if tot_act and tot_act != 0 and tot_pas is not None:
        deuda_total_activos = tot_pas / tot_act
        print(f"[LOG] Cálculo deuda/activos: {tot_pas} / {tot_act} = {deuda_total_activos}")
    else:
        print(f"[LOG] No se pudo calcular deuda/activos. Total activo: {tot_act}, Total pasivo: {tot_pas}")

    print("\n[LOG] Resumen de valores extraídos:")
    print(f"[LOG] - Ingresos/ventas: {ventas}")
    print(f"[LOG] - Ganancia bruta: {ganancia_bruta}")
    print(f"[LOG] - Activo corriente: {act_corr}")
    print(f"[LOG] - Pasivo corriente: {pas_corr}")
    print(f"[LOG] - Total activo: {tot_act}")
    print(f"[LOG] - Total pasivo: {tot_pas}")
    print(f"[LOG] - Flujo operativo: {fco}")
    
    metrics = FinanceMetrics(
        ventas_anuales=ventas or 0.0,
        margen_bruto=margen_bruto if margen_bruto is not None else 0.22,
        razon_corriente=razon_corriente if razon_corriente is not None else 1.2,
        deuda_total_activos=deuda_total_activos if deuda_total_activos is not None else 0.6,
        flujo_caja_operativo=fco or 0.0,
        # estos campos extra NO están en el modelo de scoring;
        # si los quieres, añádelos allí, o no los devuelvas.
    )
    
    print("\n[LOG] Métricas financieras calculadas:")
    print(f"[LOG] - ventas_anuales: {metrics.ventas_anuales}")
    print(f"[LOG] - margen_bruto: {metrics.margen_bruto}")
    print(f"[LOG] - razon_corriente: {metrics.razon_corriente}")
    print(f"[LOG] - deuda_total_activos: {metrics.deuda_total_activos}")
    print(f"[LOG] - flujo_caja_operativo: {metrics.flujo_caja_operativo}")

    confidence_score = _confidence(metrics, act_corr, pas_corr, tot_act, tot_pas)
    print(f"\n[LOG] Nivel de confianza en los datos extraídos: {confidence_score * 100}%")
    
    debug = {
        "confidence": confidence_score,
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
    
    print("\n[LOG] Extracción de métricas financieras completada.")
    return metrics, debug

def _confidence(m: FinanceMetrics, act_corr, pas_corr, tot_act, tot_pas) -> float:
    score = 0
    print("\n[LOG] Calculando nivel de confianza:")
    
    if m.ventas_anuales > 0:
        score += 0.25
        print(f"[LOG] - Ventas anuales > 0: +0.25 (ventas = {m.ventas_anuales})")
    else:
        print(f"[LOG] - Ventas anuales no detectadas o = 0: +0.00 (ventas = {m.ventas_anuales})")
        
    if m.margen_bruto not in (None, 0.22):
        score += 0.2
        print(f"[LOG] - Margen bruto detectado: +0.20 (margen = {m.margen_bruto})")
    else:
        print(f"[LOG] - Margen bruto no detectado o valor por defecto: +0.00 (margen = {m.margen_bruto})")
        
    if act_corr and pas_corr:
        score += 0.25
        print(f"[LOG] - Activo y pasivo corriente detectados: +0.25 (act_corr = {act_corr}, pas_corr = {pas_corr})")
    else:
        print(f"[LOG] - Activo o pasivo corriente no detectados: +0.00 (act_corr = {act_corr}, pas_corr = {pas_corr})")
        
    if tot_act and tot_pas is not None:
        score += 0.2
        print(f"[LOG] - Total activo y pasivo detectados: +0.20 (tot_act = {tot_act}, tot_pas = {tot_pas})")
    else:
        print(f"[LOG] - Total activo o pasivo no detectados: +0.00 (tot_act = {tot_act}, tot_pas = {tot_pas})")
        
    if m.flujo_caja_operativo != 0:
        score += 0.1
        print(f"[LOG] - Flujo de caja operativo detectado: +0.10 (fco = {m.flujo_caja_operativo})")
    else:
        print(f"[LOG] - Flujo de caja operativo no detectado o = 0: +0.00 (fco = {m.flujo_caja_operativo})")
    
    final_score = round(score, 2)
    print(f"[LOG] - Puntuación final de confianza: {final_score} ({final_score * 100}%)")
    return final_score
