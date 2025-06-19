from dotenv import load_dotenv
import os
from .src.bridge_api.client import BridgeAPIClient
from .src.bridge_api import data 
import json
from typing import Optional, Literal, List
from enum import Enum
import logging
import sys
from fastmcp.server.context import Context
from fastmcp.server.dependencies import get_http_headers
# from src.flood_api.client import FloodZonesClient
# from src.miami_zoning.client import find_objects, find_by_zone
# from src.florida_parcels.client import FloridaParcelsClient

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
# Add file handler for logging to /tmp/bridgeoutput-mls.log
file_handler = logging.FileHandler('/tmp/bridgeoutput-mls.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger = logging.getLogger(__name__)
logger.addHandler(file_handler)

# Load environment variables from .env file
load_dotenv()

from fastmcp import FastMCP

mcp = FastMCP("RE MCP")
mcp.logger = logger

class PropertyType(str, Enum):
    RESIDENTIAL = "Residential"
    COMMERCIAL = "Commercial"

@mcp.resource("mls://schema/")
def mls_schema() -> str:
    """Fields available to filter"""
    return json.dumps(data.FIELDS)

def get_bridge_api_credentials():
    """
    Get API credentials from environment variables or Authorization header.
    Returns (api_key, dataset_id), falling back to None if not found.
    """
    # First try environment variables
    api_key = os.getenv('BRIDGE_DATA_OUTPUT_API_KEY')
    dataset_id = os.getenv('BRIDGE_DATASET_ID')
    
    # If not found in environment, try Authorization header
    if not (api_key and dataset_id):
        headers = get_http_headers()
        auth_header = headers.get("authorization")
        if auth_header and auth_header.lower().startswith("bearer "):
            try:
                creds = auth_header[7:].strip().split(":", 1)
                if len(creds) == 2:
                    dataset_id, api_key = creds
            except Exception as e:
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to parse Authorization header: {e}")
    
    return api_key, dataset_id

@mcp.tool()
async def mls_listing(listing_id: str, ctx: Context = None) -> str:
    """Return the listing details for a given ListingId; 
    
    This includes property information, photos, broker contact details, on market date, off market date, asking price, closing price, and more.
    """
    logger.debug(f"Fetching MLS listing with ID: {listing_id}")
    api_key, dataset_id = get_bridge_api_credentials()
    client = BridgeAPIClient(api_key=api_key, dataset_id=dataset_id)
    try:
        listing_data = await client.get_listing(listing_id)
        logger.debug(f"Successfully retrieved listing data for ID {listing_id}")
        return json.dumps(listing_data, indent=2)
    except Exception as e:
        logger.error(f"Error fetching listing {listing_id}: {str(e)}")
        # Try to return response body if available
        if hasattr(e, 'response') and e.response is not None:
            try:
                return e.response.text
            except Exception:
                pass
        return f"Error fetching listing: {str(e)}"

@mcp.prompt()
def find_comparables(property_info: str) -> str:
    """Find comparable properties based on provided property information.
    
    Args:
        property_info: string containing property details including:
            - Year built
            - Address (street, city, zip)
            - Subdivision name
            - Living area (square footage)
            - Number of bedrooms
            - Number of bathrooms
            - Other relevant property characteristics
            
    Returns:
        A prompt to help find comparable properties based on the provided information
    """
    return f"""
Find up to 10 comparable properties to this one. Take in account: location, subdivision, zipcode, living area and lot size area, bathrooms, bedrooms, year built, street level photo. Choose the most similar among 10-30 options, might be bigger or smaller properties, maybe not in the same subdivision (please use partial matches looking for similar subdivision names) but close enough (less than 1km if not on the same subdivision). Also search for similar listings even if they're not currently active but were in the last 180 days . For each comparable property return a text describing similitudes and differences, distance, listing price, days on market, etc; don't describe the other property, just highlight differences to base. Add public URLs to this properties if possible. Try also searching for previous listings of the base property and use that information to complement the input data; but please take in account the time that passed between the previous listing.  

Base property info: APN: 494120061250, Address:9311 NW 39 ST SUNRISE, 33351, State: FL

\n\n{property_info}

"""


@mcp.tool()
async def search_listings(
    query: str = "",
    min_price: int = None,
    max_price: int = None,
    beds: int = None,
    beds_min: int = None,
    beds_max: int = None,
    baths: float = None,
    baths_min: float = None,
    baths_max: float = None,
    LivingArea_min: int = None,
    LivingArea_max: int = None,
    LotSizeSquareFeet_min: int = None,
    LotSizeSquareFeet_max: int = None,
    on_market_date_from: str = None,
    on_market_date_to: str = None,
    off_market_date_from: str = None,
    off_market_date_to: str = None,
    property_type: Literal["Residential", "Condo"] = None,
    city: str = None,
    zipcode: str = None,
    latitude: float = None,
    longitude: float = None,
    distance_miles: float = None,
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
    StreetName: str = None,
    StreetSuffix: str = None,
    StreetNumber: str = None,
    SubdivisionName: str = None,
    ParcelNumber: str = None,
    YearBuilt_min: int = None,
    YearBuilt_max: int = None,
    ListPrice_min: int = None,
    ListPrice_max: int = None,
    PhotosCount_min: int = None,
    PhotosCount_max: int = None,
    ctx: Context = None
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
    api_key, dataset_id = get_bridge_api_credentials()
    client = BridgeAPIClient(api_key=api_key, dataset_id=dataset_id)
    
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
        return json.dumps(results['value'])
    except Exception as e:
        logger.error(f"Error searching listings: {str(e)}")
        # Try to return response body if available
        if hasattr(e, 'response') and e.response is not None:
            try:
                return e.response.text
            except Exception:
                pass
        return f"Error searching listings: {str(e)}"

@mcp.prompt()
def prompt_with_parcel_id(parcel_id: str) -> str:
    """Prompt to get more information about a parcel"""
    return f"Please provide more information about the parcel with ID: {parcel_id}"


# @mcp.tool()
# async def check_flood_zone(
#     address: str,
#     parcel_id: str,
#     latitude: float,
#     longitude: float
# ) -> str:
#     """
#     Check flood zone information for a given location
    
#     Args:
#         address: Full address string
#         parcel_id: Property parcel ID
#         latitude: Latitude coordinate
#         longitude: Longitude coordinate
#     """
#     logger.debug(
#         f"Checking flood zone for: address={address}, parcel_id={parcel_id}, "
#         f"coordinates=({latitude}, {longitude})"
#     )
#     client = FloodZonesClient()
    
#     try:
#         flood_data = await client.get_flood_zone(
#             address=address,
#             parcel_id=parcel_id,
#             coordinates=(longitude, latitude)  # Note: API expects (longitude, latitude) order
#         )
#         logger.debug(f"Successfully retrieved flood zone data for {address}")
#         return json.dumps(flood_data, indent=2)
#     except Exception as e:
#         logger.error(f"Error checking flood zone for {address}: {str(e)}")
#         return f"Error checking flood zone: {str(e)}"

# @mcp.tool()
# async def find_geometries_by_zone(
#     zone: str,
#     latitude: Optional[float] = None,
#     longitude: Optional[float] = None,
#     radius: Optional[float] = 1
# ) -> str:
#     """
#     Find objects by transect zone (T4, T5, etc.), optionally filtered by location
    
#     Args:
#         zone: The transect zone to search for (e.g., 'T4', 'T5')
#         latitude: Optional latitude to search near
#         longitude: Optional longitude to search near
#         radius: Search radius in kilometers (default: 1)
#     """
#     return json.dumps(find_by_zone(zone, lat=latitude, lon=longitude, radius=radius), indent=2)

# @mcp.tool()
# async def get_zoning_info(latitude: float, longitude: float) -> str:
#     """
#     Get zoning and land use information for a specific location in Miami
    
#     Args:
#         latitude: Latitude coordinate
#         longitude: Longitude coordinate
#     """
#     logger.debug(f"Getting zoning info for coordinates: ({latitude}, {longitude})")
    
#     try:
#         zoning_data = find_objects(latitude, longitude)
#         logger.debug(f"Successfully retrieved zoning data for ({latitude}, {longitude})")
#         return json.dumps(zoning_data, indent=2)
#     except Exception as e:
#         logger.error(f"Error checking zoning information: {str(e)}")
#         return f"Error checking zoning information: {str(e)}"

# @mcp.resource("echo://parcels/{parcel_id}")
# async def florida_parcels_resource(parcel_id: str) -> dict:
#     """Return the parcel details for a given parcel ID"""
#     logger.debug(f"Fetching parcel details for ID: {parcel_id}")
#     client = FloridaParcelsClient()
#     try:
#         parcel_data = client.get_parcel(parcel_id)
#         logger.debug(f"Successfully retrieved parcel data for ID {parcel_id}")
#         return parcel_data
#     except Exception as e:
#         logger.error(f"Error fetching parcel data for ID {parcel_id}: {str(e)}")
#         return f"Error fetching parcel data: {str(e)}"

# @mcp.tool()
# async def search_fl_parcels_detailed(
#     # Location search parameters
#     latitude: Optional[float] = None,
#     longitude: Optional[float] = None,
#     radius_km: Optional[float] = None,
    
#     # Identification fields
#     object_id: Optional[int] = None,
#     co_no: Optional[float] = None,
#     parcel_id: Optional[str] = None,
#     alt_key: Optional[str] = None,
#     state_par: Optional[str] = None,
    
#     # Assessment and value fields
#     asmnt_yr: Optional[float] = None,
#     jv: Optional[float] = None,
#     av_sd: Optional[float] = None,
#     av_nsd: Optional[float] = None,
#     tv_sd: Optional[float] = None,
#     tv_nsd: Optional[float] = None,
#     jv_hmstd: Optional[float] = None,
    
#     # Property characteristics
#     dor_uc: Optional[str] = None,
#     #dor_uc_code: Optional[str] = None,
#     pa_uc: Optional[str] = None,
#     lnd_val: Optional[float] = None,
#     eff_yr_blt: Optional[int] = None,
#     act_yr_blt: Optional[int] = None,
#     tot_lvg_ar: Optional[float] = None,
#     no_buldng: Optional[float] = None,
#     no_res_unt: Optional[float] = None,
    
#     # Sale information
#     sale_prc1: Optional[float] = None,
#     sale_yr1: Optional[float] = None,
#     sale_mo1: Optional[str] = None,
#     qual_cd1: Optional[str] = None,
    
#     # Owner information
#     own_name: Optional[str] = None,
#     own_addr1: Optional[str] = None,
#     own_city: Optional[str] = None,
#     own_state: Optional[str] = None,
#     own_zipcd: Optional[int] = None,
    
#     # Physical location
#     phy_addr1: Optional[str] = None,
#     phy_addr2: Optional[str] = None,
#     phy_city: Optional[str] = None,
#     phy_zipcd: Optional[int] = None,
    
#     # Geographic identifiers
#     census_bk: Optional[str] = None,
#     nbrhd_cd: Optional[str] = None,
#     twn: Optional[str] = None,
#     rng: Optional[str] = None,
#     sec: Optional[str] = None,
    
#     # Query control parameters
#     return_geometry: bool = False,
#     max_records: int = 10
# ) -> str:
#     """
#     Detailed search for Florida property parcels with all available search criteria. This includes all properties in Florida, not just the ones currently listed the market
    
#     Args:
#         # Location search parameters
#         latitude: Center point latitude for radius search
#         longitude: Center point longitude for radius search
#         radius_km: Search radius in kilometers
        
#         # Identification fields
#         object_id: Internal feature number
#         co_no: County Number
#         parcel_id: Parcel Identification Number
#         alt_key: Alternate Key
#         state_par: State Parcel ID
        
#         # Assessment and value fields
#         asmnt_yr: Assessment Year
#         jv: Just Value
#         av_sd: Assessed Value - School District
#         av_nsd: Assessed Value - Non-School District
#         tv_sd: Taxable Value - School District
#         tv_nsd: Taxable Value - Non-School District
#         jv_hmstd: Just Value - Homestead
        
#         # Property characteristics
#         dor_uc: Department of Revenue Use Code (numeric code)

#         pa_uc: Property Appraiser Use Code
#         lnd_val: Land Value
#         eff_yr_blt: Effective Year Built - Adjusted year reflecting renovations/updates
#         act_yr_blt: Actual Year Built - Original construction completion year
#         tot_lvg_ar: Total Living Area - Square footage of living space
#         no_buldng: Number of Buildings on the parcel
#         no_res_unt: Number of Residential Units (for multi-family properties)
        
#         # Sale information
#         sale_prc1: Sale Price (most recent)
#         sale_yr1: Sale Year (most recent)
#         sale_mo1: Sale Month (most recent)
#         qual_cd1: Sale Qualification Code
        
#         # Owner information
#         own_name: Owner Name
#         own_addr1: Owner Address
#         own_city: Owner City
#         own_state: Owner State
#         own_zipcd: Owner Zip Code
        
#         # Physical location
#         phy_addr1: Physical Address
#         phy_addr2: Physical Address Line 2
#         phy_city: Physical City
#         phy_zipcd: Physical Zip Code
        
#         # Geographic identifiers
#         census_bk: Census Block
#         nbrhd_cd: Neighborhood Code
#         twn: Township
#         rng: Range
#         sec: Section
        
#         # Query control parameters
#         return_geometry: Whether to return parcel geometries
#         max_records: Maximum number of records to return (default: 100)
#     """
#     logger.debug("Searching FL parcels with detailed parameters")
    
#     client = FloridaParcelsClient()
    
#     try:
#         # Build query parameters from all non-None values
#         query_params = {k: v for k, v in locals().items() 
#                        if v is not None and k not in ['client']}
#         logger.debug(f"Query parameters: {query_params}")   
        
#         results = client.query_with_params(**query_params)
#         logger.debug(f"Search results: {results}")
#         logger.debug(f"Search returned {len(results.get('features', []))} results")
        
#         # Format results for better readability
#         formatted_results = []
#         for feature in results.get('features', []):
#             attrs = feature['attributes']
#             # # Include all available fields in the response
#             # formatted_result = {
#             #     key.lower(): attrs.get(key.upper())
#             #     for key in [
#             #         'PARCEL_ID', 'PHY_ADDR1', 'PHY_ADDR2', 'PHY_CITY', 'PHY_ZIPCD',
#             #         'OWN_NAME', 'JV', 'TOT_LVG_AR', 'SALE_PRC1', 'SALE_YR1',
#             #         'NO_BULDNG', 'NO_RES_UNT', 'DOR_UC', 'PA_UC',
#             #         'ASMNT_YR', 'LND_VAL'
#             #     ]
#             # }
#             formatted_results.append(attrs)
            
#         return json.dumps(formatted_results, indent=2)
#     except Exception as e:
#         logger.error(f"Error searching FL parcels: {str(e)}")
#         return f"Error searching FL parcels: {str(e)}"

@mcp.tool()
async def get_parcel_public_records(
    state: str,
    apn: str,
    zip_code: str,
    ctx: Context = None
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
        records = await client.get_parcel_public_records(state, apn, zip_code)
        return json.dumps(records, indent=2)
    except Exception as e:
        logger.error(f"Error fetching parcel public records: {str(e)}")
        # Try to return response body if available
        if hasattr(e, 'response') and e.response is not None:
            try:
                return e.response.text
            except Exception:
                pass
        return f"Error fetching parcel public records: {str(e)}"
if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=int(os.environ.get("PORT",'8080')), path="/mcp")
