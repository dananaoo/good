import google.generativeai as genai
from typing import Dict, List, Optional, Tuple
from app.models.vacancy import Vacancy
from app.models.candidate import (
    Candidate,
    CandidateExperience,
    CandidateEducation,
    CandidateSkill,
    CandidateLanguage,
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
        """Process candidate's message and return AI recruiter’s next question."""
        if not self.chat:
            raise Exception("Interview not initialized")

        response = await self.chat.send_message_async(message, generation_config=self.generation_config)

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
        }

    # -------------------------------------------------------------------------
    # PROMPT GENERATION
    # -------------------------------------------------------------------------
    def _get_system_prompt(self, context: Dict) -> str:
        """System-level prompt for Gemini — ensures natural variation."""
        return f"""You are an **AI recruiter** conducting a friendly, short, professional interview with a candidate.

🎯 **Your goal**:
- Compare candidate profile with job vacancy.
- Ask 2–3 short, natural questions per stage.
- Adjust dynamically — don’t repeat template wording.
- Evaluate and score: Resume Fit, Hard Skills, Soft Skills & Motivation.

---

### 📊 VACANCY DATA
{json.dumps(context['vacancy'], indent=2, default=str)}

### 👤 CANDIDATE DATA
{json.dumps(context['candidate'], indent=2, default=str)}

---

### 💬 COMMUNICATION STYLE
- Speak in **clear, natural English**.
- Vary phrasing: each question should sound unique and conversational.
- Use warm, polite tone: “That’s great!”, “Good to know!”, “I see, thanks for clarifying.”
- Avoid robotic or repetitive patterns.
- Keep messages concise (< 5 sentences).

---

### 🧩 INTERVIEW STAGES

#### Stage 1 — Resume Fit
Check city, experience, employment type, salary expectations, and availability.
Ask short clarifying questions (not identical to examples):
- “Where are you currently based?”
- “Would relocation be an option?”
- “Does the schedule or compensation fit your preferences?”

#### Stage 2 — Hard Skills
Explore candidate’s technical abilities using context-aware phrasing.
Example *patterns* (vary wording):
- “Tell me about a project where you used [a relevant skill].”
- “Which tools or technologies do you work with most often?”
- “How do you usually approach solving [task type] problems?”

#### Stage 3 — Soft Skills & Motivation
Ask about communication, teamwork, goals, and work style.
Vary tone and question structure:
- “What drives you to do your best work?”
- “How do you handle challenges or feedback?”
- “What kind of work environment helps you perform best?”

---

### 🧮 SCORING RULES
After each stage, estimate numeric scores (0–100%) for:
- resume_fit
- hard_skills
- soft_skills

Format strictly as:
<SCORES>{{"stage": 1, "resume_fit": 85, "hard_skills": 0, "soft_skills": 0}}</SCORES>
<STAGE>1</STAGE>

When all three categories have scores > 0:
<SCORES>{{"stage": 4, "resume_fit": 85, "hard_skills": 90, "soft_skills": 78}}</SCORES>
<STAGE>4</STAGE>

---

### 🚀 FINAL STAGE
When interview ends, summarize briefly:
- Overall match percentage
- Category breakdown
- 2–3 concise reasoning sentences
- Thank the candidate warmly

Start with a greeting and Stage 1: **Resume Fit.**
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
    # FINAL EVALUATION
    # -------------------------------------------------------------------------
    def _calculate_dynamic_weights(self, vacancy: Vacancy) -> Dict[str, float]:
        weights = {"resume_fit": 0.3, "hard_skills": 0.4, "soft_skills": 0.3}
        if vacancy.required_skills and len(vacancy.required_skills) > 5:
            weights.update({"hard_skills": 0.5, "resume_fit": 0.25, "soft_skills": 0.25})
        if getattr(vacancy.work_schedule, "value", None) == "remote":
            weights.update({"resume_fit": 0.2, "soft_skills": 0.4})
        if getattr(vacancy.employment_type, "value", None) == "internship":
            weights.update({"hard_skills": 0.3, "soft_skills": 0.4})
        return weights

    def get_final_score(self) -> Dict:
        if not all(v > 0 for v in self.scores.values()):
            return {"error": "Interview not completed"}

        weights = self._calculate_dynamic_weights(self.interview_data["vacancy"])
        final = (
            self.scores["resume_fit"] * weights["resume_fit"]
            + self.scores["hard_skills"] * weights["hard_skills"]
            + self.scores["soft_skills"] * weights["soft_skills"]
        )
        return {
            "overall_relevance": round(final, 1),
            "breakdown": self.scores,
            "weights": weights,
            "reasoning": self._generate_reasoning(),
        }

    def _generate_reasoning(self) -> str:
        parts = []
        if self.scores["resume_fit"] >= 80:
            parts.append("Strong alignment with job requirements")
        elif self.scores["resume_fit"] >= 60:
            parts.append("Good overall fit with minor mismatches")
        else:
            parts.append("Some inconsistencies in job fit")

        if self.scores["hard_skills"] >= 80:
            parts.append("Excellent technical proficiency")
        elif self.scores["hard_skills"] >= 60:
            parts.append("Solid skills with room for growth")
        else:
            parts.append("Technical knowledge below expectations")

        if self.scores["soft_skills"] >= 80:
            parts.append("Highly motivated and communicative")
        elif self.scores["soft_skills"] >= 60:
            parts.append("Good interpersonal adaptability")
        else:
            parts.append("Needs improvement in motivation or communication")

        return "; ".join(parts) + "."

    async def generate_final_evaluation(self) -> Dict:
        """Generate HR-ready evaluation summary."""
        final_data = self.get_final_score()
        if "error" in final_data:
            return final_data

        return {
            "overall_score": final_data["overall_relevance"],
            "breakdown": final_data["breakdown"],
            "reasoning": final_data["reasoning"],
            "weights": final_data["weights"],
            "ai_confidence": 0.85,
        }


# Backward compatibility
InterviewAI = InterviewManager
