#!/usr/bin/env python3
"""
SQLite Database Query Script for Construction Projects

Queries a local SQLite database of construction projects using requirements.md filters.
"""

import sqlite3
import json
import sys
import os
from datetime import datetime
from pathlib import Path


def parse_requirements(requirements_path):
    """Parse requirements.md file into filter criteria."""
    
    if not os.path.exists(requirements_path):
        raise FileNotFoundError(f"Requirements file not found: {requirements_path}")
    
    with open(requirements_path, 'r') as f:
        content = f.read()
    
    # Parse requirements (simplified parsing logic)
    requirements = {
        'start_date_after': None,
        'location': None,
        'min_square_footage': None,
        'max_square_footage': None,
        'project_types': [],
        'min_cost': None,
        'max_cost': None,
        'disqualifiers': [],
        'limit': 20
    }
    
    lines = content.split('\n')
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Handle both "- **Field**:" format and "**Requirement**:" format
        if line.startswith('- **Start Date**:') or ('start date' in line.lower() and '**requirement**' in lines[i-1].lower() if i > 0 else False):
            # Extract date info
            if 'after' in line.lower() or 'After' in line.lower():
                # Parse "After March 2026" or similar
                if 'march 2026' in line.lower():
                    requirements['start_date_after'] = '2026-03-01'
                elif 'april 2026' in line.lower() or 'q2 2026' in line.lower():
                    requirements['start_date_after'] = '2026-04-01'
                # Add more parsing as needed
        
        elif line.startswith('- **Location**:') or ('location' in line.lower() and '**requirement**' in lines[i-1].lower() if i > 0 else False):
            # Extract location
            if ':' in line:
                location = line.split(':', 1)[1].strip()
                requirements['location'] = location
        
        elif line.startswith('- **Square Footage**:') or 'square footage' in line.lower():
            # Parse "100,000+ sq ft" or "50,000-150,000 sq ft" or "More than 100,000 sq ft"
            if '+' in line or 'more than' in line.lower():
                # Extract number
                import re
                numbers = re.findall(r'[\d,]+', line)
                if numbers:
                    requirements['min_square_footage'] = int(numbers[0].replace(',', ''))
            elif '-' in line and 'sq' in line.lower():
                import re
                numbers = re.findall(r'[\d,]+', line)
                if len(numbers) >= 2:
                    requirements['min_square_footage'] = int(numbers[0].replace(',', ''))
                    requirements['max_square_footage'] = int(numbers[1].replace(',', ''))
        
        elif line.startswith('- **Project Type**:') or ('type of work' in line.lower() and '**requirement**' in lines[i-1].lower() if i > 0 else False):
            if ':' in line:
                types = line.split(':', 1)[1].strip()
                if types.lower() not in ['any', 'all', 'all types', 'all project types', 'no restrictions']:
                    requirements['project_types'] = [t.strip() for t in types.split(',')]
        
        elif line.startswith('- **Estimated Cost**:') or ('estimated cost' in line.lower() and '**requirement**' in lines[i-1].lower() if i > 0 else False):
            if ':' in line:
                cost = line.split(':', 1)[1].strip()
                if cost.lower() not in ['any', 'no restrictions', 'no minimum or maximum', 'all budget ranges']:
                    # Parse "$5M - $50M" or "$2M+"
                    import re
                    numbers = re.findall(r'\$?(\d+)M?', cost)
                    if '-' in cost and len(numbers) >= 2:
                        requirements['min_cost'] = int(numbers[0]) * 1000000
                        requirements['max_cost'] = int(numbers[1]) * 1000000
                    elif '+' in cost and numbers:
                        requirements['min_cost'] = int(numbers[0]) * 1000000
        
        elif line.startswith('- **Disqualifiers**:') or (line.startswith('## Disqualifiers') and i + 1 < len(lines)):
            # Check next line for content
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line and next_line.lower() not in ['none', 'n/a', 'none specified', '- none']:
                    requirements['disqualifiers'] = [d.strip().lower() for d in next_line.split(',')]
        
        elif line.startswith('- **Lead Limit**:') or line.startswith('- **Number of Results**:'):
            if ':' in line:
                limit_text = line.split(':', 1)[1].strip()
                import re
                numbers = re.findall(r'\d+', limit_text)
                if numbers:
                    requirements['limit'] = int(numbers[0])
    
    return requirements


