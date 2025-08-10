import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


from api.routes.chat import router as chat_router
from api.routes.documents import router as documents_router

app = FastAPI(title="AlfaTech API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(documents_router)


@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)