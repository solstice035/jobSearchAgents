"""
API routes for the Job Search functionality.

This module defines the REST API endpoints for searching and matching job opportunities,
analyzing resume matches, and managing job search preferences.
"""

from flask import Blueprint, request, jsonify

from services.job_search import JobSearchAgent
from services.document_parser import DocumentParser

# Initialize the blueprint
job_search_bp = Blueprint('job_search', __name__, url_prefix='/api/job-search')

# Create an instance of the Job Search Agent
job_agent = JobSearchAgent()

@job_search_bp.route('/search', methods=['POST'])
def search_jobs():
    """
    Search for job opportunities using provided criteria.
    
    Request body:
    {
        "keywords": "Required search terms (e.g., job title, skills)",
        "location": "Optional location (city, state, country, or 'remote')",
        "recency": "Optional time filter (month, week, day, hour)",
        "experience_level": "Optional experience level (entry, mid, senior)",
        "remote": "Boolean indicating if only remote jobs should be returned",
        "use_preferences": "Boolean indicating if user preferences should be used",
        "user_id": "Required if use_preferences is true"
    }
    
    Returns:
    {
        "jobs": [list of job listings],
        "metadata": {search metadata},
        "status": "success"
    }
    """
    try:
        data = request.json
        
        if not data or 'keywords' not in data:
            return jsonify({
                "status": "error",
                "message": "Keywords are required for job search"
            }), 400
        
        # Extract search parameters
        keywords = data.get('keywords')
        location = data.get('location')
        recency = data.get('recency')
        experience_level = data.get('experience_level')
        remote = data.get('remote', False)
        use_preferences = data.get('use_preferences', False)
        user_id = data.get('user_id')
        
        # Validate parameters
        if recency and recency not in ["month", "week", "day", "hour"]:
            return jsonify({
                "status": "error",
                "message": "Recency must be one of: month, week, day, hour"
            }), 400
        
        if experience_level and experience_level not in ["entry", "mid", "senior"]:
            return jsonify({
                "status": "error",
                "message": "Experience level must be one of: entry, mid, senior"
            }), 400
        
        # If using preferences, user_id is required
        if use_preferences and not user_id:
            return jsonify({
                "status": "error",
                "message": "User ID is required when using preferences"
            }), 400
        
        # Perform the search
        if use_preferences and user_id:
            search_results = job_agent.enhanced_job_search(
                user_id=user_id,
                keywords=keywords,
                location=location,
                recency=recency,
                experience_level=experience_level,
                remote=remote
            )
        else:
            search_results = job_agent.search_jobs(
                keywords=keywords,
                location=location,
                recency=recency,
                experience_level=experience_level,
                remote=remote
            )
        
        return jsonify({
            "jobs": search_results["jobs"],
            "metadata": search_results["metadata"],
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
            "message": f"An error occurred during job search: {str(e)}"
        }), 500

@job_search_bp.route('/match', methods=['POST'])
def match_resume():
    """
    Analyze how well a resume matches a specific job description.
    
    Request body:
    - Form data with file field 'resume_file' containing the resume and 'job_description' field
    - OR JSON with 'resume_text' and 'job_description' fields
    
    Returns:
    {
        "match_score": match score from 0-100,
        "analysis": detailed analysis of the match,
        "status": "success"
    }
    """
    try:
        job_description = None
        resume_text = None
        
        # Check if resume is uploaded as a file
        if 'resume_file' in request.files:
            file = request.files['resume_file']
            
            # Parse the document
            parser = DocumentParser()
            resume_text = parser.parse_document(file, file.filename)
            
            # Get job description from form data
            job_description = request.form.get('job_description')
        
        # Check if resume and job description are provided as text
        elif request.json:
            data = request.json
            resume_text = data.get('resume_text')
            job_description = data.get('job_description')
        
        # Validate inputs
        if not resume_text:
            return jsonify({
                "status": "error",
                "message": "Resume text or file is required"
            }), 400
        
        if not job_description:
            return jsonify({
                "status": "error",
                "message": "Job description is required"
            }), 400
        
        # Analyze the match
        match_result = job_agent.analyze_resume_match(job_description, resume_text)
        
        # Check for errors in the result
        if 'error' in match_result:
            return jsonify({
                "status": "error",
                "message": match_result['error']
            }), 500
        
        return jsonify({
            "match_score": match_result["match_score"],
            "analysis": match_result["analysis"],
            "status": "success"
        }), 200
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"An error occurred during resume match analysis: {str(e)}"
        }), 500

@job_search_bp.route('/preferences', methods=['POST'])
def save_preferences():
    """
    Save job search preferences for a user.
    
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
        result = job_agent.save_user_preferences(data['user_id'], data['preferences'])
        
        return jsonify(result), 200
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"An error occurred while saving preferences: {str(e)}"
        }), 500

@job_search_bp.route('/preferences/<user_id>', methods=['GET'])
def get_preferences(user_id):
    """
    Get job search preferences for a user.
    
    Returns:
    {
        "preferences": {Preference data},
        "status": "success"
    }
    """
    try:
        # Get the preferences
        preferences = job_agent.get_user_preferences(user_id)
        
        return jsonify({
            "preferences": preferences,
            "status": "success"
        }), 200
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"An error occurred while retrieving preferences: {str(e)}"
        }), 500
