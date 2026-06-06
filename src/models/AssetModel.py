from sqlalchemy import select

from .BaseDataModel import BaseDataModel
from .db_schemes import Asset
from .enums.DataBaseEnum import DataBaseEnum
from bson import ObjectId

class AssetModel(BaseDataModel):

    def __init__(self, db_client: object):
        super().__init__(db_client=db_client)
        self.db_client = db_client

    @classmethod
    async def create_instance(cls, db_client: object):
        instance = cls(db_client)
        return instance

    async def create_asset(self, asset: Asset):
        async with self.db_client() as session:
            async with session.begin():
                session.add(asset)
            await session.commit()
            await session.refresh(asset)
        return asset

    async def get_all_project_assets(self, asset_project_id: str, asset_type: str):
        
        project_id = ObjectId(asset_project_id) if isinstance(asset_project_id, str) else asset_project_id

        async with self.db_client() as session:
            query = select(Asset).where(
                Asset.asset_project_id == project_id,
                Asset.asset_type == asset_type
            )
            result = await session.execute(query)
            assets = result.scalars().all()
            return assets

    async def get_asset_record(self, asset_project_id: str, asset_name: str):
     
        project_id = ObjectId(asset_project_id) if isinstance(asset_project_id, str) else asset_project_id

        async with self.db_client() as session:
            query = select(Asset).where(
                Asset.asset_project_id == project_id,
                Asset.asset_name == asset_name
            )
            result = await session.execute(query)
            asset = result.scalar_one_or_none()
            return asset