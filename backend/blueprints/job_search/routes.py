"""
API routes for the Job Search functionality.

This module defines the REST API endpoints for searching and matching job opportunities,
analyzing resume matches, managing job search preferences, and configuring job sources.
"""

from flask import Blueprint, request, jsonify

from services.job_search import JobSearchAgent
from services.document_parser import DocumentParser

# Initialize the blueprint
job_search_bp = Blueprint("job_search", __name__, url_prefix="/api/job-search")

# Create an instance of the Job Search Agent
job_agent = JobSearchAgent()


@job_search_bp.route("/search", methods=["POST"])
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
        "user_id": "Required if use_preferences is true",
        "source_name": "Optional specific job source to use",
        "search_strategy": "Optional strategy for source selection (primary, load_balance, all)"
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

        if not data or "keywords" not in data:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Keywords are required for job search",
                    }
                ),
                400,
            )

        # Extract search parameters
        keywords = data.get("keywords")
        location = data.get("location")
        recency = data.get("recency")
        experience_level = data.get("experience_level")
        remote = data.get("remote", False)
        use_preferences = data.get("use_preferences", False)
        user_id = data.get("user_id")
        source_name = data.get("source_name")
        search_strategy = data.get("search_strategy", "primary")

        # Validate parameters
        if recency and recency not in ["month", "week", "day", "hour"]:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Recency must be one of: month, week, day, hour",
                    }
                ),
                400,
            )

        if experience_level and experience_level not in ["entry", "mid", "senior"]:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Experience level must be one of: entry, mid, senior",
                    }
                ),
                400,
            )

        if search_strategy not in ["primary", "load_balance", "all"]:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Search strategy must be one of: primary, load_balance, all",
                    }
                ),
                400,
            )

        # If using preferences, user_id is required
        if use_preferences and not user_id:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "User ID is required when using preferences",
                    }
                ),
                400,
            )

        # Perform the search
        if use_preferences and user_id:
            search_results = job_agent.enhanced_job_search(
                user_id=user_id,
                keywords=keywords,
                location=location,
                recency=recency,
                experience_level=experience_level,
                remote=remote,
                source_name=source_name,
                search_strategy=search_strategy,
            )
        else:
            search_results = job_agent.search_jobs(
                keywords=keywords,
                location=location,
                recency=recency,
                experience_level=experience_level,
                remote=remote,
                source_name=source_name,
                search_strategy=search_strategy,
            )

        return (
            jsonify(
                {
                    "jobs": search_results["jobs"],
                    "metadata": search_results["metadata"],
                    "status": "success",
                }
            ),
            200,
        )

    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400

    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"An error occurred during job search: {str(e)}",
                }
            ),
            500,
        )


@job_search_bp.route("/match", methods=["POST"])
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
        if "resume_file" in request.files:
            file = request.files["resume_file"]

            # Parse the document
            parser = DocumentParser()
            resume_text = parser.parse_document(file, file.filename)

            # Get job description from form data
            job_description = request.form.get("job_description")

        # Check if resume and job description are provided as text
        elif request.json:
            data = request.json
            resume_text = data.get("resume_text")
            job_description = data.get("job_description")

        # Validate inputs
        if not resume_text:
            return (
                jsonify(
                    {"status": "error", "message": "Resume text or file is required"}
                ),
                400,
            )

        if not job_description:
            return (
                jsonify({"status": "error", "message": "Job description is required"}),
                400,
            )

        # Analyze the match
        match_result = job_agent.analyze_resume_match(job_description, resume_text)

        # Check for errors in the result
        if "error" in match_result:
            return jsonify({"status": "error", "message": match_result["error"]}), 500

        return (
            jsonify(
                {
                    "match_score": match_result["match_score"],
                    "analysis": match_result["analysis"],
                    "status": "success",
                }
            ),
            200,
        )

    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"An error occurred during resume match analysis: {str(e)}",
                }
            ),
            500,
        )


@job_search_bp.route("/preferences", methods=["POST"])
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

        if not data or "user_id" not in data or "preferences" not in data:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "User ID and preferences are required",
                    }
                ),
                400,
            )

        # Save the preferences
        result = job_agent.save_user_preferences(data["user_id"], data["preferences"])

        return jsonify(result), 200

    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"An error occurred while saving preferences: {str(e)}",
                }
            ),
            500,
        )


@job_search_bp.route("/preferences/<user_id>", methods=["GET"])
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

        return jsonify({"preferences": preferences, "status": "success"}), 200

    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"An error occurred while retrieving preferences: {str(e)}",
                }
            ),
            500,
        )


# Job Source Registry Management Routes


@job_search_bp.route("/sources", methods=["GET"])
def list_sources():
    """
    Get a list of all job sources with their information.

    Returns:
    {
        "sources": [list of source information],
        "status": "success"
    }
    """
    try:
        # Get all source information
        sources = job_agent.list_sources()

        return jsonify({"sources": sources, "status": "success"}), 200

    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"An error occurred while retrieving job sources: {str(e)}",
                }
            ),
            500,
        )


@job_search_bp.route("/sources/<source_name>", methods=["GET"])
def get_source_info(source_name):
    """
    Get information about a specific job source.

    Returns:
    {
        "source": {source information},
        "status": "success"
    }
    """
    try:
        # Get source information
        source_info = job_agent.get_source_info(source_name)

        if not source_info:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"Job source '{source_name}' not found",
                    }
                ),
                404,
            )

        return jsonify({"source": source_info, "status": "success"}), 200

    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"An error occurred while retrieving source information: {str(e)}",
                }
            ),
            500,
        )


