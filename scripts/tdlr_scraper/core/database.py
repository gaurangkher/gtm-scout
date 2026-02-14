"""
Database operations for project storage
"""

import sqlite3
from typing import List, Optional, Dict, Any
from .models import Project
import logging

logger = logging.getLogger(__name__)


class ProjectDatabase:
    """Database operations for construction projects"""
    
    def __init__(self, db_path: str = "projects.db"):
        self.db_path = db_path
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
        logger.info(f"Database initialized at {self.db_path}")
    
    def save_project(self, project: Project) -> bool:
        """
        Save a project to the database
        
        Args:
            project: Project instance to save
            
        Returns:
            True if saved successfully, False if duplicate
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
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
                project.project_id,
                project.project_number,
                project.project_name,
                project.facility_name,
                project.location_address,
                project.city,
                project.county,
                project.start_date,
                project.completion_date,
                project.estimated_cost,
                project.type_of_work,
                project.type_of_funds,
                project.scope_of_work,
                project.square_footage,
                project.project_status,
                project.owner_name,
                project.owner_address,
                project.owner_phone,
                project.design_firm_name,
                project.design_firm_address,
                project.ras_name,
                project.ras_number,
                project.registration_date,
                project.date_scraped
            ))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            # Duplicate project
            return False
        finally:
            conn.close()
    
    def save_projects(self, projects: List[Project]) -> int:
        """
        Save multiple projects to the database
        
        Args:
            projects: List of Project instances to save
            
        Returns:
            Number of projects successfully saved
        """
        saved_count = 0
        for project in projects:
            if self.save_project(project):
                saved_count += 1
        return saved_count
    
    def search_projects(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for projects matching query
        
        Args:
            query: Search term to match against project fields
            
        Returns:
            List of matching projects as dictionaries
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
    
    def get_project_count(self) -> int:
        """Get total number of projects in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM projects')
        count = cursor.fetchone()[0]
        conn.close()
        return count