#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(__file__))

from gpt_interpreter import interpret_image
from ebay_fetcher import fetch_ebay_data

def test_backend():
    print("Testing backend components...")
    
    # Test with mock image
    mock_base64 = "dGVzdA=="  # "test" in base64
    
    print("Testing GPT interpreter...")
    try:
        gpt_result = interpret_image(mock_base64)
        print(f"GPT Result: {gpt_result}")
    except Exception as e:
        print(f"GPT Error: {e}")
        gpt_result = {"description": "test item", "research_notes": "test notes"}
    
    print("Testing eBay fetcher...")
    try:
        ebay_result = fetch_ebay_data(gpt_result['description'])
        print(f"eBay Result: {ebay_result}")
    except Exception as e:
        print(f"eBay Error: {e}")
        ebay_result = {"quicksell_price": "N/A", "patient_sell_price": "N/A"}
    
    combined = {**gpt_result, **ebay_result}
    print(f"Combined Result: {combined}")
    return combined

if __name__ == "__main__":
    test_backend()
