#!/usr/bin/env python3
"""
Lead Filtering Script

Filters raw lead search results against requirements.md criteria.
Outputs qualified leads ranked by match score.
"""

import json
import re
import sys
from pathlib import Path


def load_requirements(requirements_path):
    """Parse requirements.md to extract filtering criteria."""
    
    if not Path(requirements_path).exists():
        raise FileNotFoundError(f"Requirements file not found: {requirements_path}")
    
    with open(requirements_path, 'r') as f:
        content = f.read()
    
    # Simple parsing - extract key criteria
    # You can enhance this with more sophisticated parsing
    requirements = {
        "industries": extract_list(content, r"Industries[:\s]+(.+?)(?:\n|$)"),
        "company_size": extract_list(content, r"Company size[:\s]+(.+?)(?:\n|$)"),
        "geography": extract_list(content, r"Geography[:\s]+(.+?)(?:\n|$)"),
        "tech_stack": extract_list(content, r"Tech stack[:\s]+(.+?)(?:\n|$)"),
        "exclude_industries": extract_list(content, r"Exclude industries[:\s]+(.+?)(?:\n|$)"),
        "recent_funding": "recent funding" in content.lower() and "within" in content.lower(),
        "lead_limit": extract_number(content, r"Lead limit[:\s]+(\d+)"),
    }
    
    return requirements


def extract_list(text, pattern):
    """Extract comma-separated list from text using regex."""
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        items = [item.strip() for item in match.group(1).split(',')]
        return [item for item in items if item and not item.startswith('(')]
    return []


def extract_number(text, pattern):
    """Extract number from text using regex."""
    match = re.search(pattern, text, re.IGNORECASE)
    return int(match.group(1)) if match else None


def score_lead(lead, requirements):
    """Score a lead based on how well it matches requirements."""
    score = 0
    reasons = []
    
    # Industry match
    if requirements.get("industries"):
        if any(ind.lower() in lead.get("industry", "").lower() 
               for ind in requirements["industries"]):
            score += 20
            reasons.append("Industry match")
    
    # Exclude industries (disqualify)
    if requirements.get("exclude_industries"):
        if any(ind.lower() in lead.get("industry", "").lower() 
               for ind in requirements["exclude_industries"]):
            return 0, ["Excluded industry"]
    
    # Company size match
    if requirements.get("company_size"):
        if any(size in lead.get("size", "") for size in requirements["company_size"]):
            score += 15
            reasons.append("Size match")
    
    # Geography match
    if requirements.get("geography"):
        if any(geo.lower() in lead.get("location", "").lower() 
               for geo in requirements["geography"]):
            score += 10
            reasons.append("Geography match")
    
    # Tech stack match
    if requirements.get("tech_stack"):
        lead_tech = lead.get("tech_stack", [])
        matches = [tech for tech in requirements["tech_stack"] 
                   if any(tech.lower() in lt.lower() for lt in lead_tech)]
        if matches:
            score += 15 * len(matches)
            reasons.append(f"Tech match: {', '.join(matches)}")
    
    # Recent funding
    if requirements.get("recent_funding") and lead.get("recent_funding"):
        score += 25
        reasons.append("Recent funding")
    
    # Engagement signals
    if lead.get("signals"):
        score += 5 * len(lead["signals"])
        reasons.append(f"{len(lead['signals'])} engagement signals")
    
    return score, reasons


def filter_leads(raw_results, requirements):
    """Filter and rank leads based on requirements."""
    
    leads = raw_results.get("leads", [])
    scored_leads = []
    
    for lead in leads:
        score, reasons = score_lead(lead, requirements)
        if score > 0:  # Only include leads with positive score
            scored_leads.append({
                **lead,
                "match_score": score,
                "match_reasons": reasons
            })
    
    # Sort by score descending
    scored_leads.sort(key=lambda x: x["match_score"], reverse=True)
    
    # Apply lead limit if specified
    lead_limit = requirements.get("lead_limit")
    if lead_limit:
        scored_leads = scored_leads[:lead_limit]
    
    return scored_leads


def main():
    if len(sys.argv) < 3:
        print("Usage: filter_leads.py <raw_results.json> <requirements.md>", file=sys.stderr)
        sys.exit(1)
    
    raw_results_path = sys.argv[1]
    requirements_path = sys.argv[2]
    
    try:
        # Load raw results
        with open(raw_results_path, 'r') as f:
            raw_results = json.load(f)
        
        # Load requirements
        requirements = load_requirements(requirements_path)
        
        # Filter leads
        filtered_leads = filter_leads(raw_results, requirements)
        
        # Output results
        result = {
            "timestamp": raw_results.get("timestamp"),
            "total_raw_leads": raw_results.get("count", 0),
            "qualified_leads": len(filtered_leads),
            "requirements_summary": {k: v for k, v in requirements.items() if v},
            "leads": filtered_leads
        }
        
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
