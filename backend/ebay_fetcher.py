import requests
import os

EBAY_API_KEY = os.getenv("EBAY_API_KEY")

def fetch_ebay_data(description):
	# Mock response since eBay API is unavailable
	return {
		"quicksell_price": "N/A",
		"patient_sell_price": "N/A",
		"error": "eBay API unavailable; using mock data."
	}
