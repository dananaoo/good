#!/usr/bin/env python3
"""
WebSocket test script to verify real-time interview and database storage.
This script simulates a real candidate interacting with the AI agent.
"""

import asyncio
import websockets
import json
import uuid
import sys
import os

# Add backend root to import path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))


async def test_websocket_interview():
    """Test WebSocket interview with real database storage."""
    print("🌐 WebSocket Interview Test")
    print("=" * 50)
    print("This test connects to the WebSocket and simulates a real interview.")
    print("Make sure your server is running: python -m uvicorn app.main:app --reload")
    print()
    
    # You'll need to create an interview first via API
    interview_id = input("Enter interview ID (or press Enter to create one): ").strip()
    
    if not interview_id:
        print("❌ Please create an interview first via API or use the test script.")
        print("   You can use the existing test_interview_ai_live.py script.")
        return
    
    # WebSocket URL
    ws_url = f"ws://localhost:8000/interviews/ws/{interview_id}"
    
    try:
        print(f"🔌 Connecting to: {ws_url}")
        
        async with websockets.connect(ws_url) as websocket:
            print("✅ Connected to WebSocket!")
            print()
            print("💬 You can now chat with the AI agent.")
            print("💡 Type your responses as if you're a candidate.")
            print("💡 Type 'quit' to exit.")
            print("=" * 50)
            
            # Listen for messages
            async def listen_for_messages():
                try:
                    async for message in websocket:
                        data = json.loads(message)
                        
                        if data.get("type") == "message":
                            print(f"\n🤖 AI: {data.get('message', '')}")
                            if data.get("stage"):
                                print(f"📍 Stage: {data['stage']}")
                        
                        elif data.get("type") == "interview_complete":
                            print(f"\n🎉 Interview Completed!")
                            print(f"🏆 Final Score: {data.get('final_score', 'N/A')}%")
                            print(f"💾 Evaluation Saved: {data.get('evaluation_saved', False)}")
                            
                            if data.get("summary"):
                                summary = data["summary"]
                                print(f"\n📊 Summary:")
                                print(f"   • Overall Score: {summary.get('overall_score', 'N/A')}%")
                                print(f"   • Breakdown: {summary.get('breakdown', {})}")
                                print(f"   • Reasoning: {summary.get('reasoning', [])}")
                            
                            print(f"\n✅ Interview data has been saved to database!")
                            break
                        
                        elif data.get("type") == "error":
                            print(f"\n❌ Error: {data.get('message', 'Unknown error')}")
                        
                        else:
                            print(f"\n📨 Received: {data}")
                
                except websockets.exceptions.ConnectionClosed:
                    print("\n🔌 WebSocket connection closed.")
                except Exception as e:
                    print(f"\n❌ Error receiving message: {e}")
            
            # Start listening for messages
            listen_task = asyncio.create_task(listen_for_messages())
            
            # Get user input
            try:
                while True:
                    user_input = input("\n👤 You: ").strip()
                    
                    if user_input.lower() in ['quit', 'exit', 'q']:
                        break
                    
                    if not user_input:
                        continue
                    
                    # Send message to WebSocket
                    message = {
                        "type": "candidate_message",
                        "message": user_input
                    }
                    
                    await websocket.send(json.dumps(message))
                    print("📤 Message sent!")
            
            except KeyboardInterrupt:
                print("\n👋 Interrupted by user.")
            
            finally:
                listen_task.cancel()
                try:
                    await listen_task
                except asyncio.CancelledError:
                    pass
    
    except websockets.exceptions.InvalidStatus as e:
        if "403" in str(e):
            print("❌ HTTP 403 Forbidden - Authentication required.")
            print("   The WebSocket endpoint requires authentication.")
            print("   You need to provide authentication headers or use a different approach.")
        else:
            print(f"❌ WebSocket connection failed: {e}")
            print("   Make sure the server is running: python -m uvicorn app.main:app --reload")
    
    except Exception as e:
        print(f"❌ Error: {e}")


async def create_test_interview():
    """Create a test interview via API."""
    print("📝 Creating Test Interview")
    print("=" * 50)
    
    import aiohttp
    
    # This would require actual API calls to create interview
    # For now, we'll show the structure
    print("To create an interview, you need to:")
    print("1. Create a vacancy via POST /vacancies/")
    print("2. Create a candidate via POST /candidates/")
    print("3. Create an interview via POST /interviews/")
    print()
    print("Or use the existing test scripts that create mock data.")


def show_websocket_testing_guide():
    """Show guide for WebSocket testing."""
    print("\n🌐 WebSocket Testing Guide")
    print("=" * 50)
    
    print("1. 🚀 Start the Server:")
    print("   cd /Users/danazhaksylyk/Downloads/smartbot/backend")
    print("   python -m uvicorn app.main:app --reload")
    print()
    
    print("2. 📝 Create an Interview:")
    print("   • Use the API endpoints to create vacancy, candidate, and interview")
    print("   • Or use existing test scripts")
    print()
    
    print("3. 🔌 Connect via WebSocket:")
    print("   • Use this script: python test_websocket_storage.py")
    print("   • Or use a WebSocket client like Postman")
    print()
    
    print("4. 💬 Chat with AI:")
    print("   • Type responses as a candidate")
    print("   • Watch the AI conduct the interview")
    print("   • See real-time database storage")
    print()
    
    print("5. 📊 Check Results:")
    print("   • Use API endpoints to retrieve stored data")
    print("   • Check database directly")
    print("   • Verify all data is saved correctly")
    print()


async def main():
    """Main function."""
    print("🎯 WebSocket Storage Test")
    print("=" * 60)
    print("This script tests real-time interview with database storage.")
    print()
    
    # Show testing guide
    show_websocket_testing_guide()
    
    # Ask user what they want to do
    print("What would you like to do?")
    print("1. Test WebSocket interview")
    print("2. Show testing guide only")
    print("3. Exit")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        await test_websocket_interview()
    elif choice == "2":
        print("\n✅ Testing guide displayed above.")
    else:
        print("👋 Goodbye!")


if __name__ == "__main__":
    asyncio.run(main())
