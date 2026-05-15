from .BaseController import BaseController
from models.db_schemes.project import Project
from models.db_schemes.data_chunk import DataChunk
from stores.LLM.LLM_Enums import Document_Type
from typing import List
from stores.LLM.providers.OPENAI_Provider import OPENAI_Provider



class NLPController(BaseController):
    def __init__(self, vectordb_client,generation_client,embedding_client):
        super().__init__()

        self.vectordb_client = vectordb_client
        self.generation_client = generation_client
        self.embedding_client = embedding_client

    def create_collection_name(self, project_id):
        return f"collection_{project_id}".strip()
    
    def reset_vectordb_collection(self, project: Project):
        collection_name = self.create_collection_name(project_id=project.project_id)
        return self.vectordb_client.delete_collection(collection_name=collection_name)
    
    def get_vectordb_collection_info(self, project: Project):
        collection_name = self.create_collection_name(project_id=project.project_id)
        return self.vectordb_client.get_collection_info(collection_name=collection_name)
    
    def index_into_vectodb(self, project: Project, chunks: List[DataChunk],do_reset: bool = False):
        # step1: get_collection names
        collection_name = self.create_collection_name(project_id=project.project_id)
        # step2: manage Items
        texts = [chunk.chunk_text for chunk in chunks]
        metadata = [chunk.chunk_metadata for chunk in chunks]  
        vectors = [
            self.embedding_client.embed_text(text = text, document_type = Document_Type.QUERY.value)
            for text in texts
        ]
        # step3: create collection if not exists
        self.vectordb_client.create_collection(
            collection_name=collection_name,
            dimension=self.embedding_client.embedding_size,
            do_reset=do_reset
        )
        
        
        # insert into vectordb
        self.vectordb_client.insert_many_data(
            collection_name = collection_name,
            texts = texts,
            metadata = metadata,
            vectors = vectors
        )
        return True