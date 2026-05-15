from ..VectorDB_Interface import VectorDB_Interface
from ..VectorDB_Enums import DistanceMethodEnum
from qdrant_client import QdrantClient
from qdrant_client import models 
import logging

class QdrantDB(VectorDB_Interface):
    def __init__(self, db_path: str, distance_method: DistanceMethodEnum = DistanceMethodEnum.COSINE):
        self.db_path = db_path
        self.distance_method = distance_method
        self.client = None
        if distance_method == DistanceMethodEnum.COSINE:
            self.distance_method = models.Distance.COSINE
        elif distance_method == DistanceMethodEnum.EUCLIDEAN:
            self.distance_method = models.Distance.EUCLIDEAN
        elif distance_method == DistanceMethodEnum.DOT_PRODUCT:
            self.distance_method = models.Distance.DOT
        self.logger = logging.getLogger(__name__)
    def connect(self):
        self.client = QdrantClient(path=self.db_path)
        self.logger.info(f"Connected to QdrantDB at {self.db_path}")
    def disconnect(self):
        self.client = None
        self.logger.info("Disconnected from QdrantDB")

    def is_collection_excisted(self, collection_name: str) -> bool:
        
        return self.client.collection_exists(collection_name)
    
    def list_all_collections(self):
        return self.client.get_collections()
    
    def get_collection_info(self, collection_name: str):
        return self.client.get_collection(collection_name)
    
    def delete_collection(self, collection_name: str):
        if self.is_collection_excisted(collection_name):
            self.client.delete_collection(collection_name)
            self.logger.info(f"Collection '{collection_name}' deleted successfully.")

    def create_collection(self, collection_name, dimension, do_reset=False):
            self.delete_collection(collection_name) if do_reset else None

            if not self.is_collection_excisted(collection_name):
                self.client.recreate_collection(
                    collection_name=collection_name,
                    vectors_config=models.VectorParams(size=dimension, distance=self.distance_method)
                )
                self.logger.info(f"Collection '{collection_name}' created successfully.")
                return True
            else:
                self.logger.info(f"Collection '{collection_name}' already exists.")
                return False

    def insert_data(self, collection_name: str, text: str, vector: list, metadata=None, record_id=None):
            if not self.is_collection_excisted(collection_name):
                self.logger.error(f"Collection '{collection_name}' does not exist. Please create it first.")
                return False
            try:
                self.client.upload_records(
                    collection_name=collection_name,
                    records=[
                        models.Record(
                            id=record_id,
                            vector=vector,
                            payload={"text": text, "metadata": metadata} if metadata else {"text": text}
                        )
                    ]
                )
            except Exception as e:
                     self.logger.error(f"Cannot insert new record {e}")
                     return False
            self.logger.info(f"Data inserted into collection '{collection_name}' successfully.")
            return True
    def insert_many_data(self, collection_name: str,
                          texts: list, vectors: list,
                            metadatas=None,
                              record_ids=None,
                              batch_size=50,):
            if metadatas is None:
                metadatas = [None] * len(texts)

            if record_ids is None:
                record_ids = [None] * len(texts)

            for i in range(0, len(texts), batch_size):
                batch_end = i + batch_size
                batch_texts = texts[i:batch_end]
                batch_vectors = vectors[i:batch_end]
                batch_metadatas = metadatas[i:batch_end]
                batch_records = [
                    models.Record(
                        id=record_ids[j],
                        vector=batch_vectors[j],
                        payload={"text": batch_texts[j], "metadata": batch_metadatas[j]} if batch_metadatas[j] else {"text": batch_texts[j]}
                    )
                    for j in range(len(batch_texts))
                ]
                try:
                    self.client.upload_records(
                        collection_name=collection_name,
                        records=batch_records,
                    )
                except Exception as e:
                     self.logger.error(f"Error inserting batch starting at index {i}: {e}")
                     return False
                     
            self.logger.info(f"{len(texts)} records inserted into collection '{collection_name}' successfully.")
            return True
    def search_by_vector(self, collection_name: str, vector: list, top_k: int = 5, include_metadata: bool = False):
            return self.client.search(
                collection_name=collection_name,
                query_vector=vector,
                limit=top_k,
                with_payload=include_metadata
            )