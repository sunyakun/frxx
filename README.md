# RAG 检索系统设计文档

## 1. 系统概述

RAG (Retrieval-Augmented Generation) 检索系统基于向量数据库和大语言模型，为《凡人修仙传》小说提供智能问答服务。系统采用混合检索策略，结合稠密向量和稀疏向量搜索，并通过 RRFRanker 进行排序优化。

### 1.1 核心组件

| 组件 | 描述 |
|------|------|
| Milvus | 向量数据库，存储文档嵌入 |
| BGEM3 | 嵌入模型，生成稠密和稀疏向量 |
| LLM API | GLM-4.7，生成最终答案 |
| FastAPI | HTTP 服务框架 |

### 1.2 技术架构

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│  FastAPI    │────▶│  Milvus DB  │
└─────────────┘     └─────────────┘     └─────────────┘
                         │
                         ▼
                   ┌─────────────┐
                   │  LLM API    │
                   │  (GLM-4.7)  │
                   └─────────────┘
```

## 2. HTTP 接口设计

### 2.1 基础信息

| 属性 | 值 |
|------|-----|
| Base URL | `/api/v1` |
| 内容类型 | `application/json` |
| 编码 | UTF-8 |

---

### 2.2 检索问答接口

**接口路径**: `POST /api/v1/chat/completions`

**接口描述**: 基于检索结果生成流式问答响应

#### 2.2.1 请求结构

```typescript
interface ChatCompletionRequest {
  // 用户问题
  query: string;

  // 检索结果数 (可选，默认 3)
  top_k?: number;

  // 是否流式输出 (可选，默认 true)
  stream?: boolean;

  // 排序器类型 (可选，默认 "rrf")
  ranker?: "rrf" | "weighted";

  // 排序器参数 (可选)
  ranker_params?: {
    k?: number;           // RRF 参数，默认 60
    weights?: number[];   // 加权排序的权重
  };
}
```

**请求示例**:

```json
{
  "query": "虚天鼎的作用是什么？",
  "top_k": 3,
  "stream": true,
  "ranker": "rrf",
  "ranker_params": {
    "k": 60
  }
}
```

#### 2.2.2 流式响应结构 (stream=true)

SSE (Server-Sent Events) 格式，每行以 `data: ` 前缀开头。

```typescript
interface StreamChunk {
  // 块类型
  type: "thinking" | "content" | "retrieval" | "done" | "error";

  // 内容
  content?: string;

  // 检索到的文档片段
  retrieval_results?: Array<{
    id: string;
    text: string;
    score: number;
    // 来自 Milvus collection 的 metadata 字段
    metadata?: Record<string, any>;
  }>;

  // 错误信息
  error?: string;

  // 提示词信息
  prompt_tokens?: number;
  completion_tokens?: number;
  total_tokens?: number;
}
```

**流式响应示例**:

```
data: {"type":"retrieval","retrieval_results":[{"id":"abc123","text":"虚天鼎是一件通天灵宝...","score":0.95,"metadata":{"title":"虚天殿","chapter":234}}]}
data: {"type":"thinking","content":"用户询问虚天鼎的作用..."}
data: {"type":"content","content":"虚天鼎是《凡人修仙传》中的"}
data: {"type":"content","content":"重要通天灵宝，主要用于..."}
data: {"type":"done"}
```

#### 2.2.3 非流式响应结构 (stream=false)

```typescript
interface ChatCompletionResponse {
  // 最终答案
  answer: string;

  // 检索到的文档片段
  retrieval_results: Array<{
    id: string;
    text: string;
    score: number;
    // 来自 Milvus collection 的 metadata 字段
    metadata?: Record<string, any>;
  }>;

  // 思考过程
  reasoning?: string;

  // Token 使用统计
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };

  // 模型信息
  model: string;
}
```

**非流式响应示例**:

```json
{
  "answer": "虚天鼎是《凡人修仙传》中的重要通天灵宝，主要用于压制阵眼和储存灵力...",
  "retrieval_results": [
    {
      "id": "abc123",
      "text": "虚天鼎是一件通天灵宝，能够储存大量灵力...",
      "score": 0.95,
      "metadata": {
        "title": "虚天殿",
        "chapter": 234,
        "source": "凡人修仙传"
      }
    }
  ],
  "reasoning": "用户询问虚天鼎的作用...",
  "usage": {
    "prompt_tokens": 1520,
    "completion_tokens": 380,
    "total_tokens": 1900
  },
  "model": "glm-4.7"
}
```

---

### 2.3 文档检索接口

**接口路径**: `POST /api/v1/retrieval`

**接口描述**: 仅执行检索，不生成答案

#### 2.3.1 请求结构

```typescript
interface RetrievalRequest {
  // 检索查询文本
  query: string;

