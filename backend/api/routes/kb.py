from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel, Field
from services.knowledge_base import ingest_texts, ingest_text_files, ingest_pdf_bytes, query

router = APIRouter(prefix="/kb", tags=["knowledge-base"])

class IngestTextsBody(BaseModel):
    collection: str = Field("cursos", description="Nombre de la colección en Chroma", examples=["cursos"])
    texts: List[str] = Field(..., description="Lista de documentos en texto plano")
    sources: Optional[List[str]] = Field(None, description="Nombres/paths de referencia")

class QueryBody(BaseModel):
    collection: str = Field("cursos", description="Colección a consultar", examples=["cursos"])
    q: str = Field(..., description="Consulta en lenguaje natural", examples=["¿Tienen el curso de IA en AWS?"])
    k: int = Field(3, ge=1, le=10, description="Top-k resultados", examples=[2])

@router.post(
    "/ingest-texts",
    summary="Ingestar textos en la base vectorial",
    description="Recibe lista de textos, los trocea en chunks, genera embeddings y los persiste en Chroma.",
)
def kb_ingest_texts(body: IngestTextsBody):
    try:
        return ingest_texts(body.collection, body.texts, body.sources)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/ingest-files",
    summary="Ingestar archivos .txt",
    description="Sube uno o más .txt via form-data y se vectorizan en la colección indicada.",
)
async def kb_ingest_files(
    collection: str = Form("cursos"),
    files: List[UploadFile] = File(...)
):
    try:
        file_list = []
        for f in files:
            data = await f.read()
            file_list.append((f.filename, data))
        return ingest_text_files(collection, file_list)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/ingest-pdf",
    summary="Ingestar PDF (texto nativo + OCR visión) a la base vectorial",
    description="Procesa el PDF con extracción nativa + OCR por visión y vectoriza el texto combinado en Chroma.",
)
async def kb_ingest_pdf(
    file: UploadFile = File(...),
    collection: str = Form("cursos"),
    prompt: str = Form(
        "Eres un OCR para documentos financieros. Extrae todo el texto visible y describe imágenes relevantes."
    )
):
    try:
        if file.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="Debes subir un PDF")
        pdf_bytes = await file.read()
        return ingest_pdf_bytes(collection, pdf_bytes, prompt=prompt, source_name=file.filename)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/query",
    summary="Consultar la base de conocimiento (similaridad)",
    description="Realiza búsqueda semántica top-k sobre la colección indicada y devuelve fragmentos relevantes.",
)
def kb_query(body: QueryBody):
    try:
        return query(body.collection, body.q, k=body.k)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
