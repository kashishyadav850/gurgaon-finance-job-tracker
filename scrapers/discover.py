"""
Discovery scraper: for each company, finds their careers page and figures out
which ATS (job platform) they use, purely by inspecting the URL/page - no
manual visiting needed.

Run this FIRST. Its output (data/ats_classification.json) tells you exactly
which companies are on Greenhouse/Lever/Workday/Eightfold/etc, and which are
"custom" (need a dedicated scraper). Only then do you know where to spend
effort building platform-specific scrapers - instead of guessing.

How it works:
1. Tries a handful of common URL patterns for each company's careers page
   (mycompany.com/careers, careers.mycompany.com, etc.)
2. Follows redirects - the FINAL url often reveals the ATS
   (e.g. redirects to boards.greenhouse.io/company, or company.wd1.myworkdayjobs.com)
3. If the URL itself doesn't reveal it, scans the page content for known
   ATS signatures (script tags, meta tags, embedded JSON structure)
4. Buckets every company into one of: greenhouse, lever, workday, eightfold,
   smartrecruiters, oracle_cloud, successfactors, icims, phenom, custom/unknown
"""

import re
import requests
from urllib.parse import urlparse

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}

# URL-based fingerprints: if this string appears anywhere in the final URL
# (after redirects), we know the platform immediately - no page content needed.
URL_FINGERPRINTS = {
    "greenhouse.io": "greenhouse",
    "lever.co": "lever",
    "myworkdayjobs.com": "workday",
    "eightfold.ai": "eightfold",
    "smartrecruiters.com": "smartrecruiters",
    "oraclecloud.com": "oracle_cloud",
    "successfactors.com": "successfactors",
    "icims.com": "icims",
    "phenompeople.com": "phenom",
    "taleo.net": "taleo",
    "brassring.com": "brassring",
    "jobvite.com": "jobvite",
    "ashbyhq.com": "ashby",
    "tal.net": "talnet",
}

# Common places a company's careers page tends to live - tried in order.
URL_PATTERNS = [
    "https://{domain}/careers",
    "https://www.{domain}/careers",
    "https://careers.{domain}",
    "https://{domain}/careers/",
    "https://www.{domain}/career",
    "https://{domain}/en/careers",
]


def classify_by_content(html: str) -> str | None:
    """Fallback: scan page content for ATS signatures not visible in the URL."""
    content_signatures = {
        "greenhouse": ["greenhouse.io", "gh_jid"],
        "lever": ["lever.co", "lever-jobs"],
        "workday": ["myworkdayjobs", "wd-icon"],
        "eightfold": ["eightfold.ai", "canonicalPositionUrl"],
        "smartrecruiters": ["smartrecruiters.com"],
        "oracle_cloud": ["oraclecloud.com", "CandidateExperience"],
        "successfactors": ["successfactors.com", "sfsf"],
        "icims": ["icims.com"],
        "phenom": ["phenompeople.com", "phenom-"],
        "workable": ["workable.com"],
    }
    html_lower = html.lower()
    for platform, signatures in content_signatures.items():
        if any(sig.lower() in html_lower for sig in signatures):
            return platform
    return None


def discover_ats(company_name: str, domain: str) -> dict:
    """
    Tries to find the company's careers page and classify its ATS.
    Returns {"company": ..., "platform": ..., "careers_url": ..., "found": bool}
    """
    for pattern in URL_PATTERNS:
        url = pattern.format(domain=domain)
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
            if resp.status_code >= 400:
                continue

            final_url = resp.url

            # Check 1: does the final URL (after any redirects) match a known ATS?
            for fingerprint, platform in URL_FINGERPRINTS.items():
                if fingerprint in final_url:
                    return {
                        "company": company_name,
                        "platform": platform,
                        "careers_url": final_url,
                        "found": True,
                    }

            # Check 2: scan the page content itself
            platform = classify_by_content(resp.text)
            if platform:
                return {
                    "company": company_name,
                    "platform": platform,
                    "careers_url": final_url,
                    "found": True,
                }

            # We reached a real careers page but couldn't identify the platform -
            # still useful, marks it "custom" so a dedicated scraper can be built.
            return {
                "company": company_name,
                "platform": "custom_unknown",
                "careers_url": final_url,
                "found": True,
            }

        except requests.RequestException:
            continue

    # None of the common URL patterns worked at all.
    return {
        "company": company_name,
        "platform": None,
        "careers_url": None,
        "found": False,
    }


def discover_all(companies: list[dict]) -> dict:
    """
    companies: [{"name": "...", "domain": "..."}, ...]
    Returns a dict bucketed by platform, e.g.:
    {"greenhouse": ["CompanyA", ...], "custom_unknown": [...], "not_found": [...]}
    """
    buckets: dict[str, list] = {}
    details = []

    for c in companies:
        result = discover_ats(c["name"], c["domain"])
        details.append(result)

        if not result["found"]:
            bucket_key = "not_found"
        else:
            bucket_key = result["platform"]

        buckets.setdefault(bucket_key, []).append({
            "company": result["company"],
            "careers_url": result["careers_url"],
        })

        status = result["platform"] or "NOT FOUND"
        print(f"[discover] {c['name']}: {status}  ({result['careers_url'] or 'no page found'})")

    return {"buckets": buckets, "details": details}
