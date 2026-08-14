"""
Run this to update data/listings.json with the latest job listings
from every configured company. This is the script GitHub Actions
will run on a schedule.

Usage: python main.py
"""

import json
import os
from datetime import datetime, timezone

from scrapers.eightfold import scrape_all_eightfold
from scrapers.custom_sites import scrape_all_custom

COMPANIES_FILE = "companies.json"
OUTPUT_FILE = "data/listings.json"


def load_companies():
    with open(COMPANIES_FILE, "r") as f:
        return json.load(f)


def main():
    companies = load_companies()

    all_jobs = []
    all_jobs.extend(scrape_all_eightfold(companies.get("eightfold", [])))
    all_jobs.extend(scrape_all_custom())

    os.makedirs("data", exist_ok=True)
    output = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "total_jobs": len(all_jobs),
        "jobs": all_jobs,
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nDone. {len(all_jobs)} total NCR jobs written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
