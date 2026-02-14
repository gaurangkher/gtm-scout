"""
Command-line interface for TDLR scraper
"""

import argparse
import asyncio
import logging
from typing import List
from .core.scraper_manager import ScraperManager
from .sources.source_registry import list_sources, get_source_info

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def format_project(project: dict) -> str:
    """Format a project for display"""
    return f"""📋 {project.get('project_number', 'N/A')}
   Name: {project.get('project_name', 'N/A')}
   Facility: {project.get('facility_name', 'N/A')}
   Location: {project.get('city', 'N/A')}, {project.get('county', 'N/A')}
   Square Footage: {project.get('square_footage', 'N/A'):,} sqft
   Cost: ${project.get('estimated_cost', 0):,.2f}
   Status: {project.get('project_status', 'N/A')}
   Start: {project.get('start_date', 'N/A')}"""


async def scrape_command(args):
    """Handle scrape command"""
    manager = ScraperManager(args.db_path)
    
    if args.source == 'all':
        logger.info("Scraping from all sources")
        results = await manager.scrape_all_sources(
            limit_per_source=args.max_records or 100,
            db_path=args.db_path
        )
        print(f"\n📊 Scraping Results:")
        for source, count in results.items():
            print(f"  {source}: {count} projects")
    else:
        logger.info(f"Scraping from {args.source}")
        count = await manager.scrape_source(
            args.source,
            limit=args.max_records or 100,
            db_path=args.db_path
        )
        print(f"\n✅ Scraped {count} projects from {args.source}")


def search_command(args):
    """Handle search command"""
    manager = ScraperManager(args.db_path)
    results = manager.search_projects(args.query)
    
    print(f"\n🔍 Found {len(results)} matching projects:\n")
    for project in results:
        print(format_project(project))
        print()


def list_sources_command(args):
    """Handle list-sources command"""
    sources = list_sources()
    print(f"\n📚 Available Sources ({len(sources)}):")
    for source in sources:
        info = get_source_info(source)
        print(f"  {source}: {info.get('description', 'No description')}")


def main():
    parser = argparse.ArgumentParser(description='Multi-source construction project scraper')
    parser.add_argument('--db-path', type=str, default='projects.db', help='Database path')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Scrape command
    scrape_parser = subparsers.add_parser('scrape', help='Scrape projects from sources')
    scrape_parser.add_argument('--source', type=str, default='tdlr', 
                              help='Source to scrape (use "all" for all sources)')
    scrape_parser.add_argument('--max-records', type=int, 
                              help='Maximum records to fetch')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search local database')
    search_parser.add_argument('query', help='Search query')
    
    # List sources command
    list_parser = subparsers.add_parser('list-sources', help='List available sources')
    
    args = parser.parse_args()
    
    if args.command == 'scrape':
        asyncio.run(scrape_command(args))
    elif args.command == 'search':
        search_command(args)
    elif args.command == 'list-sources':
        list_sources_command(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()