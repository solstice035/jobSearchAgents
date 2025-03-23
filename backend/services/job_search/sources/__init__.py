"""
Job source package initialization.

This package contains the base job source class and implementations
for various job data sources.
"""

from .base_source import JobSource
from .perplexity_source import PerplexityJobSource

__all__ = ['JobSource', 'PerplexityJobSource']
