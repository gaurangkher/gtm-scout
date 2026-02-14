"""
Scraper manager for coordinating multiple sources
"""

import asyncio
from typing import Dict, List, Optional
from .models import Project
from .database import ProjectDatabase
from ..sources.source_registry import get_source, list_sources
import logging

logger = logging.getLogger(__name__)


class ScraperManager:
    """Manage scraping from multiple sources"""
    
    def __init__(self, db_path: str = "projects.db"):
        self.db = ProjectDatabase(db_path)
    
    async def scrape_source(self, source_name: str, limit: int = 100, **kwargs) -> int:
        """
        Scrape projects from a specific source
        
        Args:
            source_name: Name of the source to scrape
            limit: Maximum number of projects to scrape
            **kwargs: Additional arguments for the scraper
            
        Returns:
            Number of projects saved to database
        """
        logger.info(f"Scraping {limit} projects from {source_name}")
        
        try:
            # Get the scraper for this source
            scraper = get_source(source_name, **kwargs)
            
            # Scrape projects
            projects = await scraper.scrape_projects(limit)
            
            # Save to database
            saved_count = self.db.save_projects(projects)
            
            logger.info(f"Saved {saved_count} projects from {source_name}")
            return saved_count
            
        except Exception as e:
            logger.error(f"Error scraping {source_name}: {e}")
            raise
    
    async def scrape_all_sources(self, limit_per_source: int = 100, **kwargs) -> Dict[str, int]:
        """
        Scrape projects from all registered sources
        
        Args:
            limit_per_source: Maximum number of projects to scrape from each source
            **kwargs: Additional arguments for scrapers
            
        Returns:
            Dictionary mapping source names to number of projects saved
        """
        results = {}
        sources = list_sources()
        
        logger.info(f"Scraping from {len(sources)} sources: {sources}")
        
        # Scrape from all sources concurrently
        tasks = [
            self.scrape_source(source, limit_per_source, **kwargs)
            for source in sources
        ]
        
        # Execute all tasks
        task_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for source, result in zip(sources, task_results):
            if isinstance(result, Exception):
                logger.error(f"Error scraping {source}: {result}")
                results[source] = 0
            else:
                results[source] = result
        
        return results
    
    def search_projects(self, query: str) -> List[Dict]:
        """
        Search projects in the database
        
        Args:
            query: Search query
            
        Returns:
            List of matching projects
        """
        return self.db.search_projects(query)
    
    def get_project_count(self) -> int:
        """
        Get total number of projects in database
        
        Returns:
            Total project count
        """
        return self.db.get_project_count()
    
    def list_sources(self) -> List[str]:
        """
        List all available sources
        
        Returns:
            List of source names
        """
        return list_sources()