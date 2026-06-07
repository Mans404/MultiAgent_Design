import os

from pydantic_settings import BaseSettings
from typing import List
class Settings(BaseSettings):

    APP_NAME: str
    APP_VERSION: str
    

    FILE_ALLOWED_TYPES: list
    FILE_MAX_SIZE: int
    FILE_DEFAULT_CHUNK_SIZE: int



    GENERATION_BACKEND: str
    EMBEDDING_BACKEND: str

    OPENAI_API_KEY: str
    OPENAI_API_URL: str
    COHERE_API_KEY: str

    GENERATION_MODEL_NAME: str
    EMBEDDING_MODEL_NAME: str
    EMBEDDING_MODEL_SIZE: int

    INPUT_DEFAULT_MAX_CHARACTERS: int
    GENERATION_DEFAULT_MAX_TOKENS: int
    GENERATION_DEFAULT_TEMPERATURE: float
    VECTOR_DB_BACKEND_LITERALS: List[str] = ["QDRANT", "PGVECTOR"]
    VECTOR_DB_BACKEND: str
    VECTOR_DB_PATH: str
    VECTOR_DB_DISTANCE_METHOD: str = None
    VECTOR_DB_INDEX_THRESHOLD: int = 1000
    DEFAULT_LANG: str = "en"
    PRIMARY_LANG: str = "en"

    
    POSTGRES_USERNAME: str
    POSTGRES_PASSWORD : str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_MAIN_DB: str
    

    
    class Config:
        env_file = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", ".env")
        )

def get_settings():
    return Settings()
