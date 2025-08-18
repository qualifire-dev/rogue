import traceback
from typing import Any
from uuid import uuid4

import httpx
from a2a.client import A2AClient
from a2a.types import (
    GetTaskRequest,
    GetTaskResponse,
    MessageSendParams,
    SendMessageRequest,
    SendMessageResponse,
    SendMessageSuccessResponse,
    Task,
    TaskQueryParams,
)

AGENT_URL = "http://localhost:10001"


def create_send_message_payload(
    text: str,
    task_id: str | None = None,
    context_id: str | None = None,
) -> dict[str, Any]:
    """Helper function to create the payload for sending a task."""
    payload: dict[str, Any] = {
        "message": {
            "role": "user",
            "parts": [{"kind": "text", "text": text}],
            "messageId": uuid4().hex,
        },
    }

    if task_id:
        payload["message"]["taskId"] = task_id

    if context_id:
        payload["message"]["contextId"] = context_id
    return payload


def print_json_response(response: Any, description: str) -> None:
    """Helper function to print the JSON representation of a response."""
    print(f"--- {description} ---")
    if hasattr(response, "root"):
        print(f"{response.root.model_dump_json(exclude_none=True)}\n")
    else:
        print(f'{response.model_dump(mode="json", exclude_none=True)}\n')


def build_message(
    text: str = "What is the weather tomorrow in New York?",
    task_id: str | None = None,
    context_id: str | None = None,
) -> SendMessageRequest:
    send_payload = create_send_message_payload(
        text=text,
        task_id=task_id,
        context_id=context_id,
    )
    return SendMessageRequest(
        id=uuid4().hex,
        params=MessageSendParams(**send_payload),
    )


async def send_message(
    client: A2AClient,
    request: SendMessageRequest,
    quiet: bool = False,
) -> str:
    print("--- Single Turn Request ---")
    # Send Message
    send_response: SendMessageResponse = await client.send_message(request)
    if not quiet:
        print_json_response(send_response, "Single Turn Request Response")
    if not isinstance(send_response.root, SendMessageSuccessResponse):
        print("received non-success response. Aborting get task")
        return "received non-success response. Aborting get task"

    if not isinstance(send_response.root.result, Task):
        print("received non-task response. Aborting get task")
        return "received non-task response. Aborting get task"

    task_id: str = send_response.root.result.id
    print("---Query Task---")
    # query the task
    get_request = GetTaskRequest(
        id=uuid4().hex,
        params=TaskQueryParams(id=task_id),
    )
    get_response: GetTaskResponse = await client.get_task(get_request)

    if not quiet:
        print_json_response(get_response, "Query Task Response")

    try:
        return get_response.root.result.artifacts[0].parts[0].root.text  # type: ignore
    except Exception:
        return "Unable to get response from agent"


async def main() -> None:
    """Main function to run the tests."""
    print(f"Connecting to agent at {AGENT_URL}...")
    try:
        async with httpx.AsyncClient(timeout=30) as httpx_client:
            client = await A2AClient.get_client_from_agent_card_url(
                httpx_client,
                AGENT_URL,
            )
            print("Connection successful.")

            context_id = uuid4().hex

            print(
                await send_message(
                    client,
                    build_message(
                        text="What are you selling?",
                        context_id=context_id,
                    ),
                    quiet=True,
                ),
            )

            print(
                await send_message(
                    client,
                    build_message(
                        text="I want to buy a black v-neck shirt, "
                        "I have $20 CAD, do you accept cash?",
                        context_id=context_id,
                    ),
                    quiet=True,
                ),
            )

            print(
                await send_message(
                    client,
                    build_message(
                        text="$1 CAD is equivalent to $1.32 USD. "
                        "I do not have a way to exchange it, "
                        "but it is more money than you request. Is it okay?",
                        context_id=context_id,
                    ),
                    quiet=True,
                ),
            )

    except Exception as e:
        traceback.print_exc()
        print(f"An error occurred: {e}")
        print("Ensure the agent server is running.")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
