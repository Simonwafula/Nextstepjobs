# backend/scraping/spiders/generic_spider.py

import logging
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin
from config import get_site_cfg
from db import Database
from utils import get_session, rate_limited_get, detect_last_page
from dataclasses import dataclass

import warnings
from urllib3.exceptions import NotOpenSSLWarning

# suppress only the OpenSSL-warning
# warnings.filterwarnings(
#     "ignore",
#     category=NotOpenSSLWarning,
#     module="urllib3"
# )

@dataclass
class JobListing:
    title: str
    full_link: str
    content: str = ""


class SiteSpider:
    def __init__(self, site_name: str):
        cfg = get_site_cfg(site_name)
        self.base_url = cfg["base_url"]
        self.list_path = cfg["listing_path"]
        self.list_sel = cfg["listing_selector"]
        self.title_attr = cfg["title_attribute"]
        self.content_sel = cfg["content_selector"]
        self.page_sel = cfg["pagination_selector"]

        self.session = get_session()
        self.db = Database()

    def fetch(self, url):
        try:
            return rate_limited_get(self.session, url, verify=False).text
        except Exception as e:
            logging.error(f"Fetch error {url}: {e}")
            return None

    def get_pages(self):
        first = self.fetch(self.base_url + self.list_path.format(page=1))
        return detect_last_page(first, self.page_sel) if first else 1

    def parse_listings(self, html):
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.select(self.list_sel):
            title = (a.get(self.title_attr) or a.get_text()).strip()
            href = a.get("href", "")
            if href:
                yield title, urljoin(self.base_url, href)

    def parse_content(self, html):
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        node = soup.select_one(self.content_sel)
        return node.get_text(strip=True) if node else ""

    def run(self):
        self.db.connect()
        last = self.get_pages()
        logging.info(f"Scraping pages 1–{last}")

        # fetch all listing pages
        with ThreadPoolExecutor(max_workers=5) as tp:
            htmls = tp.map(lambda p: self.fetch(self.base_url + self.list_path.format(page=p)),
                           range(1, last + 1))

        jobs = []
        for html in htmls:
            if html:
                jobs.extend(self.parse_listings(html))

        # detail & store
        def worker(item):
            title, link = item
            html = self.fetch(link)
            content = self.parse_content(html) if html else ""
            return (title, link, content)

        with ThreadPoolExecutor(max_workers=5) as tp:
            rows = list(tp.map(worker, jobs))

        self.db.batch_insert(rows)
        self.db.close()
        logging.info("Done.")
