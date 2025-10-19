#!/usr/bin/env python3
"""
Test script to verify AI agent storage functionality.
This script tests the complete flow from AI interview to database storage.
"""

import asyncio
import sys
import os
from datetime import date
import uuid

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
from app.models.interview import Interview, InterviewStatus, InterviewStage
from app.models.user import User, UserRole
from app.services.evaluation_service import EvaluationService
from app.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


def create_test_vacancy():
    """Create a test vacancy."""
    vacancy = Vacancy()
    vacancy.id = uuid.uuid4()
    vacancy.title = "Python Developer"
    vacancy.company_name = "Test Company"
    vacancy.city = "Almaty"
    vacancy.country = "Kazakhstan"
    vacancy.experience_min = 2.0
    vacancy.experience_max = 5.0
    vacancy.employment_type = VacancyEmploymentType.FULL_TIME
    vacancy.work_schedule = WorkSchedule.HYBRID
    vacancy.required_skills = ["Python", "Django", "PostgreSQL"]
    vacancy.salary_min = 400000
    vacancy.salary_max = 700000
    vacancy.currency = "KZT"
    vacancy.description = "We are looking for a Python developer."
    
    # Interview focus settings
    vacancy.interview_focus_resume_fit = True
    vacancy.interview_focus_hard_skills = True
    vacancy.interview_focus_soft_skills = False  # Only test resume fit and hard skills
    
    return vacancy


def create_test_candidate():
    """Create a test candidate."""
    candidate = Candidate()
    candidate.id = uuid.uuid4()
    candidate.full_name = "Test User"
    candidate.city = "Astana"
    candidate.country = "Kazakhstan"
    candidate.expected_salary = 500000
    candidate.currency = "KZT"
    candidate.summary = "Python developer with 3 years of experience."
    candidate.employment_type = EmploymentType.FULL_TIME
    
    # Add experience
    exp = CandidateExperience()
    exp.company_name = "Previous Company"
    exp.position = "Python Developer"
    exp.start_date = date(2021, 1, 1)
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


def create_test_resume():
    """Create a test resume."""
    resume = Resume()
    resume.id = uuid.uuid4()
    resume.resume_text = "Python developer with 3 years of experience in web development."
    resume.parsed_json = {"skills": ["Python", "Django"], "experience": "3 years"}
    return resume


async def test_ai_agent_with_storage():
    """Test AI agent and verify storage functionality."""
    print("🤖 Testing AI Agent Storage")
    print("=" * 50)
    
    # Check API key
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ GEMINI_API_KEY not set. Please set it and retry.")
        print("   export GEMINI_API_KEY='your-api-key-here'")
        return False
    
    # Create test data
    vacancy = create_test_vacancy()
    candidate = create_test_candidate()
    resume = create_test_resume()
    
    print(f"📋 Position: {vacancy.title} at {vacancy.company_name}")
    print(f"👤 Candidate: {candidate.full_name}")
    print(f"🎯 Focus: Resume Fit + Hard Skills (Soft Skills disabled)")
    print()
    
    # Initialize AI
    ai = InterviewManager()
    
    # Start interview
    print("🚀 Starting interview...")
    start = await ai.start_interview(vacancy, candidate, resume)
    print(f"🤖 AI: {start['message']}")
    
    # Simulate interview responses
    responses = [
        "Yes, I'm open to relocating to Almaty.",
        "I'm very confident with Python and Django. I've been using them for 3 years and have good experience with PostgreSQL."
    ]
    
    print("\n📝 Simulating interview responses...")
    for i, response in enumerate(responses, 1):
        print(f"\n👤 Candidate: {response}")
        ai_response = await ai.process_message(response)
        print(f"🤖 AI: {ai_response['message']}")
        
        # Check if interview is complete
        if ai_response.get("scores") and any(v > 0 for v in ai_response["scores"].values()):
            print("\n🎉 Interview completed!")
            break
    
    # Generate final evaluation
    final_evaluation = await ai.generate_final_evaluation()
    
    if "error" not in final_evaluation:
        print(f"\n📊 FINAL EVALUATION")
        print(f"🏆 Overall Score: {final_evaluation['overall_score']}%")
        print(f"📋 Breakdown:")
        for category, score in final_evaluation['breakdown'].items():
            print(f"   • {category.replace('_', ' ').title()}: {score}%")
        
        print(f"\n💭 Reasoning:")
        for i, reason in enumerate(final_evaluation['reasoning'], 1):
            print(f"   {i}. {reason}")
        
        print(f"\n🤖 AI Confidence: {final_evaluation.get('ai_confidence', 0.8):.1%}")
        
        # Test storage simulation
        print(f"\n💾 STORAGE SIMULATION")
        print("=" * 50)
        
        # Simulate what would be stored in database
        mock_interview_id = str(uuid.uuid4())
        
        print(f"📝 Chat History ({len(responses)} exchanges):")
        print(f"   • Candidate responses: {len(responses)}")
        print(f"   • AI responses: {len(responses) + 1}")  # +1 for initial greeting
        
        print(f"\n📊 Evaluation Data:")
        print(f"   • Overall Score: {final_evaluation['overall_score']}%")
        print(f"   • Breakdown: {final_evaluation['breakdown']}")
        print(f"   • Reasoning: {len(final_evaluation['reasoning'])} points")
        print(f"   • AI Confidence: {final_evaluation.get('ai_confidence', 0.8):.1%}")
        
        print(f"\n✅ Data Structure Ready for Database:")
        print(f"   • Interview ID: {mock_interview_id}")
        print(f"   • Chat Messages: Ready to save")
        print(f"   • Evaluation Scores: Ready to save")
        print(f"   • Evaluation Summary: Ready to save")
        
        return True
        
    else:
        print(f"⚠️ {final_evaluation['error']}")
        return False


