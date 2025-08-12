# services/document_processor.py
from typing import Dict, Any, List, Optional
import io, os

import fitz  # PyMuPDF

# --- Umbrales ajustables ---
MIN_CHARS_PER_PAGE = 80         # si la extracción nativa de una página trae <80 chars => se intenta OCR
ZOOM = 2.0                      # 2.0 ~ 288 dpi aprox (buena para OCR)
MAX_OCR_PAGES_AUTO = 20         # seguridad: limitar OCR en PDFs grandes para optimizar velocidad

def _page_to_png_bytes(page) -> bytes:
    mat = fitz.Matrix(ZOOM, ZOOM)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    return pix.tobytes("png")

def _try_openai_vision_ocr(img_bytes: bytes) -> Optional[str]:
    # OCR con OpenAI Vision (más potente pero más caro)
    try:
        import base64
        from openai import OpenAI
        client = OpenAI()
        
        # Convertir bytes a base64
        base64_image = base64.b64encode(img_bytes).decode('utf-8')
        
        response = client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Extrae TODO el texto visible en esta imagen. Incluye números, tablas y cualquier texto que veas. Devuelve SOLO el texto extraído, sin comentarios ni explicaciones adicionales."},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                    ]
                }
            ],
            max_tokens=1000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error en OpenAI Vision OCR: {e}")
        return None

def _ocr_image(img_bytes: bytes) -> str:
    """Realiza OCR usando OpenAI Vision directamente."""
    # Usamos directamente OpenAI Vision para mejor precisión
    text = _try_openai_vision_ocr(img_bytes)
    return text or ""

def pdf_to_rich_text(pdf_bytes: bytes, force_ocr: bool = False) -> Dict[str, Any]:
    """
    Extrae texto de un PDF - OPTIMIZADO para velocidad y extracción de campos financieros:
    - Modo normal: usa extracción nativa de PyMuPDF.
    - Auto-OCR por página: si una página tiene muy poco texto nativo (< MIN_CHARS_PER_PAGE),
      la renderiza a imagen y le aplica OCR (sólo esa página).
    - Si `force_ocr=True`, hace OCR a TODAS las páginas (útil para PDFs claramente escaneados).
    - OPTIMIZACIÓN: Solo procesa las primeras 5 páginas para documentos financieros.
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    combined_parts: List[str] = []
    pages_meta: List[Dict[str, Any]] = []
    native_total = 0
    ocr_total = 0

    # Si el PDF es enorme, limitar OCR automático
    allow_auto_ocr = (doc.page_count <= MAX_OCR_PAGES_AUTO)
    
    # OPTIMIZACIÓN: Solo procesar las primeras 5 páginas para documentos financieros
    # La mayoría de los campos financieros relevantes están en las primeras páginas
    max_pages = min(5, doc.page_count)

    for i in range(max_pages):
        page = doc[i]
        # 1) extracción nativa
        native_text = page.get_text("text") or ""
        native_chars = len(native_text)
        native_total += native_chars

        # 2) decidir si hacemos OCR en esta página
        need_ocr = force_ocr or (allow_auto_ocr and native_chars < MIN_CHARS_PER_PAGE)

        ocr_text = ""
        ocr_used = False
        if need_ocr:
            try:
                img_bytes = _page_to_png_bytes(page)
                ocr_text = _ocr_image(img_bytes)
                ocr_used = len(ocr_text.strip()) > 0
            except Exception:
                ocr_text = ""

        # 3) escoger mejor resultado para la página
        #    - si hay OCR y es "mejor" que lo nativo raquítico, usa OCR
        #    - si extracción nativa ya es buena, mantenla
        page_text = native_text
        if ocr_used and (len(ocr_text) > max(native_chars, MIN_CHARS_PER_PAGE)):
            page_text = ocr_text

        ocr_chars = len(ocr_text) if ocr_used else 0
        ocr_total += ocr_chars

        # 4) acumular
        combined_parts.append(page_text.strip())
        pages_meta.append({
            "index": i,
            "native_chars": native_chars,
            "ocr_used": ocr_used,
            "ocr_chars": ocr_chars
        })

    combined_text = "\n\n".join(p for p in combined_parts if p)

    return {
        "combined_text": combined_text,
        "native_chars": native_total,
        "ocr_chars": ocr_total,
        "pages": pages_meta,
        "notes": {
            "force_ocr": force_ocr,
            "min_chars_per_page": MIN_CHARS_PER_PAGE,
            "zoom": ZOOM,
            "auto_ocr_enabled": allow_auto_ocr,
            "optimized": True,
            "max_pages_processed": max_pages
        }
    }
