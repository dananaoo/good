#!/usr/bin/env python3
"""
Live Interactive Interview Test - Real-time chat with AI Recruiter
This simulates how real candidates will interact with the system.
"""

import asyncio
import sys
import os
from datetime import date

# Add backend root to import path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.ai.interview_logic import InterviewManager
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


def create_sample_vacancy():
    """Create a sample vacancy for testing."""
    vacancy = Vacancy()
    vacancy.title = "Senior Python Developer"
    vacancy.company_name = "TechCorp"
    vacancy.city = "Almaty"
    vacancy.country = "Kazakhstan"
    vacancy.experience_min = 3.0
    vacancy.experience_max = 7.0
    vacancy.employment_type = VacancyEmploymentType.FULL_TIME
    vacancy.work_schedule = WorkSchedule.HYBRID
    vacancy.education_level = "Bachelor's"
    vacancy.required_languages = ["English", "Russian"]
    vacancy.required_skills = ["Python", "Django", "PostgreSQL", "Docker", "AWS"]
    vacancy.salary_min = 500000
    vacancy.salary_max = 800000
    vacancy.currency = "KZT"
    vacancy.responsibilities = [
        "Develop and maintain web applications",
        "Design and implement APIs",
        "Collaborate with cross-functional teams"
    ]
    vacancy.requirements = [
        "3+ years Python experience",
        "Experience with Django framework",
        "Knowledge of PostgreSQL",
        "English communication skills"
    ]
    vacancy.conditions = ["Health insurance", "Flexible hours", "Remote work options"]
    vacancy.benefits = ["Competitive salary", "Professional development", "Team events"]
    vacancy.description = "We are looking for an experienced Python developer to join our growing team."
    
    # Interview focus settings (employer can choose what to focus on)
    vacancy.interview_focus_resume_fit = True   # Default: always check basic fit
    vacancy.interview_focus_hard_skills = False  # Focus on technical skills
    vacancy.interview_focus_soft_skills = False  # Focus on soft skills
    
    return vacancy


def create_sample_candidate():
    """Create a sample candidate for testing."""
    candidate = Candidate()
    candidate.full_name = "Test Candidate"
    candidate.city = "Astana"
    candidate.country = "Kazakhstan"
    candidate.expected_salary = 600000
    candidate.currency = "KZT"
    candidate.summary = "Experienced Python developer with 4 years of experience in web development."
    candidate.employment_type = EmploymentType.FULL_TIME
    
    # Add experience
    exp = CandidateExperience()
    exp.company_name = "Previous Company"
    exp.position = "Python Developer"
    exp.start_date = date(2020, 1, 1)
    exp.end_date = date(2024, 1, 1)
    exp.responsibilities = "Developed web applications using Python and Django"
    exp.achievements = "Improved application performance by 30%"
    exp.technologies = ["Python", "Django", "PostgreSQL"]
    candidate.experiences = [exp]
    
    # Add education
    edu = CandidateEducation()
    edu.institution = "Kazakh National University"
    edu.degree = "Bachelor's"
    edu.field_of_study = "Computer Science"
    edu.start_year = 2016
    edu.end_year = 2020
    edu.is_current = False
    candidate.educations = [edu]
    
    # Add skills
    skills = []
    for skill_name in ["Python", "Django", "PostgreSQL", "Docker"]:
        skill = CandidateSkill()
        skill.skill_name = skill_name
        skill.skill_level = 4
        skill.category = "Hard"
        skills.append(skill)
    candidate.skills = skills
    
    # Add languages
    lang = CandidateLanguage()
    lang.language = "English"
    lang.level = "B2"
    candidate.languages = [lang]
    
    return candidate


def create_sample_resume():
    """Create a sample resume for testing."""
    resume = Resume()
    resume.resume_text = "Python developer with 4 years of experience in web development using Django and PostgreSQL."
    resume.parsed_json = {
        "skills": ["Python", "Django", "PostgreSQL", "Docker"],
        "experience": "4 years",
        "education": "Bachelor's in Computer Science"
    }
    return resume


