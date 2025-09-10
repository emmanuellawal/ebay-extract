# eBay API Integration

This document describes the complete eBay API integration for the appraisal app, including OAuth authentication, Browse API searches, Taxonomy API category mapping, and Catalog API product lookups.

## Overview

The eBay integration consists of several modules:

- **`auth.py`** - OAuth token generation and caching
- **`ebay_client.py`** - Comprehensive eBay API client with all endpoints
- **`gpt_interpreter.py`** - Updated to return structured JSON for eBay queries
- **`ebay_fetcher.py`** - Updated to use the new eBay API integration

## Setup

### 1. Environment Configuration

Copy the environment template and configure your credentials:

```bash
cp env_template.txt .env
```

Edit `.env` with your actual credentials:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-2024-08-06

# eBay API Configuration (Sandbox)
EBAY_SANDBOX_APP_ID=your_ebay_sandbox_app_id_here
EBAY_SANDBOX_CERT_ID=your_ebay_sandbox_cert_id_here

# Backend Configuration
BACKEND_HOST=127.0.0.1
BACKEND_PORT=5000
BACKEND_DEBUG=True
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# eBay API Settings
EBAY_MARKETPLACE_ID=EBAY_US
EBAY_TOKEN_CACHE_DURATION=7200  # 2 hours in seconds
```

### 2. eBay Developer Account Setup

1. Go to [eBay Developers Program](https://developer.ebay.com/)
2. Create a developer account
3. Create a new application
4. Get your App ID and Cert ID for sandbox environment
5. Add these to your `.env` file

## API Modules

### OAuth Authentication (`auth.py`)

Handles OAuth token generation with automatic caching:

```python
from auth import get_ebay_token

# Get a token (automatically cached for 2 hours)
token = get_ebay_token(use_sandbox=True)
```

**Features:**
- Automatic token caching (2 hours by default)
- Support for both sandbox and production environments
- Error handling and retry logic
- Global token management

### eBay API Client (`ebay_client.py`)

Comprehensive client for all eBay API endpoints:

```python
from ebay_client import EbayAPIClient

client = EbayAPIClient(use_sandbox=True)

# Search for items
results = client.search_items(
    keywords="Polaroid SX-70",
    category_id="625",
    limit=50,
    sort="price"
)

# Get category suggestions
category_id = client.get_category_suggestions("camera")

# Search catalog by UPC
catalog_data = client.search_catalog("123456789012", "UPC")

# Complete analysis workflow
result = client.search_and_analyze(openai_output, use_category=True, use_catalog=True)
```

**Features:**
- Browse API for item searches
- Taxonomy API for category mapping
- Catalog API for product identifiers
- Price analysis and sell time estimation
- Complete workflow integration

### Updated GPT Interpreter (`gpt_interpreter.py`)

Now returns structured JSON for eBay queries:

```python
from gpt_interpreter import interpret_image

result = interpret_image(image_base64)
# Returns:
# {
#   "description": "Human-readable description",
#   "research_notes": "Analysis notes",
#   "structured_data": {
#     "item_type": "camera",
#     "brand": "Polaroid",
#     "model": "SX-70",
#     "condition": "good",
#     "identifiers": {"UPC": "123456789012"},
#     "materials": ["plastic", "metal"],
#     "era_period": "1970s",
#     "special_features": ["instant film", "folding design"]
#   }
# }
```

### Updated eBay Fetcher (`ebay_fetcher.py`)

Uses the new eBay API integration:

```python
from ebay_fetcher import fetch_ebay_data

result = fetch_ebay_data(gpt_result)
# Returns:
# {
#   "quicksell_price": 45.50,
#   "patient_sell_price": 89.99,
#   "sell_time_estimate": "Moderate sell time",
#   "listings_count": 15,
#   "price_range": {"min": 25.00, "max": 120.00},
#   "average_price": 67.75,
#   "search_keywords": "Polaroid SX-70 good",
#   "category_id": "625",
#   "catalog_data": {...}
# }
```

## API Endpoints

### Browse API

Search for items on eBay:

```python
results = client.search_items(
    keywords="search terms",
    category_id="625",  # Optional
    limit=50,           # Max 200
    sort="price",       # price, distance, endTime, etc.
    condition="3000"    # Optional condition filter
)
```

### Taxonomy API

Get category suggestions:

```python
category_id = client.get_category_suggestions("camera")
```

### Catalog API

Search by product identifiers:

```python
catalog_data = client.search_catalog("123456789012", "UPC")
```

## Price Analysis

The system automatically analyzes pricing data:

- **Quick Sell Price**: Average of lowest 25% of listing prices
- **Patient Sell Price**: Average of highest 25% of listing prices
- **Sell Time Estimate**: Based on number of competing listings
- **Price Range**: Min/max prices found
- **Average Price**: Overall average

## Testing

Run the comprehensive test suite:

```bash
cd backend
python test_ebay_integration.py
```

The test suite covers:
- OAuth token generation
- Browse API searches
- Taxonomy API category mapping
- Catalog API product lookups
- Price analysis
- Complete workflow integration
- eBay fetcher integration

## Error Handling

The integration includes comprehensive error handling:

- **Authentication errors**: Clear messages about missing credentials
- **API errors**: Detailed error messages with status codes
- **Network errors**: Timeout and connection error handling
- **Data validation**: Input validation and fallback values
- **Rate limiting**: Token caching to avoid hitting limits

## Rate Limits

eBay API rate limits:
- **5,000 calls per day** for Browse API
- **Token caching** (2 hours) to minimize authentication calls
- **Automatic retry logic** for transient failures

## Production Deployment

For production deployment:

1. **Switch to production credentials**:
   ```env
   EBAY_APP_ID=your_production_app_id
   EBAY_CERT_ID=your_production_cert_id
   ```

2. **Update the client**:
   ```python
   client = EbayAPIClient(use_sandbox=False)
   ```

3. **Test thoroughly** with production API limits

## Troubleshooting

### Common Issues

1. **"eBay credentials not found"**
   - Check your `.env` file has the correct variable names
   - Ensure credentials are for the correct environment (sandbox vs production)

2. **"Token generation failed"**
   - Verify your App ID and Cert ID are correct
   - Check that your eBay application is active
   - Ensure you're using the correct environment URLs

3. **"No listings found"**
   - Try broader search terms
   - Check if the item type is supported on eBay
   - Verify the marketplace ID is correct

4. **"Network error"**
   - Check your internet connection
   - Verify eBay API endpoints are accessible
   - Check for firewall or proxy issues

### Debug Mode

Enable debug logging:

```env
LOG_LEVEL=DEBUG
```

This will show detailed API requests and responses.

## Integration Flow

The complete integration flow:

1. **Image Upload** → Frontend sends base64 image
2. **OpenAI Analysis** → GPT-4 analyzes image and returns structured data
3. **eBay Search** → Use structured data to search eBay
4. **Category Mapping** → Use Taxonomy API for better search results
5. **Product Lookup** → Use Catalog API if identifiers are available
6. **Price Analysis** → Analyze pricing data and estimate sell times
7. **Results** → Return comprehensive analysis to frontend

## Security Notes

- **Never expose credentials** in frontend code
- **All eBay API calls** go through the backend
- **Token caching** is done server-side only
- **Environment variables** are loaded securely
- **Input validation** prevents injection attacks

## Performance Optimization

- **Token caching** reduces authentication overhead
- **Parallel API calls** where possible
- **Result caching** for repeated searches
- **Efficient data structures** for price analysis
- **Connection pooling** for HTTP requests

