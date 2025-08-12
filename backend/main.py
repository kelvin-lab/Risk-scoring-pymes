import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


from api.routes.chat import router as chat_router
from api.routes.documents import router as documents_router
from api.routes.kb import router as kb_router
from api.routes.risk import router as risk_router

app = FastAPI(title="AlfaTech API", version="1.0.0")

tags_metadata = [
    {"name": "chat", "description": "Asistente AlfaTech con memoria por sesión."},
    {"name": "documents", "description": "Carga y análisis de archivos (PDF, imágenes)."},
    {"name": "knowledge-base", "description": "Ingesta y consulta de la base vectorial (Chroma)."},
]

app = FastAPI(
    title="AlfaTech API",
    version="1.0.0",
    description="API para scoring alternativo PYME: chat guiado, ingesta documental y RAG con Chroma.",
    openapi_tags=tags_metadata,
    contact={"name": "Equipo AlfaTech", "email": "equipo@alfatech.local"},
    license_info={"name": "MIT"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(documents_router)
app.include_router(kb_router)
app.include_router(risk_router)



@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)