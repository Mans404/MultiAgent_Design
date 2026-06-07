from .BaseDataModel import BaseDataModel
from .db_schemes import DataChunk
from .enums.DataBaseEnum import DataBaseEnum
from bson.objectid import ObjectId
from sqlalchemy.future import select
from sqlalchemy import func, delete


class ChunkModel(BaseDataModel):

    def __init__(self, db_client: object):
        super().__init__(db_client=db_client)
        self.db_client = db_client

    @classmethod
    async def create_instance(cls, db_client: object):
        instance = cls(db_client)
        return instance

    async def create_chunk(self, chunk: DataChunk):
        async with self.db_client() as session:
            async with session.begin():
                session.add(chunk)
            await session.commit()
            await session.refresh(chunk)
        return chunk

    async def get_chunk(self, chunk_id: str):
        async with self.db_client() as session:
            query = select(DataChunk).where(DataChunk._id == ObjectId(chunk_id))
            result = await session.execute(query)
            return result.scalar_one_or_none()

    async def insert_many_chunks(self, chunks: list, batch_size: int = 100):
        async with self.db_client() as session:
            async with session.begin():
                for i in range(0, len(chunks), batch_size):
                    batch = chunks[i:i + batch_size]
                    session.add_all(batch)
            await session.commit()
        return len(chunks)

    async def delete_chunks_by_project_id(self, project_id: ObjectId):
        async with self.db_client() as session:
            async with session.begin():
                query = delete(DataChunk).where(DataChunk.chunk_project_id == project_id)
                result = await session.execute(query)
        return result.rowcount

    async def get_project_chunks(self, project_id: ObjectId, page_no: int = 1, page_size: int = 50):
        async with self.db_client() as session:
            offset = (page_no - 1) * page_size
            query = (
                select(DataChunk)
                .where(DataChunk.chunk_project_id == project_id)
                .offset(offset)
                .limit(page_size)
            )
            result = await session.execute(query)
            return result.scalars().all()

  
    async def get_total_chunks_count(self, project_id: ObjectId):
        async with self.db_client() as session:
            query = (
                select(func.count(DataChunk.chunk_id))
                .where(DataChunk.chunk_project_id == project_id)
            )
            result = await session.execute(query)
        return result.scalar_one()


    async def update_chunks_vectors(self, chunks: list, vectors: list):
        async with self.db_client() as session:
            async with session.begin():
                for chunk, vector in zip(chunks, vectors):
                    db_chunk = await session.get(DataChunk, chunk.chunk_id)
                    if db_chunk:
                        db_chunk.chunk_vector = vector