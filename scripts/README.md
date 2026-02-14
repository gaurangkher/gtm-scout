# TDLR Project Scraper

This project consists of Python scripts to scrape project data from the Texas Department of Licensing and Regulation (TDLR) TABS system and store it in a SQLite database.

## How It Works

The scraper accesses the TDLR API endpoint that returns JSON data directly, then visits individual project detail pages to extract comprehensive project information including square footage, costs, dates, and ownership details.

## Files Included

1. **tdlr_scraper.py** - Original synchronous scraper
2. **tdlr_scraper_async.py** - New async version for faster scraping (10x speed improvement)
3. **requirements.txt** - Lists the Python dependencies

## Prerequisites

- Python 3.6 or higher
- pip (Python package installer)

## Installation

1. Clone or download this repository.

2. Install the required Python packages:
```bash
pip install -r requirements.txt
```

## Usage

### Scraping Data

#### Async Version (Recommended - 10x faster)
```bash
python3 tdlr_scraper_async.py --scrape
```

#### Original Synchronous Version
```bash
python3 tdlr_scraper.py --scrape
```

Additional options:
- `--db-path PATH`: Specify a custom path for the SQLite database (default: tdlr_projects.db)
- `--batch-size NUMBER`: Number of records to fetch per request (default: 15, max: 15)
- `--delay SECONDS`: Delay between requests/batches (default: 0.5 for async, 2.0 for sync)
- `--max-records NUMBER`: Maximum number of records to fetch (default: all)

Example - fetch first 100 projects with async scraper:
```bash
python3 tdlr_scraper_async.py --scrape --max-records 100
```

Example - fetch with custom settings:
```bash
python3 tdlr_scraper_async.py --scrape --batch-size 15 --delay 1 --max-records 500
```

### Searching the Database

To search for projects in the database:
```bash
python3 tdlr_scraper_async.py --search "SEARCH_TERM"
```

The search looks for matches in project numbers, names, facility names, cities, and counties.

Additional options:
- `--db-path PATH`: Specify a custom path for the SQLite database (default: tdlr_projects.db)

Example:
```bash
python3 tdlr_scraper_async.py --search "hospital"
```

## Database Schema

The SQLite database contains a single table named `projects` with the following fields:

- `id`: Integer primary key
- `project_id`: Unique project identifier
- `project_number`: Project number (e.g., TABS2026012632)
- `project_name`: Name of the project
- `facility_name`: Name of the facility
- `location_address`: Physical address
- `city`: City name
- `county`: County name
- `start_date`: Project start date
- `completion_date`: Project completion date
- `estimated_cost`: Estimated project cost
- `type_of_work`: Type of work description
- `type_of_funds`: Type of funding
- `scope_of_work`: Detailed scope of work
- `square_footage`: Project size in square feet
- `project_status`: Current project status
- `owner_name`: Project owner name
- `owner_address`: Owner address
- `owner_phone`: Owner phone number
- `design_firm_name`: Design firm name
- `design_firm_address`: Design firm address
- `ras_name`: Registered Architect/Engineer name
- `ras_number`: RAS license number
- `registration_date`: Project registration date
- `date_scraped`: Timestamp when the data was scraped

## Performance Comparison

| Method | 100 Projects | 1000 Projects |
|--------|--------------|---------------|
| **Synchronous** | 5-7 minutes | 50-70 minutes |
| **Asynchronous** | **30-60 seconds** | **5-10 minutes** |

The async version achieves a 10x speed improvement by:
- Concurrently fetching project detail pages
- Using connection pooling
- Maintaining rate limiting to prevent server overload

## Features

1. **Direct API Access**: Accesses the JSON API directly for search results
2. **Detailed Page Scraping**: Visits individual project pages for comprehensive data
3. **Proper Pagination**: Correctly handles pagination to fetch all requested records
4. **Robust Error Handling**: Handles network errors and database issues gracefully
5. **Duplicate Prevention**: Uses project_number as unique key to prevent duplicates
6. **Rate Limiting**: Built-in delays to prevent overwhelming the server
7. **Filtering**: Search functionality to find projects in the local database
8. **Async Support**: Concurrent scraping for dramatic performance improvements

## Legal Compliance

This script only accesses publicly available data from the TDLR website. It implements the following best practices:

1. Rate limiting with configurable delays between requests
2. Respectful batch sizes that don't overwhelm the server
3. Proper error handling to gracefully handle network issues
4. User-agent spoofing to identify itself as a legitimate browser

## Limitations

1. **API Limits**: The TDLR API appears to limit batches to 15 records at a time
2. **Rate Limiting**: Out of respect for the server, requests are delayed by default
3. **Data Size**: With hundreds of thousands of records available, scraping all data will take significant time

## Example Usage

```bash
# Scrape first 100 projects (fast async version)
python3 tdlr_scraper_async.py --scrape --max-records 100

# Search for projects with "hospital" in the name
python3 tdlr_scraper_async.py --search "hospital"

# Search for projects in Travis County
python3 tdlr_scraper_async.py --search "Travis"
```

## Troubleshooting

If you encounter any issues:

1. **Database errors**: Delete the existing `tdlr_projects.db` file and try again
2. **Network errors**: Check your internet connection and try again
3. **API changes**: If TDLR changes their API, the script may need to be updated

## License

This project is provided for educational and research purposes only. Please ensure compliance with the TDLR website's terms of service and applicable laws when using this tool.