"""
Field mapping for TDLR project data
"""

from typing import Dict, List

# Field mapping from TDLR fields to standard project schema
FIELD_MAPPING: Dict[str, List[str]] = {
    'project_number': ['project_number'],
    'project_name': ['project_name'],
    'facility_name': ['facility_name'],
    'location_address': ['location_address'],
    'city': ['city'],
    'county': ['county'],
    'start_date': ['start_date'],
    'completion_date': ['completion_date'],
    'estimated_cost': ['estimated_cost'],
    'type_of_work': ['type_of_work'],
    'type_of_funds': ['type_of_funds'],
    'scope_of_work': ['scope_of_work'],
    'square_footage': ['square_footage'],
    'project_status': ['project_status'],
    'owner_name': ['owner_name'],
    'owner_address': ['owner_address'],
    'owner_phone': ['owner_phone'],
    'design_firm_name': ['design_firm_name'],
    'design_firm_address': ['design_firm_address'],
    'ras_name': ['ras_name'],
    'ras_number': ['ras_number'],
    'registration_date': ['registration_date']
}