#!/usr/bin/env python3
"""
Test runner for Job Source Registry tests.

This script discovers and runs all tests related to the Job Source Registry.
"""

import os
import sys
import unittest

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

if __name__ == "__main__":
    # Create a test loader
    loader = unittest.TestLoader()
    
    # Start with an empty test suite
    suite = unittest.TestSuite()
    
    # Add registry core tests
    registry_tests = loader.discover('job_search', pattern='test_job_source_registry.py')
    suite.addTest(registry_tests)
    
    # Add integration tests
    integration_tests = loader.discover('job_search', pattern='test_registry_integration.py')
    suite.addTest(integration_tests)
    
    # Add API tests
    api_tests = loader.discover('job_search', pattern='test_registry_api.py')
    suite.addTest(api_tests)
    
    # Create a test runner
    runner = unittest.TextTestRunner(verbosity=2)
    
    # Run the tests
    result = runner.run(suite)
    
    # Return non-zero exit code if tests failed
    sys.exit(not result.wasSuccessful())
