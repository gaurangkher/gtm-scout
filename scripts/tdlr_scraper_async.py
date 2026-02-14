#!/usr/bin/env python3
"""
TDLR Project Scraper - Async version for faster scraping
"""

import sqlite3
import asyncio
import aiohttp
import time
import argparse
from datetime import datetime
from typing import Optional, List, Dict
import json
from bs4 import BeautifulSoup
import re


class AsyncTDLRScraper:
    """Async scraper for TDLR TABS construction projects"""
    
    def __init__(self, db_path: str = "tdlr_projects.db"):
        self.db_path = db_path
        self.api_url = "https://www.tdlr.texas.gov/TABS/Search/SearchProjects"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
            'Referer': 'https://www.tdlr.texas.gov/TABS/search'
        }
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database with projects table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT UNIQUE,
                project_number TEXT,
                project_name TEXT,
                facility_name TEXT,
                location_address TEXT,
                city TEXT,
                county TEXT,
                start_date TEXT,
                completion_date TEXT,
                estimated_cost REAL,
                type_of_work TEXT,
                type_of_funds TEXT,
                scope_of_work TEXT,
                square_footage INTEGER,
                project_status TEXT,
                owner_name TEXT,
                owner_address TEXT,
                owner_phone TEXT,
                design_firm_name TEXT,
                design_firm_address TEXT,
                ras_name TEXT,
                ras_number TEXT,
                registration_date TEXT,
                date_scraped TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        print(f"✅ Database initialized at {self.db_path}")
    
    async def _parse_project_details(self, session: aiohttp.ClientSession, project_number: str) -> Optional[Dict]:
        """
        Fetch and parse detailed project information from project detail page (async)
        
        Args:
            session: aiohttp client session
            project_number: TDLR project number (e.g., TABS2026012633)
            
        Returns:
            Dictionary of project details or None if fetch fails
        """
        detail_url = f"https://www.tdlr.texas.gov/TABS/Search/Project/{project_number}"
        
        try:
            async with session.get(detail_url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status != 200:
                    print(f"  ⚠️  Failed to fetch details for {project_number} (HTTP {response.status})")
                    return None
                
                text = await response.text()
                soup = BeautifulSoup(text, 'html.parser')
                
                # Helper function to extract text from label
                def get_field_value(label_text: str) -> Optional[str]:
                    # Look for the label text and get the next text content
                    text_content = soup.get_text()
                    lines = [line.strip() for line in text_content.split('\n') if line.strip()]
                    
                    for i, line in enumerate(lines):
                        if label_text in line:
                            # Get the value - it's usually on the same line or next line
                            if label_text == line and i + 1 < len(lines):
                                return lines[i + 1]
                            else:
                                # Extract value after the label
                                value = line.replace(label_text, '').strip()
                                if value:
                                    return value
                    return None
                
                # Extract all fields
                details = {
                    'project_number': project_number,
                    'project_name': get_field_value('Project Name:'),
                    'facility_name': get_field_value('Facility Name:'),
                    'location_address': get_field_value('Location Address:'),
                    'city': None,  # Will extract from address
                    'county': get_field_value('Location County:'),
                    'start_date': get_field_value('Start Date:'),
                    'completion_date': get_field_value('Completion Date:'),
                    'estimated_cost': None,  # Will parse from text
                    'type_of_work': get_field_value('Type of Work:'),
                    'type_of_funds': get_field_value('Type of Funds:'),
                    'scope_of_work': get_field_value('Scope of Work:'),
                    'square_footage': None,  # Will parse from text
                    'project_status': get_field_value('Current Status:'),
                    'owner_name': get_field_value('Owner Name:'),
                    'owner_address': get_field_value('Owner Address:'),
                    'owner_phone': get_field_value('Owner Phone:'),
                    'design_firm_name': get_field_value('Design Firm Name:'),
                    'design_firm_address': get_field_value('Design Firm Address:'),
                    'ras_name': get_field_value('RAS Name:'),
                    'ras_number': get_field_value('RAS #:'),
                    'registration_date': get_field_value('Registration Date:')
                }
                
                # Extract city from location address (format: "Address\nCity, State Zip")
                if details['location_address']:
                    # Try to find city in the address
                    addr_parts = details['location_address'].split(',')
                    if len(addr_parts) >= 2:
                        # City is usually before the state
                        city_candidate = addr_parts[-2].strip()
                        # Remove street numbers and common street names
                        city_words = [w for w in city_candidate.split() if not w.isdigit() and w not in ['St', 'Street', 'Ave', 'Avenue', 'Rd', 'Road']]
                        if city_words:
                            details['city'] = ' '.join(city_words)
                
                # Parse estimated cost (format: "$500,000")
                cost_text = get_field_value('Estimated Cost:')
                if cost_text:
                    cost_match = re.search(r'\$?([\d,]+)', cost_text)
                    if cost_match:
                        try:
                            details['estimated_cost'] = float(cost_match.group(1).replace(',', ''))
                        except ValueError:
                            pass
                
                # Parse square footage (format: "3,500 ft 2" or "3,500")
                sqft_text = get_field_value('Square Footage:')
                if sqft_text:
                    sqft_match = re.search(r'([\d,]+)', sqft_text)
                    if sqft_match:
                        try:
                            details['square_footage'] = int(sqft_match.group(1).replace(',', ''))
                        except ValueError:
                            pass
                
                return details
                
        except asyncio.TimeoutError:
            print(f"  ⚠️  Timeout fetching details for {project_number}")
            return None
        except Exception as e:
            print(f"  ❌ Error parsing {project_number}: {e}")
            return None
    
    async def _fetch_project_batch(self, session: aiohttp.ClientSession, project_numbers: List[str]) -> List[Dict]:
        """
        Fetch details for a batch of projects concurrently
        
        Args:
            session: aiohttp client session
            project_numbers: List of project numbers to fetch
            
        Returns:
            List of project details
        """
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
                print(f"  ❌ Task exception: {result}")
            elif result is not None:
                valid_results.append(result)
        
        return valid_results
    
    async def scrape(self, batch_size: int = 15, delay: float = 0.5, max_records: Optional[int] = None):
        """
        Scrape projects from TDLR API with full project details (async)
        
        Args:
            batch_size: Number of records per request (max 15)
            delay: Delay in seconds between batches
            max_records: Maximum number of records to fetch (None = all)
        """
        batch_size = min(batch_size, 15)  # API limit
        current_page = 1
        total_scraped = 0
        
        print(f"🚀 Starting async scrape: batch_size={batch_size}, delay={delay}s, max_records={max_records or 'all'}")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create aiohttp session
        timeout = aiohttp.ClientTimeout(total=30)
        connector = aiohttp.TCPConnector(limit=20, limit_per_host=10)
        
        async with aiohttp.ClientSession(headers=self.headers, timeout=timeout, connector=connector) as session:
            while True:
                if max_records and total_scraped >= max_records:
                    print(f"✅ Reached max_records limit: {max_records}")
                    break
                
                # Calculate how many records to fetch in this batch
                records_to_fetch = batch_size
                if max_records:
                    records_to_fetch = min(batch_size, max_records - total_scraped)
                
                print(f"\n📄 Fetching page {current_page} ({records_to_fetch} records)...")
                
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
                            print(f"❌ HTTP {response.status}: {await response.text()}")
                            break
                        
                        data = await response.json()
                        
                        # Extract projects from response
                        projects = data.get('data', [])
                        total_available = data.get('totalRecords', 0)
                        
                        if not projects:
                            print("✅ No more projects to fetch")
                            break
                        
                        # Extract project numbers for batch processing
                        project_numbers = [project.get('ProjectNumber') for project in projects if project.get('ProjectNumber')]
                        
                        # Fetch detailed information for all projects in batch concurrently
                        print(f"  🔍 Fetching details for {len(project_numbers)} projects concurrently...")
                        start_time = time.time()
                        
                        project_details = await self._fetch_project_batch(session, project_numbers)
                        
                        elapsed = time.time() - start_time
                        print(f"  ⏱️  Batch completed in {elapsed:.2f} seconds")
                        
                        # Save all project details to database
                        inserted = 0
                        duplicates = 0
                        
                        for details in project_details:
                            if not details:
                                continue
                            
                            try:
                                cursor.execute('''
                                    INSERT INTO projects (
                                        project_id, project_number, project_name, facility_name,
                                        location_address, city, county, start_date, completion_date,
                                        estimated_cost, type_of_work, type_of_funds, scope_of_work,
                                        square_footage, project_status, owner_name, owner_address,
                                        owner_phone, design_firm_name, design_firm_address,
                                        ras_name, ras_number, registration_date, date_scraped
                                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                ''', (
                                    None,  # project_id not available in search results
                                    details['project_number'],
                                    details['project_name'],
                                    details['facility_name'],
                                    details['location_address'],
                                    details['city'],
                                    details['county'],
                                    details['start_date'],
                                    details['completion_date'],
                                    details['estimated_cost'],
                                    details['type_of_work'],
                                    details['type_of_funds'],
                                    details['scope_of_work'],
                                    details['square_footage'],
                                    details['project_status'],
                                    details['owner_name'],
                                    details['owner_address'],
                                    details['owner_phone'],
                                    details['design_firm_name'],
                                    details['design_firm_address'],
                                    details['ras_name'],
                                    details['ras_number'],
                                    details['registration_date'],
                                    datetime.now().isoformat()
                                ))
                                inserted += 1
                                print(f"  ✅ Saved {details['project_number']}")
                            except sqlite3.IntegrityError:
                                duplicates += 1
                                print(f"  ⚠️  Duplicate: {details['project_number']}")
                        
                        conn.commit()
                        total_scraped += inserted
                        
                        print(f"  📊 Inserted: {inserted}, Duplicates: {duplicates}, Total: {total_scraped}/{total_available}")
                        
                        # Check if we should continue
                        if len(projects) < records_to_fetch:
                            print("✅ Reached end of available data")
                            break
                        
                        if max_records and total_scraped >= max_records:
                            break
                        
                        # Rate limiting between pages
                        current_page += 1
                        await asyncio.sleep(delay)
                        
                except asyncio.TimeoutError:
                    print(f"❌ Timeout fetching page {current_page}")
                    break
                except Exception as e:
                    print(f"❌ Error: {e}")
                    import traceback
                    traceback.print_exc()
                    break
        
        conn.close()
        print(f"\n🎉 Async scraping complete! Total records: {total_scraped}")


class ProjectSearcher:
    """Search local TDLR projects database"""
    
    def __init__(self, db_path: str = "tdlr_projects.db"):
        self.db_path = db_path
    
    def search(self, query: str) -> List[Dict]:
        """
        Search for projects matching query
        
        Args:
            query: Search term to match against project fields
            
        Returns:
            List of matching projects
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        search_pattern = f"%{query}%"
        
        cursor.execute('''
            SELECT * FROM projects
            WHERE project_number LIKE ?
               OR project_name LIKE ?
               OR facility_name LIKE ?
               OR city LIKE ?
               OR county LIKE ?
            ORDER BY registration_date DESC
            LIMIT 50
        ''', (search_pattern, search_pattern, search_pattern, search_pattern, search_pattern))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return results


async def main_async():
    parser = argparse.ArgumentParser(description='TDLR Project Scraper (Async)')
    parser.add_argument('--scrape', action='store_true', help='Scrape projects from TDLR')
    parser.add_argument('--search', type=str, help='Search local database')
    parser.add_argument('--db-path', type=str, default='tdlr_projects.db', help='Database path')
    parser.add_argument('--batch-size', type=int, default=15, help='Records per request (max 15)')
    parser.add_argument('--delay', type=float, default=0.5, help='Delay between batches (seconds)')
    parser.add_argument('--max-records', type=int, help='Maximum records to fetch')
    
    args = parser.parse_args()
    
    if args.scrape:
        scraper = AsyncTDLRScraper(db_path=args.db_path)
        await scraper.scrape(
            batch_size=args.batch_size,
            delay=args.delay,
            max_records=args.max_records
        )
    elif args.search:
        searcher = ProjectSearcher(db_path=args.db_path)
        results = searcher.search(args.search)
        
        print(f"\n🔍 Found {len(results)} matching projects:\n")
        for project in results:
            print(f"📋 {project['project_number']}")
            print(f"   Name: {project['project_name']}")
            print(f"   Facility: {project['facility_name']}")
            print(f"   Location: {project['city']}, {project['county']}")
            print(f"   Square Footage: {project['square_footage']:,} sqft" if project['square_footage'] else "   Square Footage: N/A")
            print(f"   Cost: ${project['estimated_cost']:,.2f}" if project['estimated_cost'] else "   Cost: N/A")
            print(f"   Status: {project['project_status']}")
            print(f"   Start: {project['start_date']}\n")
    else:
        parser.print_help()


def main():
    # Run the async main function
    asyncio.run(main_async())


if __name__ == '__main__':
    main()