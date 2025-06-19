# ./adk_agent_samples/mcp_agent/agent.py
import logging
import os
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from google.adk.tools import google_search
google_maps_api_key = os.environ.get("GOOGLE_MAPS_API_KEY")

# Retrieve the API key from an environment variable or directly insert it.
# Using an environment variable is generally safer.
# Ensure this environment variable is set in the terminal where you run 'adk web'.
# Example: export BRIDGE_OUTPUT_DATA_API_KEY="YOUR_ACTUAL_KEY"
bridge_output_data_api_key = os.environ.get("BRIDGE_OUTPUT_DATA_API_KEY")
bridge_dataset_id = os.environ.get("BRIDGE_DATASET_ID")

if not bridge_output_data_api_key:
    # Fallback or direct assignment for testing - NOT RECOMMENDED FOR PRODUCTION
    bridge_output_data_api_key = "YOUR_BRIDGE_OUTPUT_DATA_API_KEY_HERE" # Replace if not using env var
    if bridge_output_data_api_key == "YOUR_BRIDGE_OUTPUT_DATA_API_KEY_HERE":
        print("WARNING: BRIDGE_OUTPUT_DATA_API_KEY is not set. Please set it as an environment variable or in the script.")
        # You might want to raise an error or exit if the key is crucial and not found.
TARGET_FOLDER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../bridgeoutput_mls/")

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search
from google.genai import types
from typing import Optional, Literal, List
from enum import Enum

from dotenv import load_dotenv
import os
from agent.agents.bridgeoutput_agent.bridge_api.client import BridgeAPIClient
from agent.agents.bridgeoutput_agent.bridge_api import data 
logger = logging.getLogger(__name__)

class PropertyType(str, Enum):
    RESIDENTIAL = "Residential"
    COMMERCIAL = "Commercial"


async def mls_listing(listing_id: str) -> str:
    """Return the listing details for a given ListingId; 
    
    This includes property information, photos, broker contact details, on market date, off market date, asking price, closing price, and more.
    """
    logger.debug(f"Fetching MLS listing with ID: {listing_id}")
    api_key, dataset_id = get_bridge_api_credentials()
    client = BridgeAPIClient(api_key=api_key, dataset_id=dataset_id)
    try:
        listing_data = await client.get_listing(listing_id)
        logger.debug(f"Successfully retrieved listing data for ID {listing_id}")
        return listing_data
    except Exception as e:
        logger.error(f"Error fetching listing {listing_id}: {str(e)}")
        # Try to return response body if available
        if hasattr(e, 'response') and e.response is not None:
            try:
                return e.response.text
            except Exception:
                pass
        return f"Error fetching listing: {str(e)}"



