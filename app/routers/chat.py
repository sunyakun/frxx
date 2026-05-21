import time
import uuid
from typing import AsyncGenerator

from fastapi import APIRouter, Request, Response, status
from fastapi.responses import StreamingResponse

from app.config import get_settings
from app.models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ErrorResponse,
    RetrievalResult,
    Usage,
)
from app.services.llm import chat_completion, chat_completion_non_stream
from app.services.retrieval import search
from app.utils.log import get_logger
from app.utils.sse import (
    create_content_chunk,
    create_error_chunk,
    create_retrieval_chunk,
    create_thinking_chunk,
    create_usage_chunk,
    sse_generator,
)

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/completions", status_code=status.HTTP_200_OK)
async def chat_completions_endpoint(
    request: ChatCompletionRequest, http_request: Request, response: Response
):
    try:
        top_k = min(request.top_k, 10)

        start_time = time.time()
        retrieval_results = await search(
            query=request.query,
            collection_name="frxx",
            top_k=top_k,
            mode="hybrid",
        )

        retrieval_data = [
            RetrievalResult(
                id=r["id"],
                text=r["text"],
                score=float(r.get("score", 0.0)),
                metadata=r.get("metadata"),
            )
            for r in retrieval_results
        ]

        retrieval_text = "\n".join(
            [f"## 参考内容{idx + 1}:\n{r.text}" for idx, r in enumerate(retrieval_data)]
        )

        messages = [
            {"role": "system", "content": get_settings().system_prompt},
            {
                "role": "user",
                "content": f"# 检索结果：{retrieval_text}\n\n# 用户问题：\n{request.query}",
            },
        ]

        if request.stream:

            async def generate_stream() -> AsyncGenerator:
                try:
                    yield await create_retrieval_chunk(
                        [r.model_dump() for r in retrieval_data]
                    )

                    thinking_state = False
                    prompt_tokens = 0
                    completion_tokens = 0

                    async for chunk in chat_completion(messages, stream=True):
                        delta = chunk.get("choices", [{}])[0].get("delta", {})

                        if "reasoning_content" in delta:
                            if not thinking_state:
                                thinking_state = True
                            yield await create_thinking_chunk(
                                delta["reasoning_content"]
                            )
                        elif "content" in delta:
                            if thinking_state:
                                thinking_state = False
                            yield await create_content_chunk(delta["content"])

                        if "usage" in chunk:
                            prompt_tokens = chunk["usage"].get("prompt_tokens", 0)
                            completion_tokens = chunk["usage"].get(
                                "completion_tokens", 0
                            )

                    yield await create_usage_chunk(
                        prompt_tokens,
                        completion_tokens,
                        prompt_tokens + completion_tokens,
                    )
                except Exception as e:
                    yield await create_error_chunk(str(e))

            return StreamingResponse(
                sse_generator(generate_stream()),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
            )
        else:
            response = await chat_completion_non_stream(messages)
            content = (
                response.get("choices", [{}])[0].get("message", {}).get("content", "")
            )

            usage_data = response.get("usage", {})
            return ChatCompletionResponse(
                answer=content,
                retrieval_results=retrieval_data,
                usage=Usage(
                    prompt_tokens=usage_data.get("prompt_tokens", 0),
                    completion_tokens=usage_data.get("completion_tokens", 0),
                    total_tokens=usage_data.get("total_tokens", 0),
                ),
                model=get_settings().llm_model,
            )

    except Exception as e:
        get_logger().error(f"Failed to run chat completions: {e}", exc_info=e)
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ErrorResponse(
            code="INTERNAL_ERROR",
            message=str(e),
            request_id=str(uuid.uuid4()),
        )
