from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import re
import json 

from services.document_processor import pdf_to_rich_text
from services.financial_extractor import extract_financial_metrics_from_text
from services.scoring_service import FinanceMetrics, Reference, ScorePayload, compute_score
from services.knowledge_base import ingest_pdf_bytes
from services.ai_analyzer import chat as chat_with_kb
from services.scraping_service import collect_public_signals_existing
from services.risk_llm import llm_assessment_with_ai_analyzer

router = APIRouter(prefix="/risk", tags=["risk"])

def _top5_factores(factores):
    # factores viene como [["Liquidez (RC<1.0)","-"], ...]
    # prioriza negativos, luego neutros, luego positivos
    orden = {"-": 0, "±": 1, "+": 2}
    return sorted(factores, key=lambda x: orden.get(x[1], 3))[:5]

def _motivos_limite(finanzas, signals, scoring):
    motivos = []
    rc = finanzas.razon_corriente
    dta = finanzas.deuda_total_activos
    ventas = finanzas.ventas_anuales
    fco = finanzas.flujo_caja_operativo
    dig = (signals or {}).get("digital_rating")

    if rc is not None and rc < 1.0:
        motivos.append("Liquidez insuficiente (razón corriente < 1.0).")
    if dta is not None and dta > 0.6:
        motivos.append("Apalancamiento elevado (deuda/activos > 0.60).")
    if (ventas or 0) <= 0:
        motivos.append("No hay ventas reportadas en documentos recibidos.")
    if (fco or 0) <= 0:
        motivos.append("Flujo de caja operativo negativo o ausente.")
    if dig is not None and dig < 3.0:
        motivos.append("Reputación/actividad digital baja (rating < 3).")

    # usa factores del scoring para completar
    for label, signo in scoring.get("factores", []):
        if signo == "-" and label not in motivos:
            motivos.append(label)

    # limita a 5-6
    return motivos[:6]

def _en_que_falla(finanzas, signals):
    fallas = []
    if finanzas.razon_corriente is not None and finanzas.razon_corriente < 1.0:
        fallas.append("Liquidez de corto plazo")
    if finanzas.deuda_total_activos is not None and finanzas.deuda_total_activos > 0.6:
        fallas.append("Apalancamiento")
    if (finanzas.ventas_anuales or 0) <= 0:
        fallas.append("Evidencia de ingresos")
    if (finanzas.flujo_caja_operativo or 0) <= 0:
        fallas.append("Generación de efectivo")
    dig = (signals or {}).get("digital_rating")
    if dig is not None and dig < 3.0:
        fallas.append("Reputación/actividad digital")
    return fallas[:5]

def _focos_analista(finanzas, signals):
    focos = []
    if finanzas.razon_corriente is not None and finanzas.razon_corriente < 1.2:
        focos.append("Plan de liquidez (rotación de cartera y pasivos de corto plazo).")
    if finanzas.deuda_total_activos is not None and finanzas.deuda_total_activos > 0.5:
        focos.append("Calendario de deuda y cobertura de intereses.")
    if (finanzas.ventas_anuales or 0) == 0:
        focos.append("Solicitar Estado de Resultados auditado y contratos de ventas.")
    if (finanzas.flujo_caja_operativo or 0) <= 0:
        focos.append("Estado de Flujos y plan de cobros/pagos.")
    dig = (signals or {}).get("digital_rating")
    if dig is not None and dig < 3.5:
        focos.append("Estrategia de reputación digital (reseñas y perfiles verificados).")
    return focos[:5]

def _resumen_corto(empresa, finanzas, scoring, signals):
    # Máx ~200 palabras (2 párrafos cortos)
    rs = empresa["razon_social"]; nom = empresa["nombre_comercial"]
    rc = finanzas.razon_corriente; dta = finanzas.deuda_total_activos
    ventas = finanzas.ventas_anuales; fco = finanzas.flujo_caja_operativo
    dig = (signals or {}).get("digital_rating")
    riesgo = scoring.get("riesgo")
    ms = scoring.get("monto_sugerido", {})
    monto = ms.get("max", 0)

    p1 = (f"Se sugiere un crédito de USD {monto:,.0f} para {rs} ({nom}), "
          f"clasificada como riesgo {riesgo}. La decisión se sustenta en la liquidez "
          f"(RC={rc:.3f}),' 'apalancamiento' ' (D/A={dta:.2f}), "
          f"ventas reportadas={ventas:,.0f} y flujo operativo={fco:,.0f}. "
          f"Rating digital={dig if dig is not None else 's/d'}.")
    p2 = ("Los principales factores de riesgo incluyen liquidez de corto plazo, "
          "apalancamiento y evidencia limitada de ingresos/flujo. Para avanzar, "
          "se recomienda validar Estado de Resultados y Flujos, mejorar rotación de cartera "
          "y consolidar reputación digital con reseñas verificadas.")
    # Limpiar dobles espacios
    return " ".join(p1.split()), " ".join(p2.split())


