"""
Base job source abstract class.

This module defines the abstract base class that all job sources must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Mapping


class JobSource(ABC):
    """
    Abstract base class for job data sources.
    
    All job sources must implement these methods to provide a consistent
    interface for searching and retrieving job data.
    """
    
    @property
    @abstractmethod
    def source_name(self) -> str:
        """
        Get the name of this job source.
        
        Returns:
            The name of the job source (e.g., "Perplexity", "LinkedIn")
        """
        pass
    
    @abstractmethod
    def search_jobs(
        self,
        keywords: str,
        location: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Search for jobs using the provided criteria.
        
        Args:
            keywords: Search terms for finding jobs
            location: Optional location for the job search
            filters: Optional filters to narrow the search (e.g., job type, experience level)
            params: Optional additional parameters specific to this source
            
        Returns:
            Raw search results from the source
        """
        pass
    
    @abstractmethod
    def parse_results(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse raw search results into a standardized format.
        
        Args:
            raw_data: Raw data returned from the search_jobs method
            
        Returns:
            List of parsed job listings
        """
        pass
    
    @abstractmethod
    def normalize_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize a single job listing to a standard schema.
        
        Args:
            job_data: Job data to normalize
            
        Returns:
            Normalized job data conforming to the standard schema
        """
        pass
    
    def get_standard_schema(self) -> Dict[str, Any]:
        """
        Get the standard job schema all sources should conform to.
        
        Returns:
            A dictionary with the standard schema fields
        """
        return {
            "source": self.source_name,
            "source_id": None,
            "title": None,
            "company": None,
            "location": None,
            "job_type": None,
            "salary": None,
            "description": None,
            "requirements": [],
            "benefits": [],
            "application_link": None,
            "date_posted": None,
            "full_text": None,
            "url": None,
            "raw_data": None
        }
