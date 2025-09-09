import os
from openai import OpenAI
import base64
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def interpret_image(image_base64):
	try:
		# Validate that this is actually a proper image in base64 format
		try:
			# Try to decode the base64 string
			decoded_data = base64.b64decode(image_base64)
			if len(decoded_data) < 100:  # Arbitrary small size check
				return {"description": "Error interpreting image.", 
						"research_notes": "The image data is too small to be a valid image. Please take a proper photo."}
		except Exception as decode_error:
			return {"description": "Error interpreting image.", 
					"research_notes": f"Invalid base64 image data: {str(decode_error)}"}
		
		response = client.chat.completions.create(
			model="gpt-4o-mini",
			messages=[
				{"role": "user", "content": [
					{"type": "text", "text": "Describe this item in detail, including type, age, material, and any historical/research notes. Focus on antiques or collectibles."},
					{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
				]}
			]
		)
		description = response.choices[0].message.content
		return {"description": description, "research_notes": "Extracted from image analysis"}
	except Exception as e:
		return {"description": "Error interpreting image.", "research_notes": str(e)}