def _slug(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-")

def _safe_collection_name(base: str, slug: str) -> str:
    name = f"{base}.{slug}"
    # Solo [a-z0-9._-]
    name = re.sub(r"[^a-z0-9._-]", "-", name.lower())
    # Quita separadores al inicio/fin para cumplir “start/end alnum”
    name = re.sub(r"^[^a-z0-9]+", "", name)
    name = re.sub(r"[^a-z0-9]+$", "", name)
    # Asegura longitud mínima
    if len(name) < 3:
        name = (name + "-xxx")[:3]
    return name


@router.post("/evaluate", summary="Evaluación de riesgo (extracción + scraping + KB opcional)")
async def evaluate_risk_endpoint(
    razon_social: str = Form(...),
    nombre_comercial: str = Form(...),
    pais: str = Form(...),
    ciudad: str = Form(...),
    direccion: str = Form(...),

    instagram_url: Optional[str] = Form(None),
    facebook_url: Optional[str] = Form(None),
    tiktok_url: Optional[str] = Form(None),

    referencias_files: Optional[List[UploadFile]] = File(None, description="Hasta 3 PDFs"),
    financieros_files: Optional[List[UploadFile]] = File(None, description="Hasta 3 PDFs o CSV"),

    # KB opcional
    kb_ingest: bool = Form(False, description="Si true, ingesta los PDFs a la colección"),
    use_kb: bool = Form(False, description="Si true, genera explicación usando KB"),
    collection: str = Form("empresas", description="Nombre base de la colección"),
    k: int = Form(3, description="Top‑k para retrieval")
):
    print(json.dumps({
        "razon_social": razon_social,
        "nombre_comercial": nombre_comercial,
        "pais": pais,
        "ciudad": ciudad,
        "direccion": direccion,
        "instagram_url": instagram_url,
        "facebook_url": facebook_url,
        "tiktok_url": tiktok_url,
        "kb_ingest": kb_ingest,
        "use_kb": use_kb,
        "collection": collection,
        "k": k,
        "referencias_files": [f.filename for f in referencias_files] if referencias_files else [],
        "financieros_files": [f.filename for f in financieros_files] if financieros_files else []
    }, indent=2, ensure_ascii=False))
    try:
        # Optimización: Procesamiento paralelo de señales digitales y archivos financieros
        # 1) Recolectar señales digitales (reputación)
        signals = collect_public_signals_existing(
            business_name=nombre_comercial or razon_social,
            city=ciudad,
            instagram=instagram_url,
            facebook=facebook_url,
            tiktok=tiktok_url,
            google_maps_url=None,
            country=pais
        )
        digital_rating = signals.get("digital_rating")

        # 2) Procesar archivos financieros (optimizado)
        extraction_debug = {"confidence": 0.0, "per_file": [], "notes": []}
        fin_metrics = None
        combined_text = ""
        all_metrics = []

        if financieros_files:
            # Procesar todos los archivos financieros
            combined_parts = []
            processed_files = []
            
            # Primero procesamos todos los archivos y extraemos el texto
            for f in financieros_files:
                try:
                    file_bytes = await f.read()
                    parsed = pdf_to_rich_text(file_bytes)
                    text_i = parsed.get("combined_text", "")
                    combined_parts.append(text_i)
                    processed_files.append({"filename": f.filename, "chars": len(text_i)})

                    # Metadatos por archivo
                    extraction_debug["per_file"].append({
                        "filename": f.filename,
                        "native_chars": parsed.get("native_chars"),
                        "ocr_chars": parsed.get("ocr_chars")
                    })

                    # Ingesta opcional a KB (solo si es necesario)
                    if kb_ingest:
                        company_collection = f"{collection}.{_slug(razon_social)}"
                        ingest_pdf_bytes(company_collection, file_bytes, source_name=f.filename)
                    
                    # Extraer métricas de cada archivo individualmente
                    print(f"\n[LOG] Procesando archivo: {f.filename}")
                    file_metrics, file_debug = extract_financial_metrics_from_text(text_i)
                    all_metrics.append((file_metrics, file_debug))

                except Exception as fe:
                    print(f"[LOG] Error al procesar archivo {f.filename}: {str(fe)}")
                    extraction_debug.setdefault("per_file", []).append({
                        "filename": f.filename,
                        "error": str(fe)
                    })

            # Combinar todo el texto para un análisis completo
            combined_text = "\n\n".join(combined_parts)
            print("\n[LOG] Procesando texto combinado de todos los archivos")
            
            # Extracción de métricas financieras del texto combinado
            fin_metrics, extraction_debug_all = extract_financial_metrics_from_text(combined_text)
            
            # Si no se encontraron métricas en el texto combinado, usar las mejores métricas individuales
            if fin_metrics.ventas_anuales == 0 and fin_metrics.razon_corriente == 1.2 and len(all_metrics) > 0:
                print("\n[LOG] Usando las mejores métricas individuales de los archivos")
                # Seleccionar las mejores métricas basadas en confianza
                best_metrics = None
                best_confidence = -1
                
                for metrics, debug in all_metrics:
                    confidence = debug.get("confidence", 0)
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_metrics = metrics
                        best_debug = debug
                
                if best_metrics is not None:
                    fin_metrics = best_metrics
                    extraction_debug_all = best_debug

            # Merge de información de debug
            extraction_debug["confidence"] = extraction_debug_all.get("confidence", 0.0)
            extraction_debug["log"] = extraction_debug_all.get("log", {})
            extraction_debug["raw_values"] = extraction_debug_all.get("raw_values", {})
            extraction_debug["notes"].append(extraction_debug_all.get("notes"))
            extraction_debug["processed_files"] = processed_files

        # Valores por defecto si no hay métricas extraídas
        if not fin_metrics:
            fin_metrics = FinanceMetrics(
                ventas_anuales=0.0,
                margen_bruto=0.22,
                razon_corriente=1.2,
                deuda_total_activos=0.6,
                flujo_caja_operativo=0.0
            )

        # 3) Referencias (simplificado)
        refs: List[Reference] = []
        if referencias_files:
            for f in referencias_files[:3]:
                _ = await f.read()
                refs.append(Reference(
                    nombre=f.filename, tipo="proveedor",
                    antiguedad_meses=18, pago_prom_dias=7, monto_prom_mensual=1200.0
                ))

        # 4) Cálculo de score
        payload = ScorePayload(
            sector="Comercio",
            antiguedad_meses=36,
            digital_rating=digital_rating,
            referencias=refs or None,
            finanzas=fin_metrics
        )
        scoring = compute_score(payload)

        session_id = f"risk:{_slug(razon_social)}"
        company_collection = _safe_collection_name(collection, _slug(razon_social)) if use_kb else None

        # 5) Explicación con KB (opcional - solo si es necesario)
        kb = {"used": False}
        if use_kb and kb_ingest:  # Solo si se ingestan documentos y se solicita explicación
            company_collection = _safe_collection_name(collection, _slug(razon_social))
            q = (
                f"Con el contexto disponible y estas métricas extraídas: "
                f"ventas={fin_metrics.ventas_anuales}, margen={fin_metrics.margen_bruto}, "
                f"razon_corriente={fin_metrics.razon_corriente}, deuda_activos={fin_metrics.deuda_total_activos}, "
                f"flujo_operativo={fin_metrics.flujo_caja_operativo}. "
                "Justifica el riesgo en bullets, cita discrepancias entre métricas y contexto."
            )
            session_id = f"risk:{_slug(razon_social)}"
            res = chat_with_kb(
                session_id=session_id,
                message=q,
                use_kb=True,
                collection=company_collection,
                k=k
            )
            kb = {
                "used": True,
                "collection": company_collection,
                "explanation": res["answer"],
                "sources": res["sources"]
            }
        
        # 6) Preparación de la respuesta
        factores_top5 = _top5_factores(scoring.get("factores", []))
        monto_max = scoring.get("monto_sugerido", {}).get("max", 0)
        llm_out = llm_assessment_with_ai_analyzer(
            empresa={"razon_social": razon_social, "nombre_comercial": nombre_comercial},
            finanzas=fin_metrics,
            signals=signals,
            scoring=scoring,                 # <--- pásale el score
            session_id=f"risk:{_slug(razon_social)}",
            collection=_safe_collection_name(collection, _slug(razon_social)) if use_kb else None,
            use_kb=use_kb,
            k=k
        )

        valores_maximos_ref = {
            "ventas_anuales": 50_000_000.0,        # máximo esperado anual en USD
            "margen_bruto": 1.0,                   # 100%
            "razon_corriente": 5.0,                # ratio máximo razonable
            "deuda_total_activos": 1.0,            # 100%
            "flujo_caja_operativo": 10_000_000.0   # máximo esperado anual en USD
        }

        # --- Extraer métricas con valor y máximo
        estadisticas = {
            k: {
                "value": getattr(fin_metrics, k, None),
                "max": valores_maximos_ref.get(k)
            }
            for k in valores_maximos_ref.keys()
        }

        decision = {
            "empresa": {"razon_social": razon_social, "nombre_comercial": nombre_comercial},
            "credito_sugerido": {
                "monto": scoring.get("monto_sugerido", {}).get("max", 0),
                "moneda": "USD"
            },
            "estadisticas": estadisticas,
            "riesgo_interno": scoring.get("riesgo"),
            "factores_clave_riesgo":{
                "top_5": llm_out.get("top_5", []),               
            },
            "resumen": llm_out.get("resumen", {
                "parrafo_1": "", "parrafo_2": ""
            })
        }

        return {
            "decision": decision
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/simulate", summary="Simulación de score con parámetros básicos")
async def simulate_score_endpoint(
    ingresos: float = Form(..., description="Ingresos anuales en USD"),
    reputacion: float = Form(..., description="Reputación digital en porcentaje (0-100%)"),
    pago_a_tiempo: float = Form(..., description="Porcentaje de pagos a tiempo (0-100%)"),
    sector: str = Form("Comercio", description="Sector de la empresa"),
    antiguedad_meses: int = Form(36, description="Antigüedad de la empresa en meses")
):
    try:
        # Convertir reputación de porcentaje (0-100%) a escala 0-5
        digital_rating = min(5.0, max(0.0, reputacion * 5.0 / 100.0))
        
        # Convertir pago a tiempo de porcentaje a días de atraso promedio
        # 100% = 0 días de atraso, 0% = 30 días de atraso (aproximadamente)
        pago_prom_dias = round(max(0, 30 - (pago_a_tiempo * 30 / 100)))
        
        # Crear referencia basada en el pago a tiempo
        refs = [Reference(
            nombre="Referencia simulada", 
            tipo="proveedor",
            antiguedad_meses=24, 
            pago_prom_dias=pago_prom_dias, 
            monto_prom_mensual=ingresos / 12 * 0.1  # 10% de ingresos mensuales
        )]
        
        # Crear métricas financieras con valores razonables basados en los ingresos
        fin_metrics = FinanceMetrics(
            ventas_anuales=ingresos,
            margen_bruto=0.25,  # 25% de margen bruto
            razon_corriente=1.5,  # Razón corriente saludable
            deuda_total_activos=0.5,  # 50% de apalancamiento
            flujo_caja_operativo=ingresos * 0.15  # 15% de los ingresos como flujo operativo
        )
        
        # Crear payload para el cálculo del score
        payload = ScorePayload(
            sector=sector,
            antiguedad_meses=antiguedad_meses,
            digital_rating=digital_rating,
            referencias=refs,
            finanzas=fin_metrics
        )
        
        # Calcular score
        scoring = compute_score(payload)
        
        # Preparar respuesta
        return {
            "score": scoring["score"],
            "riesgo": scoring["riesgo"],
            "monto_sugerido": scoring["monto_sugerido"],
            "factores": scoring["factores"],
            "parametros_ingresados": {
                "ingresos_usd": ingresos,
                "reputacion_pct": reputacion,
                "pago_a_tiempo_pct": pago_a_tiempo,
                "digital_rating_calculado": digital_rating,
                "dias_atraso_calculados": pago_prom_dias
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
