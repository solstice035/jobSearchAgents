"""
Job Search Agent module initialization.

This module provides the JobSearchAgent implementation that integrates
with the agent framework for automated job discovery and matching.
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

__all__ = [
    "JobSearchAgent",
    "JOB_SEARCH_TOPIC",
    "JOB_RESULTS_TOPIC",
    "JOB_MATCH_TOPIC",
    "SEARCH_REQUEST",
    "ENHANCED_SEARCH_REQUEST",
    "RESUME_MATCH_REQUEST",
]
