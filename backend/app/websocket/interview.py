from fastapi import WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Dict, Any
from datetime import datetime
import uuid
import json
import asyncio
import redis.asyncio as redis

from app.db import get_db
from app.models.interview import Interview, InterviewMessage, MessageSender, MessageType, InterviewStage, InterviewStatus
from app.models.candidate import Candidate
from app.models.vacancy import Vacancy
from app.models.resume import Resume
from app.ai.interview_logic import InterviewAI

# Redis connection for session management
redis_client = None


async def get_redis():
    """Get Redis connection."""
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url("redis://localhost:6379")
    return redis_client


class ConnectionManager:
    """Manages WebSocket connections for interviews."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, interview_id: str):
        """Connect a WebSocket to an interview."""
        await websocket.accept()
        self.active_connections[interview_id] = websocket

    def disconnect(self, interview_id: str):
        """Disconnect a WebSocket from an interview."""
        if interview_id in self.active_connections:
            del self.active_connections[interview_id]

    async def send_message(self, interview_id: str, message: Dict[str, Any]):
        """Send a message to a specific interview."""
        if interview_id in self.active_connections:
            websocket = self.active_connections[interview_id]
            try:
                await websocket.send_json(message)
            except Exception as e:
                print(f"Error sending message to {interview_id}: {e}")
                self.disconnect(interview_id)


manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, interview_id: str):
    """WebSocket endpoint for real-time interview communication."""
    await manager.connect(websocket, interview_id)
    
    try:
        # Get interview from database
        async with get_db() as db:
            result = await db.execute(
                select(Interview).where(Interview.id == uuid.UUID(interview_id))
            )
            interview = result.scalar_one_or_none()
            
            if not interview:
                await websocket.send_json({
                    "type": "error",
                    "message": "Interview not found"
                })
                return
            
            # Get candidate and vacancy data
            result = await db.execute(
                select(Candidate).where(Candidate.id == interview.candidate_id)
            )
            candidate = result.scalar_one_or_none()
            
            result = await db.execute(
                select(Vacancy).where(Vacancy.id == interview.vacancy_id)
            )
            vacancy = result.scalar_one_or_none()
            
            if not candidate or not vacancy:
                await websocket.send_json({
                    "type": "error",
                    "message": "Interview data not found"
                })
                return
            
            # Get resume data for the candidate
            result = await db.execute(
                select(Resume).where(Resume.candidate_id == candidate.id).order_by(Resume.created_at.desc())
            )
            resume = result.scalar_one_or_none()
            
            if not resume:
                await websocket.send_json({
                    "type": "error",
                    "message": "Resume not found for candidate"
                })
                return
            
            # Initialize AI interviewer
            ai_interviewer = InterviewAI()
            await ai_interviewer.start_interview(vacancy, candidate, resume)
            
            # Send initial greeting
            await websocket.send_json({
                "type": "message",
                "sender": "bot",
                "message": "Hello! Welcome to your interview. Let's begin!",
                "stage": interview.current_stage.value
            })
            
            # Send first question if interview is just starting
            if interview.status == InterviewStatus.PENDING:
                await start_interview(websocket, interview, ai_interviewer, db)
            
            # Handle incoming messages
            while True:
                data = await websocket.receive_json()
                await handle_candidate_message(websocket, interview_id, data, ai_interviewer, db)
    
    except WebSocketDisconnect:
        manager.disconnect(interview_id)
    except Exception as e:
        print(f"WebSocket error for interview {interview_id}: {e}")
        manager.disconnect(interview_id)


async def start_interview(websocket: WebSocket, interview: Interview, ai_interviewer: InterviewAI, db: AsyncSession):
    """Start the interview and send first question."""
    # Update interview status
    interview.status = InterviewStatus.IN_PROGRESS
    interview.current_stage = InterviewStage.RESUME_FIT
    
    # Generate first question
    question = await ai_interviewer.generate_next_question()
    
    # Save bot message to database
    bot_message = InterviewMessage(
        interview_id=interview.id,
        sender=MessageSender.BOT,
        stage=interview.current_stage,
        message_type=MessageType.QUESTION,
        message=question,
        ai_generated=True
    )
    db.add(bot_message)
    await db.commit()
    
    # Send question to client
    await websocket.send_json({
        "type": "message",
        "sender": "bot",
        "message": question,
        "stage": interview.current_stage.value,
        "message_type": "question"
    })


async def handle_candidate_message(
    websocket: WebSocket, 
    interview_id: str, 
    data: Dict[str, Any], 
    ai_interviewer: InterviewAI, 
    db: AsyncSession
):
    """Handle incoming message from candidate."""
    message_text = data.get("message", "")
    
    if not message_text:
        await websocket.send_json({
            "type": "error",
            "message": "Empty message received"
        })
        return
    
    # Get interview
    result = await db.execute(
        select(Interview).where(Interview.id == uuid.UUID(interview_id))
    )
    interview = result.scalar_one_or_none()
    
    if not interview:
        await websocket.send_json({
            "type": "error",
            "message": "Interview not found"
        })
        return
    
    # Save candidate message to database
    candidate_message = InterviewMessage(
        interview_id=interview.id,
        sender=MessageSender.CANDIDATE,
        stage=interview.current_stage,
        message_type=MessageType.ANSWER,
        message=message_text
    )
    db.add(candidate_message)
    await db.commit()
    
    # Process answer and generate next question
    try:
        response = await ai_interviewer.process_answer(message_text, interview.current_stage)
        
        # Save bot response to database
        bot_message = InterviewMessage(
            interview_id=interview.id,
            sender=MessageSender.BOT,
            stage=interview.current_stage,
            message_type=MessageType.QUESTION if response.get("type") == "question" else MessageType.INFO,
            message=response.get("message", ""),
            ai_generated=True
        )
        db.add(bot_message)
        
        # Update interview stage if needed
        if response.get("stage_change"):
            interview.current_stage = response["stage_change"]
        
        # Check if interview is complete
        if response.get("interview_complete"):
            interview.status = InterviewStatus.COMPLETED
            interview.ended_at = datetime.utcnow()
            
            # Generate final evaluation
            evaluation = await ai_interviewer.generate_final_evaluation()
            interview.final_score = evaluation.get("overall_score")
            interview.summary_json = evaluation
            
            await websocket.send_json({
                "type": "interview_complete",
                "final_score": interview.final_score,
                "summary": evaluation
            })
        else:
            await websocket.send_json({
                "type": "message",
                "sender": "bot",
                "message": response.get("message", ""),
                "stage": interview.current_stage.value,
                "message_type": response.get("type", "question")
            })
        
        await db.commit()
    
    except Exception as e:
        print(f"Error processing answer: {e}")
        await websocket.send_json({
            "type": "error",
            "message": "Sorry, I encountered an error processing your answer. Please try again."
        })
