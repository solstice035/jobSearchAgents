#!/bin/bash

# Run unit tests for CV parser
echo "Running unit tests for CV parser..."
python -m pytest tests/test_advanced_cv_parser.py -v

# Run integration tests for CV parser
echo ""
echo "Running integration tests for CV parser..."
python -m pytest tests/test_cv_parser_integration.py -v

# Run with coverage (optional)
# echo ""
# echo "Running tests with coverage report..."
# python -m pytest --cov=services.advanced_cv_parser tests/test_advanced_cv_parser.py tests/test_cv_parser_integration.py
