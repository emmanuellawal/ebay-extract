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
    
    def analyze_pricing_advanced(self, search_results: Dict[str, Any], openai_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Advanced pricing analysis with sophisticated sell time estimation.
        
        Args:
            search_results: Results from eBay search
            openai_output: Enhanced structured data from OpenAI
            
        Returns:
            Dict containing comprehensive pricing and timing analysis
        """
        item_summaries = search_results.get("itemSummaries", [])
        
        if not item_summaries:
            return {
                "quick_sell_price": 0,
                "patient_sell_price": 0,
                "market_price": 0,
                "sell_time_estimate": "No similar items found - may take 60+ days or require auction format",
                "sell_time_days": "60+",
                "listings_count": 0,
                "price_range": {"min": 0, "max": 0},
                "confidence_level": "very_low",
                "market_analysis": "Insufficient data for analysis"
            }
        
        # Extract and validate prices
        prices = []
        listing_types = {"auction": 0, "buy_it_now": 0}
        condition_distribution = {}
        
        for item in item_summaries:
            price_info = item.get("price", {})
            if price_info and "value" in price_info:
                try:
                    price = float(price_info["value"])
                    prices.append(price)
                    
                    # Track listing types
                    if item.get("buyingOptions", []):
                        if "AUCTION" in item.get("buyingOptions", []):
                            listing_types["auction"] += 1
                        else:
                            listing_types["buy_it_now"] += 1
                    
                    # Track condition distribution
                    condition = item.get("condition", "Unknown")
                    condition_distribution[condition] = condition_distribution.get(condition, 0) + 1
                    
                except (ValueError, TypeError):
                    continue
        
        if not prices:
            return {
                "quick_sell_price": 0,
                "patient_sell_price": 0,
                "market_price": 0,
                "sell_time_estimate": "No valid pricing data found",
                "sell_time_days": "Unknown",
                "listings_count": len(item_summaries),
                "confidence_level": "very_low",
                "market_analysis": "Unable to extract pricing information"
            }
        
        # Sort prices and calculate statistics
        prices.sort()
        total_listings = len(prices)
        
        # Advanced pricing calculations
        percentile_10 = prices[int(total_listings * 0.1)] if total_listings > 10 else prices[0]
        percentile_25 = prices[int(total_listings * 0.25)] if total_listings > 4 else prices[0]
        median_price = prices[int(total_listings * 0.5)]
        percentile_75 = prices[int(total_listings * 0.75)] if total_listings > 4 else prices[-1]
        percentile_90 = prices[int(total_listings * 0.9)] if total_listings > 10 else prices[-1]
        average_price = sum(prices) / len(prices)
        
        # Extract market indicators from OpenAI analysis
        market_indicators = openai_output.get("market_indicators", {})
        condition = openai_output.get("condition", "unknown")
        rarity = market_indicators.get("rarity", "common")
        demand_level = market_indicators.get("demand_level", "medium")
        collectible_potential = market_indicators.get("collectible_potential", "none")
        
        # Sophisticated sell time estimation
        sell_time_factors = []
        base_sell_days = 14  # Base selling time
        
        # Factor 1: Competition level
        if total_listings < 5:
            competition_multiplier = 0.7
            sell_time_factors.append("Low competition (+fast)")
        elif total_listings < 15:
            competition_multiplier = 1.0
            sell_time_factors.append("Moderate competition")
        elif total_listings < 30:
            competition_multiplier = 1.4
            sell_time_factors.append("High competition (+slow)")
        else:
            competition_multiplier = 2.0
            sell_time_factors.append("Very high competition (+very slow)")
        
        # Factor 2: Price positioning
        if condition in ["new", "like_new"] and rarity in ["rare", "very_rare"]:
            price_multiplier = 0.8
            sell_time_factors.append("Premium item (+fast)")
        elif demand_level == "high":
            price_multiplier = 0.9
            sell_time_factors.append("High demand (+fast)")
        elif demand_level == "low":
            price_multiplier = 1.5
            sell_time_factors.append("Low demand (+slow)")
        else:
            price_multiplier = 1.0
            sell_time_factors.append("Average demand")
        
        # Factor 3: Collectible potential
        if collectible_potential == "high":
            collectible_multiplier = 0.8
            sell_time_factors.append("High collectible value (+fast)")
        elif collectible_potential == "medium":
            collectible_multiplier = 0.9
            sell_time_factors.append("Some collectible value")
        else:
            collectible_multiplier = 1.1
            sell_time_factors.append("Non-collectible")
        
        # Factor 4: Condition impact
        if condition in ["poor", "acceptable"]:
            condition_multiplier = 1.6
            sell_time_factors.append("Lower condition (+slow)")
        elif condition in ["new", "like_new"]:
            condition_multiplier = 0.8
            sell_time_factors.append("Excellent condition (+fast)")
        else:
            condition_multiplier = 1.0
            sell_time_factors.append("Good condition")
        
        # Calculate final sell time
        total_multiplier = competition_multiplier * price_multiplier * collectible_multiplier * condition_multiplier
        estimated_sell_days = int(base_sell_days * total_multiplier)
        
        # Determine pricing strategy
        quick_sell_price = percentile_25  # Price for fast sale (bottom 25%)
        market_price = median_price  # Market average price
        patient_sell_price = percentile_75  # Price for patient sale (top 25%)
        
        # Adjust prices based on condition and rarity
        condition_adjustments = {
            "new": 1.1, "like_new": 1.05, "very_good": 1.0,
            "good": 0.9, "acceptable": 0.75, "poor": 0.6
        }
        
        if condition in condition_adjustments:
            adjustment = condition_adjustments[condition]
            quick_sell_price *= adjustment
            market_price *= adjustment
            patient_sell_price *= adjustment
        
        # Confidence level calculation
        if total_listings >= 20 and len(set(condition_distribution.keys())) <= 3:
            confidence = "high"
        elif total_listings >= 10:
            confidence = "medium"
        elif total_listings >= 5:
            confidence = "low"
        else:
            confidence = "very_low"
        
        # Generate sell time description
        if estimated_sell_days <= 7:
            sell_time_desc = f"Quick sale expected (~{estimated_sell_days} days)"
        elif estimated_sell_days <= 21:
            sell_time_desc = f"Normal sale time (~{estimated_sell_days} days)"
        elif estimated_sell_days <= 45:
            sell_time_desc = f"Patient sale required (~{estimated_sell_days} days)"
        else:
            sell_time_desc = f"Long-term sale ({estimated_sell_days}+ days) - consider auction format"
        
        return {
            "quick_sell_price": round(quick_sell_price, 2),
            "market_price": round(market_price, 2),
            "patient_sell_price": round(patient_sell_price, 2),
            "sell_time_estimate": sell_time_desc,
            "sell_time_days": str(estimated_sell_days),
            "listings_count": total_listings,
            "price_range": {
                "min": round(min(prices), 2),
                "max": round(max(prices), 2)
            },
            "price_percentiles": {
                "p10": round(percentile_10, 2),
                "p25": round(percentile_25, 2),
                "p50": round(median_price, 2),
                "p75": round(percentile_75, 2),
                "p90": round(percentile_90, 2)
            },
            "average_price": round(average_price, 2),
            "confidence_level": confidence,
            "market_analysis": f"Based on {total_listings} similar listings. " + " • ".join(sell_time_factors),
            "listing_distribution": listing_types,
            "condition_distribution": condition_distribution
        }
    
    def search_and_analyze(self, 
                          openai_output: Dict[str, Any],
                          use_category: bool = True,
                          use_catalog: bool = True) -> Dict[str, Any]:
        """
        Enhanced search and analysis workflow using improved OpenAI structured data.
        
        Args:
            openai_output: Enhanced structured output from OpenAI analysis
            use_category: Whether to use Taxonomy API for category mapping
            use_catalog: Whether to use Catalog API for product identifiers
            
        Returns:
            Dict containing comprehensive analysis results
        """
        try:
            # Extract enhanced search parameters from OpenAI output
            brand = openai_output.get("brand", "").strip()
            model = openai_output.get("model", "").strip()
            condition = openai_output.get("condition", "").strip()
            item_type = openai_output.get("item_type", "").strip()
            identifiers = openai_output.get("identifiers", {})
            search_keywords = openai_output.get("search_keywords", [])
            comparable_items = openai_output.get("comparable_items", [])
            market_indicators = openai_output.get("market_indicators", {})
            
            # Build multiple search strategies for comprehensive results
            search_strategies = []
            
            # Strategy 1: Exact brand + model search
            if brand != "unknown" and model != "unknown":
                exact_search = f"{brand} {model}"
                search_strategies.append(("exact_match", exact_search))
            
            # Strategy 2: Use OpenAI-provided search keywords
            if search_keywords:
                keyword_search = " ".join(search_keywords[:4])  # Use top 4 keywords
                search_strategies.append(("ai_keywords", keyword_search))
            
            # Strategy 3: Brand + item type
            if brand != "unknown" and item_type != "unknown":
                brand_type_search = f"{brand} {item_type}"
                search_strategies.append(("brand_type", brand_type_search))
            
            # Strategy 4: Comparable items search
            for comparable in comparable_items[:2]:  # Top 2 comparable items
                if comparable and comparable != "unknown":
                    search_strategies.append(("comparable", comparable))
            
            # Fallback strategy
            if not search_strategies:
                fallback = " ".join([part for part in [brand, model, item_type] if part != "unknown"])
                if fallback:
                    search_strategies.append(("fallback", fallback))
                else:
                    search_strategies.append(("basic", item_type or "item"))
            
            logger.info(f"Using {len(search_strategies)} search strategies")
            
            # Get category ID if requested
            category_id = None
            if use_category and item_type != "unknown":
                category_id = self.get_category_suggestions(item_type)
            
            # Search catalog using identifiers
            catalog_data = None
            if use_catalog and identifiers:
                for id_type, id_value in identifiers.items():
                    if id_value and id_value != "unknown":
                        catalog_data = self.search_catalog(id_value, id_type)
                        if catalog_data:
                            logger.info(f"Found catalog data using {id_type}: {id_value}")
                            break
            
            # Execute multiple searches and combine results
            all_search_results = []
            used_keywords = []
            
            for strategy_name, keywords in search_strategies:
                logger.info(f"Executing {strategy_name} search: {keywords}")
                
                try:
                    search_results = self.search_items(
                        keywords=keywords,
                        category_id=category_id,
                        limit=30,  # Reduced per search to allow multiple searches
                        sort="price"
                    )
                    
                    if search_results.get("itemSummaries"):
                        all_search_results.extend(search_results["itemSummaries"])
                        used_keywords.append(f"{strategy_name}: {keywords}")
                        
                        # Stop if we have enough results
                        if len(all_search_results) >= 50:
                            break
                            
                except Exception as search_error:
                    logger.warning(f"Search strategy '{strategy_name}' failed: {search_error}")
                    continue
            
            # Create combined search results
            combined_results = {
                "itemSummaries": all_search_results[:50],  # Limit to 50 total results
                "total": len(all_search_results)
            }
            
            # Enhanced pricing analysis
            pricing_analysis = self.analyze_pricing_advanced(combined_results, openai_output)
            
            # Combine results
            result = {
                "search_strategies": used_keywords,
                "category_id": category_id,
                "catalog_data": catalog_data,
                "pricing_analysis": pricing_analysis,
                "raw_search_results": combined_results,
                "market_context": market_indicators
            }
            
            logger.info(f"Enhanced analysis completed: {len(all_search_results)} total listings analyzed")
            return result
            
        except Exception as e:
            logger.error(f"Error in enhanced search and analysis: {str(e)}")
            return {
                "error": str(e),
                "search_strategies": [],
                "pricing_analysis": {
                    "quick_sell_price": 0,
                    "patient_sell_price": 0,
                    "sell_time_estimate": "Analysis failed",
                    "listings_count": 0,
                    "confidence_level": "low"
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

