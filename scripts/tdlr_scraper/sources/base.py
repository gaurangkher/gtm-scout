"""
Base classes for project scrapers
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import asyncio


class BaseScraper(ABC):
    """Abstract base class for project scrapers"""
    
    def __init__(self, source_name: str):
        self.source_name = source_name
    
    @abstractmethod
    async def scrape_projects(self, limit: int = 100) -> List['Project']:
        """
        Scrape projects from the source
        
        Args:
            limit: Maximum number of projects to scrape
            
        Returns:
            List of Project instances
        """
        pass
    
    @abstractmethod
    def get_source_info(self) -> Dict[str, Any]:
        """
        Get information about this source
        
        Returns:
            Dictionary with source information
        """
        pass


class BaseParser(ABC):
    """Abstract base class for parsing project data"""
    
    @abstractmethod
    async def parse_project_list(self, response_data: Dict) -> List[str]:
        """
        Parse project identifiers from search response
        
        Args:
            response_data: Raw response data from search endpoint
            
        Returns:
            List of project identifiers
        """
        pass
    
    @abstractmethod
    async def parse_project_details(self, html_content: str, project_id: str) -> 'Project':
        """
        Parse detailed project information from HTML content
        
        Args:
            html_content: Raw HTML content of project detail page
            project_id: Project identifier
            
        Returns:
            Project instance with parsed data
        """
        pass


class FieldMapper:
    """Map source-specific fields to standard project schema"""
    
    def __init__(self, field_mapping: Dict[str, List[str]]):
        """
        Initialize field mapper
        
        Args:
            field_mapping: Dictionary mapping standard fields to source-specific field names
                          Example: {'project_name': ['title', 'name', 'project_title']}
        """
        self.field_mapping = field_mapping
    
    def map_fields(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map source-specific fields to standard project fields
        
        Args:
            source_data: Dictionary with source-specific field names and values
            
        Returns:
            Dictionary with standard project field names and values
        """
        mapped_data = {}
        
        for standard_field, source_fields in self.field_mapping.items():
            # Try each possible source field name
            for source_field in source_fields:
                if source_field in source_data and source_data[source_field] is not None:
                    mapped_data[standard_field] = source_data[source_field]
                    break
        
        return mapped_data