async def search_listings(
    query: str = "",
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    beds: Optional[int] = None,
    beds_min: Optional[int] = None,
    beds_max: Optional[int] = None,
    baths: Optional[float] = None,
    baths_min: Optional[float] = None,
    baths_max: Optional[float] = None,
    LivingArea_min: Optional[int] = None,
    LivingArea_max: Optional[int] = None,
    LotSizeSquareFeet_min: Optional[int] = None,
    LotSizeSquareFeet_max: Optional[int] = None,
    on_market_date_from: Optional[str] = None,
    on_market_date_to: Optional[str] = None,
    off_market_date_from: Optional[str] = None,
    off_market_date_to: Optional[str] = None,
    property_type: Optional[Literal["Residential", "Condo"]] = None,
    city: Optional[str] = None,
    zipcode: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    distance_miles: Optional[float] = None,
    mls_status: Literal["Active", "Closed", "Any"] = "Active",  # Default to active listings
    order_by: str = "ListPrice desc",  # Default sort by price descending
    limit: int = 2,  # Default to 2 results
    skip: int = 0,  # Default to first page
    fields: List[Literal[
        "ListingId",
        "PropertyType",
        "ListPrice",
        "BedroomsTotal",
        "BathroomsTotalDecimal",
        "LivingArea",
        "LotSizeSquareFeet",
        "StreetNumber",
        "StreetName",
        "YearBuilt",
        "StreetSuffix",
        "City",
        "StateOrProvince",
        "PostalCode",
        "ListingContractDate",
        "PublicRemarks",
        "PhotosCount",
        "Latitude",
        "Longitude",
        "SubdivisionName"
    ]] = [
        "ListingId",
        "PropertyType",
        "ListPrice",
        "BedroomsTotal",
        "BathroomsTotalDecimal",
        "LivingArea",
        "LotSizeSquareFeet",
        "StreetNumber",
        "StreetName",
        "YearBuilt",
        "StreetSuffix",
        "City",
        "StateOrProvince",
        "PostalCode",
        "ListingContractDate",
        "PublicRemarks",
        "PhotosCount",
        "Latitude",
        "Longitude",
        "SubdivisionName"
    ],
    StreetName: Optional[str] = None,
    StreetSuffix: Optional[str] = None,
    StreetNumber: Optional[str] = None,
    SubdivisionName: Optional[str] = None,
    ParcelNumber: Optional[str] = None,
    YearBuilt_min: Optional[int] = None,
    YearBuilt_max: Optional[int] = None,
    ListPrice_min: Optional[int] = None,
    ListPrice_max: Optional[int] = None,

) -> str:
    """
    Search MLS listings for properties on sale or rent with various criteria
    
    Args:
        query: Valid OData filter string, field names come from mls://schema/
        min_price: Minimum listing price
        max_price: Maximum listing price
        beds: Number of bedrooms (exact match)
        beds_min: Minimum number of bedrooms
        beds_max: Maximum number of bedrooms
        baths: Number of bathrooms (exact match)
        baths_min: Minimum number of bathrooms
        baths_max: Maximum number of bathrooms
        LivingArea_min: Minimum living area in square feet
        LivingArea_max: Maximum living area in square feet
        LotSizeSquareFeet_min: Minimum lot size in square feet
        LotSizeSquareFeet_max: Maximum lot size in square feet
        on_market_date_from: Filter for listings with OnMarketDate on or after this date (YYYY-MM-DD)
        on_market_date_to: Filter for listings with OnMarketDate on or before this date (YYYY-MM-DD)
        off_market_date_from: Filter for listings with OffMarketDate on or after this date (YYYY-MM-DD)
        off_market_date_to: Filter for listings with OffMarketDate on or before this date (YYYY-MM-DD)
        property_type: Type of property ("Residential" or "Condo")
        city: City name
        zipcode: ZIP/Postal code
        latitude: Center point latitude for geo search
        longitude: Center point longitude for geo search
        distance_miles: Maximum distance in miles from center point
        mls_status: Filter by MLS status ("Active" or "Closed", defaults to "Active")
        order_by: Field to sort by (e.g., "ListPrice desc", "ListPrice asc", "BedroomsTotal desc")
        limit: Maximum number of results to return (default: 2)
        skip: Number of results to skip for pagination (default: 0)
        fields: Optional list of specific fields to return (defaults to main features)
        StreetName: Optional Street Name
        StreetSuffix: Optional Street Suffix
        StreetNumber: Optional Street Number
        SubdivisionName: Optional Subdivision Name
        ParcelNumber: Optional Parcel Number (also called APN)
    """
    logger.debug(
        f"Searching listings with params: min_price={min_price}, max_price={max_price}, "
        f"beds={beds}, beds_min={beds_min}, beds_max={beds_max}, baths={baths}, baths_min={baths_min}, baths_max={baths_max}, "
        f"LivingArea_min={LivingArea_min}, LivingArea_max={LivingArea_max}, "
        f"LotSizeSquareFeet_min={LotSizeSquareFeet_min}, LotSizeSquareFeet_max={LotSizeSquareFeet_max}, "
        f"on_market_date_from={on_market_date_from}, on_market_date_to={on_market_date_to}, off_market_date_from={off_market_date_from}, off_market_date_to={off_market_date_to}, "
        f"property_type={property_type}, city={city}, "
        f"zipcode={zipcode}, lat/long=({latitude},{longitude}), distance={distance_miles}, "
        f"status={mls_status}, limit={limit}, skip={skip}, "
        f"StreetName={StreetName}, StreetSuffix={StreetSuffix}, StreetNumber={StreetNumber}, SubdivisionName={SubdivisionName}, ParcelNumber={ParcelNumber}"
    )
    client = BridgeAPIClient(api_key=bridge_output_data_api_key, dataset_id=bridge_dataset_id)
    
    # Build OData filter query
    filters = []
    
    if min_price is not None:
        filters.append(f"ListPrice ge {min_price}")
    if max_price is not None:
        filters.append(f"ListPrice le {max_price}")
    if beds is not None:
        filters.append(f"BedroomsTotal eq {beds}")
    if beds_min is not None:
        filters.append(f"BedroomsTotal ge {beds_min}")
    if beds_max is not None:
        filters.append(f"BedroomsTotal le {beds_max}")
    if baths is not None:
        filters.append(f"BathroomsTotalDecimal eq {baths}")
    if baths_min is not None:
        filters.append(f"BathroomsTotalDecimal ge {baths_min}")
    if baths_max is not None:
        filters.append(f"BathroomsTotalDecimal le {baths_max}")
    if LivingArea_min is not None:
        filters.append(f"LivingArea ge {LivingArea_min}")
    if LivingArea_max is not None:
        filters.append(f"LivingArea le {LivingArea_max}")
    if LotSizeSquareFeet_min is not None:
        filters.append(f"LotSizeSquareFeet ge {LotSizeSquareFeet_min}")
    if LotSizeSquareFeet_max is not None:
        filters.append(f"LotSizeSquareFeet le {LotSizeSquareFeet_max}")
    if on_market_date_from is not None:
        filters.append(f"OnMarketDate ge {on_market_date_from}")
    if on_market_date_to is not None:
        filters.append(f"OnMarketDate le {on_market_date_to}")
    if off_market_date_from is not None:
        filters.append(f"OffMarketDate ge {off_market_date_from}")
    if off_market_date_to is not None:
        filters.append(f"OffMarketDate le {off_market_date_to}")
    if property_type is not None:
        if property_type not in [pt.value for pt in PropertyType]:
            raise ValueError(f'property_type must be one of: {", ".join(pt.value for pt in PropertyType)}')
        filters.append(f"PropertyType eq '{property_type}'")
    if city is not None:
        filters.append(f"City eq '{city}'")
    if zipcode is not None:
        filters.append(f"PostalCode eq '{zipcode}'")
    if mls_status is not None and mls_status != "Any":
        if mls_status not in ["Active", "Closed"]:
            raise ValueError('mls_status must be either "Active" or "Closed"')
        filters.append(f"MlsStatus eq '{mls_status}'")
    if YearBuilt_min is not None:
        filters.append(f"YearBuilt ge {YearBuilt_min}")
    if YearBuilt_max is not None:
        filters.append(f"YearBuilt le {YearBuilt_max}")
    if ListPrice_min is not None:
        filters.append(f"ListPrice ge {ListPrice_min}")
    if ListPrice_max is not None:
        filters.append(f"ListPrice le {ListPrice_max}")
    if StreetName is not None:
        filters.append(f"tolower(StreetName) eq '{StreetName.lower()}'")
    if StreetSuffix is not None:
        filters.append(f"tolower(StreetSuffix) eq '{StreetSuffix.lower()}'")
    if StreetNumber is not None:
        filters.append(f"tolower(StreetNumber) eq '{StreetNumber.lower()}'")
    if SubdivisionName is not None:
        filters.append(f"contains(tolower(SubdivisionName), '{SubdivisionName.lower()}')")
    if ParcelNumber is not None:
        filters.append(f"ParcelNumber eq '{ParcelNumber}'")
    
    if query != "": 
        query += " and "
        
    query += " and ".join(filters) if filters else " 1 eq 1"
    
    logger.debug(f"Generated OData query: {query}")
    
    try:
        results = await client.search_listings(
            query,
            latitude=latitude,
            longitude=longitude,
            distance_miles=distance_miles,
            order_by=order_by,
            top=limit,
            skip=skip,
            select_fields=fields
        )
        logger.debug(f"Search returned {len(results['value'])} results")
        logger.debug(f"Results: {results}")        
        return results['value']
    except Exception as e:
        logger.error(f"Error searching listings: {str(e)}")
        # Try to return response body if available
        if hasattr(e, 'response') and e.response is not None:
            try:
                return e.response.text
            except Exception:
                pass
        return f"Error searching listings: {str(e)}"


