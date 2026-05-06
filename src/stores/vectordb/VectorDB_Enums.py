from enum import Enum
class VectorDBEnum(Enum):
    QDRANT = "QDRANT"

class DistanceMethodEnum(Enum):
    COSINE = "cosine"
    EUCLIDEAN = "euclidean"
    DOT_PRODUCT = "dot_product"