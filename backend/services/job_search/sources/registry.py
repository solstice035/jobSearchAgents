"""
Job Source Registry.

This module provides a registry for managing multiple job sources,
controlling their priority, and distributing search load.
"""

import importlib
import logging
import random
from typing import Dict, List, Any, Optional, Type, Tuple, Union
import json
import os

from .base_source import JobSource


class JobSourceRegistry:
    """
    Registry for managing and accessing multiple job sources.
    
    The registry supports:
    - Registering multiple job sources
    - Prioritizing sources for search operations
    - Load balancing searches across sources
    - Enabling/disabling sources
    - Configuring source parameters
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize the job source registry.
        
        Args:
            config_file: Optional path to a configuration file
        """
        # Initialize source registry
        self.sources: Dict[str, JobSource] = {}
        
        # Source configurations
        self.source_configs: Dict[str, Dict[str, Any]] = {}
        
        # Source priorities (higher number = higher priority)
        self.priorities: Dict[str, int] = {}
        
        # Enabled status
        self.enabled: Dict[str, bool] = {}
        
        # Weight factors for load balancing (higher number = more traffic)
        self.weights: Dict[str, int] = {}
        
        # Load configuration if provided
        if config_file:
            self.load_config(config_file)
    
    def register_source(
        self, 
        source: JobSource, 
        priority: int = 1, 
        enabled: bool = True,
        weight: int = 1,
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Register a job source with the registry.
        
        Args:
            source: The job source to register
            priority: Priority level (higher number = higher priority)
            enabled: Whether the source is enabled
            weight: Weight factor for load balancing (higher = more searches)
            config: Optional configuration for the source
        """
        source_name = source.source_name.lower()
        
        self.sources[source_name] = source
        self.priorities[source_name] = priority
        self.enabled[source_name] = enabled
        self.weights[source_name] = max(1, weight)  # Ensure weight is at least 1
        
        if config:
            self.source_configs[source_name] = config
        else:
            self.source_configs[source_name] = {}
    
    def register_source_class(
        self, 
        source_class: Type[JobSource], 
        priority: int = 1, 
        enabled: bool = True,
        weight: int = 1,
        config: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> None:
        """
        Register a job source class, instantiating it with the given parameters.
        
        Args:
            source_class: The job source class to instantiate
            priority: Priority level (higher number = higher priority)
            enabled: Whether the source is enabled
            weight: Weight factor for load balancing
            config: Optional configuration for the source
            **kwargs: Additional arguments to pass to the source constructor
        """
        # Instantiate the source
        source_instance = source_class(**kwargs)
        
        # Register the instance
        self.register_source(
            source=source_instance,
            priority=priority,
            enabled=enabled,
            weight=weight,
            config=config
        )
    
    def get_source(self, source_name: str) -> Optional[JobSource]:
        """
        Get a specific job source by name.
        
        Args:
            source_name: The name of the source to retrieve
            
        Returns:
            The job source if found and enabled, None otherwise
        """
        source_name = source_name.lower()
        
        if source_name in self.sources and self.enabled[source_name]:
            return self.sources[source_name]
        
        return None
    
    def get_all_sources(self, enabled_only: bool = True) -> List[JobSource]:
        """
        Get all registered job sources.
        
        Args:
            enabled_only: If True, only return enabled sources
            
        Returns:
            List of job sources
        """
        if enabled_only:
            return [source for name, source in self.sources.items() if self.enabled[name]]
        
        return list(self.sources.values())
    
    def get_primary_source(self) -> Optional[JobSource]:
        """
        Get the primary (highest priority) job source.
        
        Returns:
            The primary job source if any are enabled, None otherwise
        """
        enabled_sources = [(name, self.priorities[name]) for name in self.sources 
                         if self.enabled[name]]
        
        if not enabled_sources:
            return None
        
        # Sort by priority (descending)
        enabled_sources.sort(key=lambda x: x[1], reverse=True)
        
        # Return the highest priority source
        return self.sources[enabled_sources[0][0]]
    
    def select_source_by_load_balance(self) -> Optional[JobSource]:
        """
        Select a job source using weighted random selection.
        
        Returns:
            A randomly selected job source based on weights
        """
        enabled_sources = [(name, self.weights[name]) for name in self.sources 
                         if self.enabled[name]]
        
        if not enabled_sources:
            return None
        
        # Calculate total weight
        total_weight = sum(weight for _, weight in enabled_sources)
        
        # Select a random value
        rand_val = random.uniform(0, total_weight)
        
        # Find the source corresponding to the random value
        current = 0
        for name, weight in enabled_sources:
            current += weight
            if rand_val <= current:
                return self.sources[name]
        
        # Fallback to the first source
        return self.sources[enabled_sources[0][0]]
    
    def enable_source(self, source_name: str) -> bool:
        """
        Enable a job source.
        
        Args:
            source_name: The name of the source to enable
            
        Returns:
            True if the source was enabled, False if not found
        """
        source_name = source_name.lower()
        
        if source_name in self.sources:
            self.enabled[source_name] = True
            return True
        
        return False
    
    def disable_source(self, source_name: str) -> bool:
        """
        Disable a job source.
        
        Args:
            source_name: The name of the source to disable
            
        Returns:
            True if the source was disabled, False if not found
        """
        source_name = source_name.lower()
        
        if source_name in self.sources:
            self.enabled[source_name] = False
            return True
        
        return False
    
    def set_priority(self, source_name: str, priority: int) -> bool:
        """
        Set the priority for a job source.
        
        Args:
            source_name: The name of the source
            priority: The new priority (higher number = higher priority)
            
        Returns:
            True if the priority was set, False if source not found
        """
        source_name = source_name.lower()
        
        if source_name in self.sources:
            self.priorities[source_name] = priority
            return True
        
        return False
    
    def set_weight(self, source_name: str, weight: int) -> bool:
        """
        Set the weight for a job source for load balancing.
        
        Args:
            source_name: The name of the source
            weight: The new weight (higher number = more searches)
            
        Returns:
            True if the weight was set, False if source not found
        """
        source_name = source_name.lower()
        
        if source_name in self.sources:
            self.weights[source_name] = max(1, weight)  # Ensure weight is at least 1
            return True
        
        return False
    
    def update_source_config(self, source_name: str, config: Dict[str, Any]) -> bool:
        """
        Update configuration for a job source.
        
        Args:
            source_name: The name of the source
            config: The configuration to update
            
        Returns:
            True if the configuration was updated, False if source not found
        """
        source_name = source_name.lower()
        
        if source_name in self.sources:
            if source_name not in self.source_configs:
                self.source_configs[source_name] = {}
                
            # Update the configuration
            self.source_configs[source_name].update(config)
            return True
        
        return False
    
    def get_source_config(self, source_name: str) -> Dict[str, Any]:
        """
        Get the configuration for a job source.
        
        Args:
            source_name: The name of the source
            
        Returns:
            The source configuration or empty dict if not found
        """
        source_name = source_name.lower()
        
        if source_name in self.source_configs:
            return self.source_configs[source_name].copy()
        
        return {}
    
    def get_source_info(self, source_name: str) -> Dict[str, Any]:
        """
        Get information about a job source.
        
        Args:
            source_name: The name of the source
            
        Returns:
            Dictionary with source information
        """
        source_name = source_name.lower()
        
        if source_name in self.sources:
            return {
                "name": source_name,
                "enabled": self.enabled[source_name],
                "priority": self.priorities[source_name],
                "weight": self.weights[source_name],
                "config": self.get_source_config(source_name)
            }
        
        return {}
    
    def get_all_source_info(self) -> List[Dict[str, Any]]:
        """
        Get information about all registered job sources.
        
        Returns:
            List of dictionaries with source information
        """
        source_info = []
        
        for source_name in self.sources:
            source_info.append(self.get_source_info(source_name))
        
        # Sort by priority (descending)
        source_info.sort(key=lambda x: x["priority"], reverse=True)
        
        return source_info
    
    def save_config(self, config_file: str) -> bool:
        """
        Save the current registry configuration to a file.
        
        Args:
            config_file: Path to the configuration file
            
        Returns:
            True if the configuration was saved, False otherwise
        """
        try:
            config = {
                "sources": {}
            }
            
            for source_name, source in self.sources.items():
                # Get source class info for reconstruction
                module_name = source.__class__.__module__
                class_name = source.__class__.__name__
                
                # Save source configuration
                config["sources"][source_name] = {
                    "module": module_name,
                    "class": class_name,
                    "enabled": self.enabled[source_name],
                    "priority": self.priorities[source_name],
                    "weight": self.weights[source_name],
                    "config": self.get_source_config(source_name)
                }
            
            # Save to file
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            return True
            
        except Exception as e:
            logging.error(f"Error saving registry configuration: {str(e)}")
            return False
    
    def load_config(self, config_file: str) -> bool:
        """
        Load registry configuration from a file.
        
        Args:
            config_file: Path to the configuration file
            
        Returns:
            True if the configuration was loaded, False otherwise
        """
        if not os.path.exists(config_file):
            logging.error(f"Configuration file not found: {config_file}")
            return False
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            if "sources" not in config:
                logging.error("Invalid configuration file: missing 'sources' section")
                return False
            
            # Clear current registry
            self.sources = {}
            self.source_configs = {}
            self.priorities = {}
            self.enabled = {}
            self.weights = {}
            
            # Load sources from configuration
            for source_name, source_config in config["sources"].items():
                try:
                    # Import the module and class
                    module_name = source_config["module"]
                    class_name = source_config["class"]
                    module = importlib.import_module(module_name)
                    source_class = getattr(module, class_name)
                    
                    # Create source instance
                    source_instance = source_class()
                    
                    # Register the source
                    self.register_source(
                        source=source_instance,
                        priority=source_config.get("priority", 1),
                        enabled=source_config.get("enabled", True),
                        weight=source_config.get("weight", 1),
                        config=source_config.get("config", {})
                    )
                    
                except (ImportError, AttributeError, Exception) as e:
                    logging.error(f"Error loading source {source_name}: {str(e)}")
                    continue
            
            return True
            
        except Exception as e:
            logging.error(f"Error loading registry configuration: {str(e)}")
            return False
    
    def distribute_search(
        self,
        keywords: str,
        location: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        strategy: str = "primary"
    ) -> Tuple[Optional[JobSource], Optional[Dict[str, Any]]]:
        """
        Distribute a search to an appropriate job source based on the strategy.
        
        Args:
            keywords: Search terms for finding jobs
            location: Optional location for the job search
            filters: Optional filters to narrow the search
            params: Optional additional parameters specific to sources
            strategy: The distribution strategy:
                - "primary": Use the highest priority source
                - "load_balance": Use weighted random selection
                - "all": Use all enabled sources (returns None and aggregated results)
            
        Returns:
            Tuple of (selected source, raw results) or (None, aggregated results)
        """
        if strategy == "primary":
            source = self.get_primary_source()
            if source:
                return source, source.search_jobs(keywords, location, filters, params)
        
        elif strategy == "load_balance":
            source = self.select_source_by_load_balance()
            if source:
                return source, source.search_jobs(keywords, location, filters, params)
        
        elif strategy == "all":
            # Get all enabled sources sorted by priority
            enabled_sources = [(name, self.priorities[name]) for name in self.sources 
                             if self.enabled[name]]
            enabled_sources.sort(key=lambda x: x[1], reverse=True)
            
            # Aggregate results from all sources
            aggregated_results = {
                "sources": [],
                "raw_results": {}
            }
            
            for source_name, _ in enabled_sources:
                source = self.sources[source_name]
                try:
                    results = source.search_jobs(keywords, location, filters, params)
                    aggregated_results["sources"].append(source_name)
                    aggregated_results["raw_results"][source_name] = results
                except Exception as e:
                    logging.error(f"Error searching with source {source_name}: {str(e)}")
            
            return None, aggregated_results
        
        # Return None if no source was found or strategy is invalid
        return None, None
