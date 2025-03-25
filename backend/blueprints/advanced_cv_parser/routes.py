"""
API routes for the Advanced CV Parser functionality.

This module defines the REST API endpoints for parsing CVs with advanced extraction
of structured data, including skills, experience, education, etc.
"""

from flask import Blueprint, request, jsonify
import io
import json

from services.advanced_cv_parser.advanced_cv_parser import AdvancedCVParser

# Initialize the blueprint
advanced_cv_parser_bp = Blueprint('advanced_cv_parser', __name__, url_prefix='/api/advanced-cv-parser')

# Create an instance of the Advanced CV Parser
parser = AdvancedCVParser()

@advanced_cv_parser_bp.route('/parse', methods=['POST'])
def parse_cv():
    """
    Parse a CV and extract structured data with high accuracy.
    
    Request body:
    - Form data with file field 'cv_file' containing the CV document
    - OR JSON with 'cv_text' field containing the CV text
    
    Returns:
    {
        "parsed_data": {Structured CV data},
        "status": "success"
    }
    """
    try:
        # Check if CV is uploaded as a file
        if 'cv_file' in request.files:
            file = request.files['cv_file']
            
            # Parse the document
            parsed_data = parser.parse_cv(file, file.filename)
        
        # Check if CV is provided as text
        elif request.json and 'cv_text' in request.json:
            # Create a file-like object from the text
            cv_text = request.json['cv_text']
            file_obj = io.BytesIO(cv_text.encode('utf-8'))
            
            # Parse the document
            parsed_data = parser.parse_cv(file_obj, "document.txt")
        
        else:
            return jsonify({
                "status": "error",
                "message": "No CV file or text provided"
            }), 400
        
        return jsonify({
            "parsed_data": parsed_data,
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
            "message": f"An error occurred during CV parsing: {str(e)}"
        }), 500

@advanced_cv_parser_bp.route('/analyze-for-career-coach', methods=['POST'])
def analyze_for_career_coach():
    """
    Parse a CV and extract structured data specifically formatted for the Career Coach.
    
    Request body:
    - Form data with file field 'cv_file' containing the CV document
    - OR JSON with 'cv_text' field containing the CV text
    - Include 'session_id' field to update an existing coaching session
    
    Returns:
    {
        "analysis": {Analysis results for Career Coach},
        "session_id": "session_id" (if provided),
        "status": "success"
    }
    """
    try:
        cv_text = None
        session_id = None
        
        # Check if CV is uploaded as a file
        if 'cv_file' in request.files:
            file = request.files['cv_file']
            
            # Parse the document
            parsed_data = parser.parse_cv(file, file.filename)
            
            # Get session ID from form data
            session_id = request.form.get('session_id')
        
        # Check if CV is provided as text
        elif request.json and 'cv_text' in request.json:
            # Create a file-like object from the text
            cv_text = request.json['cv_text']
            file_obj = io.BytesIO(cv_text.encode('utf-8'))
            
            # Parse the document
            parsed_data = parser.parse_cv(file_obj, "document.txt")
            
            # Get session ID from JSON data
            session_id = request.json.get('session_id')
        
        else:
            return jsonify({
                "status": "error",
                "message": "No CV file or text provided"
            }), 400
        
        # Format the parsed data for the Career Coach
        career_coach_analysis = {
            "personal_information": parsed_data["personal_information"],
            "skills": parsed_data["skills"],
            "work_experience": parsed_data["work_experience"],
            "education": parsed_data["education"],
            "analysis": {
                "strengths": parsed_data["skills"]["technical"][:5] + parsed_data["skills"]["soft"][:3],
                "improvement_areas": [],  # Will be determined by the Career Coach
                "industry_fit": _determine_industry_fit(parsed_data),
                "role_fit": _determine_role_fit(parsed_data)
            }
        }
        
        # If a session ID is provided, update the Career Coach session
        if session_id:
            from services.career_coach import CareerCoachAgent
            coach_agent = CareerCoachAgent()
            
            try:
                # Convert parsed data to text format for the career coach
                cv_text_for_coach = json.dumps(parsed_data, indent=2)
                
                # Update the coaching session
                coach_response = coach_agent.analyze_cv(session_id, cv_text_for_coach)
                
                return jsonify({
                    "analysis": coach_response["analysis"],
                    "session_id": session_id,
                    "status": "success"
                }), 200
            except ValueError as e:
                return jsonify({
                    "status": "error",
                    "message": str(e)
                }), 404
        
        # If no session ID, just return the analysis
        return jsonify({
            "analysis": career_coach_analysis,
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
            "message": f"An error occurred during CV analysis: {str(e)}"
        }), 500

