from setuptools import setup, find_packages

setup(
    name="jobSearchAgents",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pytest>=8.1.0",
        "pytest-asyncio>=0.23.0",
        "pytest-timeout>=2.3.0",
    ],
    python_requires=">=3.8",
)
