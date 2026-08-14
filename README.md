# Gurgaon/Delhi-NCR Finance Job Tracker - Scraper v1

## What's actually working right now
- **Eightfold scraper** (`scrapers/eightfold.py`): confirmed structure by inspecting
  Amex's and HSBC's live career pages directly - both embed all job listings as
  JSON right in the page, filtered down to NCR cities automatically.
- **Companies config** (`companies.json`): add a new Eightfold company by pasting
  its careers URL - no code changes needed.

## What's built but needs one more step from you
- **Custom-site scraper** (`scrapers/custom_sites.py`): the framework is ready,
  but each custom company (starting with Barclays) needs its CSS selectors filled
  in. This means: open the live careers page, right-click a job listing → Inspect,
  and note down the class names wrapping the job card, title, location, and link.
  Fill those into the `CUSTOM_SITE_CONFIGS` list - takes a few minutes per company,
  no coding needed.

## Why I couldn't fully test this end-to-end
My sandbox here can only reach a handful of package-download sites (PyPI, GitHub),
not arbitrary company websites - so I built this based on direct inspection of the
real Amex/HSBC/Barclays pages via a separate fetch tool, but I could not run the
scraper script itself against live sites from here. It'll run for real once pushed
to GitHub, where Actions has normal internet access. First run there will tell you
immediately if anything needs adjusting (check the Actions log).

## Setup (one-time)
1. Create a GitHub repo, push this folder's contents to it
2. Go to Settings → Actions → General → enable "Read and write permissions" for
   the workflow (needed so it can commit updated listings.json automatically)
3. Go to the "Actions" tab → run "Update job listings" manually once to test
4. After that it runs automatically every 6 hours

## Adding more companies later
- **On Eightfold?** Just add `{"name": "...", "url": "..."}` to the `eightfold`
  list in `companies.json`.
- **Custom site?** Add a config block to `CUSTOM_SITE_CONFIGS` in
  `scrapers/custom_sites.py` with the selectors you found by inspecting the page.
- **New platform entirely** (e.g. Workday, Oracle Cloud for JPMorgan)? Needs a new
  scraper file, following the same pattern as `eightfold.py` - happy to build the
  next one whenever you're ready.

## Output
`data/listings.json` - every scrape overwrites this with the latest NCR listings,
company, title, location, direct application link, and when it was scraped.
This file is what your dashboard, RSS feed, and "API" will all read from.
