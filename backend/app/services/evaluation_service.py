"""
Service for handling interview evaluation data storage and retrieval.
"""

from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
from datetime import datetime

from app.models.interview import (
    Interview, 
    InterviewMessage, 
    EvaluationScore, 
    EvaluationSummary,
    MessageSender,
    MessageType,
    InterviewStage,
    EvaluationCategory
)
from app.schemas.interview import (
    EvaluationScoreCreate,
    EvaluationSummaryCreate
)


class EvaluationService:
    """Service for managing interview evaluation data."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def save_chat_message(
        self,
        interview_id: uuid.UUID,
        sender: MessageSender,
        stage: InterviewStage,
        message_type: MessageType,
        message: str,
        ai_generated: bool = False,
        score_impact: Optional[float] = None
    ) -> InterviewMessage:
        """Save a chat message to the database."""
        chat_message = InterviewMessage(
            interview_id=interview_id,
            sender=sender,
            stage=stage,
            message_type=message_type,
            message=message,
            ai_generated=ai_generated,
            score_impact=score_impact
        )
        
        self.db.add(chat_message)
        await self.db.commit()
        await self.db.refresh(chat_message)
        
        return chat_message
    
    async def save_evaluation_scores(
        self,
        interview_id: uuid.UUID,
        scores: Dict[str, float],
        weights: Optional[Dict[str, float]] = None,
        explanations: Optional[Dict[str, str]] = None
    ) -> List[EvaluationScore]:
        """Save individual evaluation scores for each category."""
        evaluation_scores = []
        
        # Map score categories to database enums
        category_mapping = {
            "resume_fit": EvaluationCategory.RESUME_FIT,
            "hard_skills": EvaluationCategory.HARD_SKILLS,
            "soft_skills": EvaluationCategory.SOFT_SKILLS
        }
        
        for category_key, score in scores.items():
            if category_key in category_mapping and score > 0:  # Only save non-zero scores
                category = category_mapping[category_key]
                weight = weights.get(category_key, 1.0) if weights else 1.0
                explanation = explanations.get(category_key) if explanations else None
                
                evaluation_score = EvaluationScore(
                    interview_id=interview_id,
                    category=category,
                    score=score,
                    weight=weight,
                    explanation=explanation
                )
                
                self.db.add(evaluation_score)
                evaluation_scores.append(evaluation_score)
        
        await self.db.commit()
        
        # Refresh all scores
        for score in evaluation_scores:
            await self.db.refresh(score)
        
        return evaluation_scores
    
    async def save_evaluation_summary(
        self,
        interview_id: uuid.UUID,
        overall_score: float,
        breakdown: Dict[str, float],
        reasoning: Optional[List[str]] = None,
        ai_confidence: Optional[float] = None
    ) -> EvaluationSummary:
        """Save the overall evaluation summary."""
        # Convert reasoning list to string if provided
        reasoning_text = None
        if reasoning:
            reasoning_text = "; ".join(reasoning)
        
        evaluation_summary = EvaluationSummary(
            interview_id=interview_id,
            overall_score=overall_score,
            breakdown=breakdown,
            reasoning=reasoning_text,
            ai_confidence=ai_confidence
        )
        
        self.db.add(evaluation_summary)
        await self.db.commit()
        await self.db.refresh(evaluation_summary)
        
        return evaluation_summary
    
    async def update_interview_final_data(
        self,
        interview_id: uuid.UUID,
        final_score: float,
        summary_json: Dict
    ) -> Interview:
        """Update the interview with final score and summary."""
        result = await self.db.execute(
            select(Interview).where(Interview.id == interview_id)
        )
        interview = result.scalar_one_or_none()
        
        if not interview:
            raise ValueError(f"Interview {interview_id} not found")
        
        interview.final_score = final_score
        interview.summary_json = summary_json
        interview.ended_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(interview)
        
        return interview
    
    async def get_interview_evaluation_data(
        self,
        interview_id: uuid.UUID
    ) -> Dict:
        """Get complete evaluation data for an interview."""
        # Get interview
        result = await self.db.execute(
            select(Interview).where(Interview.id == interview_id)
        )
        interview = result.scalar_one_or_none()
        
        if not interview:
            raise ValueError(f"Interview {interview_id} not found")
        
        # Get evaluation scores
        result = await self.db.execute(
            select(EvaluationScore).where(EvaluationScore.interview_id == interview_id)
        )
        evaluation_scores = result.scalars().all()
        
        # Get evaluation summary
        result = await self.db.execute(
            select(EvaluationSummary).where(EvaluationSummary.interview_id == interview_id)
        )
        evaluation_summary = result.scalar_one_or_none()
        
        # Get chat messages
        result = await self.db.execute(
            select(InterviewMessage)
            .where(InterviewMessage.interview_id == interview_id)
            .order_by(InterviewMessage.created_at)
        )
        chat_messages = result.scalars().all()
        
        return {
            "interview": interview,
            "evaluation_scores": evaluation_scores,
            "evaluation_summary": evaluation_summary,
            "chat_messages": chat_messages
        }
    
    async def save_complete_evaluation(
        self,
        interview_id: uuid.UUID,
        ai_evaluation: Dict,
        chat_history: Optional[List[Dict]] = None
    ) -> Dict:
        """Save complete evaluation data from AI response."""
        try:
            # Save chat history if provided
            if chat_history:
                for message in chat_history:
                    await self.save_chat_message(
                        interview_id=interview_id,
                        sender=MessageSender(message["sender"]),
                        stage=InterviewStage(message["stage"]),
                        message_type=MessageType(message["message_type"]),
                        message=message["message"],
                        ai_generated=message.get("ai_generated", False),
                        score_impact=message.get("score_impact")
                    )
            
            # Save evaluation scores
            breakdown = ai_evaluation.get("breakdown", {})
            evaluation_scores = await self.save_evaluation_scores(
                interview_id=interview_id,
                scores=breakdown
            )
            
            # Save evaluation summary
            evaluation_summary = await self.save_evaluation_summary(
                interview_id=interview_id,
                overall_score=ai_evaluation.get("overall_score", 0),
                breakdown=breakdown,
                reasoning=ai_evaluation.get("reasoning"),
                ai_confidence=ai_evaluation.get("ai_confidence")
            )
            
            # Update interview with final data
            interview = await self.update_interview_final_data(
                interview_id=interview_id,
                final_score=ai_evaluation.get("overall_score", 0),
                summary_json=ai_evaluation
            )
            
            return {
                "success": True,
                "interview": interview,
                "evaluation_scores": evaluation_scores,
                "evaluation_summary": evaluation_summary
            }
            
        except Exception as e:
            await self.db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
