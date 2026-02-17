import time
from functools import lru_cache
from uuid import uuid4

from fastapi import FastAPI

from .shirtify_agent import ShirtifyAgent

app = FastAPI()


@lru_cache(maxsize=1)
def get_agent() -> ShirtifyAgent:
    return ShirtifyAgent(reasoning_effort="low")


@app.post("/chat/completions")
async def chat_completions(request: dict):
    messages = request.get("messages", [])
    response = get_agent().invoke(messages)

    return {
        "id": f"{uuid4().hex}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": "evaluated-agent",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response.get("content", ""),
                },
                "finish_reason": "stop",
            },
        ],
    }
