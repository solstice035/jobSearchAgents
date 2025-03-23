#!/usr/bin/env python3
"""
Test script for the Career Coach Agent.

This script demonstrates the basic functionality of the Career Coach Agent
by simulating a conversation, CV analysis, and roadmap generation.
"""

import sys
import os
import json
import uuid
from dotenv import load_dotenv

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from .env file
load_dotenv()

from services.career_coach import CareerCoachAgent
from services.career_coach.conversation_flow import ConversationPhase

def test_career_coach_agent():
    """Test the Career Coach Agent by simulating key interactions."""
    try:
        # Initialize the agent
        print("Initializing Career Coach Agent...")
        agent = CareerCoachAgent()
        
        # Generate a test user ID
        user_id = f"test_user_{uuid.uuid4().hex[:8]}"
        print(f"Test User ID: {user_id}")
        
        # Create a coaching session
        print("\nCreating coaching session...")
        session_response = agent.create_session(user_id)
        session_id = session_response["session_id"]
        print(f"Session created with ID: {session_id}")
        
        # Simulate an initial message
        print("\nSimulating initial message...")
        response = agent.process_message(
            session_id,
            "Hi, I'm a software developer with 5 years of experience. I'm looking to advance my career and possibly move into a leadership role."
        )
        print(f"Current phase: {response['current_phase']}")
        print(f"Response: {response['response'][:200]}...")
        
        # Simulate another message
        print("\nSimulating follow-up message...")
        response = agent.process_message(
            session_id,
            "I've been working mostly with Python and JavaScript. I enjoy mentoring junior developers and solving complex problems."
        )
        print(f"Current phase: {response['current_phase']}")
        print(f"Response: {response['response'][:200]}...")
        
        # Get session summary
        print("\nGetting session summary...")
        summary = agent.get_session_summary(session_id)
        print(f"Session summary: {json.dumps(summary, indent=2)}")
        
        print("\nTest completed successfully!")
        return session_id
    
    except Exception as e:
        print(f"Error testing Career Coach Agent: {str(e)}")
        raise

if __name__ == "__main__":
    test_career_coach_agent()
