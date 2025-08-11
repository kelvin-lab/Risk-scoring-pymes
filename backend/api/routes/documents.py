from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from services.document_processor import pdf_to_rich_text
from services.vision import analyze_image_bytes
import tempfile, shutil, os

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post(
    "/pdf-to-text",
    summary="PDF → Texto (nativo + OCR por visión)",
    description=(
        "Sube un PDF. Se extrae texto nativo (si existe), se renderiza cada página a imagen y se aplica OCR/Descripción con el modelo de visión. "
        "Se devuelve `combined_text` listo para vectorizar."
    ),
)
async def pdf_to_text_endpoint(
    file: UploadFile = File(...),
    prompt: str = Form(
        "Eres un OCR para documentos financieros. Extrae TODO el texto visible con precisión. "
        "Si hay tablas, transcribe en texto legible. Si hay logos o imágenes relevantes, "
        "descríbelos brevemente. Devuelve solo texto plano, sin formato Markdown."
    ),
    include_pages: bool = Form(False)
):
    try:
        if file.content_type not in ("application/pdf",):
            raise HTTPException(status_code=400, detail="Debes subir un PDF")

        pdf_bytes = await file.read()
        result = pdf_to_rich_text(pdf_bytes, prompt=prompt)

        # Por defecto no devolvemos todas las páginas por tamaño; puedes activarlo con include_pages=true
        response = {
            "native_text_chars": result["native_text_chars"],
            "ocr_text_chars": result["ocr_text_chars"],
            "combined_chars": result["combined_chars"],
            "combined_text": result["combined_text"],
        }
        if include_pages:
            response["ocr_pages"] = result["ocr_pages"]
            response["native_text"] = result["native_text"]

        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/analyze-image",
    summary="Describir/extraer información de una imagen",
    description=(
        "Sube una imagen (jpeg/png/webp) y el sistema la describe con el modelo de visión. "
        "Puedes enviar un `prompt` para ajustar el tipo de análisis (por defecto: descripción)."
    ),
)
async def analyze_image_endpoint(
    file: UploadFile = File(...),
    prompt: str = Form("Describe el contenido y dame señales útiles para riesgo PYME")
):
    try:
        if file.content_type not in ("image/jpeg", "image/png", "image/webp"):
            raise HTTPException(status_code=400, detail="Formato de imagen no soportado")

        image_bytes = await file.read()
        answer = analyze_image_bytes(image_bytes, prompt)
        return {"answer": answer}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
