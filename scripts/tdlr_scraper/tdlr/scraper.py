"""
TDLR project scraper implementation
"""

import asyncio
import aiohttp
from typing import List, Optional
from ..sources.base import BaseScraper
from ..core.models import Project
from .parser import TDLRParser
import logging

logger = logging.getLogger(__name__)


class TDLRScraper(BaseScraper):
    """Scrape projects from TDLR TABS construction projects"""
    
    def __init__(self, db_path: str = "tdlr_projects.db"):
        super().__init__("tdlr")
        self.db_path = db_path
        self.api_url = "https://www.tdlr.texas.gov/TABS/Search/SearchProjects"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
            'Referer': 'https://www.tdlr.texas.gov/TABS/search'
        }
        self.parser = TDLRParser()
    
    def get_source_info(self) -> dict:
        """Get information about this source"""
        return {
            'name': 'TDLR',
            'description': 'Texas Department of Licensing and Regulation construction projects',
            'url': 'https://www.tdlr.texas.gov/TABS/search',
            'fields_available': [
                'project_number', 'project_name', 'facility_name', 'location_address',
                'city', 'county', 'start_date', 'completion_date', 'estimated_cost',
                'type_of_work', 'type_of_funds', 'scope_of_work', 'square_footage',
                'project_status', 'owner_name', 'owner_address', 'owner_phone',
                'design_firm_name', 'design_firm_address', 'ras_name', 'ras_number',
                'registration_date'
            ]
        }
    
    async def scrape_projects(self, limit: int = 100) -> List[Project]:
        """
        Scrape projects from TDLR API with full project details (async)
        
        Args:
            limit: Maximum number of projects to scrape
            
        Returns:
            List of Project instances
        """
        batch_size = min(15, limit)  # API limit
        current_page = 1
        total_scraped = 0
        all_projects = []
        
        logger.info(f"Starting TDLR scrape: limit={limit}")
        
        # Create aiohttp session
        timeout = aiohttp.ClientTimeout(total=30)
        connector = aiohttp.TCPConnector(limit=20, limit_per_host=10)
        
        async with aiohttp.ClientSession(headers=self.headers, timeout=timeout, connector=connector) as session:
            while total_scraped < limit:
                records_to_fetch = min(batch_size, limit - total_scraped)
                
                logger.info(f"Fetching page {current_page} ({records_to_fetch} records)...")
                
                try:
                    # API payload for pagination
                    payload = {
                        "pageNumber": current_page,
                        "pageSize": records_to_fetch,
                        "sortColumn": "ProjectCreatedOn",
                        "sortDirection": "desc",
                        "filters": {}
                    }
                    
                    async with session.post(self.api_url, json=payload, timeout=timeout) as response:
                        if response.status != 200:
                            logger.error(f"HTTP {response.status}: {await response.text()}")
                            break
                        
                        data = await response.json()
                        
                        # Extract projects from response
                        projects = data.get('data', [])
                        
                        if not projects:
                            logger.info("No more projects to fetch")
                            break
                        
                        # Extract project numbers for batch processing
                        project_numbers = await self.parser.parse_project_list(data)
                        
                        # Fetch detailed information for all projects in batch concurrently
                        logger.info(f"Fetching details for {len(project_numbers)} projects concurrently...")
                        
                        # Create tasks for all projects in the batch
                        tasks = [
                            self._parse_project_details(session, project_number) 
                            for project_number in project_numbers
                        ]
                        
                        # Execute all tasks concurrently with a semaphore to limit concurrency
                        semaphore = asyncio.Semaphore(10)  # Limit to 10 concurrent requests
                        
                        async def sem_task(task):
                            async with semaphore:
                                return await task
                        
                        results = await asyncio.gather(*[sem_task(task) for task in tasks], return_exceptions=True)
                        
                        # Filter out exceptions and None values
                        valid_results = []
                        for result in results:
                            if isinstance(result, Exception):
                                logger.error(f"Task exception: {result}")
                            elif result is not None:
                                valid_results.append(result)
                        
                        # Add valid results to our collection
                        all_projects.extend(valid_results)
                        total_scraped += len(valid_results)
                        
                        logger.info(f"Batch completed: {len(valid_results)} projects, total: {total_scraped}")
                        
                        # Check if we should continue
                        if len(projects) < records_to_fetch:
                            logger.info("Reached end of available data")
                            break
                        
                        # Rate limiting between pages
                        current_page += 1
                        await asyncio.sleep(0.5)
                        
                except asyncio.TimeoutError:
                    logger.error(f"Timeout fetching page {current_page}")
                    break
                except Exception as e:
                    logger.error(f"Error: {e}")
                    import traceback
                    traceback.print_exc()
                    break
        
        logger.info(f"TDLR scraping complete! Total projects: {len(all_projects)}")
        return all_projects[:limit]  # Ensure we don't exceed the limit
    
    async def _parse_project_details(self, session: aiohttp.ClientSession, project_number: str) -> Optional[Project]:
        """
        Fetch and parse detailed project information from project detail page (async)
        
        Args:
            session: aiohttp client session
            project_number: TDLR project number (e.g., TABS2026012633)
            
        Returns:
            Project instance or None if fetch fails
        """
        detail_url = f"https://www.tdlr.texas.gov/TABS/Search/Project/{project_number}"
        
        try:
            async with session.get(detail_url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status != 200:
                    logger.warning(f"Failed to fetch details for {project_number} (HTTP {response.status})")
                    return None
                
                text = await response.text()
                return await self.parser.parse_project_details(text, project_number)
                
        except asyncio.TimeoutError:
            logger.warning(f"Timeout fetching details for {project_number}")
            return None
        except Exception as e:
            logger.error(f"Error parsing {project_number}: {e}")
            return None