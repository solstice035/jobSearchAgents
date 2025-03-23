"""
API routes for the Career Coach functionality.

This module defines the REST API endpoints for interacting with the Career Coach Agent,
including session management, conversation, CV analysis, and roadmap generation.
"""

import json
from flask import Blueprint, request, jsonify
import uuid

from services.career_coach import CareerCoachAgent
from services.document_parser import DocumentParser

# Initialize the blueprint
career_coach_bp = Blueprint('career_coach', __name__, url_prefix='/api/career-coach')

# Create an instance of the Career Coach Agent
coach_agent = CareerCoachAgent()

@career_coach_bp.route('/sessions', methods=['POST'])
def create_session():
    """
    Create a new coaching session.
    
    Request body:
    {
        "user_id": "unique_user_identifier" (optional, will generate if not provided)
    }
    
    Returns:
    {
        "session_id": "unique_session_identifier",
        "status": "success",
        "message": "Session created successfully"
    }
    """
    try:
        data = request.json or {}
        
        # Generate user_id if not provided
        user_id = data.get('user_id', f"user_{uuid.uuid4().hex[:8]}")
        
        # Create the session
        session_response = coach_agent.create_session(user_id)
        
        return jsonify({
            "session_id": session_response["session_id"],
            "status": "success",
            "message": "Session created successfully"
        }), 201
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@career_coach_bp.route('/sessions/<session_id>/messages', methods=['POST'])
def send_message(session_id):
    """
    Send a message to the Career Coach Agent.
    
    Request body:
    {
        "message": "User's message text"
    }
    
    Returns:
    {
        "response": "Agent's response text",
        "current_phase": "conversation_phase",
        "session_id": "session_id"
    }
    """
    try:
        data = request.json
        
        if not data or 'message' not in data:
            return jsonify({
                "status": "error",
                "message": "Message is required"
            }), 400
        
        # Process the message
        response = coach_agent.process_message(session_id, data['message'])
        
        return jsonify({
            "response": response["response"],
            "current_phase": response["current_phase"],
            "session_id": response["session_id"],
            "status": "success"
        }), 200
    
    except ValueError as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 404
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@career_coach_bp.route('/sessions/<session_id>/cv', methods=['POST'])
def analyze_cv(session_id):
    """
    Analyze a CV and integrate insights into the coaching session.
    
    Request body:
    - Form data with file field 'cv_file' containing the CV document
    - OR JSON with 'cv_text' field containing the CV text
    
    Returns:
    {
        "analysis": {CV analysis results},
        "session_id": "session_id",
        "status": "success"
    }
    """
    try:
        # Check if CV is uploaded as a file
        if 'cv_file' in request.files:
            file = request.files['cv_file']
            
            # Parse the document
            parser = DocumentParser()
            cv_text = parser.parse_document(file, file.filename)
        
        # Check if CV is provided as text
        elif request.json and 'cv_text' in request.json:
            cv_text = request.json['cv_text']
        
        else:
            return jsonify({
                "status": "error",
                "message": "No CV file or text provided"
            }), 400
        
        # Analyze the CV
        analysis_response = coach_agent.analyze_cv(session_id, cv_text)
        
        return jsonify({
            "analysis": analysis_response["analysis"],
            "session_id": analysis_response["session_id"],
            "status": "success"
        }), 200
    
    except ValueError as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 404
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@career_coach_bp.route('/sessions/<session_id>/roadmap', methods=['GET'])
def generate_roadmap(session_id):
    """
    Generate a personalized career roadmap based on the coaching session.
    
    Returns:
    {
        "roadmap": {Roadmap data},
        "session_id": "session_id",
        "status": "success"
    }
    """
    try:
        # Generate the roadmap
        roadmap_response = coach_agent.generate_roadmap(session_id)
        
        return jsonify({
            "roadmap": roadmap_response["roadmap"],
            "session_id": roadmap_response["session_id"],
            "status": "success"
        }), 200
    
    except ValueError as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@career_coach_bp.route('/sessions/<session_id>', methods=['GET'])
def get_session_summary(session_id):
    """
    Get a summary of the current coaching session.
    
    Returns:
    {
        "summary": {Session summary data},
        "status": "success"
    }
    """
    try:
        # Get the session summary
        summary = coach_agent.get_session_summary(session_id)
        
        if "error" in summary:
            return jsonify({
                "status": "error",
                "message": summary["error"]
            }), 404
        
        return jsonify({
            "summary": summary,
            "status": "success"
        }), 200
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@career_coach_bp.route('/preferences', methods=['POST'])
def save_preferences():
    """
    Save user preferences.
    
    Request body:
    {
        "user_id": "unique_user_identifier",
        "preferences": {Preference data}
    }
    
    Returns:
    {
        "status": "success",
        "message": "Preferences saved successfully"
    }
    """
    try:
        data = request.json
        
        if not data or 'user_id' not in data or 'preferences' not in data:
            return jsonify({
                "status": "error",
                "message": "User ID and preferences are required"
            }), 400
        
        # Save the preferences
        result = coach_agent.save_user_preferences(data['user_id'], data['preferences'])
        
        return jsonify(result), 200
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
