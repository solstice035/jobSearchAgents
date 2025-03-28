"""
Test configuration and fixtures for job search agents.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Add the backend directory to the Python path
backend_dir = project_root / "backend"
sys.path.insert(0, str(backend_dir))

# pytest-asyncio configuration
pytest_plugins = ("pytest_asyncio",)
