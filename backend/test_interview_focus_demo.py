#!/usr/bin/env python3
"""
Demo script showing different interview focus settings
This demonstrates how employers can customize what AI focuses on during interviews.
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


def create_sample_candidate():
    """Create a sample candidate for testing."""
    candidate = Candidate()
    candidate.full_name = "Test Candidate"
    candidate.city = "Astana"
    candidate.country = "Kazakhstan"
    candidate.expected_salary = 600000
    candidate.currency = "KZT"
    candidate.summary = "Experienced Python developer with 4 years of experience."
    candidate.employment_type = EmploymentType.FULL_TIME
    
    # Add experience
    exp = CandidateExperience()
    exp.company_name = "Previous Company"
    exp.position = "Python Developer"
    exp.start_date = date(2020, 1, 1)
    exp.end_date = date(2024, 1, 1)
    exp.responsibilities = "Developed web applications using Python and Django"
    exp.technologies = ["Python", "Django", "PostgreSQL"]
    candidate.experiences = [exp]
    
    # Add skills
    skills = []
    for skill_name in ["Python", "Django", "PostgreSQL"]:
        skill = CandidateSkill()
        skill.skill_name = skill_name
        skill.skill_level = 4
        skill.category = "Hard"
        skills.append(skill)
    candidate.skills = skills
    
    return candidate


def create_sample_resume():
    """Create a sample resume for testing."""
    resume = Resume()
    resume.resume_text = "Python developer with 4 years of experience in web development."
    resume.parsed_json = {"skills": ["Python", "Django"], "experience": "4 years"}
    return resume


def create_vacancy_with_focus(resume_fit=True, hard_skills=False, soft_skills=False):
    """Create vacancy with specific interview focus settings."""
    vacancy = Vacancy()
    vacancy.title = "Software Engineer"
    vacancy.company_name = "TechCorp"
    vacancy.city = "Almaty"
    vacancy.country = "Kazakhstan"
    vacancy.experience_min = 3.0
    vacancy.experience_max = 7.0
    vacancy.employment_type = VacancyEmploymentType.FULL_TIME
    vacancy.work_schedule = WorkSchedule.HYBRID
    vacancy.required_skills = ["Python", "Django", "PostgreSQL"]
    vacancy.salary_min = 500000
    vacancy.salary_max = 800000
    vacancy.currency = "KZT"
    vacancy.description = "We are looking for an experienced Python developer."
    
    # Set interview focus based on parameters
    vacancy.interview_focus_resume_fit = resume_fit
    vacancy.interview_focus_hard_skills = hard_skills
    vacancy.interview_focus_soft_skills = soft_skills
    
    return vacancy


async def demo_interview_focus(focus_name, resume_fit, hard_skills, soft_skills):
    """Demo interview with specific focus settings."""
    print(f"\n🎯 {focus_name}")
    print("=" * 60)
    
    # Check API key
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ GEMINI_API_KEY not set. Please set it and retry.")
        return
    
    # Create data
    vacancy = create_vacancy_with_focus(resume_fit, hard_skills, soft_skills)
    candidate = create_sample_candidate()
    resume = create_sample_resume()
    
    print(f"📋 Interview Focus Settings:")
    print(f"   • Resume Fit: {'✅' if resume_fit else '❌'}")
    print(f"   • Hard Skills: {'✅' if hard_skills else '❌'}")
    print(f"   • Soft Skills: {'✅' if soft_skills else '❌'}")
    print()
    
    # Initialize AI
    ai = InterviewManager()
    
    # Start interview
    start = await ai.start_interview(vacancy, candidate, resume)
    print(f"🤖 AI: {start['message']}")
    
    # Simulate responses
    responses = [
        "Yes, I'm open to relocating to Almaty.",
        "I'm very confident with Python and Django - I've been using them for 4 years.",
        "I'm motivated by solving complex problems and working in teams."
    ]
    
    for i, response in enumerate(responses):
        print(f"\n👤 Candidate: {response}")
        ai_response = await ai.process_message(response)
        print(f"🤖 AI: {ai_response['message']}")
        
        # Check if interview is complete
        if ai_response.get("scores") and any(v > 0 for v in ai_response["scores"].values()):
            print("\n🎉 Interview completed! Generating final evaluation...")
            
            final = await ai.generate_final_evaluation()
            
            if "error" not in final:
                print(f"\n📊 FINAL EVALUATION")
                print(f"🏆 Overall Score: {final['overall_score']}%")
                print(f"📋 Breakdown:")
                for category, score in final['breakdown'].items():
                    status = "✅" if score > 0 else "⏭️"
                    print(f"   {status} {category.replace('_', ' ').title()}: {score}%")
                
                if "enabled_stages" in final:
                    print(f"🎯 Enabled Stages: {', '.join(final['enabled_stages'])}")
            else:
                print(f"⚠️ {final['error']}")
            
            break
    
    print("\n" + "="*60)


async def main():
    """Run demos for different focus settings."""
    print("🎯 Interview Focus Settings Demo")
    print("This shows how employers can customize what AI focuses on during interviews.")
    print()
    
    # Demo 1: Only Resume Fit (default)
    await demo_interview_focus(
        "Demo 1: Only Resume Fit Check (Default)",
        resume_fit=True,
        hard_skills=False,
        soft_skills=False
    )
    
    # Demo 2: Resume Fit + Hard Skills
    await demo_interview_focus(
        "Demo 2: Resume Fit + Hard Skills",
        resume_fit=True,
        hard_skills=True,
        soft_skills=False
    )
    
    # Demo 3: All Three Stages
    await demo_interview_focus(
        "Demo 3: Complete Interview (All Stages)",
        resume_fit=True,
        hard_skills=True,
        soft_skills=True
    )
    
    # Demo 4: Only Soft Skills
    await demo_interview_focus(
        "Demo 4: Only Soft Skills Assessment",
        resume_fit=False,
        hard_skills=False,
        soft_skills=True
    )
    
    print("\n✨ Demo completed!")
    print("\n💡 Key Benefits:")
    print("   • Employers can customize interview focus")
    print("   • AI adapts questions based on selected stages")
    print("   • Faster interviews for specific needs")
    print("   • More targeted candidate evaluation")


if __name__ == "__main__":
    asyncio.run(main())
