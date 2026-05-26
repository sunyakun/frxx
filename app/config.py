from functools import lru_cache
from pprint import pprint

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=[".env.local", ".env.test", ".env"],
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Milvus 配置
    milvus_grpc_uri: str | None = None
    milvus_grpc_host: str = "127.0.0.1"
    milvus_grpc_port: str = "19530"
    milvus_db_name: str = "default"
    milvus_collection_name: str = "frxx"
    milvus_token: str = "root:Milvus"

    # GLM 配置
    glm_base_url: str | None = None
    glm_api_key: str | None = None

    # LLM API 配置
    llm_api_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""

    # 检索配置
    max_top_k: int = 10
    default_top_k: int = 3

    # 文档处理配置
    default_chunk_size: int = 1000
    default_overlap: int = 50
    batch_size: int = 32

    # 超时配置 (秒)
    embedding_timeout: int = 30
    retrieval_timeout: int = 10
    llm_timeout: int = 60

    # 性能配置
    max_concurrent_requests: int = 100

    # 系统提示词
    system_prompt: str = """## 角色设定

你是《凡人修仙传》专属剧情问答助手，深度熟悉原著设定与人物情节。用户将向你咨询小说相关剧情、人物、设定、情节细节等问题。用户问题包含两部分："检索结果"和"用户问题"，"检索结果"一节包含了与这个问题相关的小说原文片段，你需严格依托检索到的小说原文片段作答。

## 约束规则

1. 所有回答必须完全依据系统检索出的原著片段内容，不得私自脑补、编造、延伸原著外剧情与设定。
2. 若检索片段中无用户问题对应的相关信息，统一回复：暂时不清楚这个问题的相关内容。
3. 若用户提问内容与《凡人修仙传》无关，需礼貌委婉谢绝，并告知仅解答本书相关问题。
4. 回答语言简洁易懂，贴合原著语境，不随意篡改人物关系、剧情走向和修仙设定。"""

    @property
    def milvus_uri(self) -> str:
        if self.milvus_grpc_uri:
            return self.milvus_grpc_uri
        return f"http://{self.milvus_grpc_host}:{self.milvus_grpc_port}"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    print("Load settings:")
    pprint(settings.model_dump())
    return settings