def build_query(requirements):
    """Build SQL query based on requirements."""
    
    query = "SELECT * FROM projects WHERE 1=1"
    params = []
    
    # Start date filter
    if requirements['start_date_after']:
        query += " AND start_date >= ?"
        params.append(requirements['start_date_after'])
    
    # Location filter (case-insensitive LIKE)
    if requirements['location']:
        location = requirements['location']
        if location.lower() not in ['any', 'anywhere']:
            query += " AND location LIKE ?"
            params.append(f"%{location}%")
    
    # Square footage filters
    if requirements['min_square_footage']:
        query += " AND square_footage >= ?"
        params.append(requirements['min_square_footage'])
    
    if requirements['max_square_footage']:
        query += " AND square_footage <= ?"
        params.append(requirements['max_square_footage'])
    
    # Project type filter
    if requirements['project_types']:
        type_conditions = " OR ".join(["project_type LIKE ?" for _ in requirements['project_types']])
        query += f" AND ({type_conditions})"
        params.extend([f"%{pt}%" for pt in requirements['project_types']])
    
    # Cost filters (extract numeric value from "$XXM" format)
    if requirements['min_cost']:
        query += " AND CAST(REPLACE(REPLACE(estimated_cost, '$', ''), 'M', '000000') AS INTEGER) >= ?"
        params.append(requirements['min_cost'])
    
    if requirements['max_cost']:
        query += " AND CAST(REPLACE(REPLACE(estimated_cost, '$', ''), 'M', '000000') AS INTEGER) <= ?"
        params.append(requirements['max_cost'])
    
    # Disqualifiers
    if requirements['disqualifiers']:
        for disq in requirements['disqualifiers']:
            query += " AND LOWER(project_type) NOT LIKE ?"
            params.append(f"%{disq}%")
    
    # Order by start date (earliest first)
    query += " ORDER BY start_date ASC"
    
    # Limit results
    if requirements['limit']:
        query += " LIMIT ?"
        params.append(requirements['limit'])
    
    return query, params


def query_projects(db_path, requirements):
    """Query the SQLite database with requirements filters."""
    
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found: {db_path}")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Access columns by name
    cursor = conn.cursor()
    
    query, params = build_query(requirements)
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    # Convert to list of dicts
    projects = []
    for row in rows:
        projects.append({
            'project_name': row['project_name'],
            'location': row['location'],
            'county': row['county'],
            'project_type': row['project_type'],
            'square_footage': row['square_footage'],
            'estimated_cost': row['estimated_cost'],
            'start_date': row['start_date'],
            'completion_date': row['completion_date'],
            'owner': row['owner'],
            'architect': row['architect'],
            'general_contractor': row['general_contractor'],
            'project_stage': row['project_stage'],
            'description': row['description']
        })
    
    conn.close()
    
    return projects


def main():
    if len(sys.argv) < 2:
        print("Usage: python query_db.py <requirements.md> [database.db]", file=sys.stderr)
        print("  If database.db is not provided, defaults to 'projects.db'", file=sys.stderr)
        sys.exit(1)
    
    requirements_path = sys.argv[1]
    db_path = sys.argv[2] if len(sys.argv) > 2 else 'projects.db'
    
    try:
        # Parse requirements
        requirements = parse_requirements(requirements_path)
        
        # Query database
        projects = query_projects(db_path, requirements)
        
        # Output results
        result = {
            "timestamp": datetime.now().isoformat(),
            "database": db_path,
            "requirements": requirements_path,
            "count": len(projects),
            "projects": projects
        }
        
        print(json.dumps(result, indent=2))
        
    except FileNotFoundError as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": f"Query failed: {str(e)}"}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
