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
import shutil
from dotenv import load_dotenv
import pytest

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from .env file
load_dotenv()

from services.career_coach import CareerCoachAgent
from services.career_coach.conversation_flow import ConversationPhase


@pytest.fixture
def career_coach():
    """Fixture to create and cleanup CareerCoachAgent instance."""
    # Verify required environment variables
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY environment variable not set")

    agent = CareerCoachAgent()

    # Store the data directory for cleanup
    data_dir = agent.user_data_dir

    yield agent

    # Cleanup: remove test data directory if it exists
    if os.path.exists(data_dir):
        shutil.rmtree(data_dir)


def test_career_coach_basic_flow(career_coach):
    """Test the basic conversation flow of the Career Coach Agent."""
    # Generate a test user ID
    user_id = f"test_user_{uuid.uuid4().hex[:8]}"

    # Create a coaching session
    session_response = career_coach.create_session(user_id)
    assert "session_id" in session_response
    session_id = session_response["session_id"]

    # Simulate initial message
    response = career_coach.process_message(
        session_id,
        "Hi, I'm a software developer with 5 years of experience. I'm looking to advance my career and possibly move into a leadership role.",
    )
    assert response["current_phase"] == ConversationPhase.INITIAL.value
    assert isinstance(response["response"], str)
    assert len(response["response"]) > 0

    # Simulate follow-up message
    response = career_coach.process_message(
        session_id,
        "I've been working mostly with Python and JavaScript. I enjoy mentoring junior developers and solving complex problems.",
    )
    assert response["current_phase"] in [phase.value for phase in ConversationPhase]
    assert isinstance(response["response"], str)
    assert len(response["response"]) > 0

    # Get session summary
    summary = career_coach.get_session_summary(session_id)
    assert isinstance(summary, dict)
    assert "current_phase" in summary
    assert "collected_information" in summary
    assert isinstance(summary["conversation_length"], int)
    assert summary["conversation_length"] > 0


def test_career_coach_cv_analysis(career_coach):
    """Test the CV analysis functionality."""
    # Create a session
    user_id = f"test_user_{uuid.uuid4().hex[:8]}"
    session_response = career_coach.create_session(user_id)
    session_id = session_response["session_id"]

    # Sample CV text for testing
    cv_text = """
    John Doe
    Software Engineer
    
    Experience:
    - Senior Software Engineer at Tech Corp (2018-present)
      - Led team of 5 developers
      - Implemented microservices architecture
    
    Skills:
    - Python, JavaScript, Docker
    - Team leadership, Problem-solving
    """

    # Test CV analysis
    analysis = career_coach.analyze_cv(session_id, cv_text)
    assert "analysis" in analysis
    assert isinstance(analysis["analysis"], dict)

    # Verify the analysis contains expected fields
    cv_data = analysis["analysis"]
    assert "skills" in cv_data
    assert "work_experience" in cv_data
    assert "analysis" in cv_data


def test_career_coach_roadmap_generation(career_coach):
    """Test the roadmap generation functionality."""
    # Create a session
    user_id = f"test_user_{uuid.uuid4().hex[:8]}"
    session_response = career_coach.create_session(user_id)
    session_id = session_response["session_id"]

    # Progress through phases
    messages = [
        "I'm a software developer with 5 years of experience looking to move into leadership.",
        "My technical skills include Python, JavaScript, and Docker.",
        "I value work-life balance and opportunities for growth.",
        "I'm interested in the fintech industry.",
        "I'd like to become a technical lead in the next year.",
    ]

    # Process messages to advance phases
    for msg in messages:
        career_coach.process_message(session_id, msg)

    # Generate roadmap
    try:
        roadmap = career_coach.generate_roadmap(session_id)
        assert "roadmap" in roadmap
        assert isinstance(roadmap["roadmap"], dict)

        # Verify roadmap structure
        roadmap_data = roadmap["roadmap"]
        assert "short_term_goals" in roadmap_data
        assert "medium_term_goals" in roadmap_data
        assert "long_term_vision" in roadmap_data
    except ValueError as e:
        # If we haven't reached the roadmap phase, this is expected
        assert "Cannot generate roadmap before reaching the roadmap phase" in str(e)


def test_career_coach_error_handling(career_coach):
    """Test error handling in the Career Coach Agent."""
    # Test invalid session ID
    with pytest.raises(ValueError):
        career_coach.process_message("invalid_session_id", "Hello")

    # Test empty message
    session_response = career_coach.create_session("test_user")
    session_id = session_response["session_id"]
    response = career_coach.process_message(session_id, "")
    assert isinstance(response["response"], str)

    # Test missing session data
    assert career_coach.get_session_summary("nonexistent_session") == {
        "error": "Session not found"
    }


if __name__ == "__main__":
    pytest.main([__file__])