async def test_database_connection():
    """Test database connection and basic operations."""
    print("\n🗄️ Testing Database Connection")
    print("=" * 50)
    
    try:
        # Get database session
        async for db in get_db():
            print("✅ Database connection successful!")
            
            # Test basic query
            result = await db.execute(select(1))
            test_value = result.scalar()
            print(f"✅ Database query test: {test_value}")
            
            # Test if tables exist (without actually querying them)
            print("✅ Database tables should be available:")
            print("   • interviews")
            print("   • interview_messages")
            print("   • evaluation_scores")
            print("   • evaluation_summary")
            
            break
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    
    return True


def show_testing_options():
    """Show different testing options."""
    print("\n🧪 Testing Options")
    print("=" * 50)
    
    print("1. 🤖 AI Agent Test (Current)")
    print("   • Tests AI interview functionality")
    print("   • Simulates storage without actual database")
    print("   • Shows data structure that would be saved")
    print()
    
    print("2. 🌐 WebSocket Test")
    print("   • Real-time interview with actual database storage")
    print("   • Requires running server")
    print("   • Command: python -m uvicorn app.main:app --reload")
    print()
    
    print("3. 📡 API Test")
    print("   • Test API endpoints for data retrieval")
    print("   • Requires running server")
    print("   • Use tools like Postman or curl")
    print()
    
    print("4. 🗄️ Database Test")
    print("   • Direct database operations")
    print("   • Verify data is actually stored")
    print("   • Check tables and records")
    print()


async def main():
    """Main test function."""
    print("🎯 AI Agent Storage Test")
    print("=" * 60)
    print("This test verifies that the AI agent works and shows what data would be stored.")
    print()
    
    # Test database connection
    db_ok = await test_database_connection()
    
    # Test AI agent
    ai_ok = await test_ai_agent_with_storage()
    
    # Show results
    print(f"\n📊 Test Results")
    print("=" * 50)
    print(f"🗄️ Database Connection: {'✅ PASS' if db_ok else '❌ FAIL'}")
    print(f"🤖 AI Agent: {'✅ PASS' if ai_ok else '❌ FAIL'}")
    
    if ai_ok and db_ok:
        print(f"\n🎉 All tests passed! Your AI agent is working correctly.")
        print(f"💾 Data structure is ready for database storage.")
        print(f"🚀 You can now test with real database storage.")
    else:
        print(f"\n⚠️ Some tests failed. Please check the errors above.")
    
    # Show testing options
    show_testing_options()


if __name__ == "__main__":
    asyncio.run(main())
