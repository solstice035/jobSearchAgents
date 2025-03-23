"""
Tests for the integration of the JobSearchAgent with the JobSourceRegistry.

These tests verify that the JobSearchAgent correctly uses the registry
for job search operations, including search strategies and source selection.
"""

import os
import sys
import json
import unittest
from unittest.mock import MagicMock, patch
import tempfile
from typing import Dict, Any, List, Optional

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from services.job_search import JobSearchAgent
from services.job_search.sources import JobSource, JobSourceRegistry

class TestJobSource(JobSource):
    """A test job source implementation."""
    
    def __init__(self, name: str = "test"):
        self._name = name
        self.search_count = 0
        self.search_args = []
    
    @property
    def source_name(self) -> str:
        """Get the name of this job source."""
        return self._name
    
    def search_jobs(
        self,
        keywords: str,
        location: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Mock implementation of search_jobs."""
        self.search_count += 1
        self.search_args.append({
            "keywords": keywords,
            "location": location,
            "filters": filters,
            "params": params
        })
        
        return {
            "choices": [
                {
                    "message": {
                        "content": f"Job listing for {keywords} in {location or 'Any Location'} from {self.source_name}"
                    }
                }
            ]
        }
    
    def parse_results(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Mock implementation of parse_results."""
        # Extract content from the response
        content = raw_data["choices"][0]["message"]["content"]
        parts = content.split(" from ")
        source_name = parts[1] if len(parts) > 1 else "unknown"
        
        return [{"title": content, "source": source_name}]
    
    def normalize_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock implementation of normalize_job."""
        result = self.get_standard_schema()
        result.update({
            "title": job_data.get("title", ""),
            "source": job_data.get("source", ""),
            "source_id": f"{self.source_name}_123"
        })
        return result

class JobSearchAgentIntegrationTests(unittest.TestCase):
    """Tests for JobSearchAgent integration with JobSourceRegistry."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for preferences
        self.temp_dir = tempfile.mkdtemp()
        
        # Set up environment variable for user data directory
        self.original_user_data_dir = os.environ.get("USER_DATA_DIR")
        os.environ["USER_DATA_DIR"] = self.temp_dir
        
        # Create test sources
        self.source1 = TestJobSource("source1")
        self.source2 = TestJobSource("source2")
        self.source3 = TestJobSource("source3")
        
        # Patch the JobSourceRegistry to use our test sources
        self.registry_patcher = patch('services.job_search.sources.JobSourceRegistry')
        self.MockRegistry = self.registry_patcher.start()
        
        # Create a mock registry instance
        self.mock_registry = MagicMock()
        self.MockRegistry.return_value = self.mock_registry
        
        # Set up the mock registry's get_all_sources method to return an empty list
        self.mock_registry.get_all_sources.return_value = []
        
        # Create the job search agent
        self.agent = JobSearchAgent()
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Restore environment variable
        if self.original_user_data_dir:
            os.environ["USER_DATA_DIR"] = self.original_user_data_dir
        else:
            del os.environ["USER_DATA_DIR"]
        
        # Stop the patcher
        self.registry_patcher.stop()
        
        # Clean up the temporary directory
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test that the JobSearchAgent initializes the registry correctly."""
        # Verify the registry was created
        self.MockRegistry.assert_called_once()
        
        # Verify we checked for existing sources
        self.mock_registry.get_all_sources.assert_called_with(enabled_only=False)
        
        # Verify we registered a default source
        self.mock_registry.register_source.assert_called_once()
        
        # Reset the mocks for further tests
        self.mock_registry.reset_mock()
    
    def test_search_jobs_with_source_name(self):
        """Test searching jobs with a specific source name."""
        # Set up the mock registry
        self.mock_registry.get_source.return_value = self.source1
        
        # Perform a search with a specific source
        results = self.agent.search_jobs(
            keywords="software engineer",
            location="San Francisco",
            recency="week",
            experience_level="mid",
            remote=True,
            source_name="source1"
        )
        
        # Verify we got the specific source
        self.mock_registry.get_source.assert_called_with("source1")
        
        # Verify the search was performed with the right parameters
        self.assertEqual(self.source1.search_count, 1)
        self.assertEqual(self.source1.search_args[0]["keywords"], "software engineer")
        self.assertEqual(self.source1.search_args[0]["location"], "San Francisco")
        self.assertEqual(self.source1.search_args[0]["filters"]["recency"], "week")
        self.assertEqual(self.source1.search_args[0]["filters"]["experience_level"], "mid")
        self.assertEqual(self.source1.search_args[0]["filters"]["remote"], True)
        
        # Verify the results include the source name
        self.assertEqual(results["metadata"]["source"], "source1")
    
    def test_search_jobs_source_not_found(self):
        """Test searching jobs with a non-existent source name."""
        # Set up the mock registry to return None (source not found)
        self.mock_registry.get_source.return_value = None
        
        # Verify that a ValueError is raised
        with self.assertRaises(ValueError):
            self.agent.search_jobs(
                keywords="software engineer",
                source_name="non_existent"
            )
    
    def test_search_jobs_with_primary_strategy(self):
        """Test searching jobs with the primary strategy."""
        # Set up the mock distribute_search to return a source and results
        self.mock_registry.distribute_search.return_value = (
            self.source1,
            {"choices": [{"message": {"content": "Test job listing"}}]}
        )
        
        # Perform a search with primary strategy
        results = self.agent.search_jobs(
            keywords="software engineer",
            search_strategy="primary"
        )
        
        # Verify distribute_search was called with the right parameters
        self.mock_registry.distribute_search.assert_called_with(
            keywords="software engineer",
            location=None,
            filters={"recency": None, "experience_level": None, "remote": False},
            strategy="primary"
        )
        
        # Verify we have results
        self.assertIn("jobs", results)
        self.assertIn("metadata", results)
        self.assertEqual(results["metadata"]["search_strategy"], "primary")
    
    def test_search_jobs_with_load_balance_strategy(self):
        """Test searching jobs with the load balance strategy."""
        # Set up the mock distribute_search to return a source and results
        self.mock_registry.distribute_search.return_value = (
            self.source2,
            {"choices": [{"message": {"content": "Test job listing"}}]}
        )
        
        # Perform a search with load balance strategy
        results = self.agent.search_jobs(
            keywords="software engineer",
            search_strategy="load_balance"
        )
        
        # Verify distribute_search was called with the right parameters
        self.mock_registry.distribute_search.assert_called_with(
            keywords="software engineer",
            location=None,
            filters={"recency": None, "experience_level": None, "remote": False},
            strategy="load_balance"
        )
        
        # Verify we have results
        self.assertIn("jobs", results)
        self.assertIn("metadata", results)
        self.assertEqual(results["metadata"]["search_strategy"], "load_balance")
    
    def test_search_jobs_with_all_strategy(self):
        """Test searching jobs with the all strategy."""
        # Set up the mock distribute_search to return aggregated results
        self.mock_registry.distribute_search.return_value = (
            None,
            {
                "sources": ["source1", "source2"],
                "raw_results": {
                    "source1": {"choices": [{"message": {"content": "Job from source1"}}]},
                    "source2": {"choices": [{"message": {"content": "Job from source2"}}]}
                }
            }
        )
        
        # Set up get_source to return our test sources
        def mock_get_source(name):
            sources = {"source1": self.source1, "source2": self.source2}
            return sources.get(name)
        
        self.mock_registry.get_source.side_effect = mock_get_source
        
        # Perform a search with all strategy
        results = self.agent.search_jobs(
            keywords="software engineer",
            search_strategy="all"
        )
        
        # Verify distribute_search was called with the right parameters
        self.mock_registry.distribute_search.assert_called_with(
            keywords="software engineer",
            location=None,
            filters={"recency": None, "experience_level": None, "remote": False},
            strategy="all"
        )
        
        # Verify we have results from both sources
        self.assertIn("jobs", results)
        self.assertIn("metadata", results)
        self.assertEqual(len(results["jobs"]), 2)
        self.assertEqual(results["metadata"]["search_strategy"], "all")
        self.assertIn("sources", results["metadata"])
        self.assertEqual(len(results["metadata"]["sources"]), 2)
        self.assertIn("source1", results["metadata"]["sources"])
        self.assertIn("source2", results["metadata"]["sources"])
    
    def test_search_jobs_with_no_enabled_sources(self):
        """Test searching jobs when no sources are enabled."""
        # Set up the mock distribute_search to return None (no sources)
        self.mock_registry.distribute_search.return_value = (None, None)
        
        # Perform a search
        results = self.agent.search_jobs(
            keywords="software engineer"
        )
        
        # Verify we have an error in the metadata
        self.assertIn("jobs", results)
        self.assertEqual(len(results["jobs"]), 0)
        self.assertIn("metadata", results)
        self.assertIn("error", results["metadata"])
        self.assertEqual(results["metadata"]["source"], "none")
    
    def test_enhanced_job_search_with_preferences(self):
        """Test enhanced job search with user preferences."""
        # Create a mock for get_user_preferences
        with patch.object(self.agent, 'get_user_preferences') as mock_get_prefs:
            # Set up the mock to return test preferences
            mock_get_prefs.return_value = {
                "technicalSkills": ["Python", "React", "AWS"],
                "careerGoals": "Seeking a senior software engineering role",
                "jobTypes": ["Full-time", "Remote"]
            }
            
            # Set up the mock distribute_search to return a source and results
            self.mock_registry.distribute_search.return_value = (
                self.source1,
                {"choices": [{"message": {"content": "Test job listing"}}]}
            )
            
            # Perform an enhanced search
            results = self.agent.enhanced_job_search(
                user_id="test_user",
                keywords="software engineer",
                location="San Francisco"
            )
            
            # Verify we called get_user_preferences
            mock_get_prefs.assert_called_with("test_user")
            
            # Verify distribute_search was called with enhanced keywords
            call_args = self.mock_registry.distribute_search.call_args
            self.assertIn("keywords", call_args[1])
            self.assertIn("with skills in", call_args[1]["keywords"])
            self.assertIn("Python", call_args[1]["keywords"])
            self.assertIn("React", call_args[1]["keywords"])
            self.assertIn("AWS", call_args[1]["keywords"])
            
            # Verify distribute_search was called with remote=True
            self.assertTrue(call_args[1]["filters"]["remote"])
            
            # Verify we have results
            self.assertIn("jobs", results)
            self.assertIn("metadata", results)
            self.assertIn("original_criteria", results["metadata"])
            self.assertIn("enhanced_criteria", results["metadata"])
            self.assertTrue(results["metadata"]["preferences_used"])
    
    def test_enhanced_job_search_no_preferences(self):
        """Test enhanced job search when no preferences are found."""
        # Create a mock for get_user_preferences
        with patch.object(self.agent, 'get_user_preferences') as mock_get_prefs:
            # Set up the mock to return empty preferences
            mock_get_prefs.return_value = {}
            
            # Set up the mock for search_jobs
            with patch.object(self.agent, 'search_jobs') as mock_search:
                # Set up the mock to return test results
                mock_search.return_value = {"jobs": [], "metadata": {}}
                
                # Perform an enhanced search
                self.agent.enhanced_job_search(
                    user_id="test_user",
                    keywords="software engineer"
                )
                
                # Verify we called get_user_preferences
                mock_get_prefs.assert_called_with("test_user")
                
                # Verify we fell back to regular search
                mock_search.assert_called_with(
                    keywords="software engineer",
                    location=None,
                    recency=None,
                    experience_level=None,
                    remote=False,
                    source_name=None,
                    search_strategy="primary"
                )
    
    def test_analyze_resume_match(self):
        """Test analyzing resume match using the primary source."""
        # Set up the mock get_primary_source
        self.mock_registry.get_primary_source.return_value = self.source1
        
        # Set up the source to return a specific response
        self.source1.search_jobs = MagicMock(return_value={
            "choices": [
                {
                    "message": {
                        "content": "Match score: 85\nThe resume matches the job requirements well..."
                    }
                }
            ]
        })
        
        # Test resume and job description
        job_description = "Software Engineer job description..."
        resume_text = "Resume text with skills and experience..."
        
        # Analyze the match
        match_result = self.agent.analyze_resume_match(job_description, resume_text)
        
        # Verify we got the primary source
        self.mock_registry.get_primary_source.assert_called_once()
        
        # Verify the query to the source contains both the job description and resume
        call_args = self.source1.search_jobs.call_args
        self.assertIn(job_description, call_args[0][0])
        self.assertIn(resume_text, call_args[0][0])
        
        # Verify the match score was extracted
        self.assertEqual(match_result["match_score"], 85)
        self.assertIn("analysis", match_result)
    
    def test_analyze_resume_match_no_sources(self):
        """Test analyzing resume match when no sources are available."""
        # Set up the mock get_primary_source to return None
        self.mock_registry.get_primary_source.return_value = None
        
        # Verify that a ValueError is raised
        with self.assertRaises(ValueError):
            self.agent.analyze_resume_match("job description", "resume text")
    
    def test_source_management_methods(self):
        """Test the source management methods."""
        # Test list_sources
        self.mock_registry.get_all_source_info.return_value = [
            {"name": "source1", "enabled": True},
            {"name": "source2", "enabled": False}
        ]
        sources = self.agent.list_sources()
        self.assertEqual(len(sources), 2)
        self.mock_registry.get_all_source_info.assert_called_once()
        
        # Test get_source_info
        self.mock_registry.get_source_info.return_value = {"name": "source1", "enabled": True}
        info = self.agent.get_source_info("source1")
        self.assertEqual(info["name"], "source1")
        self.mock_registry.get_source_info.assert_called_with("source1")
        
        # Test enable_source
        self.mock_registry.enable_source.return_value = True
        result = self.agent.enable_source("source1")
        self.assertEqual(result["status"], "success")
        self.mock_registry.enable_source.assert_called_with("source1")
        
        # Test disable_source
        self.mock_registry.disable_source.return_value = True
        result = self.agent.disable_source("source1")
        self.assertEqual(result["status"], "success")
        self.mock_registry.disable_source.assert_called_with("source1")
        
        # Test update_source_priority
        self.mock_registry.set_priority.return_value = True
        result = self.agent.update_source_priority("source1", 10)
        self.assertEqual(result["status"], "success")
        self.mock_registry.set_priority.assert_called_with("source1", 10)
        
        # Test update_source_weight
        self.mock_registry.set_weight.return_value = True
        result = self.agent.update_source_weight("source1", 5)
        self.assertEqual(result["status"], "success")
        self.mock_registry.set_weight.assert_called_with("source1", 5)
        
        # Test update_source_config
        config = {"key": "value"}
        self.mock_registry.update_source_config.return_value = True
        result = self.agent.update_source_config("source1", config)
        self.assertEqual(result["status"], "success")
        self.mock_registry.update_source_config.assert_called_with("source1", config)
    
    def test_save_load_registry_config(self):
        """Test saving and loading registry configuration."""
        # Test save_registry_config
        self.mock_registry.save_config.return_value = True
        result = self.agent.save_registry_config("test_config.json")
        self.assertEqual(result["status"], "success")
        self.mock_registry.save_config.assert_called_with("test_config.json")
        
        # Test with default path
        self.mock_registry.save_config.reset_mock()
        result = self.agent.save_registry_config()
        self.assertEqual(result["status"], "success")
        self.mock_registry.save_config.assert_called_once()
        
        # Test load_registry_config
        self.mock_registry.load_config.return_value = True
        result = self.agent.load_registry_config("test_config.json")
        self.assertEqual(result["status"], "success")
        self.mock_registry.load_config.assert_called_with("test_config.json")
        
        # Test with default path
        self.mock_registry.load_config.reset_mock()
        result = self.agent.load_registry_config()
        self.assertEqual(result["status"], "success")
        self.mock_registry.load_config.assert_called_once()
        
        # Test error handling
        self.mock_registry.load_config.return_value = False
        result = self.agent.load_registry_config()
        self.assertEqual(result["status"], "error")

if __name__ == '__main__':
    unittest.main()
