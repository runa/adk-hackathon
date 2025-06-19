import logging
import httpx
from typing import Optional, Dict, Any, List
import os
from dotenv import load_dotenv

logger = logging.getLogger("bridge_api.client")

class BridgeAPIClient:
    """Client for interacting with Bridge/RESO Web API"""
    
    # Default fields to return in search results
    DEFAULT_SELECT_FIELDS = [
        "ListingId",
        "PropertyType",
        "ListPrice",
        "BedroomsTotal",
        "BathroomsTotalDecimal",
        "LivingArea",
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
        "Longitude"
    ]
    
    def __init__(self, api_key, dataset_id):
        load_dotenv()
        self.api_key = api_key 
        self.dataset_id = dataset_id
        
        if not self.api_key:
            raise ValueError("API key is required")
        if not self.dataset_id:
            raise ValueError("Dataset ID is required")
        
        self.base_url = f"https://api.bridgedataoutput.com/api/v2/OData/{self.dataset_id}"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }
    
    async def get_listing(self, listing_id: str) -> Dict[Any, Any]:
        """
        Fetch a specific listing by ID; this includes much more information, photographs, etc
        
        Args:
            listing_id: The MLS listing ID
            
        Returns:
            Dict containing the listing data
        """
        url = f"{self.base_url}/Property('{listing_id}')"
        logger.debug(f"Making GET request to: {url}")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=self.headers
            )
            logger.debug(f"Response status: {response.status_code}, headers: {response.headers}, content length: {len(response.content)}")
            
            response.raise_for_status()
            return response.json()
    
    def _create_geo_filter(
        self,
        latitude: float,
        longitude: float,
        distance_miles: float
    ) -> str:
        """
        Create a geographic bounding box filter for OData query
        
        Args:
            latitude: Center point latitude
            longitude: Center point longitude
            distance_miles: Maximum distance in miles from center point
            
        Returns:
            String containing the OData filter expression for the bounding box
        """
        import math
        # Convert miles to degrees (approximate)
        # 1 degree of latitude = ~69 miles
        # 1 degree of longitude = ~69 miles * cos(latitude)
        lat_degrees = distance_miles / 69.0
        lon_degrees = distance_miles / (69.0 * math.cos(math.radians(latitude)))
        
        # Create bounding box coordinates
        min_lat = latitude - lat_degrees
        max_lat = latitude + lat_degrees
        min_lon = longitude - lon_degrees
        max_lon = longitude + lon_degrees
        
        return f"Latitude ge {min_lat} and Latitude le {max_lat} and Longitude ge {min_lon} and Longitude le {max_lon}"

    async def search_listings(
        self, 
        query: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        distance_miles: Optional[float] = None,
        order_by: Optional[str] = None,
        top: Optional[int] = None,
        skip: Optional[int] = None,
        select_fields: Optional[List[str]] = None
    ) -> Dict[Any, Any]:
        """
        Search listings using OData query parameters
        
        Args:
            query: OData formatted query string
            latitude: Center point latitude for geo search
            longitude: Center point longitude for geo search
            distance_miles: Maximum distance in miles from center point
            order_by: Field and direction to sort by
            top: Maximum number of results to return
            skip: Number of results to skip
            select_fields: List of fields to return (defaults to DEFAULT_SELECT_FIELDS)
            
        Returns:
            Dict containing search results
        """
        # If geo search parameters are provided, create bounding box filter
        if all(x is not None for x in [latitude, longitude, distance_miles]):
            geo_filter = self._create_geo_filter(latitude, longitude, distance_miles)
            query = f"({query}) and {geo_filter}" if query else geo_filter

        params = [f"$filter={query}"]
        
        # Use default fields if none specified
        fields = select_fields if select_fields is not None else self.DEFAULT_SELECT_FIELDS
        params.append(f"$select={','.join(fields)}")
        
        if order_by:
            params.append(f"$orderby={order_by}")
        if top is not None:
            params.append(f"$top={top}")
        if skip is not None:
            params.append(f"$skip={skip}")
        
        query_string = "&".join(params)
        logger.debug(f"Sending request to: {self.base_url}/Property?{query_string} with headers: {self.headers}")
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/Property?{query_string}",
                headers=self.headers
            )
            response.raise_for_status()
            logger.debug(f"Response status: {response.status_code}, headers: {response.headers}, content length: {len(response.content)}")
            return response.json() 
        
    def get_parcel_public_records(
        self,
        state: str,
        apn: str,
        zip_code: str
    ) -> Dict[Any, Any]:
        """
        Search for a specific parcel and return its public records.
        Args:
            state: The state where the parcel is located (e.g., 'CA')
            apn: The Assessor's Parcel Number
            zip_code: The ZIP code of the parcel
        Returns:
            Dict containing the parcel's public records
        """
        # Use the Bridge Data Output public parcels API
        # See: https://bridgedataoutput.com/docs/explorer/public-data#listParcels
        base_url = "https://api.bridgedataoutput.com/api/v2/pub/parcels/"
        params = {
            "state": state,
            "apn": apn,
            "address.zip": zip_code,
            "access_token": self.api_key
        }
        logger.debug(f"Requesting parcel public records: {base_url} with params: {params}")
        with httpx.AsyncClient() as client:
            response = client.get(base_url, params=params)
            logger.debug(f"Response status: {response.status_code}, headers: {response.headers}, content length: {len(response.content)}")
            response.raise_for_status()
            return response.json()
    
    