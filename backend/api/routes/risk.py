from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import re 

from services.document_processor import pdf_to_rich_text
from services.financial_extractor import extract_financial_metrics_from_text
from services.scoring_service import FinanceMetrics, Reference, ScorePayload, compute_score
from services.knowledge_base import ingest_pdf_bytes
from services.ai_analyzer import chat as chat_with_kb
from services.scraping_service import collect_public_signals_existing

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
    try:
        signals = collect_public_signals_existing(
            business_name=nombre_comercial or razon_social,
            city=ciudad,
            instagram=instagram_url,
            facebook=facebook_url,
            tiktok=tiktok_url,
            google_maps_url=None,   # si luego agregas el campo, lo pones aquí
            country=pais
        )
        digital_rating = signals.get("digital_rating")

        # 1) Procesar archivo financiero (tomamos el primero por simplicidad)
        extraction_debug = {"confidence": 0.0, "per_file": [], "notes": []}  # <-- clave
        fin_metrics = None
        combined_text = ""

        if financieros_files:
            combined_parts = []
            processed_files = []
            for f in financieros_files[:10]:
                try:
                    file_bytes = await f.read()
                    parsed = pdf_to_rich_text(file_bytes)
                    text_i = parsed.get("combined_text", "")
                    combined_parts.append(text_i)
                    processed_files.append({"filename": f.filename, "chars": len(text_i)})

                    # guarda metadatos por archivo sin explotar si faltan
                    extraction_debug["per_file"].append({
                        "filename": f.filename,
                        "native_chars": parsed.get("native_chars"),
                        "ocr_chars": parsed.get("ocr_chars")
                    })

                    # Ingesta opcional a KB (cada archivo)
                    if kb_ingest:
                        company_collection = f"{collection}.{_slug(razon_social)}"
                        ingest_pdf_bytes(company_collection, file_bytes, source_name=f.filename)

                except Exception as fe:
                    # asegúrate de que exista la clave
                    extraction_debug.setdefault("per_file", []).append({
                        "filename": f.filename,
                        "error": str(fe)
                    })

            combined_text = "\n\n".join(combined_parts)

            # Extrae métricas del texto unificado
            fin_metrics, extraction_debug_all = extract_financial_metrics_from_text(combined_text)

            # Merge seguro
            extraction_debug["confidence"] = extraction_debug_all.get("confidence", 0.0)
            extraction_debug["log"] = extraction_debug_all.get("log", {})
            extraction_debug["raw_values"] = extraction_debug_all.get("raw_values", {})
            extraction_debug["notes"].append(extraction_debug_all.get("notes"))
            extraction_debug["processed_files"] = processed_files


        # Defaults si no hay archivo o no se pudo extraer nada sólido
        if not fin_metrics:
            fin_metrics = FinanceMetrics(
                ventas_anuales=0.0,
                margen_bruto=0.22,
                razon_corriente=1.2,
                deuda_total_activos=0.6,
                flujo_caja_operativo=0.0
            )

        # 2) Referencias (mock simple por ahora)
        refs: List[Reference] = []
        if referencias_files:
            for f in referencias_files[:3]:
                _ = await f.read()
                refs.append(Reference(
                    nombre=f.filename, tipo="proveedor",
                    antiguedad_meses=18, pago_prom_dias=7, monto_prom_mensual=1200.0
                ))

        # 3) Scoring (usa digital_rating de scraping)
        payload = ScorePayload(
            sector="Comercio",
            antiguedad_meses=36,
            digital_rating=digital_rating,
            referencias=refs or None,
            finanzas=fin_metrics
        )
        scoring = compute_score(payload)

        # 4) Explicación con KB (opcional)
        kb = {"used": False}
        if use_kb:
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
                use_kb=True,               # forzamos uso de KB para la explicación
                collection=company_collection,
                k=k
            )
            kb = {
                "used": True,
                "collection": company_collection,
                "explanation": res["answer"],
                "sources": res["sources"]
            }
        
        completeness = {
            "ventas": "ok" if fin_metrics.ventas_anuales > 0 else "missing",
            "margen_bruto": "ok" if fin_metrics.margen_bruto not in (None, 0.22) else "missing_or_default",
            "razon_corriente": "ok" if fin_metrics.razon_corriente is not None else "missing",
            "deuda_total_activos": "ok" if fin_metrics.deuda_total_activos is not None else "missing",
            "flujo_caja_operativo": "ok" if fin_metrics.flujo_caja_operativo != 0 else "missing"
        }

        factores_top5 = _top5_factores(scoring.get("factores", []))
        monto_max = scoring.get("monto_sugerido", {}).get("max", 0)

        decision = {
            "empresa": (empresa := {
                "razon_social": razon_social,
                "nombre_comercial": nombre_comercial
            }),
            "credito_sugerido": {
                "monto": monto_max,
                "moneda": "USD"
            },
            "factores_clave_riesgo": {
                "top_5": factores_top5,
                "en_que_falla": _en_que_falla(fin_metrics, signals),
                "motivos_limite_credito": _motivos_limite(fin_metrics, signals, scoring),
                "focos_analista": _focos_analista(fin_metrics, signals),
                "razones_monto_actual": [
                    f"Liquidez (RC={fin_metrics.razon_corriente:.3f})",
                    f"Apalancamiento (D/A={fin_metrics.deuda_total_activos:.2f})",
                    f"Ventas detectadas={fin_metrics.ventas_anuales:,.0f}",
                    f"Flujo operativo={fin_metrics.flujo_caja_operativo:,.0f}",
                    f"Rating digital={(signals or {}).get('digital_rating', 's/d')}"
                ]
            }
        }
        p1, p2 = _resumen_corto(empresa, fin_metrics, scoring, signals)
        decision["resumen"] = {
            "parrafo_1": p1,
            "parrafo_2": p2
        }

        # 5) Respuesta
        return {
            "decision": decision
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
