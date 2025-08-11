from typing import List, Dict, Tuple, Optional
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config.settings import settings
from services.document_processor import pdf_to_rich_text  # usamos lo que ya hiciste (PDF→texto+OCR)

# Embeddings (re-usa tu API key del .env)
_embeddings = OpenAIEmbeddings(
    model=settings.EMBEDDING_MODEL,
    openai_api_key=settings.OPENAI_API_KEY
)

# Text splitter recomendado (mejor que CharacterTextSplitter)
_text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=150,
    separators=["\n\n", "\n", ". ", " ", ""],
)

def _get_vs(collection_name: str) -> Chroma:
    return Chroma(
        collection_name=collection_name,
        persist_directory=settings.VECTOR_DIR,
        embedding_function=_embeddings
    )

def _to_documents(texts: List[str], sources: Optional[List[str]]=None, meta: Optional[List[Dict]]=None) -> List[Document]:
    docs: List[Document] = []
    for i, txt in enumerate(texts):
        metadata = {}
        if sources and i < len(sources):
            metadata["source"] = sources[i]
        if meta and i < len(meta):
            metadata.update(meta[i])
        docs.append(Document(page_content=txt, metadata=metadata))
    return docs

def ingest_texts(collection: str, texts: List[str], sources: Optional[List[str]]=None, meta: Optional[List[Dict]]=None) -> Dict:
    vs = _get_vs(collection)
    docs = _to_documents(texts, sources, meta)
    # chunking
    chunks = _text_splitter.split_documents(docs)
    vs.add_documents(chunks)
    vs.persist()
    return {"ingested_docs": len(docs), "chunks": len(chunks)}

def ingest_text_files(collection: str, files: List[Tuple[str, bytes]]) -> Dict:
    texts, sources = [], []
    for path, data in files:
        try:
            txt = data.decode("utf-8")
        except UnicodeDecodeError:
            txt = data.decode("latin-1", errors="ignore")
        texts.append(txt)
        sources.append(path)
    return ingest_texts(collection, texts, sources)

def ingest_pdf_bytes(collection: str, pdf_bytes: bytes, prompt: Optional[str]=None, source_name: str="uploaded.pdf") -> Dict:
    """Usa tu pipeline PDF→TextoNativo+OCR y vectoriza el 'combined_text'."""
    result = pdf_to_rich_text(pdf_bytes, prompt=prompt or
        "Eres un OCR para documentos financieros. Extrae todo el texto visible y describe imágenes relevantes.")
    combined = result.get("combined_text", "")
    if not combined.strip():
        return {"ingested_docs": 0, "chunks": 0, "note": "PDF sin texto/OCR vacío"}
    return ingest_texts(
        collection,
        [combined],
        sources=[source_name],
        meta=[{"native_chars": result["native_text_chars"], "ocr_chars": result["ocr_text_chars"]}]
    )

def query(collection: str, q: str, k: int = 3) -> Dict:
    vs = _get_vs(collection)
    results = vs.similarity_search_with_relevance_scores(q, k=k)
    out = []
    for doc, score in results:
        out.append({
            "text": doc.page_content,
            "metadata": doc.metadata,
            "score": score
        })
    return {"matches": out, "k": k, "collection": collection, "query": q}
