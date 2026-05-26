from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class RankerParams(BaseModel):
    k: Optional[int] = Field(default=60, description="RRF 参数")
    weights: Optional[List[float]] = Field(default=None, description="加权排序权重")


class ChatCompletionRequest(BaseModel):
    query: str = Field(..., min_length=1, description="用户问题")
    top_k: Optional[int] = Field(default=3, ge=1, le=10, description="检索结果数")
    stream: Optional[bool] = Field(default=True, description="是否流式输出")
    ranker: Optional[Literal["rrf", "weighted"]] = Field(
        default="rrf", description="排序器类型"
    )
    ranker_params: Optional[RankerParams] = Field(
        default_factory=RankerParams, description="排序器参数"
    )


class RetrievalRequest(BaseModel):
    query: str = Field(..., min_length=1, description="检索查询文本")
    top_k: Optional[int] = Field(default=5, ge=1, le=10, description="返回结果数")
    mode: Optional[Literal["hybrid", "dense", "sparse"]] = Field(
        default="dense", description="检索模式"
    )
    include_embeddings: Optional[bool] = Field(
        default=False, description="是否返回嵌入向量"
    )


class ChunkingParams(BaseModel):
    max_characters: Optional[int] = Field(
        default=1000, ge=100, description="分块最大字符数"
    )
    overlap: Optional[int] = Field(default=50, ge=0, description="分块重叠字符数")


class DocumentMetadata(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    source: Optional[str] = None
    chapter: Optional[int] = None

    model_config = {"extra": "allow"}


class DocumentUploadRequest(BaseModel):
    content: str = Field(..., min_length=1, description="文档内容")
    metadata: Optional[DocumentMetadata] = Field(default=None, description="文档元数据")
    chunking: Optional[ChunkingParams] = Field(
        default_factory=ChunkingParams, description="分块参数"
    )


class RetrievalResult(BaseModel):
    id: int
    text: str
    score: float
    metadata: Optional[Dict[str, Any]] = None


class StreamChunk(BaseModel):
    type: Literal["thinking", "content", "retrieval", "done", "error"]
    content: Optional[str] = None
    retrieval_results: Optional[List[RetrievalResult]] = None
    error: Optional[str] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None


class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    answer: str
    retrieval_results: List[RetrievalResult]
    reasoning: Optional[str] = None
    usage: Usage
    model: str


class RetrievalResponse(BaseModel):
    results: List[RetrievalResult]
    latency_ms: float
    total_matches: int


class DocumentUploadResponse(BaseModel):
    document_id: str
    chunk_count: int
    indexing_latency_ms: float
    status: Literal["success", "partial", "failed"]


class ComponentHealth(BaseModel):
    status: Literal["healthy", "unhealthy"]
    latency_ms: float


class HealthResponse(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy"]
    components: Dict[str, ComponentHealth]
    version: str = "1.0.0"


class ErrorResponse(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None
    request_id: str


class ErrorMessage(BaseModel):
    message: str
