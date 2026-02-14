---
name: gtm-scout
description: "Construction project lead generation for GTM teams using OpenClaw. Collect project requirements, search for construction projects, filter results by criteria (location, size, budget, timeline), and schedule recurring searches. Use when GTM agents need to: (1) Define construction project requirements, (2) Search for projects using OpenClaw, (3) Filter and rank projects by match score, (4) Set up scheduled project searches for fresh opportunities."
---

# OpenClaw Construction Project Lead Generation

Automate construction project discovery for GTM teams by collecting requirements, running OpenClaw-based project searches, filtering results, and scheduling recurring searches.

## Setup

### Prerequisites
- OpenClaw account with API access
- API credentials configured

### Configuration

**Option 1: Environment variable**
```bash
export OPENCLAW_API_KEY="your-api-key-here"
```

**Option 2: ClawBox Settings**
Go to ClawBox Settings → Environment Variables → Add:
- Key: `OPENCLAW_API_KEY`
- Value: `your-api-key-here`

The search script will check for this environment variable and provide clear error messages if not configured.

## Workflow

### 1. Collect Requirements

Ask the user for project criteria and save to `requirements.md`:

- **Start Date** - Project start timeline
- **Project Location** - Geographic area (state, city, county)
- **Type of Work** - Construction project types
- **Square Footage** - Minimum size requirements
- **Estimated Cost** - Budget range
- **Disqualifiers** - Project types to exclude
- **Top Projects** - How many results to show

Use `references/requirements_template.md` as a guide. The template includes examples and prompts for each field.

**Example: Save requirements**

```bash
cat > requirements.md << 'EOF'
# Construction Project Requirements

## Target Criteria

### Start Date
After March 2026

### Project Location
Texas (statewide)

### Type of Work
Commercial office buildings, Industrial warehouses, Mixed-use developments

### Square Footage
100,000+ sq ft

### Estimated Cost
$5M - $50M

### Disqualifiers
Residential projects, Government contracts

## Output Preferences

### Top Projects
20
EOF
```

### 2. Run Project Search

Execute the search script to fetch raw projects from OpenClaw:

```bash
python scripts/search_projects.py > raw_results.json
```

The script:
- Connects to OpenClaw API using `OPENCLAW_API_KEY`
- Searches for construction projects
- Returns JSON with project details: name, location, size, cost, timeline, owner, architect, GC, stage

**Current implementation** includes placeholder sample data. Replace the `search_projects()` function with actual OpenClaw API integration:

```python
import openclaw_client

client = openclaw_client.Client(api_key=os.getenv("OPENCLAW_API_KEY"))

results = client.search_construction_projects(
    location="Texas",
    start_date_after="2026-03-01",
    min_square_footage=100000,
    project_types=["commercial", "industrial", "mixed-use"]
)

return results.to_dict()
```

### 3. Filter and Rank Projects

Filter raw results against requirements and score matches:

```bash
python scripts/filter_projects.py raw_results.json requirements.md > qualified_projects.json
```

The filter script:
- Parses `requirements.md` to extract criteria
- Scores each project based on match quality:
  - **Location match** (25 pts) - Project in target geography
  - **Timeline match** (20 pts) - Start date after specified date
  - **Size match** (20 pts) - Meets minimum square footage
  - **Type match** (15 pts) - Matches specified project types
  - **Budget match** (10 pts) - Within cost range
  - **Stage bonus** (10 pts) - Bidding or Pre-Construction stage
  - **Opportunity bonus** (5 pts) - No GC assigned yet
- Excludes disqualified project types
- Ranks by match score
- Limits to specified project count

**Example output:**

```json
{
  "qualified_projects": 4,
  "projects": [
    {
      "project_name": "Austin Tech Campus Phase II",
      "location": "Austin, TX",
      "project_type": "Commercial Office",
      "square_footage": 185000,
      "estimated_cost": "$42M",
      "start_date": "2026-05-01",
      "project_stage": "Bidding",
      "match_score": 90,
      "match_reasons": [
        "Location match: Texas",
        "Timeline match",
        "Size match: 185,000 sq ft",
        "Type match: Commercial Office",
        "Budget match: $42M",
        "Stage: Bidding",
        "GC not assigned (opportunity)"
      ]
    }
  ]
}
```

Present the top qualified projects to the user with match scores and reasons.

### 4. Schedule Recurring Searches

Set up a cron job to run searches automatically:

```bash
# Example: Daily search at 9 AM
create_cron_job \
  name:"Construction Project Search" \
  schedule:"0 9 * * *" \
  prompt:"Run the OpenClaw construction project search using requirements.md, filter results, and send the top 10 qualified projects to my Slack channel"
```

Common schedules:
- **Daily**: `0 9 * * *` (9 AM daily)
- **Weekly**: `0 9 * * 1` (9 AM Mondays)
- **Every 6 hours**: `6h`

## Customization

### Adjust Scoring Weights

Edit `scripts/filter_projects.py` in the `score_project()` function to customize match scoring:

```python
# Increase location importance
if req_location.lower() in project_location.lower():
    score += 30  # Changed from 25
    
# Add custom criteria
if project.get("leed_certified"):
    score += 15
    reasons.append("LEED certified")
```

### Extend Requirements Template

Add new fields to `references/requirements_template.md` and update the parser in `filter_projects.py`:

```python
# In load_requirements()
requirements = {
    # ... existing fields ...
    "leed_required": "LEED" in content,
    "preferred_contractors": extract_list(content, r"Preferred GC[:\s]+(.+?)(?:\n|$)"),
}
```

## Tips

- **Start narrow** - Fewer, higher-quality results beat high volume
- **Review and tune** - Check filtered results and adjust scoring weights
- **Monitor new projects** - Scheduled searches catch opportunities early
- **Combine with messaging** - Auto-notify team on new qualified projects
- **Track history** - Save `qualified_projects.json` files to track outreach
- **Leverage project stage** - "Bidding" and "Pre-Construction" are prime opportunities

## Example End-to-End

```bash
# 1. Requirements already saved to requirements.md

# 2. Search for projects
python scripts/search_projects.py > raw_results.json

# 3. Filter and rank
python scripts/filter_projects.py raw_results.json requirements.md > qualified_projects.json

# 4. Review top 5 projects
jq '.projects[:5] | .[] | {project_name, location, match_score, estimated_cost, start_date}' qualified_projects.json

# 5. Schedule daily searches
create_cron_job \
  name:"Daily Construction Leads" \
  schedule:"0 9 * * *" \
  prompt:"Run OpenClaw construction search and send top 10 to Slack #gtm-leads"
```

## Testing Without OpenClaw

Test the workflow using placeholder data:

```bash
# 1. Generate sample data (script already includes samples)
python scripts/search_projects.py > raw_results.json

# 2. Create test requirements
cat > requirements.md << 'EOF'
# Construction Project Requirements

## Target Criteria

### Start Date
After March 2026

### Project Location
Texas

### Type of Work
Commercial, Industrial

### Square Footage
100000

### Estimated Cost
No restrictions

## Output Preferences

### Top Projects
20
EOF

# 3. Test filtering
python scripts/filter_projects.py raw_results.json requirements.md

# Should output scored and filtered projects
```