@job_search_bp.route("/sources/<source_name>/enable", methods=["POST"])
def enable_source(source_name):
    """
    Enable a job source.

    Returns:
    {
        "status": "success",
        "message": "Job source enabled successfully"
    }
    """
    try:
        # Enable the source
        result = job_agent.enable_source(source_name)

        if result["status"] == "error":
            return jsonify(result), 404

        return jsonify(result), 200

    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"An error occurred while enabling the job source: {str(e)}",
                }
            ),
            500,
        )


@job_search_bp.route("/sources/<source_name>/disable", methods=["POST"])
def disable_source(source_name):
    """
    Disable a job source.

    Returns:
    {
        "status": "success",
        "message": "Job source disabled successfully"
    }
    """
    try:
        # Disable the source
        result = job_agent.disable_source(source_name)

        if result["status"] == "error":
            return jsonify(result), 404

        return jsonify(result), 200

    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"An error occurred while disabling the job source: {str(e)}",
                }
            ),
            500,
        )


@job_search_bp.route("/sources/<source_name>/priority", methods=["POST"])
def update_source_priority(source_name):
    """
    Update the priority of a job source.

    Request body:
    {
        "priority": priority value (higher = higher priority)
    }

    Returns:
    {
        "status": "success",
        "message": "Job source priority updated successfully"
    }
    """
    try:
        data = request.json

        if not data or "priority" not in data:
            return (
                jsonify({"status": "error", "message": "Priority value is required"}),
                400,
            )

        # Validate priority
        try:
            priority = int(data["priority"])
        except (ValueError, TypeError):
            return (
                jsonify({"status": "error", "message": "Priority must be an integer"}),
                400,
            )

        # Update the priority
        result = job_agent.update_source_priority(source_name, priority)

        if result["status"] == "error":
            return jsonify(result), 404

        return jsonify(result), 200

    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"An error occurred while updating source priority: {str(e)}",
                }
            ),
            500,
        )


@job_search_bp.route("/sources/<source_name>/weight", methods=["POST"])
def update_source_weight(source_name):
    """
    Update the weight of a job source for load balancing.

    Request body:
    {
        "weight": weight value (higher = more traffic)
    }

    Returns:
    {
        "status": "success",
        "message": "Job source weight updated successfully"
    }
    """
    try:
        data = request.json

        if not data or "weight" not in data:
            return (
                jsonify({"status": "error", "message": "Weight value is required"}),
                400,
            )

        # Validate weight
        try:
            weight = int(data["weight"])
            if weight < 1:
                return (
                    jsonify(
                        {"status": "error", "message": "Weight must be at least 1"}
                    ),
                    400,
                )
        except (ValueError, TypeError):
            return (
                jsonify({"status": "error", "message": "Weight must be an integer"}),
                400,
            )

        # Update the weight
        result = job_agent.update_source_weight(source_name, weight)

        if result["status"] == "error":
            return jsonify(result), 404

        return jsonify(result), 200

    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"An error occurred while updating source weight: {str(e)}",
                }
            ),
            500,
        )


@job_search_bp.route("/sources/<source_name>/config", methods=["POST"])
def update_source_config(source_name):
    """
    Update the configuration of a job source.

    Request body:
    {
        "config": {configuration updates}
    }

    Returns:
    {
        "status": "success",
        "message": "Job source configuration updated successfully"
    }
    """
    try:
        data = request.json

        if not data or "config" not in data:
            return (
                jsonify({"status": "error", "message": "Configuration is required"}),
                400,
            )

        # Validate config
        if not isinstance(data["config"], dict):
            return (
                jsonify(
                    {"status": "error", "message": "Configuration must be an object"}
                ),
                400,
            )

        # Update the configuration
        result = job_agent.update_source_config(source_name, data["config"])

        if result["status"] == "error":
            return jsonify(result), 404

        return jsonify(result), 200

    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"An error occurred while updating source configuration: {str(e)}",
                }
            ),
            500,
        )


@job_search_bp.route("/sources/config/save", methods=["POST"])
def save_registry_config():
    """
    Save the current registry configuration to a file.

    Request body:
    {
        "config_file": "Optional path to save the configuration"
    }

    Returns:
    {
        "status": "success",
        "message": "Registry configuration saved successfully"
    }
    """
    try:
        data = request.json or {}
        config_file = data.get("config_file")

        # Save the configuration
        result = job_agent.save_registry_config(config_file)

        return jsonify(result), 200 if result["status"] == "success" else 500

    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"An error occurred while saving registry configuration: {str(e)}",
                }
            ),
            500,
        )


@job_search_bp.route("/sources/config/load", methods=["POST"])
def load_registry_config():
    """
    Load registry configuration from a file.

    Request body:
    {
        "config_file": "Optional path to load the configuration from"
    }

    Returns:
    {
        "status": "success",
        "message": "Registry configuration loaded successfully"
    }
    """
    try:
        data = request.json or {}
        config_file = data.get("config_file")

        # Load the configuration
        result = job_agent.load_registry_config(config_file)

        # Get updated source information
        if result["status"] == "success":
            sources = job_agent.list_sources()
            result["sources"] = sources

        return jsonify(result), 200 if result["status"] == "success" else 500

    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"An error occurred while loading registry configuration: {str(e)}",
                }
            ),
            500,
        )
