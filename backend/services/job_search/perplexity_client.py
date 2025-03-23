"""
Perplexity API client for job searching.

This module handles communication with the Perplexity API, providing
functions for searching jobs and handling the API responses.
"""

import os
import requests
from typing import Dict, Any, Optional, List, Union
import logging

class PerplexityClient:
    """Client for interacting with the Perplexity API."""
    
    BASE_URL = "https://api.perplexity.ai"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Perplexity API client.
        
        Args:
            api_key: The API key for Perplexity. If not provided, it will be read from 
                    the PERPLEXITY_API_KEY environment variable.
        """
        self.api_key = api_key or os.getenv("PERPLEXITY_API_KEY")
        if not self.api_key:
            raise ValueError("Perplexity API key is required. Set the PERPLEXITY_API_KEY environment variable.")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def search(self, query: str, search_recency_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform a search using the Perplexity API.
        
        Args:
            query: The search query string
            search_recency_filter: Optional time filter for results (month, week, day, hour)
            
        Returns:
            The JSON response from the API
            
        Raises:
            requests.RequestException: If the request to the API fails
        """
        endpoint = f"{self.BASE_URL}/chat/completions"
        
        # Construct the search parameters
        request_data = {
            "model": "sonar-pro",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful job search assistant that provides detailed information about job listings."
                },
                {
                    "role": "user",
                    "content": query
                }
            ]
        }
        
        # Add search recency filter if provided
        if search_recency_filter:
            if search_recency_filter in ["month", "week", "day", "hour"]:
                search_params = {"search": {"recency_filter": search_recency_filter}}
                request_data["messages"][0]["content"] += f" Focus on jobs posted within the last {search_recency_filter}."
            else:
                logging.warning(f"Invalid search_recency_filter: {search_recency_filter}. Accepted values are: month, week, day, hour.")
        
        try:
            response = requests.post(endpoint, headers=self.headers, json=request_data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Perplexity API request failed: {str(e)}")
            raise

    def search_jobs(
        self, 
        keywords: str, 
        location: Optional[str] = None, 
        recency: Optional[str] = None, 
        experience_level: Optional[str] = None,
        remote: bool = False
    ) -> Dict[str, Any]:
        """
        Search for job opportunities with specific parameters.
        
        Args:
            keywords: Job title, skills, or other keywords
            location: City, state, country, or "remote"
            recency: Time filter (month, week, day, hour)
            experience_level: Job experience level (entry, mid, senior)
            remote: Whether to search for remote jobs only
            
        Returns:
            Processed job search results
        """
        # Construct a well-formatted job search query
        query_parts = [f"job openings for {keywords}"]
        
        if location:
            query_parts.append(f"in {location}")
        
        if remote:
            query_parts.append("remote work only")
        
        if experience_level:
            query_parts.append(f"{experience_level} level")
        
        # Add instructions to structure the response
        query_parts.append("Provide a list of at least 5 relevant job postings with company name, job title, location, " 
                          "key requirements, and application link if available. Format the jobs as a numbered list with clear sections.")
        
        query = " ".join(query_parts)
        
        # Perform the search
        search_result = self.search(query, recency)
        return search_result
