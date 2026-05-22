from ..VectorDB_Interface import VectorDB_Interface
from ..VectorDB_Enums import DistanceMethodEnum
from qdrant_client import QdrantClient
from qdrant_client import models 
import logging
from uuid import uuid4
from typing import Union

class QdrantDB(VectorDB_Interface):
    def __init__(self, db_path: str, distance_method: Union[DistanceMethodEnum, str] = DistanceMethodEnum.COSINE):
        self.db_path = db_path
        self.client = None
        if isinstance(distance_method, str):
            normalized_distance_method = distance_method.strip().lower()
            distance_method = DistanceMethodEnum(normalized_distance_method)

        distance_method_map = {
            DistanceMethodEnum.COSINE: models.Distance.COSINE,
            DistanceMethodEnum.EUCLIDEAN: models.Distance.EUCLID,
            DistanceMethodEnum.DOT_PRODUCT: models.Distance.DOT,
        }
        self.distance_method = distance_method_map[distance_method]
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
            if record_id is None:
                record_id = str(uuid4())

            payload = {"text": text, "metadata": metadata} if metadata else {"text": text}

            self.client.upsert(
                collection_name=collection_name,
                points=[
                    models.PointStruct(
                        id=record_id,
                        vector=vector,
                        payload=payload
                    )
                ]
            )
        except Exception as e:
            self.logger.error(f"Cannot insert new record {e}")
            return False
        self.logger.info(f"Data inserted into collection '{collection_name}' successfully.")
        return True
    def insert_many_data(self, collection_name: str, texts: list, vectors: list,
                        metadata=None, record_ids=None, batch_size=50):
        if metadata is None:
            metadata = [None] * len(texts)

        if record_ids is None:
            record_ids = [str(uuid4()) for _ in range(len(texts))]
        else:
            record_ids = [rid if rid is not None else str(uuid4()) for rid in record_ids]

        for i in range(0, len(texts), batch_size):
            batch_end = i + batch_size
            batch_texts = texts[i:batch_end]
            batch_vectors = vectors[i:batch_end]
            batch_metadata = metadata[i:batch_end]
            batch_ids = record_ids[i:batch_end]

            batch_points = [
                models.PointStruct(
                    id=batch_ids[j],
                    vector=batch_vectors[j],
                    payload={"text": batch_texts[j], "metadata": batch_metadata[j]} if batch_metadata[j] else {"text": batch_texts[j]}
                )
                for j in range(len(batch_texts))
            ]
            try:
                self.client.upsert(
                    collection_name=collection_name,
                    points=batch_points
                )
            except Exception as e:
                self.logger.error(f"Error inserting batch starting at index {i}: {e}")
                return False

        self.logger.info(f"{len(texts)} records inserted into collection '{collection_name}' successfully.")
        return True
    def search_by_vector(self, collection_name: str, vector: list, top_k: int = 5, include_metadata: bool = False):
        results = self.client.query_points(
        collection_name=collection_name,
        query=vector,
        limit=top_k,
        with_payload=True
        )
        return [r.model_dump() for r in results.points]