def _determine_industry_fit(parsed_data):
    """Determine which industries the candidate might be a good fit for."""
    industries = []
    
    # Technical skill-based industry mapping
    industry_keywords = {
        "software development": ["python", "java", "javascript", "c#", "c++", "react", "angular", "vue", "node.js"],
        "data science": ["python", "r", "sql", "machine learning", "tensorflow", "pytorch", "pandas", "numpy"],
        "web development": ["html", "css", "javascript", "react", "angular", "vue", "node.js", "php"],
        "cloud computing": ["aws", "azure", "gcp", "docker", "kubernetes", "terraform"],
        "cybersecurity": ["security", "penetration testing", "ethical hacking", "encryption", "firewall"],
        "product management": ["product", "roadmap", "user stories", "agile", "scrum", "jira"],
        "ux/ui design": ["ux", "ui", "user experience", "design", "figma", "sketch", "adobe xd"],
        "marketing": ["marketing", "seo", "sem", "content marketing", "social media"],
        "sales": ["sales", "business development", "account management", "client relations"],
        "finance": ["finance", "accounting", "financial analysis", "bookkeeping", "excel"],
        "healthcare": ["healthcare", "medical", "clinical", "patient", "hospital"],
        "education": ["teaching", "curriculum", "education", "instructor", "training"]
    }
    
    # Check technical skills
    all_skills = parsed_data["skills"]["technical"] + [exp["position"] for exp in parsed_data["work_experience"] if exp.get("position")]
    all_skills_text = " ".join([str(skill).lower() for skill in all_skills])
    
    for industry, keywords in industry_keywords.items():
        for keyword in keywords:
            if keyword.lower() in all_skills_text:
                if industry not in industries:
                    industries.append(industry)
                break
    
    # Limit to top 3
    return industries[:3]

def _determine_role_fit(parsed_data):
    """Determine which roles the candidate might be a good fit for."""
    roles = []
    
    # Technical skill-based role mapping
    role_keywords = {
        "Software Engineer": ["software engineer", "developer", "programming", "coding", "python", "java", "javascript"],
        "Data Scientist": ["data scientist", "data analysis", "machine learning", "statistics", "python", "r"],
        "Data Engineer": ["data engineer", "etl", "data pipeline", "sql", "database"],
        "Frontend Developer": ["frontend", "react", "angular", "vue", "html", "css", "javascript"],
        "Backend Developer": ["backend", "api", "server", "node.js", "django", "flask", "spring"],
        "Full Stack Developer": ["full stack", "frontend", "backend", "web development"],
        "DevOps Engineer": ["devops", "ci/cd", "aws", "azure", "docker", "kubernetes"],
        "Product Manager": ["product manager", "product owner", "roadmap", "user stories", "agile"],
        "UX/UI Designer": ["ux", "ui", "user experience", "design", "figma", "sketch"],
        "QA Engineer": ["qa", "quality assurance", "testing", "test automation", "selenium"],
        "System Administrator": ["sysadmin", "system administrator", "linux", "unix", "windows server"],
        "Project Manager": ["project manager", "project management", "pmp", "scrum master"]
    }
    
    # Check work experience and skills
    experience_text = " ".join([exp.get("position", "") + " " + exp.get("description", "") 
                               for exp in parsed_data["work_experience"]]).lower()
    
    skills_text = " ".join(parsed_data["skills"]["technical"] + parsed_data["skills"]["soft"]).lower()
    combined_text = experience_text + " " + skills_text
    
    for role, keywords in role_keywords.items():
        for keyword in keywords:
            if keyword.lower() in combined_text:
                if role not in roles:
                    roles.append(role)
                break
    
    # Also check existing job titles in work experience
    for exp in parsed_data["work_experience"]:
        title = exp.get("position", "").lower()
        for role in role_keywords.keys():
            if role.lower() in title:
                if role not in roles:
                    roles.append(role)
    
    # Limit to top 3
    return roles[:3]
