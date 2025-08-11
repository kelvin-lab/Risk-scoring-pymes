import os
from dotenv import load_dotenv
load_dotenv()

class Settings:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "gpt-4.1")
    MODEL_NAME_VISION: str = os.getenv("MODEL_NAME_VISION", "gpt-4o")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    VECTOR_DIR: str = os.getenv("VECTOR_DIR", "./vectorstore")
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", 0.2))

settings = Settings()
if not settings.OPENAI_API_KEY:
    raise RuntimeError("Missing OPENAI_API_KEY")
