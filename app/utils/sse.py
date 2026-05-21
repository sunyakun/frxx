import json
from typing import AsyncGenerator

from app.models import StreamChunk


async def sse_generator(
    chunks: AsyncGenerator[StreamChunk, None],
) -> AsyncGenerator[str, None]:
    async for chunk in chunks:
        data = chunk.model_dump(exclude_none=True)
        yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


async def create_thinking_chunk(content: str) -> StreamChunk:
    return StreamChunk(type="thinking", content=content)


async def create_content_chunk(content: str) -> StreamChunk:
    return StreamChunk(type="content", content=content)


async def create_retrieval_chunk(results: list) -> StreamChunk:
    return StreamChunk(type="retrieval", retrieval_results=results)


async def create_done_chunk() -> StreamChunk:
    return StreamChunk(type="done")


async def create_error_chunk(error: str) -> StreamChunk:
    return StreamChunk(type="error", error=error)


async def create_usage_chunk(
    prompt_tokens: int, completion_tokens: int, total_tokens: int
) -> StreamChunk:
    return StreamChunk(
        type="done",
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
    )