def get_parcel_public_records(
    state: str,
    apn: str,
    zip_code: str,
) -> str:
    """
    Search for a specific parcel and return its public records; this includes information from the point of view of the County Property Appraiser

    Main properties a County Property Appraiser might have about a parcel:
    - Parcel ID (APN)
    - Property Address
    - Property Type (Residential, Commercial, etc.)
    - Land Use (Single Family Residence, Agricultural, etc.)
    - Land Value
    - Building Value
    - Total Value
    - Year Built
    - Square Footage
    - Bedrooms
    - Bathrooms
    - Acres
    - Zoning
    - Tax District
    - School District
    - Last Sale Date
    - Last Sale Price
    - Owner Information (Name, Address)
    Args:
        state: The state where the parcel is located (e.g., 'CA')
        apn: The Assessor's Parcel Number
        zip_code: The ZIP code of the parcel
    Returns:
        Dict containing the parcel's public records
    """    
    api_key, dataset_id = get_bridge_api_credentials()
    if not apn:
        raise ValueError("APN (Assessor's Parcel Number) is required and cannot be blank")
    client = BridgeAPIClient(api_key=api_key, dataset_id=dataset_id)
    try:
        records =  client.get_parcel_public_records(state, apn, zip_code)
        records
    except Exception as e:
        logger.error(f"Error fetching parcel public records: {str(e)}")
        # Try to return response body if available
        if hasattr(e, 'response') and e.response is not None:
            try:
                return e.response.text
            except Exception:
                pass
        return f"Error fetching parcel public records: {str(e)}"



