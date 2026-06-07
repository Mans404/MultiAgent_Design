from ..VectorDB_Interface import VectorDB_Interface
from ..VectorDB_Enums import DistanceMethodEnum
from qdrant_client import AsyncQdrantClient
from qdrant_client import models
import logging
import hashlib
from typing import Union


class QdrantDB(VectorDB_Interface):
    def __init__(self, db_client: str, default_vector_size: int = 786,
                 distance_method: DistanceMethodEnum = DistanceMethodEnum.COSINE.value,
                 index_threshold: int = 1000):
        self.db_client = db_client
        self.client = None
        self.default_vector_size = default_vector_size

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

    # -------------------------------------------------------------------------
    # Connection management
    # -------------------------------------------------------------------------

    async def connect(self):
        self.client = AsyncQdrantClient(path=self.db_client)
        self.logger.info(f"Connected to QdrantDB at {self.db_client}")

    async def disconnect(self):
        if self.client is not None:
            await self.client.close()
            self.client = None
        self.logger.info("Disconnected from QdrantDB")

    # -------------------------------------------------------------------------
    # Collection helpers
    # -------------------------------------------------------------------------

    async def is_collection_excisted(self, collection_name: str) -> bool:
        return await self.client.collection_exists(collection_name)

    async def list_all_collections(self):
        return await self.client.get_collections()

    async def get_collection_info(self, collection_name: str):
        return await self.client.get_collection(collection_name)

    async def delete_collection(self, collection_name: str):
        if await self.is_collection_excisted(collection_name):
            await self.client.delete_collection(collection_name)
            self.logger.info(f"Collection '{collection_name}' deleted successfully.")

    async def create_collection(self, collection_name: str, dimension: int, do_reset: bool = False):
        if do_reset:
            await self.delete_collection(collection_name)

        if not await self.is_collection_excisted(collection_name):
            await self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=dimension,
                    distance=self.distance_method,
                ),
            )
            self.logger.info(f"Collection '{collection_name}' created successfully.")
            return True

        self.logger.info(f"Collection '{collection_name}' already exists.")
        return False

    # -------------------------------------------------------------------------
    # Data insertion
    # -------------------------------------------------------------------------

    async def insert_data(self, collection_name: str, text: str, vector: list,
                          metadata=None, record_id=None) -> bool:
        if not await self.is_collection_excisted(collection_name):
            self.logger.error(f"Collection '{collection_name}' does not exist.")
            return False

        try:
            if record_id is None:
                record_id = hashlib.md5(text.encode()).hexdigest()

            payload = {"text": text, "metadata": metadata} if metadata else {"text": text}
            await self.client.upsert(
                collection_name=collection_name,
                points=[models.PointStruct(id=record_id, vector=vector, payload=payload)],
            )
        except Exception as e:
            self.logger.error(f"Cannot insert new record: {e}")
            return False

        self.logger.info(f"Data inserted into '{collection_name}' successfully.")
        return True

    # FIX: renamed parameter `metadata` to match the interface signature (was `metadata` here,
    # but interface previously had `metadatas` — now both are unified as `metadata`).
    #
    # FIX: removed MD5 hash fallback as the primary ID strategy.
    # Previously all record IDs were MD5(text), so two chunks with identical text
    # (e.g. duplicate uploads, shared boilerplate paragraphs) produced the same hash,
    # causing Qdrant's upsert to silently collapse them into one point. The DB still
    # had two chunk rows referencing that single point → duplicate results on search.
    # Now we use the real DB chunk_id (integer) passed from NLPController, which is
    # always unique. MD5 is only used as a last resort when no record_id is provided.
    async def insert_many_data(self, collection_name: str, texts: list, vectors: list,
                               metadata=None, record_ids=None, batch_size: int = 50) -> bool:
        if metadata is None:
            metadata = [None] * len(texts)

        if record_ids is None:
            # Last-resort fallback: should not be reached in normal flow because
            # NLPController now always passes chunk_ids as record_ids.
            self.logger.warning(
                "insert_many_data called without record_ids — falling back to MD5 hashes. "
                "Identical chunk texts will collide. Pass chunk_ids to avoid this."
            )
            record_ids = [hashlib.md5(text.encode()).hexdigest() for text in texts]
        else:
            # Only fill in None slots with MD5, leave explicit IDs untouched.
            record_ids = [
                rid if rid is not None else hashlib.md5(text.encode()).hexdigest()
                for rid, text in zip(record_ids, texts)
            ]

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
                    payload=(
                        {"text": batch_texts[j], "metadata": batch_metadata[j]}
                        if batch_metadata[j]
                        else {"text": batch_texts[j]}
                    ),
                )
                for j in range(len(batch_texts))
            ]

            try:
                await self.client.upsert(collection_name=collection_name, points=batch_points)
            except Exception as e:
                self.logger.error(f"Error inserting batch at index {i}: {e}")
                return False

        self.logger.info(f"{len(texts)} records inserted into '{collection_name}' successfully.")
        return True

    # -------------------------------------------------------------------------
    # Search
    # -------------------------------------------------------------------------

    async def search_by_vector(self, collection_name: str, vector: list, top_k: int = 5,
                               include_metadata: bool = False) -> list:
        try:
            results = await self.client.query_points(
                collection_name=collection_name,
                query=vector,
                limit=top_k,
                with_payload=True,
            )
        except ValueError as e:
            if "not found" in str(e).lower():
                self.logger.error(f"Collection '{collection_name}' does not exist. Index the project first.")
                raise ValueError(f"Collection '{collection_name}' not found. Please index the project before searching.")
            raise

        # Returns a consistent { score, payload: { text, metadata } } structure
        # so that NLPController can always access doc["payload"]["text"] safely
        # regardless of which vector DB provider is active.
        return [
            {
                "score": r.score,
                "payload": {
                    "text": r.payload.get("text", ""),
                    "metadata": r.payload.get("metadata"),
                }
            }
            for r in results.points
        ]