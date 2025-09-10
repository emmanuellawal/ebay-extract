import os
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from ebay_client import EbayAPIClient

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

def fetch_ebay_data(gpt_result: Dict[str, Any]) -> Dict[str, Any]:
	"""
	Fetch eBay data for item pricing using the new eBay API integration.
	
	Args:
		gpt_result: Result from GPT interpreter containing description and structured_data
		
	Returns:
		Dict containing pricing analysis and eBay data
	"""
	try:
		# Check if we have the required eBay credentials
		sandbox_app_id = os.getenv("EBAY_SANDBOX_APP_ID")
		sandbox_cert_id = os.getenv("EBAY_SANDBOX_CERT_ID")
		
		if not sandbox_app_id or not sandbox_cert_id:
			logger.warning("eBay sandbox credentials not found. Using mock data.")
			return {
				"quicksell_price": "N/A",
				"patient_sell_price": "N/A",
				"sell_time_estimate": "N/A",
				"listings_count": 0,
				"error": "eBay API credentials not configured. Please set EBAY_SANDBOX_APP_ID and EBAY_SANDBOX_CERT_ID in your .env file."
			}
		
		# Extract structured data from GPT result
		structured_data = gpt_result.get("structured_data", {})
		description = gpt_result.get("description", "")
		
		if not structured_data or structured_data.get("item_type") == "unknown":
			logger.warning("No structured data available from GPT analysis")
			return {
				"quicksell_price": "N/A",
				"patient_sell_price": "N/A",
				"sell_time_estimate": "N/A",
				"listings_count": 0,
				"error": "Unable to extract item information from image for eBay search."
			}
		
		# Initialize eBay API client
		ebay_client = EbayAPIClient(use_sandbox=True)
		
		# Perform complete search and analysis
		logger.info(f"Searching eBay for item: {structured_data.get('item_type', 'unknown')}")
		analysis_result = ebay_client.search_and_analyze(
			openai_output=structured_data,
			use_category=True,
			use_catalog=True
		)
		
		# Extract pricing analysis
		pricing_analysis = analysis_result.get("pricing_analysis", {})
		
		# Format results for backward compatibility
		result = {
			"quicksell_price": pricing_analysis.get("quick_sell_price", "N/A"),
			"patient_sell_price": pricing_analysis.get("patient_sell_price", "N/A"),
			"sell_time_estimate": pricing_analysis.get("sell_time_estimate", "N/A"),
			"listings_count": pricing_analysis.get("listings_count", 0),
			"price_range": pricing_analysis.get("price_range", {"min": 0, "max": 0}),
			"average_price": pricing_analysis.get("average_price", 0),
			"search_keywords": analysis_result.get("search_keywords", ""),
			"category_id": analysis_result.get("category_id"),
			"catalog_data": analysis_result.get("catalog_data")
		}
		
		# Add error if present
		if "error" in analysis_result:
			result["error"] = analysis_result["error"]
		
		logger.info(f"eBay analysis completed: {pricing_analysis.get('listings_count', 0)} listings found")
		return result
		
	except Exception as e:
		logger.error(f"Error in eBay data fetching: {str(e)}")
		return {
			"quicksell_price": "N/A",
			"patient_sell_price": "N/A",
			"sell_time_estimate": "N/A",
			"listings_count": 0,
			"error": f"eBay API error: {str(e)}"
		}

def fetch_ebay_data_legacy(description: str) -> Dict[str, Any]:
	"""
	Legacy function for backward compatibility.
	
	Args:
		description: Text description of the item
		
	Returns:
		Dict containing pricing analysis
	"""
	logger.warning("Using legacy fetch_ebay_data function. Consider updating to use structured data.")
	
	# Create a minimal structured data object from description
	structured_data = {
		"item_type": "unknown",
		"brand": "unknown", 
		"model": "unknown",
		"condition": "unknown",
		"identifiers": {}
	}
	
	# Try to extract some basic info from description
	description_lower = description.lower()
	if any(word in description_lower for word in ["camera", "lens", "photography"]):
		structured_data["item_type"] = "camera"
	elif any(word in description_lower for word in ["watch", "timepiece", "clock"]):
		structured_data["item_type"] = "watch"
	elif any(word in description_lower for word in ["book", "novel", "manual"]):
		structured_data["item_type"] = "book"
	elif any(word in description_lower for word in ["furniture", "chair", "table", "desk"]):
		structured_data["item_type"] = "furniture"
	
	gpt_result = {
		"description": description,
		"structured_data": structured_data
	}
	
	return fetch_ebay_data(gpt_result)