  // 返回结果数 (可选，默认 5)
  top_k?: number;

  // 检索模式 (可选)
  mode?: "hybrid" | "dense" | "sparse";

  // 是否返回嵌入向量 (可选，默认 false)
  include_embeddings?: boolean;
}
```

**请求示例**:

```json
{
  "query": "韩立的修为等级",
  "top_k": 5,
  "mode": "hybrid"
}
```

#### 2.3.2 响应结构

```typescript
interface RetrievalResponse {
  // 检索到的文档片段
  results: Array<{
    id: string;
    text: string;
    score: number;
    dense_score?: number;
    sparse_score?: number;
    dense_embed?: number[];
    sparse_embed?: Record<number, number>;
  }>;

  // 检索耗时 (毫秒)
  latency_ms: number;

  // 总匹配数
  total_matches: number;
}
```

**响应示例**:

```json
{
  "results": [
    {
      "id": "record_001",
      "text": "韩立此时已是元婴后期大圆满修为...",
      "score": 0.892,
      "dense_score": 0.875,
      "sparse_score": 0.810
    }
  ],
  "latency_ms": 45,
  "total_matches": 152
}
```

---

### 2.4 文档上传接口

**接口路径**: `POST /api/v1/documents`

**接口描述**: 上传文档并建立索引

#### 2.4.1 请求结构

```typescript
interface DocumentUploadRequest {
  // 文档内容
  content: string;

  // 文档元数据
  metadata?: {
    title?: string;
    author?: string;
    source?: string;
    [key: string]: any;
  };

  // 分块参数 (可选)
  chunking?: {
    max_characters?: number;  // 默认 1000
    overlap?: number;         // 默认 50
  };
}
```

**请求示例**:

```json
{
  "content": "这里是文档内容...",
  "metadata": {
    "title": "仙界篇",
    "author": "忘语"
  },
  "chunking": {
    "max_characters": 800,
    "overlap": 50
  }
}
```

#### 2.4.2 响应结构

```typescript
interface DocumentUploadResponse {
  // 文档 ID
  document_id: string;

  // 创建的 chunk 数量
  chunk_count: number;

  // 索引耗时 (毫秒)
  indexing_latency_ms: number;

  // 状态
  status: "success" | "partial" | "failed";
}
```

---

### 2.5 健康检查接口

**接口路径**: `GET /api/v1/health`

**接口描述**: 检查服务及依赖组件健康状态

#### 2.5.1 响应结构

```typescript
interface HealthResponse {
  // 整体状态
  status: "healthy" | "degraded" | "unhealthy";

  // 组件状态
  components: {
    milvus: {
      status: "healthy" | "unhealthy";
      latency_ms: number;
    };
    embedding_model: {
      status: "healthy" | "unhealthy";
      latency_ms: number;
    };
    llm_api: {
      status: "healthy" | "unhealthy";
      latency_ms: number;
    };
  };

  // 版本信息
  version: string;
}
```

**响应示例**:

```json
{
  "status": "healthy",
  "components": {
    "milvus": {
      "status": "healthy",
      "latency_ms": 8
    },
    "embedding_model": {
      "status": "healthy",
      "latency_ms": 120
    },
    "llm_api": {
      "status": "healthy",
      "latency_ms": 45
    }
  },
  "version": "1.0.0"
}
```

---

### 2.6 错误响应格式

所有错误响应统一使用以下格式：

```typescript
interface ErrorResponse {
  // 错误代码
  code: string;

  // 错误消息
  message: string;

  // 详细错误信息 (可选)
  details?: any;

