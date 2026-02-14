"""
Source registry for managing multiple scraping sources
"""

from typing import Dict, Type, List
from ..sources.base import BaseScraper
from ..tdlr.scraper import TDLRScraper

# Registry of available sources
SOURCES: Dict[str, Type[BaseScraper]] = {
    'tdlr': TDLRScraper,
}

def register_source(name: str, scraper_class: Type[BaseScraper]):
    """
    Register a new scraping source
    
    Args:
        name: Source identifier
        scraper_class: Scraper class implementation
    """
    SOURCES[name] = scraper_class

def get_source(name: str, **kwargs) -> BaseScraper:
    """
    Get a scraper instance for a source
    
    Args:
        name: Source identifier
        **kwargs: Arguments to pass to scraper constructor
        
    Returns:
        Scraper instance
        
    Raises:
        ValueError: If source is not registered
    """
    if name not in SOURCES:
        raise ValueError(f"Unknown source: {name}. Available sources: {list(SOURCES.keys())}")
    
    return SOURCES[name](**kwargs)

def list_sources() -> List[str]:
    """
    List all registered sources
    
    Returns:
        List of source identifiers
    """
    return list(SOURCES.keys())

def get_source_info(name: str) -> Dict:
    """
    Get information about a source
    
    Args:
        name: Source identifier
        
    Returns:
        Source information dictionary
    """
    scraper = get_source(name)
    return scraper.get_source_info()