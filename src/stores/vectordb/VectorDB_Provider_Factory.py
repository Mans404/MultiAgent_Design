from .providers import QdrantDB
from .VectorDB_Enums import VectorDBEnum
from controllers.BaseController import BaseController

class VectorDB_Provider_Factory:
    def __init__(self, config):
        self.config = config
        self.base_controller = BaseController()

    def create_provider(self, provider_type: str) -> BaseController:
        if provider_type == VectorDBEnum.QDRANT.value:
            db_path = self.base_controller.get_database_path(dbname=self.config.VECTOR_DB_PATH)

            return QdrantDB(db_path=db_path, distance_method=self.config.VECTOR_DB_DISTANCE_METHOD) 
            
        else:
            raise ValueError(f"Unsupported provider type: {provider_type}")
        
        return None