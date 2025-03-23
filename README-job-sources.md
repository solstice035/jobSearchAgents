# Job Source Registry

This document provides information about the Job Source Registry component implemented in the jobSearchAgents application.

## Overview

The Job Source Registry is a component that manages multiple job data sources, allowing the application to:

- Register and manage multiple job source implementations
- Prioritize job sources for search operations
- Implement load balancing across sources
- Enable/disable specific sources
- Configure source-specific parameters

## Architecture

The Job Source Registry consists of the following components:

1. **Registry Class (`JobSourceRegistry`)**: Core class for managing job sources
2. **Base Source Interface (`JobSource`)**: Abstract base class that all job sources must implement
3. **Source Implementations**: Concrete implementations of job sources (e.g., `PerplexityJobSource`)
4. **JobSearchAgent Integration**: Updates to use the registry for job searches
5. **API Endpoints**: Routes for managing sources
6. **Frontend Component**: UI for registry management

## Features

### Multiple Source Management

The registry can manage multiple job sources simultaneously, allowing the application to search across different data providers.

```python
# Register a job source
registry.register_source(
    source=PerplexityJobSource(),
    priority=10,
    enabled=True,
    weight=5
)
```

### Source Prioritization

Job sources can be assigned priorities, determining which source is used for operations that require a single source.

```python
# Update priority
registry.set_priority("perplexity", 15)
```

### Load Balancing

The registry supports load balancing across enabled sources using weighted random selection.

```python
# Select a source using load balancing
source = registry.select_source_by_load_balance()
```

### Search Distribution Strategies

When searching for jobs, the application can use different strategies:

- **Primary**: Use the highest priority source
- **Load Balance**: Distribute search requests across sources using weighted selection
- **All**: Query all enabled sources and aggregate results

```python
# Distribute search using a strategy
source, results = registry.distribute_search(
    keywords="software engineer",
    location="New York",
    strategy="load_balance"
)
```

### Source Configuration

Each source can have custom configuration parameters:

```python
# Update source configuration
registry.update_source_config("perplexity", {
    "model": "sonar-pro",
    "max_jobs_per_search": 15
})
```

### Configuration Persistence

The registry configuration can be saved to and loaded from a file:

```python
# Save configuration
registry.save_config("config/job_sources.json")

# Load configuration
registry.load_config("config/job_sources.json")
```

## Integration with JobSearchAgent

The `JobSearchAgent` class has been updated to use the registry for all job search operations:

```python
def __init__(self, config_file=None):
    # Initialize the job source registry
    self.registry = JobSourceRegistry(config_file)
    
    # Register default sources if registry is empty
    if not self.registry.get_all_sources(enabled_only=False):
        self.registry.register_source(
            source=PerplexityJobSource(),
            priority=10,
            enabled=True,
            weight=10
        )
```

## API Endpoints

The application provides RESTful API endpoints for managing job sources:

### List Sources

```
GET /api/job-search/sources
```

Returns a list of all registered job sources with their information.

### Get Source Info

```
GET /api/job-search/sources/{source_name}
```

Returns information about a specific job source.

### Enable/Disable Source

```
POST /api/job-search/sources/{source_name}/enable
POST /api/job-search/sources/{source_name}/disable
```

Enable or disable a job source.

### Update Source Priority

```
POST /api/job-search/sources/{source_name}/priority
```

Update the priority of a job source.

### Update Source Weight

```
POST /api/job-search/sources/{source_name}/weight
```

Update the weight of a job source for load balancing.

### Update Source Configuration

```
POST /api/job-search/sources/{source_name}/config
```

Update the configuration of a job source.

### Save/Load Registry Configuration

```
POST /api/job-search/sources/config/save
POST /api/job-search/sources/config/load
```

Save or load the registry configuration.

## Frontend Management

The application includes a React component (`JobSourceManager`) for managing job sources through a user-friendly interface:

- View all registered sources
- Enable/disable sources
- Adjust source priorities and weights
- View source configurations
- Save/load registry configuration

## Implementing a New Job Source

To implement a new job source:

1. Create a new class that inherits from `JobSource`
2. Implement the required methods:
   - `source_name` property
   - `search_jobs` method
   - `parse_results` method
   - `normalize_job` method
3. Register the source with the registry

Example:

```python
from .base_source import JobSource

class CustomJobSource(JobSource):
    @property
    def source_name(self) -> str:
        return "Custom"
    
    def search_jobs(self, keywords, location=None, filters=None, params=None):
        # Implement search logic
        pass
    
    def parse_results(self, raw_data):
        # Implement parsing logic
        pass
    
    def normalize_job(self, job_data):
        # Implement normalization logic
        pass

# Register the source
registry.register_source(CustomJobSource())
```

## Configuration File Format

The registry configuration file uses the following JSON format:

```json
{
  "sources": {
    "perplexity": {
      "module": "services.job_search.sources.perplexity_source",
      "class": "PerplexityJobSource",
      "enabled": true,
      "priority": 10,
      "weight": 10,
      "config": {
        "model": "sonar-pro",
        "max_jobs_per_search": 10,
        "default_recency": "month"
      }
    }
  }
}
```

## Benefits

The Job Source Registry provides several benefits:

1. **Extensibility**: Easily add new job data sources without modifying existing code
2. **Redundancy**: Continue operation even if some sources fail
3. **Optimization**: Use the most appropriate source for each operation
4. **Load Distribution**: Balance queries across multiple sources
5. **Configuration**: Adjust source behavior without code changes
6. **Management**: Enable/disable sources dynamically

## Future Enhancements

Potential enhancements for the Job Source Registry:

1. **Source-Specific Metrics**: Track performance and reliability of each source
2. **Auto-Failover**: Automatically switch to backup sources when primary sources fail
3. **Smart Routing**: Route specific query types to specialized sources
4. **Source Authentication**: Manage credentials for sources that require authentication
5. **Result Deduplication**: Identify and merge duplicate job listings from different sources
6. **Source Health Monitoring**: Periodically check source availability and functionality
