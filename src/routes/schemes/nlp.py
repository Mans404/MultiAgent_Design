from pydantic import BaseModel, field_validator
from typing import Optional

class PushRequest(BaseModel):
    file_id: str = None
    chunk_size: Optional[int] = 100
    overlap_size: Optional[int] = 20
    do_reset: Optional[int] = 0

class SearchRequest(BaseModel):
    text: str
    top_k: Optional[int] = 2