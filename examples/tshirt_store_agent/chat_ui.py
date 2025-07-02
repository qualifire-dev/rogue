import asyncio
import traceback
from typing import Any
from uuid import uuid4

import gradio as gr
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
A2A_CLIENT: A2AClient | None = None
HTTPX_CLIENT: httpx.AsyncClient | None = None


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


def build_message(
    text: str,
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


async def get_agent_response(
    message: str,
    context_id: str,
) -> str:
    """Sends a message to the agent and waits for the complete response."""
    if not A2A_CLIENT:
        return "Error: A2A Client is not initialized."

    try:
        # 1. Send the message
        request = build_message(text=message, context_id=context_id)
        send_response: SendMessageResponse = await A2A_CLIENT.send_message(request)

        if not isinstance(
            send_response.root, SendMessageSuccessResponse
        ) or not isinstance(send_response.root.result, Task):
            return "Error: Failed to send message to agent."

        task_id: str = send_response.root.result.id

        # 2. Poll for the task result
        get_request = GetTaskRequest(
            id=uuid4().hex,
            params=TaskQueryParams(id=task_id),
        )
        get_response: GetTaskResponse = await A2A_CLIENT.get_task(get_request)

        # 3. Extract the text from the response artifact
        return get_response.root.result.artifacts[0].parts[0].root.text  # type: ignore
    except Exception as e:
        traceback.print_exc()
        return f"An error occurred: {e}"


async def handle_chat_message(message: str, history: list, state: dict):
    """Gradio handler for processing a new chat message."""
    context_id = state["context_id"]
    history.append([message, None])
    yield history, gr.update(value="", interactive=False)

    response = await get_agent_response(message, context_id)

    history[-1][1] = response
    yield history, gr.update(interactive=True)


def create_ui():
    """Creates the Gradio UI for the chat client."""
    with gr.Blocks(
        title="T-Shirt Store Agent",
        theme=gr.themes.Default(primary_hue="blue"),
    ) as demo:
        # Initialize state for the session
        state = gr.State({"context_id": uuid4().hex})

        gr.Markdown("# T-Shirt Store Agent Chat")
        gr.Markdown(
            "This is a chat interface for the Shirtify T-Shirt Store agent. "
            "Start by asking it what it sells!"
        )

        chatbot = gr.Chatbot(
            elem_id="chatbot",
            label="T-Shirt Store Agent",
            height=600,
        )
        with gr.Row():
            txt = gr.Textbox(
                show_label=False,
                placeholder="Enter text and press enter",
                container=False,
                scale=10,
            )

        txt.submit(handle_chat_message, [txt, chatbot, state], [chatbot, txt])

    return demo


async def main():
    """Initializes the clients and launches the Gradio app."""
    global A2A_CLIENT, HTTPX_CLIENT
    print(f"Attempting to connect to agent at {AGENT_URL}...")
    try:
        HTTPX_CLIENT = httpx.AsyncClient(timeout=30)
        A2A_CLIENT = await A2AClient.get_client_from_agent_card_url(
            HTTPX_CLIENT, AGENT_URL
        )
        print("Connection to agent successful.")

        ui = create_ui()
        ui.launch()

    except Exception as e:
        traceback.print_exc()
        print(f"An error occurred: {e}")
        print(
            "\nCould not connect to the agent. "
            "Please ensure the T-Shirt Store Agent server is running."
        )
    finally:
        if HTTPX_CLIENT:
            await HTTPX_CLIENT.aclose()


if __name__ == "__main__":
    asyncio.run(main())