async def run_live_interview():
    """Run a live interactive interview session."""
    print("🎯 Live Interactive Interview with AI Recruiter")
    print("=" * 60)
    print("This simulates how real candidates will interact with the system.")
    print("The AI will conduct a 3-stage interview and provide evaluation.")
    print()
    
    # Check API key
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ GEMINI_API_KEY not set. Please set it and retry.")
        print("   export GEMINI_API_KEY='your-api-key-here'")
        return
    
    # Initialize AI recruiter
    ai = InterviewManager()
    
    # Create sample data
    vacancy = create_sample_vacancy()
    candidate = create_sample_candidate()
    resume = create_sample_resume()
    
    print(f"📋 Position: {vacancy.title} at {vacancy.company_name}")
    print(f"📍 Location: {vacancy.city}, {vacancy.country}")
    print(f"💰 Salary: {vacancy.salary_min:,} - {vacancy.salary_max:,} {vacancy.currency}")
    print(f"🎯 Required Skills: {', '.join(vacancy.required_skills)}")
    print()
    print("🚀 Starting interview...")
    print("💡 Type your answers naturally, as you would in a real interview.")
    print("💡 Type 'quit' to exit at any time.")
    print("=" * 60)
    
    # Start the interview
    start = await ai.start_interview(vacancy, candidate, resume)
    print(f"\n🤖 AI Recruiter: {start['message']}")
    
    # Interactive conversation loop
    message_count = 0
    max_messages = 10  # Prevent infinite loops
    
    while message_count < max_messages:
        try:
            # Get user input
            user_input = input(f"\n👤 You: ").strip()
            
            if user_input.lower() in {'quit', 'exit', 'q', 'bye'}:
                print("\n👋 Interview ended. Thank you for your time!")
                break
            
            if not user_input:
                print("⚠️ Please enter a response.")
                continue
            
            # Process the response
            response = await ai.process_message(user_input)
            print(f"\n🤖 AI Recruiter: {response['message']}")
            
            # Check if interview is complete
            if response.get("scores") and all(score > 0 for score in response["scores"].values()):
                print("\n🎉 Interview completed! Generating final evaluation...")
                print("=" * 60)
                
                final = await ai.generate_final_evaluation()
                
                if "error" not in final:
                    print(f"\n📊 FINAL EVALUATION")
                    print(f"🏆 Overall Score: {final['overall_score']}%")
                    print(f"\n📋 Breakdown:")
                    for category, score in final['breakdown'].items():
                        print(f"   • {category.replace('_', ' ').title()}: {score}%")
                    
                    print(f"\n💭 Reasoning:")
                    for i, reason in enumerate(final['reasoning'], 1):
                        print(f"   {i}. {reason}")
                    
                    print(f"\n🤖 AI Confidence: {final.get('ai_confidence', 0.8):.1%}")
                    print("\n✨ Thank you for participating in this interview!")
                else:
                    print(f"⚠️ {final['error']}")
                
                break
            
            message_count += 1
            
        except KeyboardInterrupt:
            print("\n\n👋 Interview interrupted. Thank you for your time!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            break
    
    if message_count >= max_messages:
        print(f"\n⚠️ Maximum messages reached ({max_messages}). Interview ended.")


async def run_demo_mode():
    """Run a demo with simulated responses."""
    print("🎯 Demo Mode - Simulated Interview")
    print("=" * 50)
    print("This shows how the AI conducts an interview with sample responses.")
    print()
    
    # Check API key
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ GEMINI_API_KEY not set. Please set it and retry.")
        return
    
    # Initialize AI recruiter
    ai = InterviewManager()
    
    # Create sample data
    vacancy = create_sample_vacancy()
    candidate = create_sample_candidate()
    resume = create_sample_resume()
    
    print(f"📋 Position: {vacancy.title} at {vacancy.company_name}")
    print(f"📍 Location: {vacancy.city}, {vacancy.country}")
    print()
    
    # Start the interview
    start = await ai.start_interview(vacancy, candidate, resume)
    print(f"🤖 AI: {start['message']}")
    
    # Simulated responses
    demo_responses = [
        "Yes, I'm open to relocating to Almaty. I've been looking for opportunities in that area.",
        "I'm very confident with Python and Django - I've been using them for 4 years. I have good experience with PostgreSQL and some exposure to Docker. I'd rate myself 4 out of 5 for the required skills.",
        "I'm motivated by solving complex problems and working in a collaborative environment. I enjoy learning new technologies and contributing to meaningful projects. I work best in teams where I can both contribute my expertise and learn from others."
    ]
    
    for i, response in enumerate(demo_responses, 1):
        print(f"\n👤 Candidate: {response}")
        ai_response = await ai.process_message(response)
        print(f"🤖 AI: {ai_response['message']}")
        
        # Check if interview is complete
        if ai_response.get("scores") and all(score > 0 for score in ai_response["scores"].values()):
            print("\n🎉 Interview completed! Generating final evaluation...")
            
            final = await ai.generate_final_evaluation()
            
            if "error" not in final:
                print(f"\n📊 FINAL EVALUATION")
                print(f"🏆 Overall Score: {final['overall_score']}%")
                print(f"\n📋 Breakdown:")
                for category, score in final['breakdown'].items():
                    print(f"   • {category.replace('_', ' ').title()}: {score}%")
                
                print(f"\n💭 Reasoning:")
                for i, reason in enumerate(final['reasoning'], 1):
                    print(f"   {i}. {reason}")
                
                print(f"\n🤖 AI Confidence: {final.get('ai_confidence', 0.8):.1%}")
            else:
                print(f"⚠️ {final['error']}")
            
            break
    
    print("\n✨ Demo completed!")


def main():
    """Main entry point."""
    print("🎯 AI Recruiter Interview System")
    print("=" * 40)
    print("Choose mode:")
    print("1. Live Interactive Interview (real-time chat)")
    print("2. Demo Mode (simulated responses)")
    print("3. Exit")
    
    while True:
        try:
            choice = input("\nEnter choice (1-3): ").strip()
            
            if choice == "1":
                asyncio.run(run_live_interview())
                break
            elif choice == "2":
                asyncio.run(run_demo_mode())
                break
            elif choice == "3":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please enter 1, 2, or 3.")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            break


if __name__ == "__main__":
    main()
