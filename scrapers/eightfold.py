"""
Scraper for companies using the Eightfold AI careers platform.
One function here works for EVERY Eightfold company - just point it
at a different company's careers URL (see companies.json).

Confirmed working structure (checked on Amex + HSBC, Aug 2026):
Eightfold embeds all job listings as a JSON blob directly in the page HTML,
inside a <script> tag. No clicking through individual jobs needed - the
whole India job list comes back in one page load.
"""

import re
import json
import requests
from datetime import datetime, timezone

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}

# Cities that count as "Delhi-NCR" for this project's scope.
NCR_KEYWORDS = ["gurgaon", "gurugram", "delhi", "noida", "faridabad", "ghaziabad", "new delhi"]


def is_ncr(location_str: str) -> bool:
    if not location_str:
        return False
    loc = location_str.lower()
    return any(city in loc for city in NCR_KEYWORDS)


def scrape_eightfold(company_name: str, url: str) -> list[dict]:
    """
    Fetches an Eightfold careers page and extracts every job listing.
    Returns a list of normalized job dicts (only NCR-based roles).
    """
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    html = resp.text

    # Eightfold pages embed a large JSON object containing a "positions" key.
    # We pull that array out directly rather than parsing the whole page.
    match = re.search(r'"positions"\s*:\s*(\[.*?\])\s*,\s*"debug"', html, re.DOTALL)
    if not match:
        # Fallback: looser match in case the surrounding keys differ
        match = re.search(r'"positions"\s*:\s*(\[.*?\])', html, re.DOTALL)
    if not match:
        print(f"[eightfold] WARNING: could not find positions data for {company_name}. "
              f"Site structure may have changed - inspect manually.")
        return []

    try:
        positions = json.loads(match.group(1))
    except json.JSONDecodeError as e:
        print(f"[eightfold] WARNING: failed to parse positions JSON for {company_name}: {e}")
        return []

    jobs = []
    for p in positions:
        location = p.get("location", "")
        if not is_ncr(location):
            continue  # skip non-NCR roles, keeps output focused on your scope

        jobs.append({
            "company": company_name,
            "title": p.get("name", ""),
            "location": location,
            "department": p.get("department") or p.get("business_unit") or "",
            "url": p.get("canonicalPositionUrl", ""),
            "platform": "eightfold",
            "scraped_at": datetime.now(timezone.utc).isoformat(),
        })
    return jobs


def scrape_all_eightfold(company_list: list[dict]) -> list[dict]:
    """company_list: [{"name": "American Express", "url": "..."}, ...]"""
    all_jobs = []
    for c in company_list:
        try:
            jobs = scrape_eightfold(c["name"], c["url"])
            print(f"[eightfold] {c['name']}: {len(jobs)} NCR roles found")
            all_jobs.extend(jobs)
        except Exception as e:
            print(f"[eightfold] ERROR scraping {c['name']}: {e}")
    return all_jobs
