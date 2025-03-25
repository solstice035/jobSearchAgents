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
from blueprints.advanced_cv_parser import advanced_cv_parser_bp


def create_app(testing=False, test_config=None):
    """Create and configure the Flask application.

    Args:
        testing (bool): Whether to create the app in testing mode
        test_config (dict): Test configuration to override default config

    Returns:
        Flask: The configured Flask application
    """
    app = Flask(__name__, instance_relative_config=True)

    # Default configuration
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev"),
        DATABASE=os.path.join(app.instance_path, "app.sqlite"),
    )

    if testing:
        # Test configuration
        app.config["TESTING"] = True
        if test_config is not None:
            app.config.update(test_config)
    else:
        # Load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Enable CORS
    CORS(app)

    # Register blueprints
    app.register_blueprint(career_coach_bp)
    app.register_blueprint(job_search_bp)
    app.register_blueprint(advanced_cv_parser_bp)

    @app.route("/api/health", methods=["GET"])
    def health_check():
        """Health check endpoint to verify that the API is running."""
        return jsonify(
            {
                "status": "healthy",
                "message": "Job Search Agent API is running",
                "version": "0.1.0",
            }
        )

    return app


# Create the application instance
app = create_app()

if __name__ == "__main__":
    # Set debug mode based on environment variable or default to True for development
    debug = os.getenv("FLASK_DEBUG", "True").lower() == "true"

    # Get port from environment variable or default to 5000
    port = int(os.getenv("PORT", 5000))

    # Run the application
    app.run(debug=debug, host="0.0.0.0", port=port)