  // 请求 ID (用于追踪)
  request_id: string;
}
```

**错误代码表**:

| 错误码 | HTTP 状态 | 描述 |
|--------|-----------|------|
| `INVALID_REQUEST` | 400 | 请求参数错误 |
| `UNAUTHORIZED` | 401 | 未授权 |
| `FORBIDDEN` | 403 | 无权限访问 |
| `NOT_FOUND` | 404 | 资源不存在 |
| `RATE_LIMIT_EXCEEDED` | 429 | 请求频率超限 |
| `INTERNAL_ERROR` | 500 | 服务器内部错误 |
| `SERVICE_UNAVAILABLE` | 503 | 服务不可用 |

**错误响应示例**:

```json
{
  "code": "INVALID_REQUEST",
  "message": "query field is required",
  "details": {
    "field": "query",
    "constraint": "non-empty string"
  },
  "request_id": "req_abc123def456"
}
```

## 3. 数据模型

### 3.1 Milvus Collection 结构

| 字段名 | 类型 | 描述 |
|--------|------|------|
| `id` | VARCHAR | 主键 |
| `element_id` | VARCHAR | 文本元素 ID |
| `record_id` | VARCHAR | 记录 ID |
| `dense_embed` | FLOAT_VECTOR | 稠密向量 |
| `sparse_embed` | SPARSE_FLOAT_VECTOR | 稀疏向量 |
| `text` | VARCHAR | 原始文本 |
| `metadata` | JSON | 元数据 |

### 3.2 向量配置

| 配置项 | 值 |
|--------|-----|
| 稠密向量维度 | 1024 |
| 稠密向量度量 | IP (内积) |
| 稀疏向量度量 | IP (内积) |
| 索引类型 | IVF_FLAT |

## 4. 系统提示词

```markdown
## 角色设定

你是《凡人修仙传》专属剧情问答助手，深度熟悉原著设定与人物情节。用户将向你咨询小说相关剧情、人物、设定、情节细节等问题。用户问题包含两部分："检索结果"和"用户问题"，"检索结果"一节包含了与这个问题相关的小说原文片段，你需严格依托检索到的小说原文片段作答。

## 约束规则

1. 所有回答必须完全依据系统检索出的原著片段内容，不得私自脑补、编造、延伸原著外剧情与设定。
2. 若检索片段中无用户问题对应的相关信息，统一回复：暂时不清楚这个问题的相关内容。
3. 若用户提问内容与《凡人修仙传》无关，需礼貌委婉谢绝，并告知仅解答本书相关问题。
4. 回答语言简洁易懂，贴合原著语境，不随意篡改人物关系、剧情走向和修仙设定。
```

## 5. 配置参数

### 5.1 环境变量

| 变量名 | 默认值 | 描述 |
|--------|--------|------|
| `MILVUS_GRPC_HOST` | `127.0.0.1` | Milvus 主机地址 |
| `MILVUS_GRPC_PORT` | `19530` | Milvus 端口 |
| `LLM_API_BASE_URL` | - | LLM API 基础 URL |
| `LLM_API_KEY` | - | LLM API 密钥 |
| `LLM_MODEL` | `glm-4.7` | 使用的模型 |
| `MAX_TOP_K` | `10` | 最大检索数 |
| `DEFAULT_TOP_K` | `3` | 默认检索数 |
| `DEFAULT_CHUNK_SIZE` | `1000` | 默认分块大小 |
| `DEFAULT_OVERLAP` | `50` | 默认重叠大小 |

### 5.2 性能参数

| 参数 | 默认值 | 描述 |
|------|--------|------|
| `BATCH_SIZE` | `32` | 批量插入大小 |
| `EMBEDDING_TIMEOUT` | `30s` | 嵌入生成超时 |
| `RETRIEVAL_TIMEOUT` | `10s` | 检索超时 |
| `LLM_TIMEOUT` | `60s` | LLM 请求超时 |
| `MAX_CONCURRENT_REQUESTS` | `100` | 最大并发请求数 |

## 6. 实现要点

### 6.1 混合检索流程

```
1. 接收用户查询
2. 生成稠密向量 (BGEM3 dense)
3. 生成稀疏向量 (BGEM3 sparse)
4. 并行执行 AnnSearchRequest (dense + sparse)
5. 使用 RRFRanker 合并排序
6. 返回 Top-K 结果
```

### 6.2 流式处理

使用 SSE (Server-Sent Events) 格式实时返回：
- 检索结果
- 思考过程 (`reasoning_content`)
- 生成内容 (`content`)

### 6.3 错误处理

- Milvus 连接失败 → 降级为纯 LLM 模式
- LLM API 超时 → 返回检索结果 + 错误提示
- 嵌入生成失败 → 返回 500 错误

## 7. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0.0 | 2026-05-20 | 初始版本 |