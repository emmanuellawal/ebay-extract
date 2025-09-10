"""
eBay API Client Module

This module provides comprehensive eBay API integration including:
- Browse API for item searches
- Taxonomy API for category mapping
- Catalog API for product identifiers
- Price analysis and sell time estimation
"""

import requests
import os
import logging
from typing import Optional, Dict, Any, List, Tuple
from dotenv import load_dotenv
from auth import get_ebay_token

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

class EbayAPIClient:
    """Comprehensive eBay API client with all required functionality."""
    
    def __init__(self, use_sandbox: bool = True):
        """
        Initialize eBay API client.
        
        Args:
            use_sandbox: If True, use sandbox environment; if False, use production
        """
        self.use_sandbox = use_sandbox
        self.marketplace_id = os.getenv("EBAY_MARKETPLACE_ID", "EBAY_US")
        
        if use_sandbox:
            self.base_url = "https://api.sandbox.ebay.com"
        else:
            self.base_url = "https://api.ebay.com"
        
        self.browse_url = f"{self.base_url}/buy/browse/v1"
        self.taxonomy_url = f"{self.base_url}/commerce/taxonomy/v1"
        self.catalog_url = f"{self.base_url}/commerce/catalog/v1_beta"
    
    def _get_headers(self, token: str) -> Dict[str, str]:
        """Get standard headers for API requests."""
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "X-EBAY-C-MARKETPLACE-ID": self.marketplace_id
        }
    
    def search_items(self, 
                    keywords: str, 
                    category_id: Optional[str] = None,
                    limit: int = 50,
                    sort: str = "price",
                    condition: Optional[str] = None) -> Dict[str, Any]:
        """
        Search for items using the Browse API.
        
        Args:
            keywords: Search keywords
            category_id: Optional eBay category ID
            limit: Maximum number of results (max 200)
            sort: Sort order (price, distance, endTime, etc.)
            condition: Item condition filter
            
        Returns:
            Dict containing search results
            
        Raises:
            Exception: If API call fails
        """
        token = get_ebay_token(use_sandbox=self.use_sandbox)
        url = f"{self.browse_url}/item_summary/search"
        
        headers = self._get_headers(token)
        params = {
            "q": keywords,
            "limit": min(limit, 200),  # eBay API limit
            "sort": sort
        }
        
        if category_id:
            params["category_ids"] = category_id
        
        if condition:
            params["filter"] = f"conditionIds:{{{condition}}}"
        
        try:
            logger.info(f"Searching eBay for: {keywords}")
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Found {len(data.get('itemSummaries', []))} items")
                return data
            else:
                error_msg = f"Browse API failed with status {response.status_code}: {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error during Browse API call: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def get_category_suggestions(self, item_type: str) -> Optional[str]:
        """
        Get eBay category ID for an item type using Taxonomy API.
        
        Args:
            item_type: Type of item (e.g., "camera", "watch", "book")
            
        Returns:
            str: Category ID if found, None otherwise
        """
        token = get_ebay_token(use_sandbox=self.use_sandbox)
        url = f"{self.taxonomy_url}/category_tree/0/get_category_suggestions"
        
        headers = self._get_headers(token)
        params = {"q": item_type}
        
        try:
            logger.info(f"Getting category suggestions for: {item_type}")
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                suggestions = data.get("categorySuggestions", [])
                
                if suggestions:
                    category_id = suggestions[0]["category"]["categoryId"]
                    logger.info(f"Found category ID: {category_id}")
                    return category_id
                else:
                    logger.warning(f"No category suggestions found for: {item_type}")
                    return None
            else:
                logger.warning(f"Taxonomy API failed with status {response.status_code}: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"Network error during Taxonomy API call: {str(e)}")
            return None
    
    def search_catalog(self, 
                      identifier: str, 
                      identifier_type: str = "UPC") -> Optional[Dict[str, Any]]:
        """
        Search catalog using product identifiers.
        
        Args:
            identifier: Product identifier (UPC, EAN, etc.)
            identifier_type: Type of identifier (UPC, EAN, etc.)
            
        Returns:
            Dict containing catalog data if found, None otherwise
        """
        token = get_ebay_token(use_sandbox=self.use_sandbox)
        url = f"{self.catalog_url}/product_summary/search"
        
        headers = self._get_headers(token)
        params = {identifier_type.lower(): identifier}
        
        try:
            logger.info(f"Searching catalog for {identifier_type}: {identifier}")
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                logger.info("Found catalog data")
                return data
            else:
                logger.warning(f"Catalog API failed with status {response.status_code}: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"Network error during Catalog API call: {str(e)}")
            return None
    
    def analyze_pricing(self, search_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze pricing data from search results.
        
        Args:
            search_results: Results from search_items()
            
        Returns:
            Dict containing pricing analysis
        """
        item_summaries = search_results.get("itemSummaries", [])
        
        if not item_summaries:
            return {
                "quick_sell_price": 0,
                "patient_sell_price": 0,
                "sell_time_estimate": "No listings found",
                "listings_count": 0,
                "price_range": {"min": 0, "max": 0},
                "average_price": 0
            }
        
        # Extract prices
        prices = []
        for item in item_summaries:
            price_info = item.get("price", {})
            if price_info and "value" in price_info:
                try:
                    price = float(price_info["value"])
                    prices.append(price)
                except (ValueError, TypeError):
                    continue
        
        if not prices:
            return {
                "quick_sell_price": 0,
                "patient_sell_price": 0,
                "sell_time_estimate": "No valid prices found",
                "listings_count": len(item_summaries),
                "price_range": {"min": 0, "max": 0},
                "average_price": 0
            }
        
        # Sort prices
        prices.sort()
        total_listings = len(prices)
        
        # Calculate quick sell (lowest 25%) and patient sell (highest 25%) prices
        quarter_size = max(1, total_listings // 4)
        quick_sell_prices = prices[:quarter_size]
        patient_sell_prices = prices[-quarter_size:]
        
        quick_sell_price = sum(quick_sell_prices) / len(quick_sell_prices)
        patient_sell_price = sum(patient_sell_prices) / len(patient_sell_prices)
        average_price = sum(prices) / len(prices)
        
        # Estimate sell time based on competition
        if total_listings < 5:
            sell_time_estimate = "Quick sell (low competition)"
        elif total_listings < 20:
            sell_time_estimate = "Moderate sell time"
        else:
            sell_time_estimate = "Patient sell (high competition)"
        
        return {
            "quick_sell_price": round(quick_sell_price, 2),
            "patient_sell_price": round(patient_sell_price, 2),
            "sell_time_estimate": sell_time_estimate,
            "listings_count": total_listings,
            "price_range": {
                "min": round(min(prices), 2),
                "max": round(max(prices), 2)
            },
            "average_price": round(average_price, 2)
        }
    
    def search_and_analyze(self, 
                          openai_output: Dict[str, Any],
                          use_category: bool = True,
                          use_catalog: bool = True) -> Dict[str, Any]:
        """
        Complete search and analysis workflow.
        
        Args:
            openai_output: Structured output from OpenAI analysis
            use_category: Whether to use Taxonomy API for category mapping
            use_catalog: Whether to use Catalog API for product identifiers
            
        Returns:
            Dict containing complete analysis results
        """
        try:
            # Extract search parameters from OpenAI output
            brand = openai_output.get("brand", "")
            model = openai_output.get("model", "")
            condition = openai_output.get("condition", "")
            item_type = openai_output.get("item_type", "")
            identifiers = openai_output.get("identifiers", {})
            
            # Build search keywords
            keywords_parts = [part for part in [brand, model, condition] if part]
            keywords = " ".join(keywords_parts)
            
            if not keywords:
                keywords = item_type or "item"
            
            logger.info(f"Searching for: {keywords}")
            
            # Get category ID if requested
            category_id = None
            if use_category and item_type:
                category_id = self.get_category_suggestions(item_type)
            
            # Search catalog if identifiers are available
            catalog_data = None
            if use_catalog and identifiers:
                for id_type, id_value in identifiers.items():
                    if id_value:
                        catalog_data = self.search_catalog(id_value, id_type)
                        if catalog_data:
                            break
            
            # Search for items
            search_results = self.search_items(
                keywords=keywords,
                category_id=category_id,
                limit=50,
                sort="price"
            )
            
            # Analyze pricing
            pricing_analysis = self.analyze_pricing(search_results)
            
            # Combine results
            result = {
                "search_keywords": keywords,
                "category_id": category_id,
                "catalog_data": catalog_data,
                "pricing_analysis": pricing_analysis,
                "raw_search_results": search_results
            }
            
            logger.info("Complete search and analysis completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error in search and analysis: {str(e)}")
            return {
                "error": str(e),
                "search_keywords": keywords if 'keywords' in locals() else "",
                "pricing_analysis": {
                    "quick_sell_price": 0,
                    "patient_sell_price": 0,
                    "sell_time_estimate": "Analysis failed",
                    "listings_count": 0
                }
            }

# Convenience functions for backward compatibility
def search_ebay_items(token: str, keywords: str, category_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Legacy function for backward compatibility.
    
    Args:
        token: OAuth token (ignored, will generate new one)
        keywords: Search keywords
        category_id: Optional category ID
        
    Returns:
        Dict containing search results
    """
    client = EbayAPIClient(use_sandbox=True)
    return client.search_items(keywords=keywords, category_id=category_id)

def get_category_id(token: str, item_type: str) -> Optional[str]:
    """
    Legacy function for backward compatibility.
    
    Args:
        token: OAuth token (ignored, will generate new one)
        item_type: Type of item
        
    Returns:
        str: Category ID if found, None otherwise
    """
    client = EbayAPIClient(use_sandbox=True)
    return client.get_category_suggestions(item_type)

def search_catalog(token: str, identifier: str, identifier_type: str = "UPC") -> Optional[Dict[str, Any]]:
    """
    Legacy function for backward compatibility.
    
    Args:
        token: OAuth token (ignored, will generate new one)
        identifier: Product identifier
        identifier_type: Type of identifier
        
    Returns:
        Dict containing catalog data if found, None otherwise
    """
    client = EbayAPIClient(use_sandbox=True)
    return client.search_catalog(identifier, identifier_type)

