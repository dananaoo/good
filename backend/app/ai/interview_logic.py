import google.generativeai as genai
from typing import Dict, List, Optional, Tuple
from app.models.vacancy import Vacancy
from app.models.candidate import (
    Candidate,
    CandidateExperience,
    CandidateEducation,
    CandidateSkill,
    CandidateLanguage,
    CandidateAchievement
)
from app.models.resume import Resume
from app.models.interview import InterviewStage
import os
from dotenv import load_dotenv
import json
import re
from datetime import datetime

load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


class InterviewManager:
    """AI Recruiter using Gemini Flash to conduct adaptive interviews."""

    def __init__(self):
        # Initialize Gemini model
        self.model = genai.GenerativeModel("gemini-2.0-flash")
        self.chat = None
        self.current_stage = 1
        self.scores = {"resume_fit": 0, "hard_skills": 0, "soft_skills": 0}
        self.weights = {"resume_fit": 0.3, "hard_skills": 0.4, "soft_skills": 0.3}
        self.interview_data = {}
        self.conversation_history = []

        # Configure model generation
        self.generation_config = genai.types.GenerationConfig(
            temperature=0.7,
            top_p=0.9,
            top_k=40,
            candidate_count=1,
            max_output_tokens=2048,
            stop_sequences=["</SCORES>", "</STAGE>"],
        )

    # -------------------------------------------------------------------------
    # INTERVIEW FLOW
    # -------------------------------------------------------------------------
    async def start_interview(self, vacancy: Vacancy, candidate: Candidate, resume: Resume) -> Dict:
        """Initialize interview session with vacancy and candidate data"""
        context = self._prepare_context(vacancy, candidate, resume)

        # Initialize Gemini chat session
        self.chat = self.model.start_chat(history=[])
        self.chat.model_config = self.generation_config

        # Send system prompt
        system_prompt = self._get_system_prompt(context)
        response = await self.chat.send_message_async(system_prompt, generation_config=self.generation_config)

        return {"message": response.text, "stage": self.current_stage}

    async def process_message(self, message: str) -> Dict:
        """Process candidate's message and return AI recruiter's next question."""
        if not self.chat:
            raise Exception("Interview not initialized")

        response = await self.chat.send_message_async(message, generation_config=self.generation_config)
        
        # Store the response for final evaluation extraction
        self._last_response = response.text

        scores = self._extract_scores(response.text)
        if scores:
            self.scores.update(scores)

        self._update_stage(response.text)

        return {
            "message": response.text,
            "stage": self.current_stage,
            "scores": self.scores if self.current_stage == 4 else None,
        }

    # -------------------------------------------------------------------------
    # CONTEXT PREPARATION
    # -------------------------------------------------------------------------
    def _prepare_context(self, vacancy: Vacancy, candidate: Candidate, resume: Resume) -> Dict:
        """Build structured context for Gemini prompt."""
        total_experience = self._calculate_experience_years(candidate.experiences)
        candidate_skills = self._extract_candidate_skills(candidate.skills)
        education_history = self._extract_education_history(candidate.educations)
        employment_history = self._extract_employment_history(candidate.experiences)

        self.interview_data = {"vacancy": vacancy, "candidate": candidate, "resume": resume}

        return {
            "vacancy": {
                "title": vacancy.title,
                "company_name": vacancy.company_name,
                "city": vacancy.city,
                "country": vacancy.country,
                "experience_min": vacancy.experience_min,
                "experience_max": vacancy.experience_max,
                "employment_type": getattr(vacancy.employment_type, "value", None),
                "work_schedule": getattr(vacancy.work_schedule, "value", None),
                "education_level": vacancy.education_level,
                "required_languages": vacancy.required_languages,
                "required_skills": vacancy.required_skills,
                "salary_min": vacancy.salary_min,
                "salary_max": vacancy.salary_max,
                "currency": vacancy.currency,
                "responsibilities": vacancy.responsibilities,
                "requirements": vacancy.requirements,
                "conditions": vacancy.conditions,
                "benefits": vacancy.benefits,
                "description": vacancy.description,
            },
            "candidate": {
                "full_name": candidate.full_name,
                "city": candidate.city,
                "country": candidate.country,
                "expected_salary": candidate.expected_salary,
                "currency": candidate.currency,
                "employment_type": getattr(candidate.employment_type, "value", None),
                "summary": candidate.summary,
                "experience_years": total_experience,
                "skills": candidate_skills,
                "education_history": education_history,
                "employment_history": employment_history,
                "languages": [
                    {"language": lang.language, "level": lang.level} for lang in candidate.languages
                ],
            },
            "resume": {
                "resume_text": resume.resume_text,
                "parsed_json": resume.parsed_json,
                "file_url": resume.file_url,
            },
        }

    # -------------------------------------------------------------------------
    # PROMPT GENERATION
    # -------------------------------------------------------------------------
    def _get_system_prompt(self, context: Dict) -> str:
        """System-level prompt for Gemini — ensures smooth flow and instant final evaluation."""
        return f"""
You are an **AI HR expert and recruiter** conducting a structured, friendly, and professional interview.  
Your goal is to evaluate the candidate’s **resume fit, hard skills, and soft skills** based on the provided structured data and the conversation.

---

### 📊 JOB VACANCY
{json.dumps(context['vacancy'], indent=2, default=str)}

### 👤 CANDIDATE PROFILE
{json.dumps(context['candidate'], indent=2, default=str)}

### 📄 RESUME DATA
{json.dumps(context['resume'], indent=2, default=str)}

---

### 💬 COMMUNICATION RULES
- Always ask the **next relevant question immediately** after the candidate responds.  
  Never wait silently or request them to continue.  
- Maintain a **natural flow** — your message should always include either:
  - a short reaction to their answer **and**
  - the **next clear question**.
- Use warm, polite English with natural variation (“That’s great!”, “Thanks for sharing!”, “Good to know!”).
- Keep each message under 4 sentences.
- Adapt dynamically — use the structured data to guide questions (ask only about missing, mismatched, or unclear points).

---

### 🧩 INTERVIEW FLOW (3 STAGES ONLY)

#### **Stage 1 — Resume Fit Check**
Compare candidate and vacancy data:
- City, country, relocation, experience range
- Salary, schedule, employment type, education level, languages

If mismatches or missing info → ask 1–2 clarifying questions directly related to them.  
Example:
> “This role is based in Almaty — would relocation work for you?”  
> “You mentioned full-time work preference — this position is hybrid, is that fine?”

Then assign a **resume_fit score** based on data matching accuracy.

#### **Stage 2 — Hard Skills**
Check the technical and professional match:
- Compare required_skills, responsibilities, and requirements with candidate’s skills, projects, and resume text.
- Ask 1–2 concise, context-aware questions about real project experience or tool usage.
- Score based on overlap and demonstrated competency.

#### **Stage 3 — Soft Skills & Motivation**
Ask 2–3 questions about motivation, communication, teamwork, adaptability, and learning attitude.  
Then directly give the **final evaluation** — do not wait for a new “Stage 4”.

---

### 🧮 EVALUATION RULES (ACCURACY MODE)
Evaluate based on structured data and the candidate’s answers.

Use quantitative logic where possible:
- Resume Fit = (matching fields ÷ relevant fields) × 100
- Hard Skills = (matched or equivalent skills ÷ required skills) × 100 ± context adjustment (±10%)
- Soft Skills = (traits shown ÷ expected traits) × 100

Partial matches count as 0.5.  
Missing data is neutral (score ≈ 50%).  
Never assign random values.

---



**Output format after each response:**
<SCORES>{{"stage": 1, "resume_fit": 85, "hard_skills": 0, "soft_skills": 0}}</SCORES>
<STAGE>1</STAGE>

After finishing **Stage 3**, immediately provide the **final structured summary** — no Stage 4 required:

<SCORES>{{"stage": 3, "resume_fit": 85, "hard_skills": 90, "soft_skills": 78}}</SCORES>
<STAGE>3</STAGE>


---

### 🚀 FINAL EVALUATION

Also give the final evaluation immediately after finishing Stage 3, without waiting for the candidate's response.
The final evaluation should be in the following format:

**Overall Assessment**: [Overall match percentage]%

**Breakdown**:
- Resume Fit: [score]% - [brief reason]
- Hard Skills: [score]% - [brief reason]  
- Soft Skills: [score]% - [brief reason]

**Key Insights**:
- [2-3 specific observations about strengths/concerns]
- [Recommendation for next steps]

Thank the candidate warmly and professionally.


---

**Start the interview with a friendly greeting and begin Stage 1.**
"""

    # -------------------------------------------------------------------------
    # SCORING / STAGE LOGIC
    # -------------------------------------------------------------------------
    def _extract_scores(self, response: str) -> Optional[Dict]:
        """Extract structured scores from Gemini output."""
        match = re.search(r"<SCORES>(.*?)</SCORES>", response, re.DOTALL)
        if not match:
            return None
        try:
            scores = json.loads(match.group(1))
            for key, value in scores.items():
                if key in ["resume_fit", "hard_skills", "soft_skills"]:
                    scores[key] = max(0, min(100, float(value)))
            return scores
        except json.JSONDecodeError:
            return None

    def _extract_stage(self, response: str) -> Optional[int]:
        match = re.search(r"<STAGE>(\d+)</STAGE>", response)
        return int(match.group(1)) if match else None

    def _update_stage(self, response: str) -> None:
        """Progress interview stage."""
        stage = self._extract_stage(response)
        if stage:
            self.current_stage = stage
        elif self.scores["resume_fit"] > 0 and self.current_stage == 1:
            self.current_stage = 2
        elif self.scores["hard_skills"] > 0 and self.current_stage == 2:
            self.current_stage = 3
        elif self.scores["soft_skills"] > 0 and self.current_stage == 3:
            self.current_stage = 4

    # -------------------------------------------------------------------------
    # DATA HELPERS
    # -------------------------------------------------------------------------
    def _calculate_experience_years(self, experiences: List[CandidateExperience]) -> float:
        if not experiences:
            return 0.0
        total_months = 0
        for exp in experiences:
            start = exp.start_date
            end = exp.end_date or datetime.now().date()
            months = (end.year - start.year) * 12 + (end.month - start.month)
            total_months += months
        return round(total_months / 12, 1)

    def _extract_candidate_skills(self, skills: List[CandidateSkill]) -> List[Dict]:
        return [{"name": s.skill_name, "level": s.skill_level, "category": s.category} for s in skills]

    def _extract_education_history(self, educations: List[CandidateEducation]) -> List[Dict]:
        return [
            {
                "institution": e.institution,
                "degree": e.degree,
                "field_of_study": e.field_of_study,
                "start_year": e.start_year,
                "end_year": e.end_year,
                "is_current": e.is_current,
            }
            for e in educations
        ]

    def _extract_employment_history(self, experiences: List[CandidateExperience]) -> List[Dict]:
        return [
            {
                "company": e.company_name,
                "position": e.position,
                "industry": e.industry,
                "start_date": e.start_date.isoformat() if e.start_date else None,
                "end_date": e.end_date.isoformat() if e.end_date else None,
                "responsibilities": e.responsibilities,
                "achievements": e.achievements,
                "technologies": e.technologies,
            }
            for e in experiences
        ]

    # -------------------------------------------------------------------------
    # FINAL EVALUATION (AI-DRIVEN)
    # -------------------------------------------------------------------------
    def _extract_final_evaluation(self, response: str) -> Optional[Dict]:
        """Extract final evaluation from AI response."""
        # Look for structured evaluation in the response
        import re
        
        # Try to extract overall assessment percentage
        overall_match = re.search(r"Overall Assessment[:\s]*(\d+)%", response, re.IGNORECASE)
        if not overall_match:
            overall_match = re.search(r"Overall[:\s]*(\d+)%", response, re.IGNORECASE)
        
        # Try to extract breakdown scores
        breakdown = {}
        breakdown_patterns = [
            r"Resume Fit[:\s]*(\d+)%",
            r"Hard Skills[:\s]*(\d+)%", 
            r"Soft Skills[:\s]*(\d+)%"
        ]
        
        for pattern in breakdown_patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                score = int(match.group(1))
                if "Resume Fit" in pattern:
                    breakdown["resume_fit"] = score
                elif "Hard Skills" in pattern:
                    breakdown["hard_skills"] = score
                elif "Soft Skills" in pattern:
                    breakdown["soft_skills"] = score
        
        if overall_match and breakdown:
            return {
                "overall_relevance": int(overall_match.group(1)),
                "breakdown": breakdown,
                "reasoning": self._extract_reasoning_from_response(response)
            }
        
        return None
    
    def _extract_reasoning_from_response(self, response: str) -> List[str]:
        """Extract reasoning points from AI response."""
        import re
        
        # Look for bullet points or numbered lists
        reasoning_patterns = [
            r"[-•]\s*([^-\n]+)",
            r"\d+\.\s*([^0-9\n]+)",
            r"Key Insights[:\s]*([^$]+)",
        ]
        
        reasoning = []
        for pattern in reasoning_patterns:
            matches = re.findall(pattern, response, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                clean_match = match.strip()
                if len(clean_match) > 10 and len(clean_match) < 200:  # Reasonable length
                    reasoning.append(clean_match)
        
        return reasoning[:3]  # Limit to 3 key points

    def get_final_score(self) -> Dict:
        """Get final evaluation from AI-generated scores."""
        if not all(v > 0 for v in self.scores.values()):
            return {"error": "Interview not completed"}
        
        # Use the scores that were extracted during the interview
        return {
            "overall_relevance": round(sum(self.scores.values()) / len(self.scores), 1),
            "breakdown": self.scores.copy(),
            "reasoning": self._generate_simple_reasoning(),
        }
    
    def _generate_simple_reasoning(self) -> List[str]:
        """Generate simple reasoning based on scores."""
        reasoning = []
        
        if self.scores["resume_fit"] >= 80:
            reasoning.append("Strong alignment with job requirements")
        elif self.scores["resume_fit"] >= 60:
            reasoning.append("Good overall fit with minor gaps")
        else:
            reasoning.append("Some mismatches in basic requirements")
            
        if self.scores["hard_skills"] >= 80:
            reasoning.append("Excellent technical competency")
        elif self.scores["hard_skills"] >= 60:
            reasoning.append("Solid technical skills")
        else:
            reasoning.append("Technical skills need development")
            
        if self.scores["soft_skills"] >= 80:
            reasoning.append("Strong communication and motivation")
        elif self.scores["soft_skills"] >= 60:
            reasoning.append("Good interpersonal skills")
        else:
            reasoning.append("Soft skills could be improved")
            
        return reasoning

    async def generate_final_evaluation(self) -> Dict:
        """Generate final evaluation - AI-driven with fallback to extracted scores."""
        # First try to get evaluation from the last AI response
        if hasattr(self, '_last_response'):
            ai_evaluation = self._extract_final_evaluation(self._last_response)
            if ai_evaluation:
                return {
                    "overall_score": ai_evaluation["overall_relevance"],
                    "breakdown": ai_evaluation["breakdown"],
                    "reasoning": ai_evaluation["reasoning"],
                    "ai_confidence": 0.9,
                }
        
        # Fallback to extracted scores
        final_data = self.get_final_score()
        if "error" in final_data:
            return final_data

        return {
            "overall_score": final_data["overall_relevance"],
            "breakdown": final_data["breakdown"],
            "reasoning": final_data["reasoning"],
            "ai_confidence": 0.8,
        }


# Backward compatibility
InterviewAI = InterviewManager
