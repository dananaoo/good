import asyncio
import sys
import os
from datetime import date

# Add backend root to import path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.ai.interview_logic import InterviewManager  # fixed import path
from app.models.vacancy import Vacancy, VacancyEmploymentType, WorkSchedule
from app.models.candidate import (
    Candidate,
    EmploymentType,
    CandidateExperience,
    CandidateEducation,
    CandidateSkill,
    CandidateLanguage,
)
from app.models.resume import Resume


# -------------------------------------------------------------------------
# 🎯 INTERACTIVE REAL-TIME CHAT WITH GEMINI
# -------------------------------------------------------------------------
async def interactive_interview():
    """Run a real-time interactive chat with Gemini AI Recruiter."""
    print("🎯 Interactive Interview Mode")
    print("=" * 60)

    if not os.getenv("GEMINI_API_KEY"):
        print("❌ GEMINI_API_KEY not set. Please set it and retry.")
        return

    ai = InterviewManager()

    # Create small sample vacancy & candidate
    vacancy = Vacancy()
    vacancy.title = "Software Engineer"
    vacancy.company_name = "TechCorp"
    vacancy.city = "Almaty"
    vacancy.country = "Kazakhstan"
    vacancy.experience_min = 2
    vacancy.experience_max = 5
    vacancy.employment_type = VacancyEmploymentType.FULL_TIME
    vacancy.work_schedule = WorkSchedule.HYBRID
    vacancy.required_skills = ["Python", "FastAPI", "PostgreSQL"]

    candidate = Candidate()
    candidate.full_name = "You"
    candidate.city = "Astana"
    candidate.country = "Kazakhstan"
    candidate.expected_salary = 600000
    candidate.currency = "KZT"
    candidate.summary = "Backend developer with FastAPI and PostgreSQL experience."
    candidate.employment_type = EmploymentType.FULL_TIME

    resume = Resume()
    resume.resume_text = "Python backend developer"
    resume.parsed_json = {"skills": ["Python", "FastAPI"], "experience": "2 years"}

    # Start chat
    print("🚀 Starting interview...")
    start = await ai.start_interview(vacancy, candidate, resume)
    print("\n🤖 AI:", start["message"])

    # Live conversation loop
    while True:
        try:
            user_input = input("\n👤 You: ").strip()
            if user_input.lower() in {"quit", "exit", "q"}:
                print("👋 Interview ended.")
                break

            if not user_input:
                continue

            response = await ai.process_message(user_input)
            print("\n🤖 AI:", response["message"])

            # Check completion
            if response.get("scores") and all(v > 0 for v in response["scores"].values()):
                print("\n📊 Final evaluation generating...\n")
                final = await ai.generate_final_evaluation()
                print(f"🏆 Overall Score: {final['overall_score']}%")
                print(f"📋 Breakdown: {final['breakdown']}")
                print(f"💭 Reasoning: {final['reasoning']}")
                print(f"⚖️ Weights: {final['weights']}")
                break

        except KeyboardInterrupt:
            print("\n👋 Interview interrupted.")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            break


# -------------------------------------------------------------------------
# ENTRY POINT
# -------------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        asyncio.run(interactive_interview())
    else:
        print("🧪 Running test mode (no API)")
        print("💡 Use '--interactive' for live chat\n")
        asyncio.run(interactive_interview())
