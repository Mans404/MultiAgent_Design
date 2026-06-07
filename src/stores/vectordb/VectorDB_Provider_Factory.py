from .providers import QdrantDB, PG_Vector_Provider
from .VectorDB_Enums import VectorDBEnum
from .VectorDB_Interface import VectorDB_Interface  # FIX: import the correct return type
from controllers.BaseController import BaseController
from sqlalchemy.orm import sessionmaker
class VectorDB_Provider_Factory:
    def __init__(self, config, db_client: sessionmaker):
        self.config = config
        self.base_controller = BaseController()
        self.db_client = db_client

    def create_provider(self, provider_type: str) -> VectorDB_Interface:  # FIX: was BaseController
        if provider_type == VectorDBEnum.QDRANT.value:
            quadrant_db_client = self.base_controller.get_database_path(dbname=self.config.VECTOR_DB_PATH)
            return QdrantDB(db_client = quadrant_db_client, distance_method=self.config.VECTOR_DB_DISTANCE_METHOD,
            default_vector_size=self.config.EMBEDDING_MODEL_SIZE,
            index_threshold=self.config.VECTOR_DB_INDEX_THRESHOLD)

        if provider_type == VectorDBEnum.PG_VECTOR.value:
            return PG_Vector_Provider(db_client=self.db_client, distance_method=self.config.VECTOR_DB_DISTANCE_METHOD,
            default_vector_size=self.config.EMBEDDING_MODEL_SIZE,
            index_threshold=self.config.VECTOR_DB_INDEX_THRESHOLD)

        

        raise ValueError(f"Unsupported provider type: {provider_type}")