from abc import ABC, abstractmethod

class VectorDB_Interface(ABC):
    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def disconnect(self):
        pass

    @abstractmethod
    def is_collection_excisted(self, collection_name: str):
        pass

    @abstractmethod
    def list_all_collections(self):
        pass

    @abstractmethod
    def get_collection_info(self, collection_name: str):
        pass

    @abstractmethod
    def delete_collection(self, collection_name: str):
        pass

    @abstractmethod
    def create_collection(self, collection_name, dimension, do_reset=False):
        pass

    @abstractmethod
    def insert_data(self, collection_name: str, text: str, vector: list, metadata=None, record_id=None):
        pass

    
    @abstractmethod
    def insert_many_data(self, collection_name: str, texts: list, vectors: list,
                         metadata=None, record_ids=None, batch_size=50):
        pass

    @abstractmethod
    def search_by_vector(self, collection_name: str, vector: list, top_k: int = 5, include_metadata: bool = False):
        pass