from ..VectorDB_Interface import VectorDB_Interface
from ..VectorDB_Enums import (DistanceMethodEnums, PgVectorIndexTypeEnum,
                               PgVectorTableSchema, DistanceMethodEnum)
import logging
from models.db_schemes import RetrievedDocument
from typing import Union, List
from sqlalchemy.sql import text as sql_text


class PG_Vector_Provider(VectorDB_Interface):
    def __init__(self, db_client, default_vector_size: int = 786,
                 distance_method: DistanceMethodEnum = DistanceMethodEnum.COSINE.value,
                 index_threshold: int = 1000):
        self.db_client = db_client
        self.default_vector_size = default_vector_size
        self.distance_method = distance_method
        self.index_threshold = index_threshold
        self.pgvector_table_prefix = PgVectorTableSchema._PREFIX.value
        self.logger = logging.getLogger("uvicorn")
        self.default_index_name = lambda collection_name: f"{self.pgvector_table_prefix}{collection_name}_idx"

    async def connect(self):
        async with self.db_client() as connection:
            async with connection.begin():
                await connection.execute(sql_text("CREATE EXTENSION IF NOT EXISTS vector;"))

    async def disconnect(self):
        pass

    async def is_collection_excisted(self, collection_name: str) -> bool:
        record = None
        async with self.db_client() as connection:
            async with connection.begin():
                list_table = sql_text(
                    "SELECT * FROM pg_tables WHERE tablename = :collection_name"
                )
                result = await connection.execute(
                    list_table,
                    {"collection_name": self.pgvector_table_prefix + collection_name}
                )
                record = result.scalar_one_or_none()
        return record

    async def list_all_collections(self):
        records = None
        async with self.db_client() as connection:
            async with connection.begin():
                list_table = sql_text(
                    "SELECT tablename FROM pg_tables WHERE tablename LIKE :prefix"
                )
                result = await connection.execute(
                    list_table,
                    {"prefix": self.pgvector_table_prefix + "%"}
                )
                records = result.scalars().all()
        return [record[len(self.pgvector_table_prefix):] for record in records]

    async def get_collection_info(self, collection_name: str) -> Union[dict, None]:
        async with self.db_client() as connection:
            async with connection.begin():
                table_info_sql = sql_text(f"""
                SELECT schemaname, tablename, tableowner, tablespace, hasindexes
                FROM pg_tables
                WHERE tablename = :collection_name
                """)
                count_sql = sql_text(
                    f"SELECT COUNT(*) FROM {self.pgvector_table_prefix + collection_name}"
                )
                table_info_result = await connection.execute(
                    table_info_sql,
                    {"collection_name": self.pgvector_table_prefix + collection_name}
                )
                record_count = await connection.execute(count_sql)
                table_data = table_info_result.fetchone()
                if not table_data:
                    return None
                return {
                    "table_data": dict(table_data._mapping),
                    "record_count": record_count.scalar_one()
                }

    async def delete_collection(self, collection_name: str):
        if await self.is_collection_excisted(collection_name):
            async with self.db_client() as connection:
                async with connection.begin():
                    self.logger.info(f"Deleting collection '{collection_name}'...")
                    drop_table = sql_text(
                        f"DROP TABLE {self.pgvector_table_prefix + collection_name}"
                    )
                    await connection.execute(drop_table)
                    self.logger.info(f"Collection '{collection_name}' deleted successfully.")
            return True

    # FIX: removed the FOREIGN KEY constraint that referenced a non-existent
    # `{prefix}{collection_name}_chunks` table. That table is never created anywhere
    # in this codebase, so every call to create_collection was raising a
    # "referenced table does not exist" error and the collection was never created.
    # The chunk relationship is already tracked on the application side via
    # ChunkModel / DataChunk; a DB-level FK here is unnecessary and broken.
    async def create_collection(self, collection_name, dimension, do_reset=False):
        if do_reset:
            await self.delete_collection(collection_name)

        if not await self.is_collection_excisted(collection_name):
            async with self.db_client() as connection:
                async with connection.begin():
                    create_table = sql_text(f"""
                    CREATE TABLE {self.pgvector_table_prefix + collection_name} (
                        {PgVectorTableSchema.ID.value} SERIAL PRIMARY KEY,
                        {PgVectorTableSchema.TEXT.value} TEXT,
                        {PgVectorTableSchema.VECTOR.value} VECTOR({dimension}),
                        {PgVectorTableSchema.METADATA.value} JSONB DEFAULT '{{}}'::jsonb,
                        {PgVectorTableSchema.CHUNK_ID.value} INTEGER UNIQUE  -- <-- ADD UNIQUE
                    );
                    """)
                    await connection.execute(create_table)
                    self.logger.info(f"Collection '{collection_name}' created successfully.")
            return True
        else:
            self.logger.info(f"Collection '{collection_name}' already exists.")
            return False

    async def is_index_existed(self, collection_name: str) -> bool:
        index_name = self.default_index_name(collection_name)
        async with self.db_client() as connection:
            async with connection.begin():
                list_index = sql_text(
                    "SELECT * FROM pg_indexes WHERE tablename = :collection_name AND indexname = :index_name"
                )
                result = await connection.execute(
                    list_index,
                    {"collection_name": self.pgvector_table_prefix + collection_name,
                     "index_name": index_name}
                )
                record = bool(result.scalar_one_or_none())
            return record

    async def create_index_vector(self, collection_name: str,
                                   index_type: PgVectorIndexTypeEnum = PgVectorIndexTypeEnum.IVFFLAT.value):
        is_index_existed = await self.is_index_existed(collection_name)
        if is_index_existed:
            self.logger.info(f"Index for collection '{collection_name}' already exists.")
            return False
        async with self.db_client() as connection:
            async with connection.begin():
                count_sql = sql_text(
                    f"SELECT COUNT(*) FROM {self.pgvector_table_prefix + collection_name}"
                )
                record_count = await connection.execute(count_sql)
                record_count = record_count.scalar_one()
                if record_count < self.index_threshold:
                    self.logger.info(
                        f"Collection '{collection_name}' has {record_count} records, "
                        f"below threshold of {self.index_threshold}. Skipping index creation."
                    )
                    return False
                self.logger.info(
                    f"START: Creating index for '{collection_name}' with {record_count} records."
                )
                index_name = self.default_index_name(collection_name)
                create_index_sql = sql_text(
                    f"CREATE INDEX {index_name} ON {self.pgvector_table_prefix + collection_name} "
                    f"USING {index_type} "
                    f"({PgVectorTableSchema.VECTOR.value} {DistanceMethodEnums[self.distance_method.upper()].value})"
                )
                await connection.execute(create_index_sql)
                self.logger.info(
                    f"END: Creating index for '{collection_name}' with {record_count} records."
                )

    async def reset_vector_index(self, collection_name: str,
                                  index_type: PgVectorIndexTypeEnum = PgVectorIndexTypeEnum.HNSW.value) -> bool:
        index_name = self.default_index_name(collection_name)
        async with self.db_client() as connection:
            async with connection.begin():
                drop_index_sql = sql_text(f"DROP INDEX IF EXISTS {index_name}")
                await connection.execute(drop_index_sql)
                self.logger.info(f"Index '{index_name}' dropped successfully.")
        return await self.create_index_vector(collection_name, index_type=index_type)

    async def insert_data(self, collection_name: str, text: str, vector: list,
                      metadata=None, record_id=None):
        is_collection_existed = await self.is_collection_excisted(collection_name)
        if not is_collection_existed:
            self.logger.error(f"Collection '{collection_name}' does not exist.")
            return False
        if not record_id:
            self.logger.error("record_id is required for PG_Vector_Provider.")
            return False

        async with self.db_client() as connection:
            async with connection.begin():
                insert_sql = sql_text(f"""
                INSERT INTO {self.pgvector_table_prefix + collection_name}
                    ({PgVectorTableSchema.TEXT.value},
                    {PgVectorTableSchema.VECTOR.value},
                    {PgVectorTableSchema.METADATA.value},
                    {PgVectorTableSchema.CHUNK_ID.value})
                VALUES (:text, :vector, :metadata, :chunk_id)
                ON CONFLICT ({PgVectorTableSchema.CHUNK_ID.value}) DO UPDATE
                    SET {PgVectorTableSchema.TEXT.value}     = EXCLUDED.{PgVectorTableSchema.TEXT.value},
                        {PgVectorTableSchema.VECTOR.value}   = EXCLUDED.{PgVectorTableSchema.VECTOR.value},
                        {PgVectorTableSchema.METADATA.value} = EXCLUDED.{PgVectorTableSchema.METADATA.value}
                """)
                await connection.execute(insert_sql, {
                    "text": text,
                    "vector": f"[{','.join(map(str, vector))}]",
                    "metadata": metadata,
                    "chunk_id": record_id,
                })
        return True

    
    async def insert_many_data(self, collection_name: str, texts: list, vectors: list,
                           metadata=None, record_ids=None, batch_size=50):
        is_collection_existed = await self.is_collection_excisted(collection_name)
        if not is_collection_existed:
            self.logger.error(f"Collection '{collection_name}' does not exist.")
            return False
        if record_ids and len(record_ids) != len(texts):
            self.logger.error("Length of record_ids must match length of texts.")
            return False

        if metadata is None:
            metadata = [None] * len(texts)

        async with self.db_client() as connection:
            async with connection.begin():
                for i in range(0, len(texts), batch_size):
                    batch_texts    = texts[i:i + batch_size]
                    batch_vectors  = vectors[i:i + batch_size]
                    batch_metadatas = metadata[i:i + batch_size]
                    batch_record_ids = (
                        record_ids[i:i + batch_size]
                        if record_ids else [None] * len(batch_texts)
                    )

                    # FIX: Use ON CONFLICT (chunk_id) DO UPDATE instead of plain INSERT.
                    # Plain INSERT adds a new row every time push is called (even without
                    # do_reset), because SERIAL gives a fresh PK each time. This caused
                    # identical chunks to appear multiple times in search results.
                    # ON CONFLICT makes the operation idempotent — re-indexing the same
                    # chunk updates the existing row instead of duplicating it.
                    insert_sql = sql_text(f"""
                    INSERT INTO {self.pgvector_table_prefix + collection_name}
                        ({PgVectorTableSchema.TEXT.value},
                        {PgVectorTableSchema.VECTOR.value},
                        {PgVectorTableSchema.METADATA.value},
                        {PgVectorTableSchema.CHUNK_ID.value})
                    VALUES (:text, :vector, :metadata, :chunk_id)
                    ON CONFLICT ({PgVectorTableSchema.CHUNK_ID.value}) DO UPDATE
                        SET {PgVectorTableSchema.TEXT.value}     = EXCLUDED.{PgVectorTableSchema.TEXT.value},
                            {PgVectorTableSchema.VECTOR.value}   = EXCLUDED.{PgVectorTableSchema.VECTOR.value},
                            {PgVectorTableSchema.METADATA.value} = EXCLUDED.{PgVectorTableSchema.METADATA.value}
                    """)
                    await connection.executemany(insert_sql, [
                        {
                            "text": text,
                            "vector": f"[{','.join(map(str, vector))}]",
                            "metadata": meta,
                            "chunk_id": chunk_id,
                        }
                        for text, vector, meta, chunk_id in zip(
                            batch_texts, batch_vectors, batch_metadatas, batch_record_ids
                        )
                    ])
        return True

    async def search_by_vector(self, collection_name: str, vector: list, top_k: int = 5,
                                include_metadata: bool = False):
        is_collection_existed = await self.is_collection_excisted(collection_name)
        if not is_collection_existed:
            self.logger.error(f"Collection '{collection_name}' does not exist.")
            return []
        vector_str = f"[{','.join(map(str, vector))}]"
        async with self.db_client() as connection:
            async with connection.begin():
                search_sql = sql_text(f"""
                SELECT {PgVectorTableSchema.ID.value},
                       {PgVectorTableSchema.TEXT.value},
                       {PgVectorTableSchema.METADATA.value},
                       1 - ({PgVectorTableSchema.VECTOR.value} <-> :vector) AS score
                FROM {self.pgvector_table_prefix + collection_name}
                ORDER BY {PgVectorTableSchema.VECTOR.value} <-> :vector
                LIMIT :top_k
                """)
                result = await connection.execute(search_sql, {"vector": vector_str, "top_k": top_k})
                records = result.fetchall()
                return [
                    {
                        "score": record.score,
                        "payload": {
                            "text": record[PgVectorTableSchema.TEXT.value],
                            "metadata": record[PgVectorTableSchema.METADATA.value],
                        }
                    }
                    for record in records
                ]