"""
Sample job source implementation.

This module provides a demonstration job source that returns mock job listings.
It's intended for testing and development purposes.
"""

import logging
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from .base_source import JobSource

class SampleJobSource(JobSource):
    """
    Sample job source implementation that returns mock job data.
    """
    
    def __init__(self):
        """Initialize the sample job source."""
        # List of sample job titles
        self.job_titles = [
            "Software Engineer", "Senior Developer", "Full Stack Engineer", 
            "Frontend Developer", "Backend Engineer", "DevOps Engineer",
            "Data Scientist", "Machine Learning Engineer", "UI/UX Designer",
            "Product Manager", "Project Manager", "QA Engineer",
            "Technical Writer", "Database Administrator", "Cloud Architect"
        ]
        
        # List of sample companies
        self.companies = [
            "TechCorp", "InnoSoft", "CodeMasters", "DataMinds", "CloudFlow",
            "DevHub", "PixelPerfect", "Algorithmix", "ByteWorks", "NexGen",
            "FutureTech", "WebSphere", "AppNexus", "CyberSys", "Quantum Computing"
        ]
        
        # List of sample locations
        self.locations = [
            "San Francisco, CA", "New York, NY", "Austin, TX", "Seattle, WA", 
            "Boston, MA", "Chicago, IL", "Denver, CO", "Los Angeles, CA",
            "Atlanta, GA", "Portland, OR", "Remote", "Hybrid - San Francisco",
            "Hybrid - New York", "Hybrid - Seattle", "Remote - US"
        ]
        
        # List of sample skills
        self.skills = [
            "Python", "JavaScript", "React", "TypeScript", "Node.js", "Django", "Flask",
            "AWS", "Docker", "Kubernetes", "SQL", "NoSQL", "MongoDB", "PostgreSQL",
            "Git", "CI/CD", "REST API", "GraphQL", "Java", "C#", "Go", "Rust",
            "Machine Learning", "TensorFlow", "PyTorch", "Data Analysis", "Linux",
            "Agile", "Scrum", "Team Leadership", "Communication", "Problem Solving"
        ]
        
        # List of sample job types
        self.job_types = [
            "Full-time", "Part-time", "Contract", "Freelance", 
            "Internship", "Temporary", "Permanent"
        ]
        
        # List of sample benefits
        self.benefits = [
            "Health insurance", "Dental insurance", "Vision insurance", 
            "401(k) matching", "Unlimited PTO", "Remote work options",
            "Flexible schedule", "Professional development budget", 
            "Gym membership", "Stock options", "Performance bonuses",
            "Company events", "Free lunch", "Mental health resources",
            "Paid parental leave", "Education reimbursement"
        ]
    
    @property
    def source_name(self) -> str:
        """
        Get the name of this job source.
        
        Returns:
            The name of the job source
        """
        return "Sample"
    
    def search_jobs(
        self,
        keywords: str,
        location: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate sample job listings matching the search criteria.
        
        Args:
            keywords: Search terms for finding jobs
            location: Optional location for the job search
            filters: Optional filters including:
                - recency: Time filter (month, week, day, hour)
                - experience_level: Job experience level (entry, mid, senior)
                - remote: Whether to search for remote jobs only
            params: Optional additional parameters
            
        Returns:
            Mock search results with sample job listings
        """
        try:
            # Parse parameters
            filters = filters or {}
            params = params or {}
            
            # Extract filter values
            remote = filters.get('remote', False)
            recency = filters.get('recency')
            experience_level = filters.get('experience_level')
            
            # Generate a random number of jobs (3-8) that match the criteria
            num_jobs = random.randint(3, 8)
            
            # Filter job titles based on keywords
            matching_titles = [
                title for title in self.job_titles 
                if any(kw.lower() in title.lower() for kw in keywords.split())
            ]
            
            # Use matching titles if found, otherwise use all titles
            job_titles = matching_titles if matching_titles else self.job_titles
            
            # Filter locations based on location parameter
            matching_locations = self.locations
            if location:
                matching_locations = [
                    loc for loc in self.locations
                    if location.lower() in loc.lower() or (
                        remote and ("Remote" in loc or "Hybrid" in loc)
                    )
                ]
            
            # If remote filter is applied, only include remote jobs
            if remote:
                matching_locations = [
                    loc for loc in matching_locations
                    if "Remote" in loc or "Hybrid" in loc
                ]
            
            # Build mock API response
            mock_response = {
                "choices": [
                    {
                        "message": {
                            "content": self._generate_job_listings(
                                num_jobs=num_jobs,
                                job_titles=job_titles,
                                locations=matching_locations,
                                keywords=keywords,
                                experience_level=experience_level,
                                recency=recency
                            )
                        }
                    }
                ]
            }
            
            return mock_response
            
        except Exception as e:
            logging.error(f"Error in sample job search: {str(e)}")
            # Return empty response on error
            return {
                "choices": [
                    {
                        "message": {
                            "content": "No job listings found."
                        }
                    }
                ]
            }
    
    def parse_results(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse raw search results into a list of job listings.
        
        Args:
            raw_data: Raw data returned from the search_jobs method
            
        Returns:
            List of parsed job listings
        """
        try:
            # Extract content from the mock API response
            if "choices" not in raw_data or not raw_data["choices"]:
                return []
            
            content = raw_data["choices"][0]["message"]["content"]
            if not content:
                return []
            
            # Split content into job sections
            job_sections = content.split("\n\n")
            
            # Process each job section
            parsed_jobs = []
            for section in job_sections:
                lines = section.strip().split("\n")
                if len(lines) < 2:
                    continue
                
                # Extract job data from the section
                job_data = {}
                
                # First line should have title and company
                title_company = lines[0].split(" at ", 1)
                if len(title_company) == 2:
                    job_data["title"] = title_company[0].strip()
                    job_data["company"] = title_company[1].strip()
                else:
                    # Fallback parsing
                    job_data["title"] = title_company[0].strip()
                    job_data["company"] = "Unknown Company"
                
                # Process remaining lines
                for line in lines[1:]:
                    if line.startswith("Location:"):
                        job_data["location"] = line.replace("Location:", "").strip()
                    elif line.startswith("Job Type:"):
                        job_data["job_type"] = line.replace("Job Type:", "").strip()
                    elif line.startswith("Salary:"):
                        job_data["salary"] = line.replace("Salary:", "").strip()
                    elif line.startswith("Posted:"):
                        job_data["date_posted"] = line.replace("Posted:", "").strip()
                    elif line.startswith("Requirements:"):
                        # Requirements could span multiple lines
                        req_start_idx = lines.index(line)
                        requirements = []
                        for req_line in lines[req_start_idx+1:]:
                            if req_line.startswith("-"):
                                requirements.append(req_line.replace("-", "").strip())
                            elif req_line.startswith("Benefits:"):
                                break
                        job_data["requirements"] = requirements
                    elif line.startswith("Benefits:"):
                        # Benefits could span multiple lines
                        ben_start_idx = lines.index(line)
                        benefits = []
                        for ben_line in lines[ben_start_idx+1:]:
                            if ben_line.startswith("-"):
                                benefits.append(ben_line.replace("-", "").strip())
                        job_data["benefits"] = benefits
                
                # Add full text
                job_data["full_text"] = section.strip()
                
                parsed_jobs.append(job_data)
            
            return parsed_jobs
            
        except Exception as e:
            logging.error(f"Error parsing sample job results: {str(e)}")
            return []
    
    def normalize_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize a single job listing to the standard schema.
        
        Args:
            job_data: Job data to normalize
            
        Returns:
            Normalized job data conforming to the standard schema
        """
        schema = self.get_standard_schema()
        
        # Map the parsed job data to the standard schema
        schema.update({
            "title": job_data.get("title"),
            "company": job_data.get("company"),
            "location": job_data.get("location"),
            "job_type": job_data.get("job_type"),
            "salary": job_data.get("salary"),
            "description": job_data.get("full_text", "").split("Requirements:")[0] if "Requirements:" in job_data.get("full_text", "") else None,
            "requirements": job_data.get("requirements", []),
            "benefits": job_data.get("benefits", []),
            "application_link": f"https://example.com/jobs/{hash(job_data.get('title', '') + job_data.get('company', ''))}",
            "full_text": job_data.get("full_text"),
            # Generate a source-specific ID based on content hash
            "source_id": f"sample_{hash(job_data.get('full_text', ''))}",
            # Use provided date or current date
            "date_posted": job_data.get("date_posted") or datetime.now().isoformat(),
            # Store raw data for debugging and future reference
            "raw_data": job_data
        })
        
        return schema
    
    def _generate_job_listings(
        self,
        num_jobs: int,
        job_titles: List[str],
        locations: List[str],
        keywords: str,
        experience_level: Optional[str] = None,
        recency: Optional[str] = None
    ) -> str:
        """
        Generate mock job listings.
        
        Args:
            num_jobs: Number of job listings to generate
            job_titles: List of job titles to select from
            locations: List of locations to select from
            keywords: Search keywords (used to tailor job content)
            experience_level: Optional experience level filter
            recency: Optional recency filter
            
        Returns:
            String with formatted job listings
        """
        job_listings = []
        
        # Handle experience level prefix
        level_prefix = ""
        if experience_level:
            if experience_level.lower() == "entry":
                level_prefix = "Junior "
            elif experience_level.lower() == "mid":
                level_prefix = ""  # No prefix for mid-level
            elif experience_level.lower() == "senior":
                level_prefix = "Senior "
        
        # Handle recency for posting dates
        max_days_ago = 30  # Default to last month
        if recency:
            if recency.lower() == "hour":
                max_days_ago = 0  # Today, shown as hours ago
            elif recency.lower() == "day":
                max_days_ago = 1
            elif recency.lower() == "week":
                max_days_ago = 7
            # month is the default 30 days
        
        for _ in range(num_jobs):
            # Generate a job title, potentially with level prefix
            job_title = random.choice(job_titles)
            if level_prefix and not job_title.startswith(level_prefix):
                job_title = level_prefix + job_title
            
            # Select company and location
            company = random.choice(self.companies)
            location = random.choice(locations)
            
            # Generate salary range
            min_salary = random.randint(70, 150) * 1000
            max_salary = min_salary + random.randint(10, 50) * 1000
            salary = f"${min_salary:,} - ${max_salary:,} per year"
            
            # Generate job type
            job_type = random.choice(self.job_types)
            
            # Generate posting date
            days_ago = random.randint(0, max_days_ago)
            if days_ago == 0:
                hours_ago = random.randint(1, 12)
                posting_date = f"{hours_ago} hours ago"
            else:
                posting_date = f"{days_ago} days ago"
            
            # Generate requirements
            num_requirements = random.randint(3, 6)
            # Ensure at least one keyword is in the requirements if possible
            requirements = []
            for kw in keywords.split():
                matching_skills = [s for s in self.skills if kw.lower() in s.lower()]
                if matching_skills:
                    requirements.append(random.choice(matching_skills))
            
            # Add more random skills to meet the requirement count
            while len(requirements) < num_requirements:
                skill = random.choice(self.skills)
                if skill not in requirements:
                    requirements.append(skill)
            
            # Randomize requirement order
            random.shuffle(requirements)
            
            # Generate benefits
            num_benefits = random.randint(3, 5)
            benefits = random.sample(self.benefits, num_benefits)
            
            # Create formatted job listing
            job_listing = f"{job_title} at {company}\n"
            job_listing += f"Location: {location}\n"
            job_listing += f"Job Type: {job_type}\n"
            job_listing += f"Salary: {salary}\n"
            job_listing += f"Posted: {posting_date}\n"
            job_listing += "Requirements:\n"
            for req in requirements:
                job_listing += f"- {req}\n"
            job_listing += "Benefits:\n"
            for benefit in benefits:
                job_listing += f"- {benefit}\n"
            
            job_listings.append(job_listing)
        
        # Join job listings with double newlines
        return "\n\n".join(job_listings)
