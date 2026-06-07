from enum import Enum
class VectorDBEnum(Enum):
    QDRANT = "QDRANT"
    PGVECTOR = "PGVECTOR"

class DistanceMethodEnum(Enum):
    COSINE = "cosine"
    EUCLIDEAN = "euclidean"
    DOT_PRODUCT = "dot_product"

class PgVectorTableSchema(Enum):
    ID = "id"
    VECTOR = "vector"
    TEXT = "text"
    CHUNK_ID = "chunk_id"
    METADATA = "metadata"
    _PREFIX = "pgvector_"

class DistanceMethodEnums(Enum):
    COSINE = "vector_cosine_ops"
    EUCLIDEAN = "vector_l2_ops"
class PgVectorIndexTypeEnum(Enum):
    IVFFLAT = "ivfflat"
    HNSW = "hnsw"