import logging
from typing import List
import os

import pandas as pd
import requests
from bs4 import BeautifulSoup
from fastmcp import FastMCP
from rapidfuzz import fuzz, process
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

mcp = FastMCP("licensed-sponsor-swv-mcp")

REGISTER_OF_LICENCED_SPONSORS_PAGE_URL = "https://www.gov.uk/government/publications/register-of-licensed-sponsors-workers"
REGISTRY_LINK_CSS_SELECTOR = "div.gem-c-attachment__details > h3 > a"
ORGANISATION_NAME_COLUMN_NAME = "Organisation Name"
COMPANIES_HOUSE_API_BASE = "https://api.company-information.service.gov.uk"


@mcp.tool()
def search_in_sponsor_registry(company_name: str) -> List[str]:
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

@mcp.tool()
def get_sponsor_details(company_name: str) -> dict:
    response = requests.get(REGISTER_OF_LICENCED_SPONSORS_PAGE_URL)
    soup = BeautifulSoup(response.text, "html.parser")
    registry_link = soup.select_one(REGISTRY_LINK_CSS_SELECTOR)
    if registry_link and (registry_link_href := registry_link.get("href")):
        try:
            licensed_sponsors = pd.read_csv(registry_link_href)
            best_match = process.extractOne(company_name, licensed_sponsors[ORGANISATION_NAME_COLUMN_NAME].str.lower().str.strip(), scorer=fuzz.ratio)
            if best_match[1] == 100:
                return licensed_sponsors.iloc[best_match[2]].to_dict()
            return {"error": "no perfect match found search in the sponsor registry"}
        except Exception as e:
            return {"error": f"Error reading CSV file: {e}"}
    return {"error": "No link found"}

@mcp.tool()
def search_companies_house(company_name: str) -> dict:
    """Search for companies using Companies House API"""
    api_key = os.getenv("COMPANIES_HOUSE_API_KEY", "")
    if not api_key:
        return {"error": "API key required"}
    
    try:
        response = requests.get(
            f"{COMPANIES_HOUSE_API_BASE}/search/companies",
            params={"q": company_name},
            auth=(api_key, "")
        )
        response.raise_for_status()
        data = response.json()
        return [{"title": item["title"], "company_number": item["company_number"]}
                for item in data.get("items", [])]
    except Exception as e:
        return {"error": str(e)}

#GET https://api.company-information.service.gov.uk/search/companies
# Example of HTTP basic authentication
#For an API key of my_api_key, the following curl request demonstrates the setting of the Authorization HTTP request header, as defined by RFC2617:

#curl -XGET -u my_api_key: https://api.company-information.service.gov.uk/company/00000006
#GET /company/00000006 HTTP/1.1
#Host: api.company-information.service.gov.uk
#Authorization: Basic bXlfYXBpX2tleTo=
  




if __name__ == "__main__":
    mcp.run(transport="stdio")
