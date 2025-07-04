import logging
from typing import List
import os

import requests
from fastmcp import FastMCP
from rapidfuzz import fuzz, process
from dotenv import load_dotenv
from cache import register_data

# Load environment variables from .env file
load_dotenv()

mcp = FastMCP("licensed-sponsor-swv-mcp")

COMPANIES_HOUSE_API_KEY = os.getenv("COMPANIES_HOUSE_API_KEY", "")
ORGANISATION_NAME_COLUMN_NAME = "Organisation Name"
COMPANIES_HOUSE_API_BASE = "https://api.company-information.service.gov.uk"

@mcp.tool()
def search_in_sponsors_register(company_name: str) -> dict:
    """
    Search for companies in the UK's register of licensed sponsors.
    
    This function searches the government's register of licensed sponsors for
    companies that match the provided company name. It uses fuzzy string matching
    to find similar company names and returns the top 10 matches with their
    similarity scores.
    
    Args:
        company_name (str): The name of the company to search for. The search
                           is case-insensitive and whitespace is stripped.
    
    Returns:
        dict: A dictionary containing the search results with keys:
              - 'search_company_name': The normalized search term used
              - 'match': Boolean indicating if a perfect match was found
              - 'results': List of matching company names from the register
    """
    company_name = company_name.lower().strip()
    if register_data is None:
        return {"error": "Register data not available"}
    
    matches = process.extract(company_name, register_data[ORGANISATION_NAME_COLUMN_NAME].str.lower().str.strip(), limit=10, scorer=fuzz.ratio)
    results = [register_data[ORGANISATION_NAME_COLUMN_NAME].iloc[m[2]] for m in matches]
    match = any(m[1] == 100 for m in matches)
    return {
        "search_company_name": company_name,
        "match": match,
        "results": results
    }

@mcp.tool()
def get_company_from_sponsors_register(company_name: str) -> dict:
    """
    Get detailed information for a specific company from the licensed sponsors register.
    
    This function retrieves comprehensive details about a company from the UK's
    register of licensed sponsors. It requires a perfect match (100% similarity)
    with a company name in the register to return the company's information.
    
    Args:
        company_name (str): The exact name of the company to retrieve details for.
                           The search is case-insensitive and whitespace is stripped.
    
    Returns:
        dict: A dictionary containing all available company information from the
              register when a perfect match is found.
    """
    company_name = company_name.lower().strip()
    if register_data is None:
        return {"error": "Register data not available"}
    
    best_match = process.extractOne(company_name, register_data[ORGANISATION_NAME_COLUMN_NAME].str.lower().str.strip(), scorer=fuzz.ratio)
    if best_match[1] == 100:
        return register_data.iloc[best_match[2]].to_dict()
    return {"error": "no perfect match found search in the sponsors register"}

# See https://forum.companieshouse.gov.uk/t/status-code-401/6607/2 for more details on how to connect to Companies House API

@mcp.tool()
def search_in_companies_house(company_name: str) -> dict:
    """
    Search for companies using the Companies House API.
    
    This function searches the UK Companies House database for companies that
    match the provided company name. It uses the official Companies House API
    to perform the search and returns basic information about matching companies.
    
    Args:
        company_name (str): The name of the company to search for in the
                           Companies House database.
    
    Returns:
        dict: A dictionary containing the search results with keys:
              - 'search_company_name': The search term used
              - 'companies': List of company information dictionaries
    """
    try:
        response = requests.get(
            f"{COMPANIES_HOUSE_API_BASE}/search/companies",
            params={"q": company_name},
            auth=(COMPANIES_HOUSE_API_KEY, "")
        )
        response.raise_for_status()
        data = response.json()
        companies = [{"title": item["title"], "company_number": item["company_number"]}
                     for item in data.get("items", [])]
        return {
            "search_company_name": company_name,
            "companies": companies
        }
    except Exception as e:
        return {"error": str(e)}
  
@mcp.tool()
def get_company_profile_from_companies_house(company_number: str) -> dict:
    """
    Get detailed company profile information from Companies House.
    
    This function retrieves comprehensive company information from the UK
    Companies House database using the company's unique registration number.
    It provides detailed profile data including company status, incorporation
    date, registered address, and other official company information.
    
    Args:
        company_number (str): The unique company registration number assigned
                             by Companies House (e.g., "12345678").
    
    Returns:
        dict: A dictionary containing detailed company profile information
              from Companies House.
    """
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
    """
    Get company officers information from Companies House.
    
    This function retrieves information about a company's officers (directors,
    secretaries, etc.) from the UK Companies House database. It provides details
    about current and former officers including their roles, appointment dates,
    and other relevant information.
    
    Args:
        company_number (str): The unique company registration number assigned
                             by Companies House (e.g., "12345678").
    
    Returns:
        dict: A dictionary containing officers information with keys:
              - 'active_count': Number of currently active officers
              - 'officers': List of officer details including name, role, and dates
              - 'resigned_count': Number of resigned officers
              - 'inactive_count': Number of inactive officers
              - 'total_results': Total number of officers found
    """
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

@mcp.prompt()
def check_if_company_is_licensed_sponsor(company_name: str) -> str:
    return f"""Company name: {company_name}
    You are a helpful assistant that checks if a company is a licensed sponsor.
    You will be given a company name and you will need to check if it is a licensed sponsor.
    """

@mcp.prompt()
def check_company_full_profile(company_name: str) -> str:
    return f"""Company name: {company_name}
    You are a helpful assistant that does a full check of a company's profile.
    You will be given a company name and you will need to check if it is a licensed sponsor and the company's information in companies house.
    Follow the following steps:
    1. Search for the company in the sponsors register
    2. If the company is found in the sponsors register, get the details of the company from the sponsors register
    3. Search for the company in companies house
    4. If the company is found in companies house, get the profile of the company from companies house
    5. Get the officers of the company from companies house
    6. Write a summary of the company's profile (main information) and the company's officers
    """

if __name__ == "__main__":
    mcp.run(transport="stdio")