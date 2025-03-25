from typing import Optional, Dict, Any, List
from backend.services.job_search.sources.base_source import BaseJobSource
from backend.services.job_search.sources.perplexity_source import PerplexityJobSource


class JobSearchService:
    """Service for handling job search operations."""

    def __init__(
        self, config_file: Optional[str] = None, source: Optional[BaseJobSource] = None
    ):
        """
        Initialize the job search service.

        Args:
            config_file: Optional path to configuration file
            source: Optional job source to use. If not provided, defaults to PerplexityJobSource
        """
        self.config_file = config_file
        self.source = source
        if not self.source:
            self.source = PerplexityJobSource()

    async def search_jobs(
        self, query: str, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for jobs using the configured source.

        Args:
            query: Search query string
            filters: Optional filters to apply

        Returns:
            List of job postings
        """
        return await self.source.search(query, filters)

    async def match_resume(
        self, resume_text: str, job_description: str
    ) -> Dict[str, Any]:
        """
        Match a resume against a job description.

        Args:
            resume_text: The resume text content
            job_description: The job description to match against

        Returns:
            Match results
        """
        return await self.source.match_resume(resume_text, job_description)
