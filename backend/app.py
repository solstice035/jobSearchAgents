"""
Main application file for the Job Search Agent.

This file initializes the Flask application and registers all blueprints.
"""

from flask import Flask, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import blueprints
from blueprints.career_coach import career_coach_bp
from blueprints.job_search import job_search_bp

# Create the application
app = Flask(__name__)
CORS(app)

# Register blueprints
app.register_blueprint(career_coach_bp)
app.register_blueprint(job_search_bp)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint to verify that the API is running."""
    return jsonify({
        "status": "healthy", 
        "message": "Job Search Agent API is running",
        "version": "0.1.0"
    })

if __name__ == '__main__':
    # Set debug mode based on environment variable or default to True for development
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    # Get port from environment variable or default to 5000
    port = int(os.getenv('PORT', 5000))
    
    # Run the application
    app.run(debug=debug, host='0.0.0.0', port=port)
