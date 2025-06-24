# backend/scraping/utils.py

import time, logging
from ratelimit import limits, sleep_and_retry
import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

# from config import REQUESTS_PER_MINUTE

ONE_MINUTE = 60

def get_session(retries=3, backoff=0.3):
    session = requests.Session()
    strategy = Retry(total=retries,
                     backoff_factor=backoff,
                     status_forcelist=[500,502,503,504])
    adapter = HTTPAdapter(max_retries=strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

@sleep_and_retry
# @limits(calls=REQUESTS_PER_MINUTE, period=ONE_MINUTE)
def rate_limited_get(session, url, **kwargs):
    logging.info(f"GET {url}")
    r = session.get(url, **kwargs)
    r.raise_for_status()
    time.sleep(0.05)
    return r

def detect_last_page(html, pagination_selector):
    """Given the HTML of page 1, return max page number found by CSS selector."""
    from bs4 import BeautifulSoup
    import re

    soup = BeautifulSoup(html, "html.parser")
    anchors = soup.select(pagination_selector)
    pages = []
    for a in anchors:
        href = a.get("href","")
        m = re.search(r"([?&/](?:page|p)=)(\d+)", href)
        if m:
            pages.append(int(m.group(2)))
    last = max(pages) if pages else 1
    logging.info(f"Detected last page = {last}")
    return last