root_agent = LlmAgent(
    model='gemini-2.0-flash',
    name='bridgeoutput_agent',
    instruction="""You are a real estate agent who can find comparables for a base property; 
    Comparables are properties that are currently listed or were listed in the last year that have similar:

* property type (single family, condo, etc)
* location
* subdivision
* zipcode
* living area
* lot size area
* bathrooms
* bedrooms
* year built

When looking for comparables, location is the most important factor, then, living area and lot size, year built and the amount of bedrooms and bathrooms; you might evaluate bigger or smaller properties even if they're not in the same subdivision.

A property in the same subdivision with roughly the same year built, lot size, living are, bathrooms and bedrooms is a great comparable

Start by getting parcel information from the base property (from the county records), then search for previous listing of the base property and then use that information to complement the input data.

When filtering for subdivision names, make sure to use the important part in the name, not the whole text; for example, if the subdivision name is "WELLEBY UNIT 2", you should filter for "WELLEBY" not "WELLEBY UNIT 2".

Also add asking price, days on market and the distance to the base property in km to each comparable.

Listings include PublicRemarks describing the property; it might be interesting to extract the following information:

* pool 
* bathroom notes
* kitchen notes (appliances, furniture, etc)
* paint
* floors
* roof notes
* rennovations notes
* needs work

Find at least 4 comparables; if you can't find 4, keep relaxing filters; prioritize the closest properties even if they're not the same size.

""",
    tools=[
        MCPToolset(
            connection_params=StdioServerParameters(
                command='npx',
                args=[
                    "-y",
                    "@modelcontextprotocol/server-google-maps",
                ],
                # Pass the API key as an environment variable to the npx process
                # This is how the MCP server for Google Maps expects the key.
                env={
                    "GOOGLE_MAPS_API_KEY": google_maps_api_key
                }
            ),
            # You can filter for specific Maps tools if needed:
            # tool_filter=['get_directions', 'find_place_by_id']
        ),        
        mls_listing,
        get_parcel_public_records,
        search_listings
    ],
    output_key="comparables"
)