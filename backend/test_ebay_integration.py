#!/usr/bin/env python3
"""
Test script for eBay API integration.

This script tests the complete eBay API integration including:
- OAuth token generation
- Browse API searches
- Taxonomy API category mapping
- Catalog API product lookups
- Price analysis
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from auth import get_ebay_token, EbayAuth
from ebay_client import EbayAPIClient
from gpt_interpreter import interpret_image
from ebay_fetcher import fetch_ebay_data

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_oauth_token():
    """Test OAuth token generation."""
    logger.info("Testing OAuth token generation...")
    
    try:
        # Test sandbox token generation
        token = get_ebay_token(use_sandbox=True)
        logger.info(f"✅ OAuth token generated successfully (length: {len(token)})")
        return True
    except Exception as e:
        logger.error(f"❌ OAuth token generation failed: {str(e)}")
        return False

def test_browse_api():
    """Test Browse API search functionality."""
    logger.info("Testing Browse API search...")
    
    try:
        client = EbayAPIClient(use_sandbox=True)
        
        # Test basic search
        results = client.search_items(
            keywords="Polaroid camera",
            limit=10,
            sort="price"
        )
        
        item_summaries = results.get("itemSummaries", [])
        logger.info(f"✅ Browse API search successful: {len(item_summaries)} items found")
        
        if item_summaries:
            # Show first item details
            first_item = item_summaries[0]
            title = first_item.get("title", "No title")
            price = first_item.get("price", {}).get("value", "No price")
            logger.info(f"   First item: {title} - ${price}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Browse API test failed: {str(e)}")
        return False

def test_taxonomy_api():
    """Test Taxonomy API category mapping."""
    logger.info("Testing Taxonomy API category mapping...")
    
    try:
        client = EbayAPIClient(use_sandbox=True)
        
        # Test category suggestions
        category_id = client.get_category_suggestions("camera")
        
        if category_id:
            logger.info(f"✅ Taxonomy API successful: Found category ID {category_id} for 'camera'")
        else:
            logger.warning("⚠️  Taxonomy API returned no category suggestions for 'camera'")
        
        return True
    except Exception as e:
        logger.error(f"❌ Taxonomy API test failed: {str(e)}")
        return False

def test_catalog_api():
    """Test Catalog API product lookup."""
    logger.info("Testing Catalog API product lookup...")
    
    try:
        client = EbayAPIClient(use_sandbox=True)
        
        # Test with a sample UPC (this might not return results in sandbox)
        catalog_data = client.search_catalog("123456789012", "UPC")
        
        if catalog_data:
            logger.info("✅ Catalog API successful: Found product data")
        else:
            logger.info("ℹ️  Catalog API: No product data found (expected for test UPC)")
        
        return True
    except Exception as e:
        logger.error(f"❌ Catalog API test failed: {str(e)}")
        return False

def test_price_analysis():
    """Test price analysis functionality."""
    logger.info("Testing price analysis...")
    
    try:
        client = EbayAPIClient(use_sandbox=True)
        
        # Get search results
        results = client.search_items(
            keywords="vintage watch",
            limit=20,
            sort="price"
        )
        
        # Analyze pricing
        pricing_analysis = client.analyze_pricing(results)
        
        logger.info("✅ Price analysis successful:")
        logger.info(f"   Quick sell price: ${pricing_analysis.get('quick_sell_price', 'N/A')}")
        logger.info(f"   Patient sell price: ${pricing_analysis.get('patient_sell_price', 'N/A')}")
        logger.info(f"   Listings count: {pricing_analysis.get('listings_count', 0)}")
        logger.info(f"   Sell time estimate: {pricing_analysis.get('sell_time_estimate', 'N/A')}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Price analysis test failed: {str(e)}")
        return False

def test_complete_workflow():
    """Test the complete search and analysis workflow."""
    logger.info("Testing complete search and analysis workflow...")
    
    try:
        client = EbayAPIClient(use_sandbox=True)
        
        # Mock OpenAI output
        mock_openai_output = {
            "item_type": "camera",
            "brand": "Polaroid",
            "model": "SX-70",
            "condition": "good",
            "identifiers": {}
        }
        
        # Run complete analysis
        result = client.search_and_analyze(
            openai_output=mock_openai_output,
            use_category=True,
            use_catalog=True
        )
        
        pricing_analysis = result.get("pricing_analysis", {})
        
        logger.info("✅ Complete workflow successful:")
        logger.info(f"   Search keywords: {result.get('search_keywords', 'N/A')}")
        logger.info(f"   Category ID: {result.get('category_id', 'N/A')}")
        logger.info(f"   Quick sell: ${pricing_analysis.get('quick_sell_price', 'N/A')}")
        logger.info(f"   Patient sell: ${pricing_analysis.get('patient_sell_price', 'N/A')}")
        logger.info(f"   Listings: {pricing_analysis.get('listings_count', 0)}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Complete workflow test failed: {str(e)}")
        return False

def test_ebay_fetcher():
    """Test the eBay fetcher integration."""
    logger.info("Testing eBay fetcher integration...")
    
    try:
        # Mock GPT result
        mock_gpt_result = {
            "description": "A vintage Polaroid SX-70 camera in good condition",
            "structured_data": {
                "item_type": "camera",
                "brand": "Polaroid",
                "model": "SX-70",
                "condition": "good",
                "identifiers": {}
            }
        }
        
        # Test eBay fetcher
        result = fetch_ebay_data(mock_gpt_result)
        
        logger.info("✅ eBay fetcher integration successful:")
        logger.info(f"   Quick sell price: {result.get('quicksell_price', 'N/A')}")
        logger.info(f"   Patient sell price: {result.get('patient_sell_price', 'N/A')}")
        logger.info(f"   Sell time estimate: {result.get('sell_time_estimate', 'N/A')}")
        logger.info(f"   Listings count: {result.get('listings_count', 0)}")
        
        return True
    except Exception as e:
        logger.error(f"❌ eBay fetcher test failed: {str(e)}")
        return False

def check_environment():
    """Check if required environment variables are set."""
    logger.info("Checking environment configuration...")
    
    required_vars = [
        "EBAY_SANDBOX_APP_ID",
        "EBAY_SANDBOX_CERT_ID",
        "OPENAI_API_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set these variables in your .env file")
        return False
    else:
        logger.info("✅ All required environment variables are set")
        return True

def main():
    """Run all tests."""
    logger.info("Starting eBay API integration tests...")
    logger.info("=" * 50)
    
    # Check environment first
    if not check_environment():
        logger.error("Environment check failed. Please configure your .env file.")
        return False
    
    tests = [
        ("OAuth Token Generation", test_oauth_token),
        ("Browse API Search", test_browse_api),
        ("Taxonomy API Category Mapping", test_taxonomy_api),
        ("Catalog API Product Lookup", test_catalog_api),
        ("Price Analysis", test_price_analysis),
        ("Complete Workflow", test_complete_workflow),
        ("eBay Fetcher Integration", test_ebay_fetcher)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} ---")
        try:
            if test_func():
                passed += 1
        except Exception as e:
            logger.error(f"❌ {test_name} failed with exception: {str(e)}")
    
    logger.info("\n" + "=" * 50)
    logger.info(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! eBay API integration is working correctly.")
        return True
    else:
        logger.warning(f"⚠️  {total - passed} tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

