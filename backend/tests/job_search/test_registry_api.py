"""
Tests for the API endpoints related to the Job Source Registry.

These tests verify that the API endpoints for managing job sources
work correctly, including error handling and response formatting.
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

from app import create_app
from services.job_search import JobSearchAgent
from services.job_search.sources import JobSource, JobSourceRegistry

class JobSourceRegistryAPITests(unittest.TestCase):
    """Tests for the API endpoints related to the Job Source Registry."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a Flask test client
        self.app = create_app(testing=True)
        self.client = self.app.test_client()
        
        # Patch the JobSearchAgent class
        self.agent_patcher = patch('blueprints.job_search.routes.job_agent')
        self.mock_agent = self.agent_patcher.start()
        
        # Set up common mock responses
        self.mock_agent.list_sources.return_value = [
            {"name": "source1", "enabled": True, "priority": 10, "weight": 5, "config": {}},
            {"name": "source2", "enabled": False, "priority": 5, "weight": 3, "config": {}}
        ]
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Stop the patcher
        self.agent_patcher.stop()
    
    def test_list_sources_endpoint(self):
        """Test the endpoint for listing all job sources."""
        # Call the endpoint
        response = self.client.get('/api/job-search/sources')
        
        # Verify the response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "success")
        self.assertIn("sources", data)
        self.assertEqual(len(data["sources"]), 2)
        
        # Verify we called the agent method
        self.mock_agent.list_sources.assert_called_once()
    
    def test_list_sources_error(self):
        """Test error handling for the list sources endpoint."""
        # Set up the mock to raise an exception
        self.mock_agent.list_sources.side_effect = Exception("Test error")
        
        # Call the endpoint
        response = self.client.get('/api/job-search/sources')
        
        # Verify the response
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "error")
        self.assertIn("message", data)
    
    def test_get_source_info_endpoint(self):
        """Test the endpoint for getting information about a specific job source."""
        # Set up the mock response
        self.mock_agent.get_source_info.return_value = {
            "name": "source1", 
            "enabled": True, 
            "priority": 10, 
            "weight": 5, 
            "config": {"key": "value"}
        }
        
        # Call the endpoint
        response = self.client.get('/api/job-search/sources/source1')
        
        # Verify the response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "success")
        self.assertIn("source", data)
        self.assertEqual(data["source"]["name"], "source1")
        
        # Verify we called the agent method
        self.mock_agent.get_source_info.assert_called_with("source1")
    
    def test_get_source_info_not_found(self):
        """Test the endpoint for getting information about a non-existent source."""
        # Set up the mock to return an empty dict
        self.mock_agent.get_source_info.return_value = {}
        
        # Call the endpoint
        response = self.client.get('/api/job-search/sources/non_existent')
        
        # Verify the response
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "error")
        self.assertIn("message", data)
    
    def test_enable_source_endpoint(self):
        """Test the endpoint for enabling a job source."""
        # Set up the mock response
        self.mock_agent.enable_source.return_value = {
            "status": "success",
            "message": "Job source 'source1' enabled successfully"
        }
        
        # Call the endpoint
        response = self.client.post('/api/job-search/sources/source1/enable')
        
        # Verify the response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "success")
        self.assertIn("message", data)
        
        # Verify we called the agent method
        self.mock_agent.enable_source.assert_called_with("source1")
    
    def test_enable_source_not_found(self):
        """Test the endpoint for enabling a non-existent source."""
        # Set up the mock to return an error
        self.mock_agent.enable_source.return_value = {
            "status": "error",
            "message": "Job source 'non_existent' not found"
        }
        
        # Call the endpoint
        response = self.client.post('/api/job-search/sources/non_existent/enable')
        
        # Verify the response
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "error")
        self.assertIn("message", data)
    
    def test_disable_source_endpoint(self):
        """Test the endpoint for disabling a job source."""
        # Set up the mock response
        self.mock_agent.disable_source.return_value = {
            "status": "success",
            "message": "Job source 'source1' disabled successfully"
        }
        
        # Call the endpoint
        response = self.client.post('/api/job-search/sources/source1/disable')
        
        # Verify the response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "success")
        self.assertIn("message", data)
        
        # Verify we called the agent method
        self.mock_agent.disable_source.assert_called_with("source1")
    
    def test_update_priority_endpoint(self):
        """Test the endpoint for updating a job source's priority."""
        # Set up the mock response
        self.mock_agent.update_source_priority.return_value = {
            "status": "success",
            "message": "Priority for job source 'source1' updated successfully"
        }
        
        # Call the endpoint
        response = self.client.post('/api/job-search/sources/source1/priority', 
                                   json={"priority": 15})
        
        # Verify the response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "success")
        self.assertIn("message", data)
        
        # Verify we called the agent method
        self.mock_agent.update_source_priority.assert_called_with("source1", 15)
    
    def test_update_priority_invalid_input(self):
        """Test the endpoint for updating priority with invalid input."""
        # Call the endpoint with missing priority
        response = self.client.post('/api/job-search/sources/source1/priority', 
                                   json={})
        
        # Verify the response
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "error")
        self.assertIn("message", data)
        
        # Call the endpoint with non-integer priority
        response = self.client.post('/api/job-search/sources/source1/priority', 
                                   json={"priority": "invalid"})
        
        # Verify the response
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "error")
        self.assertIn("message", data)
    
    def test_update_weight_endpoint(self):
        """Test the endpoint for updating a job source's weight."""
        # Set up the mock response
        self.mock_agent.update_source_weight.return_value = {
            "status": "success",
            "message": "Weight for job source 'source1' updated successfully"
        }
        
        # Call the endpoint
        response = self.client.post('/api/job-search/sources/source1/weight', 
                                   json={"weight": 8})
        
        # Verify the response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "success")
        self.assertIn("message", data)
        
        # Verify we called the agent method
        self.mock_agent.update_source_weight.assert_called_with("source1", 8)
    
    def test_update_weight_invalid_input(self):
        """Test the endpoint for updating weight with invalid input."""
        # Call the endpoint with missing weight
        response = self.client.post('/api/job-search/sources/source1/weight', 
                                   json={})
        
        # Verify the response
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "error")
        self.assertIn("message", data)
        
        # Call the endpoint with weight less than 1
        response = self.client.post('/api/job-search/sources/source1/weight', 
                                   json={"weight": 0})
        
        # Verify the response
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "error")
        self.assertIn("message", data)
    
    def test_update_config_endpoint(self):
        """Test the endpoint for updating a job source's configuration."""
        # Set up the mock response
        self.mock_agent.update_source_config.return_value = {
            "status": "success",
            "message": "Configuration for job source 'source1' updated successfully"
        }
        
        # Call the endpoint
        config = {"model": "advanced", "max_jobs": 20}
        response = self.client.post('/api/job-search/sources/source1/config', 
                                   json={"config": config})
        
        # Verify the response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "success")
        self.assertIn("message", data)
        
        # Verify we called the agent method
        self.mock_agent.update_source_config.assert_called_with("source1", config)
    
    def test_update_config_invalid_input(self):
        """Test the endpoint for updating config with invalid input."""
        # Call the endpoint with missing config
        response = self.client.post('/api/job-search/sources/source1/config', 
                                   json={})
        
        # Verify the response
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "error")
        self.assertIn("message", data)
        
        # Call the endpoint with non-dict config
        response = self.client.post('/api/job-search/sources/source1/config', 
                                   json={"config": "invalid"})
        
        # Verify the response
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "error")
        self.assertIn("message", data)
    
    def test_save_config_endpoint(self):
        """Test the endpoint for saving registry configuration."""
        # Set up the mock response
        self.mock_agent.save_registry_config.return_value = {
            "status": "success",
            "message": "Registry configuration saved successfully"
        }
        
        # Call the endpoint
        response = self.client.post('/api/job-search/sources/config/save')
        
        # Verify the response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "success")
        self.assertIn("message", data)
        
        # Verify we called the agent method
        self.mock_agent.save_registry_config.assert_called_once()
        
        # Test with custom path
        self.mock_agent.save_registry_config.reset_mock()
        response = self.client.post('/api/job-search/sources/config/save', 
                                  json={"config_file": "custom_path.json"})
        
        # Verify we called the agent method with the custom path
        self.mock_agent.save_registry_config.assert_called_with("custom_path.json")
    
    def test_load_config_endpoint(self):
        """Test the endpoint for loading registry configuration."""
        # Set up the mock response
        self.mock_agent.load_registry_config.return_value = {
            "status": "success",
            "message": "Registry configuration loaded successfully",
            "sources": [{"name": "source1", "enabled": True}]
        }
        
        # Call the endpoint
        response = self.client.post('/api/job-search/sources/config/load')
        
        # Verify the response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "success")
        self.assertIn("message", data)
        self.assertIn("sources", data)
        
        # Verify we called the agent method
        self.mock_agent.load_registry_config.assert_called_once()
        
        # Test with custom path
        self.mock_agent.load_registry_config.reset_mock()
        response = self.client.post('/api/job-search/sources/config/load', 
                                  json={"config_file": "custom_path.json"})
        
        # Verify we called the agent method with the custom path
        self.mock_agent.load_registry_config.assert_called_with("custom_path.json")
    
    def test_load_config_error(self):
        """Test error handling for loading registry configuration."""
        # Set up the mock to return an error
        self.mock_agent.load_registry_config.return_value = {
            "status": "error",
            "message": "Failed to load registry configuration"
        }
        
        # Call the endpoint
        response = self.client.post('/api/job-search/sources/config/load')
        
        # Verify the response
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "error")
        self.assertIn("message", data)
    
    def test_search_with_strategy(self):
        """Test that search endpoint accepts search strategy parameter."""
        # Set up the mock response
        self.mock_agent.search_jobs.return_value = {
            "jobs": [],
            "metadata": {"search_strategy": "load_balance"}
        }
        
        # Call the endpoint with a search strategy
        response = self.client.post('/api/job-search/search', json={
            "keywords": "software engineer",
            "search_strategy": "load_balance"
        })
        
        # Verify the response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "success")
        self.assertIn("metadata", data)
        self.assertEqual(data["metadata"]["search_strategy"], "load_balance")
        
        # Verify we called the agent method with the right strategy
        self.mock_agent.search_jobs.assert_called_with(
            keywords="software engineer",
            location=None,
            recency=None,
            experience_level=None,
            remote=False,
            source_name=None,
            search_strategy="load_balance"
        )
    
    def test_search_with_invalid_strategy(self):
        """Test error handling for invalid search strategy."""
        # Call the endpoint with an invalid strategy
        response = self.client.post('/api/job-search/search', json={
            "keywords": "software engineer",
            "search_strategy": "invalid_strategy"
        })
        
        # Verify the response
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "error")
        self.assertIn("message", data)
        self.assertIn("search strategy", data["message"].lower())
    
    def test_enhanced_search_with_strategy(self):
        """Test that enhanced search endpoint accepts search strategy parameter."""
        # Set up the mock response
        self.mock_agent.enhanced_job_search.return_value = {
            "jobs": [],
            "metadata": {
                "search_strategy": "all",
                "preferences_used": True
            }
        }
        
        # Call the endpoint with a search strategy
        response = self.client.post('/api/job-search/search', json={
            "keywords": "software engineer",
            "use_preferences": True,
            "user_id": "test_user",
            "search_strategy": "all"
        })
        
        # Verify the response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "success")
        self.assertIn("metadata", data)
        self.assertEqual(data["metadata"]["search_strategy"], "all")
        
        # Verify we called the agent method with the right strategy
        self.mock_agent.enhanced_job_search.assert_called_with(
            user_id="test_user",
            keywords="software engineer",
            location=None,
            recency=None,
            experience_level=None,
            remote=False,
            source_name=None,
            search_strategy="all"
        )

if __name__ == '__main__':
    unittest.main()
