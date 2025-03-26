"""
Job Search Agents

This package contains agents related to job searching and career development.
"""

from .job_search_agent import (
    JobSearchAgent,
    JOB_SEARCH_TOPIC,
    JOB_RESULTS_TOPIC,
    JOB_MATCH_TOPIC,
    SEARCH_REQUEST,
    ENHANCED_SEARCH_REQUEST,
    RESUME_MATCH_REQUEST,
)
from .cv_parser_agent import CVParserAgent
from .career_coach_agent import CareerCoachAgent

__all__ = [
    "JobSearchAgent",
    "JOB_SEARCH_TOPIC",
    "JOB_RESULTS_TOPIC",
    "JOB_MATCH_TOPIC",
    "SEARCH_REQUEST",
    "ENHANCED_SEARCH_REQUEST",
    "RESUME_MATCH_REQUEST",
    "CVParserAgent",
    "CareerCoachAgent",
]
