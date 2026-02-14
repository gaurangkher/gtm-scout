"""
Data models for construction projects
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime


@dataclass
class Project:
    """Standard project data model"""
    
    # Core identifiers
    project_id: Optional[str] = None
    project_number: Optional[str] = None
    project_name: Optional[str] = None
    facility_name: Optional[str] = None
    
    # Location information
    location_address: Optional[str] = None
    city: Optional[str] = None
    county: Optional[str] = None
    
    # Project timeline
    start_date: Optional[str] = None
    completion_date: Optional[str] = None
    
    # Financial details
    estimated_cost: Optional[float] = None
    square_footage: Optional[int] = None
    
    # Project classification
    type_of_work: Optional[str] = None
    type_of_funds: Optional[str] = None
    scope_of_work: Optional[str] = None
    project_status: Optional[str] = None
    
    # Stakeholders
    owner_name: Optional[str] = None
    owner_address: Optional[str] = None
    owner_phone: Optional[str] = None
    design_firm_name: Optional[str] = None
    design_firm_address: Optional[str] = None
    ras_name: Optional[str] = None
    ras_number: Optional[str] = None
    
    # Metadata
    registration_date: Optional[str] = None
    date_scraped: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Project':
        """Create Project instance from dictionary"""
        # Filter out any keys that aren't in the dataclass fields
        valid_fields = {k: v for k, v in data.items() if k in cls.__annotations__}
        return cls(**valid_fields)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Project instance to dictionary"""
        return {k: v for k, v in self.__dict__.items() if v is not None}