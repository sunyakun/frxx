from typing import Optional

from pymilvus import CollectionSchema, DataType, FieldSchema, MilvusClient

from app.config import Settings, get_settings

settings: Settings = get_settings()

_milvus_client: Optional[MilvusClient] = None

_fields = [
    FieldSchema(
        name="id", dtype=DataType.INT64, auto_id=True, is_primary=True, max_length=200
    ),
    FieldSchema(name="dense_embed", dtype=DataType.FLOAT_VECTOR, dim=1024),
    FieldSchema(name="sparse_embed", dtype=DataType.SPARSE_FLOAT_VECTOR),
    FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
    FieldSchema(name="metadata", dtype=DataType.JSON),
]

milvus_collection_schema = CollectionSchema(fields=_fields)


def get_milvus_client() -> MilvusClient:
    global _milvus_client
    if _milvus_client is None:
        _milvus_client = MilvusClient(
            uri=settings.milvus_uri,
            token=settings.milvus_token,
            db_name=settings.milvus_db_name,
        )
    return _milvus_client
