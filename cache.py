import logging
import pandas as pd
import requests
from bs4 import BeautifulSoup

REGISTER_OF_LICENCED_SPONSORS_PAGE_URL = "https://www.gov.uk/government/publications/register-of-licensed-sponsors-workers"
REGISTER_LINK_CSS_SELECTOR = "div.gem-c-attachment__details > h3 > a"

def load_register_data():
    """Load register data during module import"""
    try:
        logging.info("Loading register data on startup")
        response = requests.get(REGISTER_OF_LICENCED_SPONSORS_PAGE_URL)
        soup = BeautifulSoup(response.text, "html.parser")
        register_link = soup.select_one(REGISTER_LINK_CSS_SELECTOR)
        if register_link and (href := register_link.get("href")):
            data = pd.read_csv(href, dtype='string', engine='c')
            logging.info(f"Loaded {len(data)} register rows")
            return data
    except Exception as e:
        logging.error(f"Failed to load register data: {e}")
    return None

# Load data immediately when module is imported
register_data = load_register_data()