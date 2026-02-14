---
name: openclaw-gtm
description: "Automate GTM lead generation using OpenClaw. Collect requirements, search for leads, filter results based on criteria, and schedule recurring searches. Use when GTM agents need to: (1) Define lead generation requirements, (2) Search for potential leads using OpenClaw, (3) Filter and rank leads by match score, (4) Set up scheduled lead searches for fresh results."
---

# OpenClaw GTM Lead Generation

Automate lead generation for GTM agents by collecting requirements, running OpenClaw-based lead searches, filtering results, and scheduling recurring searches.

## Workflow

### 1. Collect Requirements

Ask the user for lead generation criteria and save to `requirements.md`:

- Industries, company size, geography, stage
- Tech stack, job postings, GitHub activity
- Engagement signals (funding, launches, growth)
- Disqualifiers and exclusions
- Output preferences (lead limit, contact preferences)

Use `references/requirements_template.md` as a guide for what to ask.

**Save requirements:**

```bash
# Save user's criteria to requirements.md in current directory
cat > requirements.md << 'EOF'
# Lead Requirements

## Target Criteria
- Industries: SaaS, FinTech
- Company size: 50-200 employees
- Geography: North America
- Tech stack: Python, AWS, React
- Recent funding: within 6 months

## Disqualifiers
- Exclude industries: gambling

## Output
- Lead limit: 20
EOF
```

### 2. Run Lead Search

Execute the search script to fetch raw leads from OpenClaw:

```bash
python scripts/search_leads.py > raw_results.json
```

**Note:** The current `search_leads.py` is a placeholder. Replace the `search_leads()` function with actual OpenClaw API integration for your lead sources.

### 3. Filter and Rank Leads

Filter raw results against requirements and score matches:

```bash
python scripts/filter_leads.py raw_results.json requirements.md > qualified_leads.json
```

The filter script:
- Scores leads based on criteria match (industry, size, tech stack, funding, etc.)
- Excludes disqualified leads
- Ranks by match score
- Limits to specified lead count

Present the top qualified leads to the user with match scores and reasons.

### 4. Schedule Recurring Searches

Set up a cron job to run searches automatically:

```bash
# Example: Daily search at 9 AM
create_cron_job \
  name:"GTM Lead Search" \
  schedule:"0 9 * * *" \
  prompt:"Run the OpenClaw GTM lead search using requirements.md, filter results, and send the top 10 qualified leads to my Slack channel"
```

Common schedules:
- Daily: `0 9 * * *` (9 AM daily)
- Weekly: `0 9 * * 1` (9 AM Mondays)
- Every 6 hours: `6h`

## Script Customization

### Customize search_leads.py

Replace the placeholder `search_leads()` function with your OpenClaw integration:

```python
def search_leads():
    # Example OpenClaw API integration
    import openclaw_client
    
    client = openclaw_client.Client(api_key=os.getenv("OPENCLAW_API_KEY"))
    
    results = client.search(
        sources=["crunchbase", "linkedin", "github"],
        filters={
            "company_size": "50-200",
            "industries": ["SaaS", "FinTech"],
            "signals": ["recent_funding", "hiring_surge"]
        }
    )
    
    return results.to_dict()
```

### Customize filter_leads.py

Adjust the scoring logic in `score_lead()` to match your GTM priorities:

- Increase/decrease points for different criteria
- Add custom signal detection
- Implement more sophisticated matching (fuzzy, weighted)

## Tips

- Start with narrow requirements (fewer results, higher quality)
- Review filtered results and adjust scoring weights
- Use scheduled searches to catch new leads early
- Combine with messaging skill to auto-notify on new qualified leads
- Save `qualified_leads.json` history to track outreach

## Example End-to-End

```bash
# 1. Requirements already saved to requirements.md

# 2. Search
python scripts/search_leads.py > raw_results.json

# 3. Filter
python scripts/filter_leads.py raw_results.json requirements.md > qualified_leads.json

# 4. Review top 5
jq '.leads[:5] | .[] | {company, match_score, contact}' qualified_leads.json

# 5. Schedule daily
create_cron_job name:"Daily GTM Leads" schedule:"0 9 * * *" \
  prompt:"Run OpenClaw GTM search and send top 10 to Slack"
```
