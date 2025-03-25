#!/usr/bin/env python3
"""
Test runner for Job Source Registry tests.

This script discovers and runs all tests related to the Job Source Registry.
"""

import os
import sys
import unittest
from dotenv import load_dotenv

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

# Load environment variables from .env file
print("Loading environment variables from .env file...")
dotenv_path = os.path.join(os.path.dirname(__file__), '../.env')
load_dotenv(dotenv_path)

# Print whether the API key is set (without showing the key)
if os.getenv("PERPLEXITY_API_KEY"):
    print("PERPLEXITY_API_KEY is set")
else:
    print("PERPLEXITY_API_KEY is NOT set")

if __name__ == "__main__":
    # Create a test loader
    loader = unittest.TestLoader()
    
    # Start with an empty test suite
    suite = unittest.TestSuite()
    
    # Add registry core tests first since they don't require external dependencies
    print("\nRunning Job Source Registry unit tests...")
    registry_tests = loader.loadTestsFromName('job_search.test_job_source_registry', module=None)
    suite.addTest(registry_tests)
    
    # Run the unit tests
    runner = unittest.TextTestRunner(verbosity=2)
    unit_result = runner.run(suite)
    
    # If unit tests pass, try running the integration tests
    if unit_result.wasSuccessful():
        print("\nUnit tests passed. Running integration tests...")
        integration_tests = loader.loadTestsFromName('job_search.test_registry_integration', module=None)
        integration_suite = unittest.TestSuite()
        integration_suite.addTest(integration_tests)
        integration_result = runner.run(integration_suite)
        
        # Return overall success/failure
        print("\nTest Summary:")
        print(f"Unit Tests: {'PASSED' if unit_result.wasSuccessful() else 'FAILED'}")
        print(f"Integration Tests: {'PASSED' if integration_result.wasSuccessful() else 'FAILED'}")
        
        sys.exit(not (unit_result.wasSuccessful() and integration_result.wasSuccessful()))
    else:
        print("\nUnit tests failed. Skipping integration tests.")
        sys.exit(1)
