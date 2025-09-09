from flask import Flask, request, jsonify
from flask_cors import CORS
from gpt_interpreter import interpret_image
from ebay_fetcher import fetch_ebay_data

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/process', methods=['POST'])
def process_image():
	data = request.json
	image_base64 = data['image_base64']
	gpt_result = interpret_image(image_base64)
	ebay_result = fetch_ebay_data(gpt_result['description'])
	return jsonify({**gpt_result, **ebay_result})

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=5000, debug=True)
