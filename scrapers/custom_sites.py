"""
Scraper for companies with custom (non-standard) career sites - e.g. Barclays.

This is the "one scraper, many configs" approach: instead of writing new
Python code for every custom company, you describe WHERE on the page the
job title/location/link live (as CSS selectors), and this same function
handles all of them.

To add a new custom-site company:
1. Open their careers/job-search page in a browser
2. Right-click a job listing -> Inspect -> find the CSS class/tag wrapping
   each job card, the title, the location, and the link
3. Add a block to CUSTOM_SITE_CONFIGS below - no new function needed

Note: many custom sites load jobs via JavaScript after the page loads,
so a plain requests.get() sometimes won't see them. Those need Playwright
(a headless browser) instead - flagged per-config below with "needs_js": true.
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}

# --- Add new custom-site companies here, no new code required ---
CUSTOM_SITE_CONFIGS = [
    {
        "name": "Barclays",
        "url": "https://search.jobs.barclays/location/gurugram-haryana-india-jobs/",
        "needs_js": True,  # Barclays' search results load via JS - requests alone won't see them
        "job_card_selector": None,       # fill in after inspecting the live page
        "title_selector": None,
        "location_selector": None,
        "link_selector": None,
    },
    # Example of what a filled-in config looks like once you've inspected a site:
    # {
    #     "name": "SomeCompany",
    #     "url": "https://somecompany.com/careers",
    #     "needs_js": False,
    #     "job_card_selector": "div.job-listing-card",
    #     "title_selector": "h3.job-title",
    #     "location_selector": "span.job-location",
    #     "link_selector": "a.job-link",  # href attribute is used
    # },
]


def scrape_custom_static(config: dict) -> list[dict]:
    """Handles custom sites that DON'T need JavaScript (needs_js: False)."""
    if not config.get("job_card_selector"):
        print(f"[custom] SKIPPED {config['name']}: selectors not filled in yet. "
              f"Inspect the live page and update companies config.")
        return []

    resp = requests.get(config["url"], headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    jobs = []
    cards = soup.select(config["job_card_selector"])
    for card in cards:
        title_el = card.select_one(config["title_selector"])
        loc_el = card.select_one(config["location_selector"])
        link_el = card.select_one(config["link_selector"])

        jobs.append({
            "company": config["name"],
            "title": title_el.get_text(strip=True) if title_el else "",
            "location": loc_el.get_text(strip=True) if loc_el else "",
            "url": link_el["href"] if link_el and link_el.has_attr("href") else "",
            "platform": "custom",
            "scraped_at": datetime.now(timezone.utc).isoformat(),
        })
    return jobs


def scrape_custom_js(config: dict) -> list[dict]:
    """
    Handles custom sites that DO need JavaScript (needs_js: True), e.g. Barclays.
    Requires Playwright, which works in GitHub Actions but is heavier to run.
    """
    if not config.get("job_card_selector"):
        print(f"[custom-js] SKIPPED {config['name']}: selectors not filled in yet.")
        return []

    from playwright.sync_api import sync_playwright

    jobs = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(user_agent=HEADERS["User-Agent"])
        page.goto(config["url"], timeout=30000)
        page.wait_for_selector(config["job_card_selector"], timeout=15000)

        cards = page.query_selector_all(config["job_card_selector"])
        for card in cards:
            title_el = card.query_selector(config["title_selector"])
            loc_el = card.query_selector(config["location_selector"])
            link_el = card.query_selector(config["link_selector"])

            jobs.append({
                "company": config["name"],
                "title": title_el.inner_text().strip() if title_el else "",
                "location": loc_el.inner_text().strip() if loc_el else "",
                "url": link_el.get_attribute("href") if link_el else "",
                "platform": "custom",
                "scraped_at": datetime.now(timezone.utc).isoformat(),
            })
        browser.close()
    return jobs


def scrape_all_custom() -> list[dict]:
    all_jobs = []
    for config in CUSTOM_SITE_CONFIGS:
        try:
            if config.get("needs_js"):
                jobs = scrape_custom_js(config)
            else:
                jobs = scrape_custom_static(config)
            print(f"[custom] {config['name']}: {len(jobs)} roles found")
            all_jobs.extend(jobs)
        except Exception as e:
            print(f"[custom] ERROR scraping {config['name']}: {e}")
    return all_jobs
