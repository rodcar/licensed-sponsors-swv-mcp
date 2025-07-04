import logging
import pandas as pd
import requests
from bs4 import BeautifulSoup

REGISTER_OF_LICENCED_SPONSORS_PAGE_URL = "https://www.gov.uk/government/publications/register-of-licensed-sponsors-workers"
REGISTRY_LINK_CSS_SELECTOR = "div.gem-c-attachment__details > h3 > a"

def load_registry_data():
    """Load registry data during module import"""
    try:
        logging.info("Loading registry data on startup")
        response = requests.get(REGISTER_OF_LICENCED_SPONSORS_PAGE_URL)
        soup = BeautifulSoup(response.text, "html.parser")
        registry_link = soup.select_one(REGISTRY_LINK_CSS_SELECTOR)
        if registry_link and (href := registry_link.get("href")):
            data = pd.read_csv(href, dtype='string', engine='c')
            logging.info(f"Loaded {len(data)} registry rows")
            return data
    except Exception as e:
        logging.error(f"Failed to load registry data: {e}")
    return None

# Load data immediately when module is imported
registry_data = load_registry_data()