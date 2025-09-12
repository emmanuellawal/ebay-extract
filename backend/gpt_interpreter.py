import os
from openai import OpenAI
import base64
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# Get OpenAI API key with validation
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY not found in environment variables. Please set it in your .env file.")
    raise ValueError("OPENAI_API_KEY is required. Please set it in your .env file.")

client = OpenAI(api_key=OPENAI_API_KEY)

def interpret_image(image_base64):
	"""
	Analyze an image and return structured data for eBay API queries.
	
	Returns both human-readable description and structured JSON for API calls.
	"""
	try:
		# Validate that this is actually a proper image in base64 format
		try:
			# Try to decode the base64 string
			decoded_data = base64.b64decode(image_base64)
			if len(decoded_data) < 100:  # Arbitrary small size check
				return {
					"description": "Error interpreting image.", 
					"research_notes": "The image data is too small to be a valid image. Please take a proper photo.",
					"structured_data": {
						"item_type": "unknown",
						"brand": "unknown",
						"model": "unknown",
						"condition": "unknown",
						"identifiers": {}
					}
				}
		except Exception as decode_error:
			return {
				"description": "Error interpreting image.", 
				"research_notes": f"Invalid base64 image data: {str(decode_error)}",
				"structured_data": {
					"item_type": "unknown",
					"brand": "unknown",
					"model": "unknown",
					"condition": "unknown",
					"identifiers": {}
				}
			}
		
		# Enhanced structured analysis prompt for precise product identification
		structured_prompt = """
		You are a professional product identification expert. Analyze this item image and provide EXTREMELY detailed identification.

		Return a JSON object with this EXACT structure:
		{
			"item_type": "specific category (e.g., 'wireless headphones', 'vintage wristwatch', 'hardcover novel', 'office chair')",
			"brand": "exact brand name if visible or identifiable from design/logos",
			"model": "specific model name/number if identifiable",
			"condition": "precise condition assessment (new, like_new, very_good, good, acceptable, poor)",
			"estimated_age": "age estimate (e.g., '2020-2023', '1990s', 'vintage 1960s', 'antique pre-1950')",
			"retail_category": "eBay category (Electronics, Collectibles, Fashion, Home & Garden, etc.)",
			"key_features": ["specific features that affect value", "notable characteristics", "visible defects or wear"],
			"materials": ["primary materials visible (leather, plastic, metal, wood, etc.)"],
			"color_finish": "primary color and finish (matte black, glossy white, brushed silver, etc.)",
			"size_estimate": "size description (small, medium, large, or dimensions if visible)",
			"identifiers": {
				"UPC": "UPC barcode if clearly visible",
				"EAN": "EAN barcode if clearly visible", 
				"model_number": "model number from labels/text",
				"serial_number": "serial number if visible",
				"part_number": "part number if visible"
			},
			"market_indicators": {
				"rarity": "common, uncommon, rare, very_rare",
				"demand_level": "high, medium, low (based on product type and condition)",
				"collectible_potential": "none, low, medium, high"
			},
			"search_keywords": ["optimized", "keywords", "for", "ebay", "search"],
			"comparable_items": ["similar product 1", "similar product 2", "alternative search terms"],
			"value_factors": ["factors that increase value", "factors that decrease value"]
		}
		
		CRITICAL REQUIREMENTS:
		- Be EXTREMELY specific with item_type (not just "headphones" but "wireless noise-canceling headphones")
		- Identify brand from ANY visible logos, design patterns, or distinctive features
		- Assess condition based on visible wear, scratches, missing parts
		- Provide search_keywords that would find similar items on eBay
		- Use "unknown" ONLY if absolutely no information is determinable
		- Focus on details that affect pricing and sellability
		"""
		
		# Enhanced detailed description prompt
		description_prompt = """
		You are a professional appraiser and product expert. Provide a comprehensive analysis of this item including:
		
		1. PRECISE IDENTIFICATION: What exactly is this item? Be as specific as possible.
		2. CONDITION ASSESSMENT: Detailed condition analysis noting any wear, damage, or defects
		3. MARKET POSITIONING: How this item fits in the current market (premium, mid-range, budget)
		4. VALUE INDICATORS: Features or characteristics that increase or decrease its value
		5. COLLECTIBILITY: Is this item collectible, vintage, or has special significance?
		6. AUTHENTICITY NOTES: Any indicators of authenticity or potential red flags
		7. COMPARABLE MARKET: What similar items would buyers cross-shop with this?
		
		Focus on information that would help determine accurate market pricing and sell time.
		Be brutally honest about condition and market positioning.
		"""

		response = client.chat.completions.create(
			model=OPENAI_MODEL,
			messages=[
				{"role": "user", "content": [
					{"type": "text", "text": description_prompt},
					{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
				]}
			]
		)
		description = response.choices[0].message.content
		
		# Get structured data
		structured_response = client.chat.completions.create(
			model=OPENAI_MODEL,
			messages=[
				{"role": "user", "content": [
					{"type": "text", "text": structured_prompt},
					{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
				]}
			]
		)
		
		structured_text = structured_response.choices[0].message.content
		
		# Try to parse JSON from structured response
		import json
		try:
			# Extract JSON from response (in case it's wrapped in markdown or other text)
			import re
			json_match = re.search(r'\{.*\}', structured_text, re.DOTALL)
			if json_match:
				structured_data = json.loads(json_match.group())
			else:
				structured_data = json.loads(structured_text)
		except (json.JSONDecodeError, AttributeError):
			# Fallback if JSON parsing fails
			logger.warning("Failed to parse structured JSON from OpenAI response")
			structured_data = {
				"item_type": "unknown",
				"brand": "unknown",
				"model": "unknown",
				"condition": "unknown",
				"identifiers": {}
			}
		
		return {
			"description": description, 
			"research_notes": "Extracted from image analysis",
			"structured_data": structured_data
		}
	except Exception as e:
		logger.error(f"Error in image interpretation: {str(e)}")
		return {
			"description": "Error interpreting image.", 
			"research_notes": str(e),
			"structured_data": {
				"item_type": "unknown",
				"brand": "unknown",
				"model": "unknown",
				"condition": "unknown",
				"identifiers": {}
			}
		}
