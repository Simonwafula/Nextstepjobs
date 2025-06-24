# backend/scraping/config.py

import os, yaml

# find YAML
_CONFIG_PATH = os.getenv("JOB_CONFIG", os.path.join(os.path.dirname(__file__), "config.yaml"))

with open(_CONFIG_PATH, "r") as f:
    _cfg = yaml.safe_load(f)

# defaults
DB_PATH           = os.getenv("JOB_DB_PATH", _cfg["default"]["db_path"])
TABLE_NAME        = os.getenv("JOB_TABLE",   _cfg["default"]["table_name"])
# REQUESTS_PER_MINUTE = int(os.getenv("JOB_RPM", _cfg["default"]["requests_per_minute"]))

# per-site configs
SITES = _cfg["sites"]

def get_site_cfg(name: str) -> dict:
    """Return the dict for site `name`; KeyError if missing."""
    return SITES[name]
