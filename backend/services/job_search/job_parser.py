"""
Job posting parser for Perplexity API responses.

This module provides functionality to parse raw API responses and extract
structured job listing data.
"""

import re
from typing import Dict, Any, List, Optional
import logging


def parse_job_listings(api_response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Parse job listings from a Perplexity API response.
    
    Args:
        api_response: The raw API response
        
    Returns:
        A list of structured job listings
    """
    # Extract the content from the API response
    if "choices" not in api_response or not api_response["choices"]:
        logging.warning("No choices found in API response")
        return []
    
    content = api_response["choices"][0]["message"]["content"]
    if not content:
        logging.warning("Empty content in API response")
        return []
    
    # Split content into job listings
    # The approach depends on the structure of the response which can vary
    # Try different splitting patterns
    
    # Method 1: Look for numbered job listings (e.g., "1. Job Title")
    job_sections = re.split(r'\n\s*\d+[\.\)]\s+', content)
    
    # If there are at least 2 sections (the first is usually intro text)
    if len(job_sections) > 1:
        job_sections = job_sections[1:]  # Skip the intro text
    else:
        # Method 2: Look for job titles with company names
        job_sections = re.split(r'\n\s*(?=.*?(?:at|@|with|-).*?(?:Company|Inc|Ltd|LLC))', content)
        if len(job_sections) <= 1:
            # Method 3: Look for sections separated by double newlines
            job_sections = re.split(r'\n\s*\n\s*', content)
    
    # Process each job section
    parsed_jobs = []
    for job_section in job_sections:
        if not job_section.strip():
            continue
        
        job_data = parse_job_section(job_section)
        if job_data:
            parsed_jobs.append(job_data)
    
    return parsed_jobs


def parse_job_section(job_text: str) -> Optional[Dict[str, Any]]:
    """
    Parse a single job listing section.
    
    Args:
        job_text: Text describing a single job
        
    Returns:
        A structured representation of the job or None if parsing fails
    """
    if not job_text or len(job_text.strip()) < 10:
        return None
    
    # Initialize the job data
    job_data = {
        "title": None,
        "company": None,
        "location": None,
        "job_type": None,
        "salary": None,
        "description": None,
        "requirements": [],
        "benefits": [],
        "application_link": None,
        "full_text": job_text.strip()
    }
    
    # Extract job title and company
    title_company_match = re.search(
        r'^(.*?(?:Engineer|Developer|Designer|Manager|Director|Specialist|Analyst|Consultant|Assistant|Representative|Coordinator|Agent|Officer|Administrator|Lead|Head|Chief|Architect|Scientist|Advisor|Support|Operator|Technician|VP|Executive|President|COO|CEO|CTO|CFO))(?:\s+at|\s+with|\s*[-@])?\s+(.*?)(?:[\n\r]|$)', 
        job_text, 
        re.IGNORECASE
    )
    
    if title_company_match:
        job_data["title"] = title_company_match.group(1).strip()
        job_data["company"] = title_company_match.group(2).strip()
    else:
        # Try a more general pattern
        lines = job_text.strip().split('\n')
        if lines:
            # Assume first line might contain title/company
            first_line = lines[0].strip()
            
            # Look for common patterns
            if ':' in first_line:
                title_parts = first_line.split(':', 1)
                job_data["title"] = title_parts[0].strip()
                if len(title_parts) > 1:
                    job_data["company"] = title_parts[1].strip()
            elif '-' in first_line or '@' in first_line or 'at' in first_line.lower():
                for separator in [' - ', ' @ ', ' at ', '-', '@']:
                    if separator in first_line:
                        parts = first_line.split(separator, 1)
                        job_data["title"] = parts[0].strip()
                        if len(parts) > 1:
                            job_data["company"] = parts[1].strip()
                        break
            else:
                # Just use the first line as title
                job_data["title"] = first_line
    
    # Extract location
    location_match = re.search(
        r'(?:Location|Located in|located in|based in|remote in|in|from)\s*(?::|is|at)?\s*([A-Za-z\s,]+(?:Remote|Hybrid|On-site|On site|Onsite|Work from home|WFH)?)',
        job_text,
        re.IGNORECASE
    )
    if location_match:
        job_data["location"] = location_match.group(1).strip()
    else:
        # Look for location patterns
        location_patterns = [
            r'([A-Za-z\s]+,\s*[A-Z]{2})',  # City, State
            r'(Remote|Hybrid|On-site|On site|Onsite|Work from home|WFH)',  # Work arrangement
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, job_text, re.IGNORECASE)
            if match:
                job_data["location"] = match.group(1).strip()
                break
    
    # Extract job type
    job_type_match = re.search(
        r'(?:Job Type|Employment Type|Type|Position Type)(?:\s*:\s*|\s+is\s+|\s+)([A-Za-z\s\-]+(?:Full-time|Part-time|Contract|Temporary|Freelance|Permanent))',
        job_text,
        re.IGNORECASE
    )
    if job_type_match:
        job_data["job_type"] = job_type_match.group(1).strip()
    else:
        # Look for common job type terms
        job_type_patterns = [
            r'(Full-time|Full time|Fulltime)',
            r'(Part-time|Part time|Parttime)',
            r'(Contract|Contractor)',
            r'(Temporary|Temp)',
            r'(Freelance)',
            r'(Permanent|Perm)'
        ]
        
        for pattern in job_type_patterns:
            match = re.search(pattern, job_text, re.IGNORECASE)
            if match:
                job_data["job_type"] = match.group(1).strip()
                break
    
    # Extract salary information
    salary_match = re.search(
        r'(?:Salary|Compensation|Pay|Wage)(?:\s*:\s*|\s+is\s+|\s+)([A-Za-z0-9\s\-\$\,\.\€\£\¥]+(?:per|\/|\s+a\s+)(?:year|annum|month|hour|yr|mo|hr))',
        job_text,
        re.IGNORECASE
    )
    if salary_match:
        job_data["salary"] = salary_match.group(1).strip()
    else:
        # Look for currency symbols followed by numbers
        salary_patterns = [
            r'(\$\s*\d[\d\,\.]+\s*(?:-\s*\$\s*\d[\d\,\.]+)?(?:\s*(?:per|\/|\s+a\s+)(?:year|annum|month|hour|yr|mo|hr))?)',
            r'((?:USD|EUR|GBP|AUD|CAD)\s*\d[\d\,\.]+\s*(?:-\s*(?:USD|EUR|GBP|AUD|CAD)\s*\d[\d\,\.]+)?)',
            r'(\d[\d\,\.]+\s*(?:-\s*\d[\d\,\.]+)?\s*(?:USD|EUR|GBP|AUD|CAD|dollars|euros|pounds))'
        ]
        
        for pattern in salary_patterns:
            match = re.search(pattern, job_text, re.IGNORECASE)
            if match:
                job_data["salary"] = match.group(1).strip()
                break
    
    # Extract description
    description_match = re.search(
        r'(?:Description|About the job|Job Description|About the role|About this job|Summary)(?:\s*:\s*|\s*-\s*|\n)([^:]+?)(?:\n\s*(?:Requirements|Qualifications|Skills|Responsibilities|Benefits|About the company|Apply|Application|How to apply)|$)',
        job_text,
        re.IGNORECASE | re.DOTALL
    )
    if description_match:
        job_data["description"] = description_match.group(1).strip()
    
    # Extract requirements
    requirements_section = re.search(
        r'(?:Requirements|Qualifications|Skills|What you\'ll need)(?:\s*:\s*|\s*-\s*|\n)(.*?)(?:\n\s*(?:Benefits|About the company|Apply|Application|How to apply|Description|About the job)|$)',
        job_text,
        re.IGNORECASE | re.DOTALL
    )
    if requirements_section:
        requirements_text = requirements_section.group(1).strip()
        
        # Try to split into bullet points
        requirements = []
        
        # Check if there are bullet points
        bullet_items = re.findall(r'(?:^|\n)\s*(?:[\*\-•◦‣⁃▪▹►▻▸▹]|\d+[\.\)])\s*(.*?)(?=(?:\n\s*(?:[\*\-•◦‣⁃▪▹►▻▸▹]|\d+[\.\)]))|$)', requirements_text, re.DOTALL)
        
        if bullet_items:
            for item in bullet_items:
                if item.strip():
                    requirements.append(item.strip())
        else:
            # No bullet points, try to split by sentences or newlines
            for line in re.split(r'(?:\.|\n)+', requirements_text):
                if line.strip():
                    requirements.append(line.strip())
        
        job_data["requirements"] = requirements
    
    # Extract benefits
    benefits_section = re.search(
        r'(?:Benefits|Perks|What we offer|We offer)(?:\s*:\s*|\s*-\s*|\n)(.*?)(?:\n\s*(?:Apply|Application|How to apply|Requirements|Qualifications)|$)',
        job_text,
        re.IGNORECASE | re.DOTALL
    )
    if benefits_section:
        benefits_text = benefits_section.group(1).strip()
        
        # Try to split into bullet points
        benefits = []
        
        # Check if there are bullet points
        bullet_items = re.findall(r'(?:^|\n)\s*(?:[\*\-•◦‣⁃▪▹►▻▸▹]|\d+[\.\)])\s*(.*?)(?=(?:\n\s*(?:[\*\-•◦‣⁃▪▹►▻▸▹]|\d+[\.\)]))|$)', benefits_text, re.DOTALL)
        
        if bullet_items:
            for item in bullet_items:
                if item.strip():
                    benefits.append(item.strip())
        else:
            # No bullet points, try to split by sentences or newlines
            for line in re.split(r'(?:\.|\n)+', benefits_text):
                if line.strip():
                    benefits.append(line.strip())
        
        job_data["benefits"] = benefits
    
    # Extract application link
    link_match = re.search(
        r'(?:Apply|Application|Apply now|Apply at|Learn more|For more details|For more information|To apply)(?:\s*(?:at|:|\-)\s*)((?:https?:\/\/|www\.)[^\s\n]+)',
        job_text,
        re.IGNORECASE
    )
    if link_match:
        job_data["application_link"] = link_match.group(1).strip()
    else:
        # Look for URLs in the text
        url_match = re.search(r'((?:https?:\/\/|www\.)[^\s\n]+)', job_text)
        if url_match:
            job_data["application_link"] = url_match.group(1).strip()
    
    return job_data
