import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "Curalink AI"
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "curalink")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "llama3")

    # Groq (OpenAI-compatible): https://console.groq.com/
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_BASE_URL: str = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

    # Legacy local LM Studio when GROQ_API_KEY is unset
    LM_STUDIO_URL: str = os.getenv("LM_STUDIO_URL", "http://localhost:1234/v1")
    LM_STUDIO_MODEL: str = os.getenv("LM_STUDIO_MODEL", "qwen2.5-3b-instruct")

    # Embeddings: leave HTTP URL empty to use bundled SentenceTransformer (768-dim nomic by default).
    # Set to LM Studio / OpenAI-compatible embeddings URL to use remote embeddings instead.
    EMBEDDING_HTTP_URL: str = os.getenv("EMBEDDING_HTTP_URL", "") or os.getenv("EMBED_URL", "")
    EMBEDDING_HTTP_MODEL: str = os.getenv("EMBEDDING_HTTP_MODEL", "nomic-embed-text-v1.5")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "nomic-ai/nomic-embed-text-v1.5")

settings = Settings()
