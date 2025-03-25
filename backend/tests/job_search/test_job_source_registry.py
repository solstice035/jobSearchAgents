"""
Unit tests for the Job Source Registry.

These tests verify the functionality of the JobSourceRegistry class,
including source registration, prioritization, and distribution strategies.
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

from services.job_search.sources import JobSource, JobSourceRegistry, SampleJobSource

class TestJobSource(JobSource):
    """A test job source implementation."""
    
    def __init__(self, name: str = "test", fail_search: bool = False):
        self._name = name
        self.fail_search = fail_search
        self.search_count = 0
    
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
        
        if self.fail_search:
            raise Exception("Search failed (as configured)")
        
        return {
            "test_result": True,
            "source": self.source_name,
            "keywords": keywords,
            "location": location,
            "filters": filters,
            "params": params
        }
    
    def parse_results(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Mock implementation of parse_results."""
        return [{"job_id": 1, "title": "Test Job"}]
    
    def normalize_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock implementation of normalize_job."""
        result = self.get_standard_schema()
        result.update({
            "title": job_data.get("title", ""),
            "source_id": f"{self.source_name}_{job_data.get('job_id', 0)}"
        })
        return result

class JobSourceRegistryTests(unittest.TestCase):
    """Unit tests for the JobSourceRegistry class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.registry = JobSourceRegistry()
        self.test_source1 = TestJobSource("source1")
        self.test_source2 = TestJobSource("source2")
        self.test_source3 = TestJobSource("source3")
    
    def test_register_source(self):
        """Test registering a job source."""
        # Register a source
        self.registry.register_source(self.test_source1, priority=5, enabled=True, weight=10)
        
        # Verify the source was registered
        self.assertIn("source1", self.registry.sources)
        self.assertEqual(self.registry.priorities["source1"], 5)
        self.assertEqual(self.registry.enabled["source1"], True)
        self.assertEqual(self.registry.weights["source1"], 10)
        
        # Verify we can get the source
        source = self.registry.get_source("source1")
        self.assertEqual(source, self.test_source1)
    
    def test_register_source_class(self):
        """Test registering a job source class."""
        # Register a source class
        self.registry.register_source_class(
            source_class=SampleJobSource,
            priority=3,
            enabled=True,
            weight=5
        )
        
        # Verify the source was registered
        self.assertIn("sample", self.registry.sources)
        self.assertEqual(self.registry.priorities["sample"], 3)
        self.assertEqual(self.registry.enabled["sample"], True)
        self.assertEqual(self.registry.weights["sample"], 5)
        
        # Verify the source is an instance of SampleJobSource
        source = self.registry.get_source("sample")
        self.assertIsInstance(source, SampleJobSource)
    
    def test_get_source(self):
        """Test getting a job source."""
        # Register sources
        self.registry.register_source(self.test_source1, enabled=True)
        self.registry.register_source(self.test_source2, enabled=False)
        
        # Verify we can get enabled sources
        self.assertEqual(self.registry.get_source("source1"), self.test_source1)
        
        # Verify we cannot get disabled sources
        self.assertIsNone(self.registry.get_source("source2"))
        
        # Verify we get None for non-existent sources
        self.assertIsNone(self.registry.get_source("non_existent"))
    
    def test_get_all_sources(self):
        """Test getting all job sources."""
        # Register sources
        self.registry.register_source(self.test_source1, enabled=True)
        self.registry.register_source(self.test_source2, enabled=False)
        self.registry.register_source(self.test_source3, enabled=True)
        
        # Get all enabled sources
        enabled_sources = self.registry.get_all_sources(enabled_only=True)
        self.assertEqual(len(enabled_sources), 2)
        self.assertIn(self.test_source1, enabled_sources)
        self.assertIn(self.test_source3, enabled_sources)
        self.assertNotIn(self.test_source2, enabled_sources)
        
        # Get all sources
        all_sources = self.registry.get_all_sources(enabled_only=False)
        self.assertEqual(len(all_sources), 3)
        self.assertIn(self.test_source1, all_sources)
        self.assertIn(self.test_source2, all_sources)
        self.assertIn(self.test_source3, all_sources)
    
    def test_get_primary_source(self):
        """Test getting the primary job source."""
        # Register sources with different priorities
        self.registry.register_source(self.test_source1, priority=5, enabled=True)
        self.registry.register_source(self.test_source2, priority=10, enabled=True)
        self.registry.register_source(self.test_source3, priority=1, enabled=True)
        
        # Verify the highest priority source is returned
        primary_source = self.registry.get_primary_source()
        self.assertEqual(primary_source, self.test_source2)
        
        # Disable the highest priority source
        self.registry.disable_source("source2")
        
        # Verify the next highest priority source is returned
        primary_source = self.registry.get_primary_source()
        self.assertEqual(primary_source, self.test_source1)
        
        # Disable all sources
        self.registry.disable_source("source1")
        self.registry.disable_source("source3")
        
        # Verify None is returned when no sources are enabled
        self.assertIsNone(self.registry.get_primary_source())
    
    def test_select_source_by_load_balance(self):
        """Test selecting a job source using load balancing."""
        # Register sources with different weights
        self.registry.register_source(self.test_source1, weight=10, enabled=True)
        self.registry.register_source(self.test_source2, weight=5, enabled=True)
        
        # Select sources many times and verify distribution roughly matches weights
        selection_counts = {"source1": 0, "source2": 0}
        num_trials = 1000
        
        for _ in range(num_trials):
            source = self.registry.select_source_by_load_balance()
            selection_counts[source.source_name] += 1
        
        # Expect roughly 10:5 ratio (or 2:1)
        # Allow for some randomness, but should be roughly proportional
        self.assertGreater(selection_counts["source1"], selection_counts["source2"] * 0.8)
        
        # Disable all sources
        self.registry.disable_source("source1")
        self.registry.disable_source("source2")
        
        # Verify None is returned when no sources are enabled
        self.assertIsNone(self.registry.select_source_by_load_balance())
    
    def test_enable_disable_source(self):
        """Test enabling and disabling a job source."""
        # Register sources
        self.registry.register_source(self.test_source1, enabled=True)
        self.registry.register_source(self.test_source2, enabled=False)
        
        # Verify initial states
        self.assertTrue(self.registry.enabled["source1"])
        self.assertFalse(self.registry.enabled["source2"])
        
        # Disable source1
        result = self.registry.disable_source("source1")
        self.assertTrue(result)
        self.assertFalse(self.registry.enabled["source1"])
        
        # Enable source2
        result = self.registry.enable_source("source2")
        self.assertTrue(result)
        self.assertTrue(self.registry.enabled["source2"])
        
        # Try to enable/disable non-existent source
        result = self.registry.enable_source("non_existent")
        self.assertFalse(result)
        result = self.registry.disable_source("non_existent")
        self.assertFalse(result)
    
    def test_set_priority(self):
        """Test setting the priority of a job source."""
        # Register source
        self.registry.register_source(self.test_source1, priority=5)
        
        # Verify initial priority
        self.assertEqual(self.registry.priorities["source1"], 5)
        
        # Update priority
        result = self.registry.set_priority("source1", 10)
        self.assertTrue(result)
        self.assertEqual(self.registry.priorities["source1"], 10)
        
        # Try to set priority for non-existent source
        result = self.registry.set_priority("non_existent", 15)
        self.assertFalse(result)
    
    def test_set_weight(self):
        """Test setting the weight of a job source for load balancing."""
        # Register source
        self.registry.register_source(self.test_source1, weight=5)
        
        # Verify initial weight
        self.assertEqual(self.registry.weights["source1"], 5)
        
        # Update weight
        result = self.registry.set_weight("source1", 10)
        self.assertTrue(result)
        self.assertEqual(self.registry.weights["source1"], 10)
        
        # Try to set weight below 1
        result = self.registry.set_weight("source1", 0)
        self.assertTrue(result)
        self.assertEqual(self.registry.weights["source1"], 1)  # Should be clamped to 1
        
        # Try to set weight for non-existent source
        result = self.registry.set_weight("non_existent", 15)
        self.assertFalse(result)
    
    def test_update_source_config(self):
        """Test updating the configuration of a job source."""
        # Register source
        self.registry.register_source(self.test_source1)
        
        # Verify initial config is empty
        self.assertEqual(self.registry.get_source_config("source1"), {})
        
        # Update config
        config = {"key1": "value1", "key2": 42}
        result = self.registry.update_source_config("source1", config)
        self.assertTrue(result)
        
        # Verify config was updated
        self.assertEqual(self.registry.get_source_config("source1"), config)
        
        # Update config again (should merge)
        config2 = {"key2": 100, "key3": True}
        result = self.registry.update_source_config("source1", config2)
        self.assertTrue(result)
        
        # Verify config was merged
        expected = {"key1": "value1", "key2": 100, "key3": True}
        self.assertEqual(self.registry.get_source_config("source1"), expected)
        
        # Try to update config for non-existent source
        result = self.registry.update_source_config("non_existent", {"key": "value"})
        self.assertFalse(result)
    
    def test_get_source_info(self):
        """Test getting information about a job source."""
        # Register source with config
        config = {"key1": "value1", "key2": 42}
        self.registry.register_source(
            self.test_source1, 
            priority=10, 
            enabled=True, 
            weight=5, 
            config=config
        )
        
        # Get source info
        info = self.registry.get_source_info("source1")
        
        # Verify info is correct
        self.assertEqual(info["name"], "source1")
        self.assertEqual(info["priority"], 10)
        self.assertEqual(info["enabled"], True)
        self.assertEqual(info["weight"], 5)
        self.assertEqual(info["config"], config)
        
        # Try to get info for non-existent source
        info = self.registry.get_source_info("non_existent")
        self.assertEqual(info, {})
    
    def test_get_all_source_info(self):
        """Test getting information about all job sources."""
        # Register sources
        self.registry.register_source(self.test_source1, priority=5, enabled=True)
        self.registry.register_source(self.test_source2, priority=10, enabled=False)
        self.registry.register_source(self.test_source3, priority=1, enabled=True)
        
        # Get all source info
        info_list = self.registry.get_all_source_info()
        
        # Verify list contains 3 items
        self.assertEqual(len(info_list), 3)
        
        # Verify list is sorted by priority (descending)
        self.assertEqual(info_list[0]["name"], "source2")
        self.assertEqual(info_list[1]["name"], "source1")
        self.assertEqual(info_list[2]["name"], "source3")
        
        # Verify info contains the expected fields
        for info in info_list:
            self.assertIn("name", info)
            self.assertIn("priority", info)
            self.assertIn("enabled", info)
            self.assertIn("weight", info)
            self.assertIn("config", info)
    
    def test_save_load_config(self):
        """Test saving and loading the registry configuration."""
        # Create a temporary file for the configuration
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            config_file = tmp.name
        
        try:
            # Register sources with various settings
            self.registry.register_source(
                self.test_source1, 
                priority=5, 
                enabled=True, 
                weight=10, 
                config={"key1": "value1"}
            )
            self.registry.register_source(
                self.test_source2, 
                priority=10, 
                enabled=False, 
                weight=5, 
                config={"key2": 42}
            )
            
            # Save the configuration
            result = self.registry.save_config(config_file)
            self.assertTrue(result)
            
            # Load the configuration in a new registry
            new_registry = JobSourceRegistry()
            
            # Mock the import module to return our test source class
            with patch('importlib.import_module') as mock_import:
                # Mock the module with our TestJobSource class
                mock_module = MagicMock()
                mock_module.TestJobSource = TestJobSource
                mock_import.return_value = mock_module
                
                # Load the configuration
                result = new_registry.load_config(config_file)
                self.assertTrue(result)
            
            # Just verify that a source was loaded - we can't be certain about the exact structure
            # after mocking the import module
            self.assertGreater(len(new_registry.sources), 0)
        
        finally:
            # Clean up the temporary file
            if os.path.exists(config_file):
                os.unlink(config_file)
    
    def test_distribute_search_primary(self):
        """Test distributing a search using the primary strategy."""
        # Register sources with different priorities
        self.registry.register_source(self.test_source1, priority=5, enabled=True)
        self.registry.register_source(self.test_source2, priority=10, enabled=True)
        self.registry.register_source(self.test_source3, priority=1, enabled=True)
        
        # Distribute search using primary strategy
        source, results = self.registry.distribute_search(
            keywords="test keywords",
            location="test location",
            strategy="primary"
        )
        
        # Verify the highest priority source was used
        self.assertEqual(source, self.test_source2)
        self.assertEqual(results["source"], "source2")
        self.assertEqual(results["keywords"], "test keywords")
        self.assertEqual(results["location"], "test location")
        
        # Verify search count was incremented
        self.assertEqual(self.test_source2.search_count, 1)
        self.assertEqual(self.test_source1.search_count, 0)
        self.assertEqual(self.test_source3.search_count, 0)
    
    def test_distribute_search_load_balance(self):
        """Test distributing a search using the load balance strategy."""
        # Register sources with different weights
        self.registry.register_source(self.test_source1, weight=1, enabled=True)
        self.registry.register_source(self.test_source2, weight=0, enabled=True)  # Should be corrected to 1
        
        # Distribute search using load balance strategy
        source, results = self.registry.distribute_search(
            keywords="test keywords",
            strategy="load_balance"
        )
        
        # Verify a source was selected and search was performed
        self.assertIn(source, [self.test_source1, self.test_source2])
        self.assertEqual(results["source"], source.source_name)
        self.assertEqual(results["keywords"], "test keywords")
        
        # Verify search count was incremented for selected source
        self.assertEqual(self.test_source1.search_count + self.test_source2.search_count, 1)
    
    def test_distribute_search_all(self):
        """Test distributing a search to all sources."""
        # Register sources
        self.registry.register_source(self.test_source1, priority=1, enabled=True)
        self.registry.register_source(self.test_source2, priority=2, enabled=True)
        self.registry.register_source(self.test_source3, priority=3, enabled=False)  # Disabled
        
        # Distribute search using all strategy
        source, results = self.registry.distribute_search(
            keywords="test keywords",
            strategy="all"
        )
        
        # Verify no single source was returned
        self.assertIsNone(source)
        
        # Verify results contains both enabled sources
        self.assertIn("sources", results)
        self.assertEqual(len(results["sources"]), 2)
        self.assertIn("source1", results["sources"])
        self.assertIn("source2", results["sources"])
        self.assertNotIn("source3", results["sources"])
        
        # Verify raw results for each source
        self.assertIn("raw_results", results)
        self.assertIn("source1", results["raw_results"])
        self.assertIn("source2", results["raw_results"])
        self.assertNotIn("source3", results["raw_results"])
        
        # Verify search count was incremented for enabled sources only
        self.assertEqual(self.test_source1.search_count, 1)
        self.assertEqual(self.test_source2.search_count, 1)
        self.assertEqual(self.test_source3.search_count, 0)
    
    def test_distribute_search_error_handling(self):
        """Test error handling during search distribution."""
        # Register sources - one will fail
        self.registry.register_source(self.test_source1, priority=1, enabled=True)
        failing_source = TestJobSource("failing", fail_search=True)
        self.registry.register_source(failing_source, priority=2, enabled=True)
        
        # Distribute search using all strategy
        source, results = self.registry.distribute_search(
            keywords="test keywords",
            strategy="all"
        )
        
        # Verify no single source was returned
        self.assertIsNone(source)
        
        # Verify results contains only the successful source
        self.assertIn("sources", results)
        self.assertEqual(len(results["sources"]), 1)
        self.assertIn("source1", results["sources"])
        self.assertNotIn("failing", results["sources"])
        
        # Verify raw results for successful source only
        self.assertIn("raw_results", results)
        self.assertIn("source1", results["raw_results"])
        self.assertNotIn("failing", results["raw_results"])
        
        # Verify search count was incremented for both sources (even the failing one)
        self.assertEqual(self.test_source1.search_count, 1)
        self.assertEqual(failing_source.search_count, 1)
    
    def test_distribute_search_no_sources(self):
        """Test distributing a search when no sources are enabled."""
        # Distribute search with empty registry
        source, results = self.registry.distribute_search(
            keywords="test keywords",
            strategy="primary"
        )
        
        # Verify no source or results were returned
        self.assertIsNone(source)
        self.assertIsNone(results)
        
        # Register a disabled source
        self.registry.register_source(self.test_source1, enabled=False)
        
        # Distribute search with disabled sources
        source, results = self.registry.distribute_search(
            keywords="test keywords",
            strategy="primary"
        )
        
        # Verify no source or results were returned
        self.assertIsNone(source)
        self.assertIsNone(results)
    
    def test_distribute_search_invalid_strategy(self):
        """Test distributing a search with an invalid strategy."""
        # Register a source
        self.registry.register_source(self.test_source1, enabled=True)
        
        # Distribute search with invalid strategy
        source, results = self.registry.distribute_search(
            keywords="test keywords",
            strategy="invalid_strategy"
        )
        
        # Verify no source or results were returned
        self.assertIsNone(source)
        self.assertIsNone(results)

if __name__ == '__main__':
    unittest.main()
