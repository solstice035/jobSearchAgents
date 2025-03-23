"""
Job Search Agent implementation.

This class provides functionality for discovering, filtering, and ranking job
opportunities based on user preferences and profiles.
"""

import json
import os
import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import uuid

# Import the job source implementations
from .sources import JobSource, PerplexityJobSource


class JobSearchAgent:
    """
    Agent for automated job discovery and matching.
    
    This agent handles searching for job opportunities across sources,
    filtering them based on user preferences, and presenting them in a 
    structured format.
    """
    
    def __init__(self):
        """Initialize the Job Search Agent."""
        # Initialize job sources
        self.sources = {
            "perplexity": PerplexityJobSource()
        }
        
        # Set the primary source (can be configurable in the future)
        self.primary_source = self.sources["perplexity"]
        
        # Setup preferences directory
        self.preferences_dir = os.path.expanduser(os.getenv("USER_DATA_DIR", "~/.jobSearchAgent"))
        os.makedirs(self.preferences_dir, exist_ok=True)

    def search_jobs(
        self, 
        keywords: str, 
        location: Optional[str] = None, 
        recency: Optional[str] = None,
        experience_level: Optional[str] = None,
        remote: bool = False,
        source_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search for job opportunities based on specific criteria.
        
        Args:
            keywords: Job title, skills, or other keywords
            location: City, state, country, or "remote"
            recency: Time filter (month, week, day, hour)
            experience_level: Job experience level (entry, mid, senior)
            remote: Whether to search for remote jobs only
            source_name: Optional name of the specific job source to use
            
        Returns:
            Structured job search results with metadata
        """
        # Validate parameters
        if not keywords or not keywords.strip():
            raise ValueError("Keywords are required for job search")
        
        if recency and recency not in ["month", "week", "day", "hour"]:
            raise ValueError("Recency must be one of: month, week, day, hour")
        
        if experience_level and experience_level not in ["entry", "mid", "senior"]:
            raise ValueError("Experience level must be one of: entry, mid, senior")
        
        # Select the job source to use
        job_source = self._get_job_source(source_name)
        
        # Create filters dictionary
        filters = {
            "recency": recency,
            "experience_level": experience_level,
            "remote": remote
        }
        
        # Perform the search
        raw_results = job_source.search_jobs(keywords, location, filters)
        
        # Parse and normalize the results
        parsed_jobs = job_source.parse_results(raw_results)
        normalized_jobs = [job_source.normalize_job(job) for job in parsed_jobs]
        
        # Return structured results with metadata
        return {
            "jobs": normalized_jobs,
            "metadata": {
                "source": job_source.source_name,
                "search_criteria": {
                    "keywords": keywords,
                    "location": location,
                    "recency": recency,
                    "experience_level": experience_level,
                    "remote": remote
                },
                "timestamp": datetime.now().isoformat(),
                "search_id": str(uuid.uuid4())
            }
        }
    
    def enhanced_job_search(
        self, 
        user_id: str, 
        keywords: str,
        location: Optional[str] = None, 
        recency: Optional[str] = None,
        experience_level: Optional[str] = None,
        remote: bool = False,
        source_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform a job search enhanced with user preferences.
        
        Args:
            user_id: Unique identifier for the user
            keywords: Basic search keywords
            location: Job location
            recency: Time filter
            experience_level: Job experience level
            remote: Whether to search for remote jobs only
            source_name: Optional name of the specific job source to use
            
        Returns:
            Enhanced job search results
        """
        # Get user preferences
        preferences = self.get_user_preferences(user_id)
        
        if not preferences:
            # If no preferences are found, fall back to basic search
            return self.search_jobs(
                keywords=keywords,
                location=location,
                recency=recency,
                experience_level=experience_level,
                remote=remote,
                source_name=source_name
            )
        
        # Enhance search keywords with user skills and preferences
        enhanced_keywords = keywords
        
        # Add technical skills if available
        if "technicalSkills" in preferences and preferences["technicalSkills"]:
            # Take the most relevant skills (up to 3) to avoid query overload
            relevant_skills = [skill for skill in preferences["technicalSkills"] 
                              if skill.lower() not in keywords.lower()][:3]
            if relevant_skills:
                enhanced_keywords += f" with skills in {', '.join(relevant_skills)}"
        
        # Use career goals to enhance the search if available
        if "careerGoals" in preferences and preferences["careerGoals"]:
            # Extract key terms from career goals
            goal_terms = self._extract_key_terms(preferences["careerGoals"])
            if goal_terms:
                # Add up to 2 goal terms that aren't already in the keywords
                new_terms = [term for term in goal_terms 
                            if term.lower() not in enhanced_keywords.lower()][:2]
                if new_terms:
                    enhanced_keywords += f" related to {' '.join(new_terms)}"
        
        # Use job type preference if available
        preferred_job_type = None
        if "jobTypes" in preferences and preferences["jobTypes"]:
            # Check if remote is preferred
            if "Remote" in preferences["jobTypes"] and not remote:
                remote = True
            
            # Extract non-remote job types for the query
            job_types = [jt for jt in preferences["jobTypes"] if jt.lower() != "remote"]
            if job_types and not experience_level:
                # Use the first job type as experience level if not provided
                if any(jt.lower() in ["full-time", "part-time", "contract", "freelance"] for jt in job_types):
                    preferred_job_type = next((jt for jt in job_types 
                                            if jt.lower() in ["full-time", "part-time", "contract", "freelance"]), None)
        
        # Select the job source to use
        job_source = self._get_job_source(source_name)
        
        # Create filters dictionary
        filters = {
            "recency": recency,
            "experience_level": experience_level or preferred_job_type,
            "remote": remote
        }
        
        # Perform the enhanced search
        raw_results = job_source.search_jobs(enhanced_keywords, location, filters)
        
        # Parse and normalize the results
        parsed_jobs = job_source.parse_results(raw_results)
        normalized_jobs = [job_source.normalize_job(job) for job in parsed_jobs]
        
        # Return the enhanced results with original and enhanced metadata
        return {
            "jobs": normalized_jobs,
            "metadata": {
                "source": job_source.source_name,
                "original_criteria": {
                    "keywords": keywords,
                    "location": location,
                    "recency": recency,
                    "experience_level": experience_level,
                    "remote": remote
                },
                "enhanced_criteria": {
                    "keywords": enhanced_keywords,
                    "location": location,
                    "recency": recency,
                    "experience_level": experience_level or preferred_job_type,
                    "remote": remote
                },
                "preferences_used": True,
                "timestamp": datetime.now().isoformat(),
                "search_id": str(uuid.uuid4())
            }
        }

    def analyze_resume_match(self, job_description: str, resume_text: str) -> Dict[str, Any]:
        """
        Analyze how well a resume matches a job description.
        
        Args:
            job_description: The job description text
            resume_text: The resume text to compare
            
        Returns:
            Analysis of the match including score and recommendations
        """
        # Select the job source to use (use primary source for resume matching)
        job_source = self.primary_source
        
        # Prepare the query for the API
        query = (
            f"Analyze how well the following resume matches the job description. "
            f"Include a match score from 0-100, list matching skills, identify missing skills, "
            f"and provide recommendations for improving the resume for this job.\n\n"
            f"JOB DESCRIPTION:\n{job_description}\n\n"
            f"RESUME:\n{resume_text}"
        )
        
        # Use the source-specific implementation to get the analysis
        params = {"model": "sonar-pro"}  # For Perplexity
        raw_result = job_source.search_jobs(query, params=params)
        
        # Extract the response content
        if isinstance(raw_result, dict) and "choices" in raw_result and raw_result["choices"]:
            analysis_text = raw_result["choices"][0]["message"]["content"]
            
            # Extract the match score using regex
            match_score = 0
            score_match = re.search(r'(?:match score|score|rating|match)(?:[:\s]+)(\d{1,3})', 
                                  analysis_text, re.IGNORECASE)
            if score_match:
                try:
                    match_score = int(score_match.group(1))
                    # Ensure score is in range 0-100
                    match_score = max(0, min(100, match_score))
                except (ValueError, IndexError):
                    pass
            
            # Return structured analysis
            return {
                "match_score": match_score,
                "analysis": analysis_text,
                "timestamp": datetime.now().isoformat(),
                "analysis_id": str(uuid.uuid4())
            }
        
        # Handle case where the API response doesn't contain expected data
        return {
            "error": "Could not generate resume match analysis",
            "timestamp": datetime.now().isoformat()
        }
    
    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """
        Get user preferences from storage.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            User preference data or empty dict if not found
        """
        preferences_file = os.path.join(self.preferences_dir, "preferences.json")
        
        if not os.path.exists(preferences_file):
            return {}
        
        try:
            with open(preferences_file, 'r') as f:
                all_preferences = json.load(f)
                return all_preferences.get(user_id, {})
        except (json.JSONDecodeError, IOError) as e:
            logging.error(f"Error reading preferences file: {str(e)}")
            return {}
    
    def save_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save user preferences to storage.
        
        Args:
            user_id: Unique identifier for the user
            preferences: Preference data to save
            
        Returns:
            Success status message
        """
        preferences_file = os.path.join(self.preferences_dir, "preferences.json")
        
        # Load existing preferences
        all_preferences = {}
        if os.path.exists(preferences_file):
            try:
                with open(preferences_file, 'r') as f:
                    all_preferences = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logging.error(f"Error reading preferences file: {str(e)}")
        
        # Update with new preferences
        all_preferences[user_id] = preferences
        
        # Save updated preferences
        try:
            with open(preferences_file, 'w') as f:
                json.dump(all_preferences, f, indent=2)
            return {
                "status": "success",
                "message": "Preferences saved successfully"
            }
        except IOError as e:
            logging.error(f"Error saving preferences file: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to save preferences: {str(e)}"
            }
    
    def _get_job_source(self, source_name: Optional[str] = None) -> JobSource:
        """
        Get the job source to use for a search.
        
        Args:
            source_name: Optional name of the specific job source to use
            
        Returns:
            The selected job source
            
        Raises:
            ValueError: If the specified source name is not found
        """
        if not source_name:
            return self.primary_source
        
        if source_name.lower() in self.sources:
            return self.sources[source_name.lower()]
        
        raise ValueError(f"Job source '{source_name}' not found. Available sources: {', '.join(self.sources.keys())}")
    
    def _extract_key_terms(self, text: str) -> List[str]:
        """
        Extract key terms from a text.
        
        Args:
            text: The text to extract terms from
            
        Returns:
            List of extracted key terms
        """
        # Simple extraction based on common job-related terms
        # A more sophisticated approach could use NLP techniques
        job_related_terms = [
            "software", "developer", "engineer", "manager", "director",
            "data", "science", "analyst", "researcher", "product",
            "marketing", "sales", "finance", "accounting", "hr",
            "human resources", "operations", "customer", "service",
            "support", "design", "frontend", "backend", "full stack",
            "mobile", "web", "cloud", "devops", "machine learning", "ai"
        ]
        
        # Extract terms that appear in the text
        found_terms = []
        for term in job_related_terms:
            if term.lower() in text.lower():
                found_terms.append(term)
        
        return found_terms
    
    def list_sources(self) -> List[str]:
        """
        Get a list of available job sources.
        
        Returns:
            List of job source names
        """
        return list(self.sources.keys())
