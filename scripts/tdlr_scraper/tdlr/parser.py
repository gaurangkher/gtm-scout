"""
TDLR project parser implementation
"""

import re
from typing import List, Dict, Optional, Any
from bs4 import BeautifulSoup
from ..sources.base import BaseParser
from ..core.models import Project
from .mapper import FIELD_MAPPING


class TDLRParser(BaseParser):
    """Parse TDLR project data"""
    
    async def parse_project_list(self, response_data: Dict) -> List[str]:
        """
        Parse project numbers from TDLR search response
        
        Args:
            response_data: Raw response data from TDLR search endpoint
            
        Returns:
            List of project numbers
        """
        projects = response_data.get('data', [])
        return [project.get('ProjectNumber') for project in projects if project.get('ProjectNumber')]
    
    async def parse_project_details(self, html_content: str, project_number: str) -> Project:
        """
        Parse detailed project information from TDLR project detail page
        
        Args:
            html_content: Raw HTML content of project detail page
            project_number: TDLR project number
            
        Returns:
            Project instance with parsed data
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
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
        raw_data = {
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
        if raw_data['location_address']:
            # Try to find city in the address
            addr_parts = raw_data['location_address'].split(',')
            if len(addr_parts) >= 2:
                # City is usually before the state
                city_candidate = addr_parts[-2].strip()
                # Remove street numbers and common street names
                city_words = [w for w in city_candidate.split() if not w.isdigit() and w not in ['St', 'Street', 'Ave', 'Avenue', 'Rd', 'Road']]
                if city_words:
                    raw_data['city'] = ' '.join(city_words)
        
        # Parse estimated cost (format: "$500,000")
        cost_text = raw_data['estimated_cost']
        if cost_text:
            cost_match = re.search(r'\$?([\d,]+)', cost_text)
            if cost_match:
                try:
                    raw_data['estimated_cost'] = float(cost_match.group(1).replace(',', ''))
                except ValueError:
                    pass
        
        # Parse square footage (format: "3,500 ft 2" or "3,500")
        sqft_text = raw_data['square_footage']
        if sqft_text:
            sqft_match = re.search(r'([\d,]+)', sqft_text)
            if sqft_match:
                try:
                    raw_data['square_footage'] = int(sqft_match.group(1).replace(',', ''))
                except ValueError:
                    pass
        
        # Map fields to standard schema
        mapped_data = {}
        for standard_field, source_fields in FIELD_MAPPING.items():
            # For TDLR, the field names are the same, so we just copy the values
            if standard_field in raw_data and raw_data[standard_field] is not None:
                mapped_data[standard_field] = raw_data[standard_field]
        
        # Create project instance
        project = Project.from_dict(mapped_data)
        project.date_scraped = __import__('datetime').datetime.now().isoformat()
        
        return project