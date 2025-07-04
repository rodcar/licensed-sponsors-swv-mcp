import logging
from typing import List

import pandas as pd
import requests
from bs4 import BeautifulSoup
from fastmcp import FastMCP
from rapidfuzz import fuzz, process

mcp = FastMCP("licensed-sponsor-swv-mcp")

REGISTER_OF_LICENCED_SPONSORS_PAGE_URL = "https://www.gov.uk/government/publications/register-of-licensed-sponsors-workers"
REGISTRY_LINK_CSS_SELECTOR = "div.gem-c-attachment__details > h3 > a"
ORGANISATION_NAME_COLUMN_NAME = "Organisation Name"


@mcp.tool()
def search(company_name: str) -> List[str]:
    company_name = company_name.lower().strip()
    # get the registry download link from government page
    response = requests.get(REGISTER_OF_LICENCED_SPONSORS_PAGE_URL)
    soup = BeautifulSoup(response.text, "html.parser")
    registry_link = soup.select_one(REGISTRY_LINK_CSS_SELECTOR)

    if registry_link:
        registry_link_href = registry_link.get("href")
        if registry_link_href:
            try:
                logging.info(f"Reading CSV file: {registry_link_href}")
                licensed_sponsors = pd.read_csv(registry_link_href)
                # find the company name in the licensed_sponsors dataframe
                matches = process.extract(company_name, licensed_sponsors[ORGANISATION_NAME_COLUMN_NAME].str.lower().str.strip(), limit=10, scorer=fuzz.ratio)
                results = [licensed_sponsors[ORGANISATION_NAME_COLUMN_NAME].iloc[m[2]] for m in matches]
                # check if it is a perfect match
                match = any(m[1] == 100 for m in matches)
                return {
                    "search_company_name": company_name,
                    "match": match,
                    "results": results
                }
            except Exception as e:
                return [f"Error reading CSV file: {e}"]
    return ["No link found"]

if __name__ == "__main__":
    mcp.run(transport="stdio")
