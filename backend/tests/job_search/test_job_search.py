"""
Test script for the Job Search Agent.

This script provides a simple way to test the job search functionality
without running the full Flask application.
"""

import os
import sys
import json
from dotenv import load_dotenv

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

# Load environment variables
load_dotenv()

from services.job_search import JobSearchAgent


def test_basic_search():
    """Test basic job search functionality."""
    print("Testing basic job search...")

    agent = JobSearchAgent()

    # List available sources
    sources = agent.list_sources()
    print(f"Available job sources: {', '.join(sources)}")

    # Search for software engineering jobs
    search_results = agent.search_jobs(
        keywords="software engineer",
        location="United States",
        recency="month",
        experience_level="mid",
    )

    # Print the number of jobs found
    print(f"Found {len(search_results['jobs'])} jobs")
    print(f"Source: {search_results['metadata']['source']}")

    # Print the first job as an example
    if search_results["jobs"]:
        first_job = search_results["jobs"][0]
        print("\nExample job:")
        print(f"Title: {first_job['title']}")
        print(f"Company: {first_job['company']}")
        print(f"Location: {first_job['location']}")
        print(f"Source ID: {first_job['source_id']}")
        if first_job["salary"]:
            print(f"Salary: {first_job['salary']}")
        if first_job["requirements"]:
            print("\nRequirements:")
            for req in first_job["requirements"][:3]:  # Print first 3 requirements
                print(f"- {req}")

    # Return the search results
    return search_results


def test_enhanced_search():
    """Test enhanced job search with user preferences."""
    print("\nTesting enhanced job search...")

    agent = JobSearchAgent()

    # Create some test preferences
    test_user_id = "test_user_123"
    test_preferences = {
        "technicalSkills": ["Python", "React", "AWS"],
        "softSkills": ["Communication", "Teamwork"],
        "careerGoals": "Seeking a senior software engineering role in a fintech company",
        "jobTypes": ["Full-time", "Remote"],
        "workValues": ["Work-life balance", "Innovation"],
    }

    # Save the test preferences
    agent.save_user_preferences(test_user_id, test_preferences)

    # Perform an enhanced search
    search_results = agent.enhanced_job_search(
        user_id=test_user_id, keywords="software engineer", location="United States"
    )

    # Print the number of jobs found
    print(f"Found {len(search_results['jobs'])} jobs")
    print(f"Source: {search_results['metadata']['source']}")

    # Print the enhanced search criteria
    print("\nEnhanced search criteria:")
    for key, value in search_results["metadata"]["enhanced_criteria"].items():
        print(f"{key}: {value}")

    # Return the search results
    return search_results


def test_resume_match():
    """Test resume matching functionality."""
    print("\nTesting resume match analysis...")

    agent = JobSearchAgent()

    # Example job description
    job_description = """
    Senior Software Engineer
    
    We are looking for a Senior Software Engineer to join our team. The ideal candidate has 5+ years of experience with Python, cloud services (AWS/GCP), and web development frameworks.
    
    Requirements:
    - 5+ years of software development experience
    - Strong knowledge of Python
    - Experience with AWS or GCP
    - Experience with web frameworks like Flask or Django
    - Bachelor's degree in Computer Science or related field
    
    Nice to have:
    - Experience with React
    - Knowledge of CI/CD pipelines
    - Experience with microservices architecture
    """

    # Example resume
    resume = """
    John Doe
    Software Engineer
    
    Experience:
    - Senior Developer at Tech Company (2020-Present)
      * Developed web applications using Python and Django
      * Deployed services on AWS
      * Implemented CI/CD pipelines
    
    - Software Engineer at Another Company (2018-2020)
      * Built RESTful APIs using Flask
      * Worked on front-end features using React
    
    Skills:
    - Languages: Python, JavaScript, SQL
    - Frameworks: Flask, Django, React
    - Cloud: AWS (EC2, S3, Lambda)
    - Tools: Git, Docker, Jenkins
    
    Education:
    Bachelor of Science in Computer Science, University of Technology (2018)
    """

    # Analyze the match
    match_result = agent.analyze_resume_match(job_description, resume)

    # Print the match score
    print(f"Match score: {match_result['match_score']}/100")

    # Print the analysis
    print("\nAnalysis excerpt:")
    analysis_excerpt = (
        match_result["analysis"][:300] + "..."
        if len(match_result["analysis"]) > 300
        else match_result["analysis"]
    )
    print(analysis_excerpt)

    # Return the match result
    return match_result


if __name__ == "__main__":
    try:
        # Run the tests
        basic_results = test_basic_search()
        enhanced_results = test_enhanced_search()
        match_results = test_resume_match()

        print("\nAll tests completed successfully!")
    except Exception as e:
        print(f"\nError during testing: {str(e)}")
