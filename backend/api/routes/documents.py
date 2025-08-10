from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from services.document_processor import parse_financials_from_file
from services.ai_analyzer import analyze_image_bytes
import tempfile, shutil, os

router = APIRouter(prefix="/documents", tags=["documents"])

# A la espera de implementar la base de conocimiento para poder comparar
# con los datos extraídos de los documentos
@router.post("/financials")
async def upload_financials(file: UploadFile = File(...)):
    try:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name
        metrics = parse_financials_from_file(tmp_path)
        os.unlink(tmp_path)
        return {"metrics": metrics}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/analyze-image")
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
