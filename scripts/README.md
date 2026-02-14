# TDLR Project Scraper - Fixed Version

This project consists of Python scripts to scrape project data from the Texas Department of Licensing and Regulation (TDLR) TABS system and store it in a SQLite database.

## How It Works

Unlike the previous version, this fixed version correctly accesses the TDLR API endpoint that returns JSON data directly, bypassing the need to scrape HTML.

The API endpoint is: `https://www.tdlr.texas.gov/TABS/Search/SearchProjects`

## Files Included

1. **tdlr_scraper.py** - Main Python script with two classes:
   - `TDLRScraper`: Scrapes project data from the TDLR API and stores it in SQLite
   - `ProjectSearcher`: Searches the local database for specific projects

2. **test_scraper.py** - Simple test script to verify the database was created correctly

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

To scrape project data from the TDLR website:
```bash
python3 tdlr_scraper.py --scrape
```

Additional options:
- `--db-path PATH`: Specify a custom path for the SQLite database (default: tdlr_projects.db)
- `--batch-size NUMBER`: Number of records to fetch per request (default: 15, max: 15)
- `--delay SECONDS`: Delay in seconds between requests (default: 1.0)
- `--max-records NUMBER`: Maximum number of records to fetch (default: all)

Example - fetch first 100 projects:
```bash
python3 tdlr_scraper.py --scrape --max-records 100
```

Example - fetch with custom settings:
```bash
python3 tdlr_scraper.py --scrape --batch-size 15 --delay 2 --max-records 500
```

### Searching the Database

To search for projects in the database:
```bash
python3 tdlr_scraper.py --search "SEARCH_TERM"
```

The search looks for matches in project numbers, names, and facility names.

Additional options:
- `--db-path PATH`: Specify a custom path for the SQLite database (default: tdlr_projects.db)

Example:
```bash
python3 tdlr_scraper.py --search "hospital"
```

## Database Schema

The SQLite database contains a single table named `projects` with the following fields:

- `id`: Integer primary key
- `project_id`: Unique project identifier (UUID)
- `project_number`: Project number (e.g., TABS2026012632)
- `project_name`: Name of the project
- `project_created_on`: Timestamp when project was created
- `project_status`: Status code of the project
- `facility_name`: Name of the facility
- `city`: City code
- `county`: County code
- `type_of_work`: Type of work code
- `estimated_cost`: Estimated project cost
- `data_version_id`: Data version identifier
- `estimated_start_date`: Estimated start date
- `estimated_end_date`: Estimated end date
- `date_scraped`: Timestamp when the data was scraped

## Features

1. **Direct API Access**: Accesses the JSON API directly, no HTML parsing required
2. **Proper Pagination**: Correctly handles pagination to fetch all requested records
3. **Robust Error Handling**: Handles network errors and database issues gracefully
4. **Duplicate Prevention**: Uses project_id as unique key to prevent duplicates
5. **Rate Limiting**: Built-in delays to prevent overwhelming the server
6. **Filtering**: Search functionality to find projects in the local database

## Legal Compliance

This script only accesses publicly available data from the TDLR website. It implements the following best practices:

1. Rate limiting with configurable delays between requests
2. Respectful batch sizes that don't overwhelm the server
3. Proper error handling to gracefully handle network issues
4. User-agent spoofing to identify itself as a legitimate browser

## Limitations

1. **API Limits**: The TDLR API appears to limit batches to 15 records at a time
2. **Rate Limiting**: Out of respect for the server, requests are delayed by default
3. **Data Size**: With over 327,000 records available, scraping all data will take significant time

## Testing

To verify the database was created correctly:
```bash
python3 test_scraper.py
```

## Example Usage

```bash
# Scrape first 100 projects
python3 tdlr_scraper.py --scrape --max-records 100

# Search for projects with "hospital" in the name
python3 tdlr_scraper.py --search "hospital"

# Search for projects with "school" in any field
python3 tdlr_scraper.py --search "school"
```

## Troubleshooting

If you encounter any issues:

1. **Database errors**: Delete the existing `tdlr_projects.db` file and try again
2. **Network errors**: Check your internet connection and try again
3. **API changes**: If TDLR changes their API, the script may need to be updated

## License

This project is provided for educational and research purposes only. Please ensure compliance with the TDLR website's terms of service and applicable laws when using this tool.
