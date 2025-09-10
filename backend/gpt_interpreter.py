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
		
		# Create structured analysis prompt
		structured_prompt = """
		Analyze this item image and return a JSON object with the following structure:
		{
			"item_type": "general category (e.g., camera, watch, book, furniture)",
			"brand": "brand name if visible/identifiable",
			"model": "model name or number if visible",
			"condition": "estimated condition (new, like_new, good, fair, poor)",
			"identifiers": {
				"UPC": "UPC code if visible",
				"EAN": "EAN code if visible",
				"ISBN": "ISBN if it's a book",
				"serial_number": "serial number if visible"
			},
			"materials": ["list of materials if identifiable"],
			"era_period": "time period or era if identifiable",
			"special_features": ["notable features or characteristics"]
		}
		
		Only include fields where you can confidently identify the information. Use "unknown" for unclear items.
		Focus on information that would help with eBay searches and pricing.
		"""
		
		response = client.chat.completions.create(
			model=OPENAI_MODEL,
			messages=[
				{"role": "user", "content": [
					{"type": "text", "text": "Describe this item in detail, including type, age, material, and any historical/research notes. Focus on antiques or collectibles."},
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
