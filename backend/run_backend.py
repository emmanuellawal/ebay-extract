import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from gpt_interpreter import interpret_image
from ebay_fetcher import fetch_ebay_data

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# Get configuration from environment
BACKEND_HOST = os.getenv("BACKEND_HOST", "127.0.0.1")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "5000"))
BACKEND_DEBUG = os.getenv("BACKEND_DEBUG", "True").lower() == "true"
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")

app = Flask(__name__)
CORS(app, origins=CORS_ORIGINS)  # Enable CORS with configured origins

@app.route('/process', methods=['POST'])
def process_image():
	"""
	Process an image and return item description and pricing information.
	"""
	try:
		data = request.json
		if not data or 'image_base64' not in data:
			return jsonify({"error": "No image data provided"}), 400
		
		image_base64 = data['image_base64']
		logger.info("Processing image request")
		
		gpt_result = interpret_image(image_base64)
		ebay_result = fetch_ebay_data(gpt_result)
		
		result = {**gpt_result, **ebay_result}
		logger.info("Image processing completed successfully")
		return jsonify(result)
		
	except Exception as e:
		logger.error(f"Error processing image: {str(e)}")
		return jsonify({"error": "Internal server error", "details": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
	"""
	Health check endpoint to verify the server is running.
	"""
	return jsonify({
		"status": "healthy",
		"openai_configured": bool(os.getenv("OPENAI_API_KEY")),
		"ebay_configured": bool(os.getenv("EBAY_SANDBOX_APP_ID") and os.getenv("EBAY_SANDBOX_CERT_ID"))
	})

if __name__ == '__main__':
	logger.info(f"Starting backend server on {BACKEND_HOST}:{BACKEND_PORT}")
	logger.info(f"Debug mode: {BACKEND_DEBUG}")
	logger.info(f"CORS origins: {CORS_ORIGINS}")
	app.run(host=BACKEND_HOST, port=BACKEND_PORT, debug=BACKEND_DEBUG)
