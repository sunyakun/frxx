import json
from typing import AsyncGenerator, List

import httpx

from app.config import Settings, get_settings

settings: Settings = get_settings()


async def chat_completion(
    messages: List[dict],
    stream: bool = True,
    reasoning_effort: str = "low",
) -> AsyncGenerator[dict, None]:
    async with httpx.AsyncClient(
        base_url=settings.llm_api_base_url, timeout=settings.llm_timeout
    ) as client:
        async with client.stream(
            "POST",
            "/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.llm_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.llm_model,
                "messages": messages,
                "reasoning_effort": reasoning_effort,
                "stream": stream,
            },
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if "data: " not in line:
                    continue
                _, data = line.split("data: ", 1)
                try:
                    yield json.loads(data)
                except json.JSONDecodeError:
                    pass


async def chat_completion_non_stream(
    messages: List[dict],
    reasoning_effort: str = "low",
) -> dict:
    async with httpx.AsyncClient(
        base_url=settings.llm_api_base_url, timeout=settings.llm_timeout
    ) as client:
        resp = await client.post(
            "/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.llm_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.llm_model,
                "messages": messages,
                "reasoning_effort": reasoning_effort,
                "stream": False,
            },
        )
        resp.raise_for_status()
        return resp.json()


async def check_health() -> bool:
    try:
        async with httpx.AsyncClient(
            base_url=settings.llm_api_base_url, timeout=5
        ) as client:
            resp = await client.get("/v1/models")
            return resp.status_code < 500
    except Exception:
        return False