#!/usr/bin/env python3
"""
TDLR Project Scraper - Scrapes construction project data from Texas TDLR TABS system
"""

import sqlite3
import requests
import time
import argparse
from datetime import datetime
from typing import Optional, List, Dict
import json


class TDLRScraper:
    """Scraper for TDLR TABS construction projects"""
    
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
                project_created_on TEXT,
                project_status TEXT,
                facility_name TEXT,
                city TEXT,
                county TEXT,
                type_of_work TEXT,
                estimated_cost REAL,
                data_version_id TEXT,
                estimated_start_date TEXT,
                estimated_end_date TEXT,
                date_scraped TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        print(f"✅ Database initialized at {self.db_path}")
    
    def scrape(self, batch_size: int = 15, delay: float = 1.0, max_records: Optional[int] = None):
        """
        Scrape projects from TDLR API
        
        Args:
            batch_size: Number of records per request (max 15)
            delay: Delay in seconds between requests
            max_records: Maximum number of records to fetch (None = all)
        """
        batch_size = min(batch_size, 15)  # API limit
        current_page = 1
        total_scraped = 0
        
        print(f"🚀 Starting scrape: batch_size={batch_size}, delay={delay}s, max_records={max_records or 'all'}")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
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
                
                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload,
                    timeout=30
                )
                
                if response.status_code != 200:
                    print(f"❌ HTTP {response.status_code}: {response.text}")
                    break
                
                data = response.json()
                
                # Extract projects from response
                projects = data.get('data', [])
                total_available = data.get('totalRecords', 0)
                
                if not projects:
                    print("✅ No more projects to fetch")
                    break
                
                # Insert projects into database
                inserted = 0
                duplicates = 0
                
                for project in projects:
                    try:
                        cursor.execute('''
                            INSERT INTO projects (
                                project_id, project_number, project_name,
                                project_created_on, project_status, facility_name,
                                city, county, type_of_work, estimated_cost,
                                data_version_id, estimated_start_date,
                                estimated_end_date, date_scraped
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            project.get('ProjectId'),
                            project.get('ProjectNumber'),
                            project.get('ProjectName'),
                            project.get('ProjectCreatedOn'),
                            project.get('ProjectStatus'),
                            project.get('FacilityName'),
                            project.get('City'),
                            project.get('County'),
                            project.get('TypeOfWork'),
                            project.get('EstimatedCost'),
                            project.get('DataVersionId'),
                            project.get('EstimatedStartDate'),
                            project.get('EstimatedEndDate'),
                            datetime.now().isoformat()
                        ))
                        inserted += 1
                    except sqlite3.IntegrityError:
                        duplicates += 1
                
                conn.commit()
                total_scraped += inserted
                
                print(f"  ✅ Inserted: {inserted}, Duplicates: {duplicates}, Total: {total_scraped}/{total_available}")
                
                # Check if we should continue
                if len(projects) < records_to_fetch:
                    print("✅ Reached end of available data")
                    break
                
                if max_records and total_scraped >= max_records:
                    break
                
                # Rate limiting
                current_page += 1
                time.sleep(delay)
                
            except requests.RequestException as e:
                print(f"❌ Network error: {e}")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                break
        
        conn.close()
        print(f"\n🎉 Scraping complete! Total records: {total_scraped}")


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
            ORDER BY project_created_on DESC
            LIMIT 50
        ''', (search_pattern, search_pattern, search_pattern, search_pattern, search_pattern))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return results


def main():
    parser = argparse.ArgumentParser(description='TDLR Project Scraper')
    parser.add_argument('--scrape', action='store_true', help='Scrape projects from TDLR')
    parser.add_argument('--search', type=str, help='Search local database')
    parser.add_argument('--db-path', type=str, default='tdlr_projects.db', help='Database path')
    parser.add_argument('--batch-size', type=int, default=15, help='Records per request (max 15)')
    parser.add_argument('--delay', type=float, default=1.0, help='Delay between requests (seconds)')
    parser.add_argument('--max-records', type=int, help='Maximum records to fetch')
    
    args = parser.parse_args()
    
    if args.scrape:
        scraper = TDLRScraper(db_path=args.db_path)
        scraper.scrape(
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
            print(f"   Cost: ${project['estimated_cost']:,.2f}" if project['estimated_cost'] else "   Cost: N/A")
            print(f"   Created: {project['project_created_on']}\n")
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
