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

COMPANIES_HOUSE_API_KEY = os.getenv("COMPANIES_HOUSE_API_KEY", "")
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

# See https://forum.companieshouse.gov.uk/t/status-code-401/6607/2 for more details on how to connect to Companies House API

@mcp.tool()
def search_in_companies_house(company_name: str) -> dict:
    """Search for companies using Companies House API"""
    try:
        response = requests.get(
            f"{COMPANIES_HOUSE_API_BASE}/search/companies",
            params={"q": company_name},
            auth=(COMPANIES_HOUSE_API_KEY, "")
        )
        response.raise_for_status()
        data = response.json()
        return [{"title": item["title"], "company_number": item["company_number"]}
                for item in data.get("items", [])]
    except Exception as e:
        return {"error": str(e)}
  
@mcp.tool()
def get_company_profile_from_companies_house(company_number: str) -> dict:
    """Get company details using Companies House API"""
    try:
        response = requests.get(
            f"{COMPANIES_HOUSE_API_BASE}/company/{company_number}",
            auth=(COMPANIES_HOUSE_API_KEY, "")
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        if response.status_code == 404:
            return {"error": "Company not found in Companies House. Check the company number."}
        return {"error": str(e)}

@mcp.tool()
def get_company_officers_from_companies_house(company_number: str) -> dict:
    """Get company officers using Companies House API"""
    try:
        response = requests.get(
            f"{COMPANIES_HOUSE_API_BASE}/company/{company_number}/officers",
            auth=(COMPANIES_HOUSE_API_KEY, "")
        )
        response.raise_for_status()
        data = response.json()
        return {
            "active_count": data.get("active_count"),
            "officers": [{k: officer.get(k) for k in ["name", "officer_role", "appointed_on", "is_pre_1992_appointment", "occupation"]} for officer in data.get("items", [])],
            "resigned_count": data.get("resigned_count"),
            "inactive_count": data.get("inactive_count"),
            "total_results": data.get("total_results")
        }
    except Exception as e:
        if response.status_code == 404:
            return {"error": "Company not found in Companies House. Check the company number."}
        return {"error": str(e)}

if __name__ == "__main__":
    mcp.run(transport="stdio")