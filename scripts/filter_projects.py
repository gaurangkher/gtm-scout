#!/usr/bin/env python3
"""
Construction Project Filtering Script

Filters raw project search results against requirements.md criteria.
Outputs qualified projects ranked by match score.
"""

import json
import re
import sys
from pathlib import Path
from datetime import datetime


def load_requirements(requirements_path):
    """Parse requirements.md to extract filtering criteria."""
    
    if not Path(requirements_path).exists():
        raise FileNotFoundError(f"Requirements file not found: {requirements_path}")
    
    with open(requirements_path, 'r') as f:
        content = f.read()
    
    # Parse construction-specific criteria
    requirements = {
        "start_date_after": extract_date(content, r"Start Date[:\s]+[Aa]fter\s+([A-Za-z]+\s+\d{4})"),
        "location": extract_text(content, r"Project Location[:\s]+(.+?)(?:\n|$)"),
        "project_types": extract_list(content, r"Type of Work[:\s]+(.+?)(?:\n|$)"),
        "min_square_footage": extract_number(content, r"Square Footage[:\s]+(\d+)"),
        "min_cost": extract_cost(content, r"Estimated Cost[:\s]+\$?([\d.]+)M"),
        "max_cost": extract_cost(content, r"Estimated Cost[:\s]+.+?-\s*\$?([\d.]+)M"),
        "exclude_types": extract_list(content, r"Disqualifiers[:\s]+(.+?)(?:\n|$)"),
        "project_limit": extract_number(content, r"Top Projects[:\s]+(\d+)") or 20,
    }
    
    return requirements


def extract_text(text, pattern):
    """Extract text from pattern."""
    match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip() if match else None


def extract_list(text, pattern):
    """Extract comma-separated list from text using regex."""
    match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
    if match:
        items = [item.strip() for item in match.group(1).split(',')]
        return [item for item in items if item and not item.startswith('(')]
    return []


def extract_number(text, pattern):
    """Extract number from text using regex."""
    match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
    return int(match.group(1)) if match else None


def extract_cost(text, pattern):
    """Extract cost in millions from text."""
    match = re.search(pattern, text, re.IGNORECASE)
    return float(match.group(1)) if match else None


def extract_date(text, pattern):
    """Extract date string from text."""
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else None


def parse_cost(cost_str):
    """Parse cost string like '$42M' to float."""
    if not cost_str:
        return None
    match = re.search(r'\$?([\d.]+)M', cost_str, re.IGNORECASE)
    return float(match.group(1)) if match else None


def parse_date(date_str):
    """Parse date string to datetime object."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except:
        return None


def score_project(project, requirements):
    """Score a project based on how well it matches requirements."""
    score = 0
    reasons = []
    
    # Location match
    req_location = requirements.get("location")
    if req_location:
        project_location = project.get("location", "")
        if req_location.lower() in project_location.lower():
            score += 25
            reasons.append(f"Location match: {req_location}")
    
    # Start date match
    start_date_after = requirements.get("start_date_after")
    if start_date_after:
        project_date = parse_date(project.get("start_date"))
        # Simple comparison - could be enhanced with proper date parsing
        if project_date and project.get("start_date", "").split("-")[0] >= "2026":
            score += 20
            reasons.append("Timeline match")
    
    # Square footage match
    min_sqft = requirements.get("min_square_footage")
    if min_sqft:
        project_sqft = project.get("square_footage")
        if project_sqft and project_sqft >= min_sqft:
            score += 20
            reasons.append(f"Size match: {project_sqft:,} sq ft")
    
    # Project type match
    project_types = requirements.get("project_types")
    if project_types:
        project_type = project.get("project_type", "")
        if any(ptype.lower() in project_type.lower() for ptype in project_types):
            score += 15
            reasons.append(f"Type match: {project_type}")
    
    # Cost range match
    project_cost = parse_cost(project.get("estimated_cost"))
    if project_cost:
        min_cost = requirements.get("min_cost")
        max_cost = requirements.get("max_cost")
        
        if min_cost and project_cost >= min_cost:
            score += 10
            reasons.append(f"Budget match: {project.get('estimated_cost')}")
        elif max_cost and project_cost <= max_cost:
            score += 10
            reasons.append(f"Budget match: {project.get('estimated_cost')}")
        elif not min_cost and not max_cost:
            score += 5
    
    # Exclude types (disqualify)
    exclude_types = requirements.get("exclude_types")
    if exclude_types:
        project_type = project.get("project_type", "")
        if any(etype.lower() in project_type.lower() for etype in exclude_types):
            return 0, ["Excluded project type"]
    
    # Project stage bonus
    stage = project.get("project_stage", "")
    if stage in ["Bidding", "Pre-Construction"]:
        score += 10
        reasons.append(f"Stage: {stage}")
    
    # GC not assigned bonus (opportunity)
    if not project.get("general_contractor"):
        score += 5
        reasons.append("GC not assigned (opportunity)")
    
    return score, reasons


def filter_projects(raw_results, requirements):
    """Filter and rank projects based on requirements."""
    
    projects = raw_results.get("projects", [])
    scored_projects = []
    
    for project in projects:
        score, reasons = score_project(project, requirements)
        if score > 0:  # Only include projects with positive score
            scored_projects.append({
                **project,
                "match_score": score,
                "match_reasons": reasons
            })
    
    # Sort by score descending
    scored_projects.sort(key=lambda x: x["match_score"], reverse=True)
    
    # Apply project limit
    project_limit = requirements.get("project_limit", 20)
    if project_limit:
        scored_projects = scored_projects[:project_limit]
    
    return scored_projects


def main():
    if len(sys.argv) < 3:
        print("Usage: filter_projects.py <raw_results.json> <requirements.md>", file=sys.stderr)
        sys.exit(1)
    
    raw_results_path = sys.argv[1]
    requirements_path = sys.argv[2]
    
    try:
        # Load raw results
        with open(raw_results_path, 'r') as f:
            raw_results = json.load(f)
        
        # Load requirements
        requirements = load_requirements(requirements_path)
        
        # Filter projects
        filtered_projects = filter_projects(raw_results, requirements)
        
        # Output results
        result = {
            "timestamp": raw_results.get("timestamp"),
            "total_raw_projects": raw_results.get("count", 0),
            "qualified_projects": len(filtered_projects),
            "requirements_summary": {k: v for k, v in requirements.items() if v},
            "projects": filtered_projects
        }
        
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
