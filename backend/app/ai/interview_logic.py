from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from app.models.candidate import Candidate
from app.models.vacancy import Vacancy
from app.models.interview import Interview, InterviewStage, InterviewMessage, MessageSender
from app.core.config import settings


class InterviewAI:
    """AI interviewer that conducts interviews and evaluates candidates."""
    
    def __init__(self, candidate: Candidate, vacancy: Vacancy, interview: Interview):
        self.candidate = candidate
        self.vacancy = vacancy
        self.interview = interview
        self.current_stage = interview.current_stage
        self.conversation_history = []
        self.stage_questions = {
            InterviewStage.RESUME_FIT: [],
            InterviewStage.HARD_SKILLS: [],
            InterviewStage.SOFT_SKILLS: []
        }
        self.evaluation_scores = {
            "resume_fit": 0.0,
            "hard_skills": 0.0,
            "soft_skills": 0.0
        }
    
    async def generate_next_question(self) -> str:
        """Generate the next question based on current stage."""
        if self.current_stage == InterviewStage.RESUME_FIT:
            return await self._generate_resume_fit_question()
        elif self.current_stage == InterviewStage.HARD_SKILLS:
            return await self._generate_hard_skills_question()
        elif self.current_stage == InterviewStage.SOFT_SKILLS:
            return await self._generate_soft_skills_question()
        else:
            return "Thank you for completing the interview!"
    
    async def process_answer(self, answer: str, stage: InterviewStage) -> Dict[str, Any]:
        """Process candidate's answer and determine next action."""
        self.conversation_history.append({
            "stage": stage.value,
            "answer": answer,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Evaluate the answer
        score_impact = await self._evaluate_answer(answer, stage)
        
        # Check if we should move to next stage
        if await self._should_move_to_next_stage(stage):
            next_stage = self._get_next_stage(stage)
            if next_stage == InterviewStage.FINISHED:
                return {
                    "type": "info",
                    "message": "Thank you! We've completed the interview. Let me prepare your evaluation.",
                    "interview_complete": True
                }
            else:
                self.current_stage = next_stage
                next_question = await self.generate_next_question()
                return {
                    "type": "question",
                    "message": next_question,
                    "stage_change": next_stage
                }
        else:
            # Continue with more questions in current stage
            next_question = await self._generate_follow_up_question(stage)
            return {
                "type": "question",
                "message": next_question
            }
    
    async def _generate_resume_fit_question(self) -> str:
        """Generate questions to assess resume fit."""
        questions = [
            f"I see this position is based in {self.vacancy.city or 'the specified location'}. Would you be able to work from this location?",
            f"The role requires {self.vacancy.experience_min or 0}+ years of experience. Can you tell me about your relevant experience?",
            f"This is a {self.vacancy.employment_type or 'full-time'} position. Is this type of employment suitable for you?",
            f"The salary range for this role is {self.vacancy.salary_min or 'competitive'} - {self.vacancy.salary_max or 'competitive'}. Does this align with your expectations?"
        ]
        
        # Check for mismatches and ask clarifying questions
        if self.vacancy.city and self.candidate.city and self.vacancy.city.lower() != self.candidate.city.lower():
            return questions[0]
        elif self.vacancy.experience_min and self._get_candidate_experience() < self.vacancy.experience_min:
            return questions[1]
        elif self.vacancy.employment_type and self.candidate.employment_type and self.vacancy.employment_type != self.candidate.employment_type:
            return questions[2]
        elif self.vacancy.salary_min and self.candidate.expected_salary and self.candidate.expected_salary < self.vacancy.salary_min:
            return questions[3]
        else:
            return "Great! Your basic profile seems to match well with this position. Let's move on to discussing your technical skills."
    
    async def _generate_hard_skills_question(self) -> str:
        """Generate questions to assess hard skills."""
        required_skills = self.vacancy.required_skills or []
        candidate_skills = [skill.skill_name for skill in self.candidate.skills] if self.candidate.skills else []
        
        if required_skills:
            missing_skills = [skill for skill in required_skills if skill.lower() not in [s.lower() for s in candidate_skills]]
            if missing_skills:
                return f"I notice the job requires experience with {', '.join(missing_skills[:3])}. Can you tell me about your experience with these technologies?"
            else:
                return f"I see you have experience with {', '.join(required_skills[:3])}. Can you tell me about a specific project where you used these skills?"
        else:
            return "Can you tell me about your most relevant technical experience for this role?"
    
    async def _generate_soft_skills_question(self) -> str:
        """Generate questions to assess soft skills."""
        questions = [
            "What motivates you most in your work?",
            "How do you handle tight deadlines and pressure?",
            "Can you tell me about a time when you had to work with a difficult team member?",
            "What's your approach to learning new technologies or skills?",
            "Where do you see yourself in 5 years?"
        ]
        
        # Return a random question (in real implementation, you'd track which questions were asked)
        import random
        return random.choice(questions)
    
    async def _generate_follow_up_question(self, stage: InterviewStage) -> str:
        """Generate follow-up questions for current stage."""
        if stage == InterviewStage.RESUME_FIT:
            return "Is there anything else about your background or availability you'd like to clarify?"
        elif stage == InterviewStage.HARD_SKILLS:
            return "Can you provide more details about your technical expertise?"
        elif stage == InterviewStage.SOFT_SKILLS:
            return "That's interesting. Can you give me another example?"
        else:
            return "Is there anything else you'd like to add?"
    
    async def _evaluate_answer(self, answer: str, stage: InterviewStage) -> float:
        """Evaluate candidate's answer and return score impact."""
        # Simple keyword-based evaluation (in production, use more sophisticated NLP)
        score = 0.0
        
        if stage == InterviewStage.RESUME_FIT:
            score = self._evaluate_resume_fit_answer(answer)
        elif stage == InterviewStage.HARD_SKILLS:
            score = self._evaluate_hard_skills_answer(answer)
        elif stage == InterviewStage.SOFT_SKILLS:
            score = self._evaluate_soft_skills_answer(answer)
        
        # Update evaluation scores
        stage_key = stage.value
        if stage_key in self.evaluation_scores:
            current_score = self.evaluation_scores[stage_key]
            self.evaluation_scores[stage_key] = (current_score + score) / 2
        
        return score
    
    def _evaluate_resume_fit_answer(self, answer: str) -> float:
        """Evaluate resume fit answer."""
        positive_keywords = ["yes", "sure", "can do", "willing", "interested", "available"]
        negative_keywords = ["no", "cannot", "unable", "not interested", "not available"]
        
        answer_lower = answer.lower()
        
        for keyword in positive_keywords:
            if keyword in answer_lower:
                return 0.8
        
        for keyword in negative_keywords:
            if keyword in answer_lower:
                return 0.2
        
        return 0.5  # Neutral score
    
    def _evaluate_hard_skills_answer(self, answer: str) -> float:
        """Evaluate hard skills answer."""
        # Check for technical keywords
        technical_keywords = ["experience", "project", "developed", "implemented", "designed", "built"]
        answer_lower = answer.lower()
        
        score = 0.3  # Base score
        for keyword in technical_keywords:
            if keyword in answer_lower:
                score += 0.1
        
        return min(score, 1.0)
    
    def _evaluate_soft_skills_answer(self, answer: str) -> float:
        """Evaluate soft skills answer."""
        positive_keywords = ["collaborate", "team", "learn", "motivated", "challenge", "growth"]
        answer_lower = answer.lower()
        
        score = 0.4  # Base score
        for keyword in positive_keywords:
            if keyword in answer_lower:
                score += 0.1
        
        return min(score, 1.0)
    
    async def _should_move_to_next_stage(self, stage: InterviewStage) -> bool:
        """Determine if we should move to the next stage."""
        # Simple logic: move after 2-3 questions per stage
        stage_question_count = len([msg for msg in self.conversation_history if msg["stage"] == stage.value])
        
        if stage_question_count >= 2:
            return True
        
        return False
    
    def _get_next_stage(self, current_stage: InterviewStage) -> InterviewStage:
        """Get the next stage in the interview process."""
        stage_order = [
            InterviewStage.RESUME_FIT,
            InterviewStage.HARD_SKILLS,
            InterviewStage.SOFT_SKILLS,
            InterviewStage.FINISHED
        ]
        
        try:
            current_index = stage_order.index(current_stage)
            return stage_order[current_index + 1]
        except (ValueError, IndexError):
            return InterviewStage.FINISHED
    
    def _get_candidate_experience(self) -> float:
        """Calculate candidate's total experience in years."""
        # Simple calculation based on experiences
        if not self.candidate.experiences:
            return 0.0
        
        total_months = 0
        for exp in self.candidate.experiences:
            if exp.start_date:
                start = exp.start_date
                end = exp.end_date or datetime.now().date()
                
                # Calculate months between dates
                months = (end.year - start.year) * 12 + (end.month - start.month)
                total_months += months
        
        return total_months / 12  # Convert to years
    
    async def generate_final_evaluation(self) -> Dict[str, Any]:
        """Generate final evaluation summary."""
        # Calculate overall score
        weights = {
            "resume_fit": 0.3,
            "hard_skills": 0.4,
            "soft_skills": 0.3
        }
        
        overall_score = sum(
            self.evaluation_scores[category] * weight 
            for category, weight in weights.items()
        ) * 100  # Convert to percentage
        
        # Generate reasoning
        reasoning = self._generate_reasoning()
        
        return {
            "overall_score": round(overall_score, 1),
            "breakdown": {
                "resume_fit": round(self.evaluation_scores["resume_fit"] * 100, 1),
                "hard_skills": round(self.evaluation_scores["hard_skills"] * 100, 1),
                "soft_skills": round(self.evaluation_scores["soft_skills"] * 100, 1)
            },
            "reasoning": reasoning,
            "ai_confidence": 0.85,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def _generate_reasoning(self) -> str:
        """Generate reasoning for the evaluation."""
        reasoning_parts = []
        
        # Resume fit reasoning
        if self.evaluation_scores["resume_fit"] > 0.7:
            reasoning_parts.append("Strong alignment with job requirements")
        elif self.evaluation_scores["resume_fit"] < 0.4:
            reasoning_parts.append("Some concerns about basic job fit")
        
        # Hard skills reasoning
        if self.evaluation_scores["hard_skills"] > 0.7:
            reasoning_parts.append("Demonstrated solid technical capabilities")
        elif self.evaluation_scores["hard_skills"] < 0.4:
            reasoning_parts.append("Limited technical experience for this role")
        
        # Soft skills reasoning
        if self.evaluation_scores["soft_skills"] > 0.7:
            reasoning_parts.append("Good communication and motivation")
        elif self.evaluation_scores["soft_skills"] < 0.4:
            reasoning_parts.append("Some concerns about soft skills")
        
        return ". ".join(reasoning_parts) + "."
