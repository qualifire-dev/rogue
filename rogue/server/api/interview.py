"""
Interview API endpoints - Server-native interview operations.

This module provides REST API endpoints for interview operations.
"""

import uuid
from typing import Dict

from fastapi import APIRouter, HTTPException
from rogue_sdk.types import (
    GetConversationResponse,
    InterviewMessage,
    SendMessageRequest,
    SendMessageResponse,
    StartInterviewRequest,
    StartInterviewResponse,
)

from ...common.logging import get_logger
from ..services.interviewer_service import InterviewerService

router = APIRouter(prefix="/interview", tags=["interview"])
logger = get_logger(__name__)

# In-memory storage for interview sessions
# In production, this would be replaced with a proper database
interview_sessions: Dict[str, InterviewerService] = {}


@router.post("/start", response_model=StartInterviewResponse)
async def start_interview(request: StartInterviewRequest):
    """
    Start a new interview session.

    This endpoint creates a new InterviewerService instance and returns
    a session ID for subsequent interactions.
    """
    try:
        session_id = str(uuid.uuid4())

        logger.info(
            "Starting new interview session",
            extra={
                "session_id": session_id,
                "model": request.model,
            },
        )

        # Create new interviewer service
        interviewer = InterviewerService(
            model=request.model,
            llm_provider_api_key=request.api_key,
        )

        # Store in session storage
        interview_sessions[session_id] = interviewer

        # Get initial message (the interviewer starts the conversation)
        initial_message = (
            "Hi! We'll conduct a short interview to understand your agent's "
            "business context. Please start by describing your agent's primary "
            "function and the industry it operates in."
        )

        logger.info(f"Interview session {session_id} started successfully")

        return StartInterviewResponse(
            session_id=session_id,
            initial_message=initial_message,
            message="Interview session started successfully",
        )

    except Exception:
        logger.exception("Failed to start interview session")
        raise HTTPException(status_code=500, detail="Failed to start interview session")


@router.post("/message", response_model=SendMessageResponse)
async def send_message(request: SendMessageRequest):
    """
    Send a message in an interview session.

    This endpoint sends a user message to the interviewer and returns
    the interviewer's response.
    """
    try:
        # Get the interview session
        interviewer = interview_sessions.get(request.session_id)
        if not interviewer:
            raise HTTPException(
                status_code=404,
                detail=f"Interview session {request.session_id} not found",
            )

        logger.info(
            "Sending message to interview session",
            extra={
                "session_id": request.session_id,
                "message_preview": (
                    request.message[:50] + "..."
                    if len(request.message) > 50
                    else request.message
                ),
            },
        )

        # Send message and get response
        response = interviewer.send_message(request.message)

        # Count user messages to determine if interview is complete
        user_message_count = interviewer.count_user_messages()
        is_complete = user_message_count >= 3

        logger.info(
            f"Interview session {request.session_id} - message processed",
            extra={
                "user_message_count": user_message_count,
                "is_complete": is_complete,
            },
        )

        return SendMessageResponse(
            session_id=request.session_id,
            response=response,
            is_complete=is_complete,
            message_count=user_message_count,
        )

    except HTTPException:
        raise
    except Exception:
        logger.exception(
            f"Failed to send message to interview session {request.session_id}",
            extra={"session_id": request.session_id},
        )
        raise HTTPException(status_code=500, detail="Failed to send message")


@router.get("/conversation/{session_id}", response_model=GetConversationResponse)
async def get_conversation(session_id: str):
    """
    Get the full conversation for an interview session.

    This endpoint returns all messages in the interview conversation.
    """
    try:
        # Get the interview session
        interviewer = interview_sessions.get(session_id)
        if not interviewer:
            raise HTTPException(
                status_code=404,
                detail=f"Interview session {session_id} not found",
            )

        # Convert messages to response format (skip system message)
        messages = []
        for msg in interviewer.iter_messages(include_system=False):
            messages.append(
                InterviewMessage(
                    role=msg["role"],
                    content=msg["content"],
                ),
            )

        # Count user messages
        user_message_count = interviewer.count_user_messages()
        is_complete = user_message_count >= 3

        return GetConversationResponse(
            session_id=session_id,
            messages=messages,
            is_complete=is_complete,
            message_count=user_message_count,
        )

    except HTTPException:
        raise
    except Exception:
        logger.exception(
            "Failed to get conversation for session",
            extra={"session_id": session_id},
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to get conversation",
        )


@router.delete("/session/{session_id}")
async def end_interview(session_id: str):
    """
    End an interview session and clean up resources.

    This endpoint removes the interview session from memory.
    """
    try:
        if session_id in interview_sessions:
            del interview_sessions[session_id]
            logger.info(f"Interview session {session_id} ended and cleaned up")
            return {"message": f"Interview session {session_id} ended successfully"}
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Interview session {session_id} not found",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            "Failed to end interview session",
            extra={"session_id": session_id},
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to end interview session: {str(e)}",
        )
