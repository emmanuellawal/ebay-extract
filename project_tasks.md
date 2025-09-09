# Project Tasks: Simplified Inherited Item Appraisal App

## Overview
This project is a diluted, cost-effective version of a high-capacity appraisal platform for a school assignment. The goal is to create a basic mobile app that allows users to take photos of inherited items, interpret the images using the ChatGPT API (via OpenAI's free tier or limited access), and retrieve market data using the eBay API (free developer account). To keep it "spendless," we'll rely on free API tiers, local development, and avoid cloud services like AWS or Google Cloud. The app will be built using Flutter for cross-platform mobile development (free and open-source), with backend logic in Python scripts.

Key simplifications:
- No serverless architecture or scalability features—just local or simple hosting.
- Image processing: Use ChatGPT's vision capabilities (gpt-4o-mini or similar free-tier model) for item identification and research.
- Market data: Use eBay's Browse API (free for developers) to fetch similar item prices.
- Separation: Image interpretation/research in one Python file (`gpt_interpreter.py`), eBay data retrieval in another (`ebay_fetcher.py`).
- No database: Store results in simple JSON files or display directly in the app.
- Resilience/Speed: Minimal—focus on functionality for grading purposes.
- Total cost: $0 (using free tiers; monitor API limits to avoid charges).

The app flow:
1. User takes a photo in the mobile app.
2. App sends the image (as base64) to a local Python backend (via HTTP or direct call if simulated).
3. Backend: `gpt_interpreter.py` queries ChatGPT API to describe the item and suggest research (e.g., "This is a vintage porcelain doll from the 1950s").
4. Backend: `ebay_fetcher.py` uses the description to query eBay API for "quicksell" (lowest Buy It Now price) and "patient sell" (lowest listing price) proxies.
5. App displays results (description, research notes, prices).

Assumptions for grading:
- Focus on clean code, separation of concerns, API integration, and basic error handling.
- Test with sample images (e.g., local photos of common items).
- Document everything for clarity.

## Tech Stack
- **Mobile App**: Flutter (Dart) for UI and camera access.
- **Backend**: Python 3.x with libraries: `openai` for ChatGPT, `requests` for eBay API, `base64` for image encoding.
- **APIs**:
  - OpenAI ChatGPT: Sign up for a free API key (limited usage).
  - eBay API: Get a free developer key via eBay Developers Program.
- **Development Tools**: VS Code (free), Git for version control.
- **No extras**: No Docker, NoSQL, or cloud—run backend locally or on a free Heroku tier if needed.

## Project Structure
```
appraisal_app/
├── lib/                # Flutter app code
│   ├── main.dart       # Entry point: UI for camera and results display
│   └── api_client.dart # Handles HTTP calls to backend
├── backend/            # Python scripts
│   ├── gpt_interpreter.py  # ChatGPT image analysis
│   ├── ebay_fetcher.py     # eBay data retrieval
│   ├── requirements.txt    # Python dependencies
│   └── run_backend.py      # Simple server to handle app requests (using Flask)
├── assets/             # Sample images for testing
├── README.md           # Project documentation
└── project_tasks.md    # This file
```

## Tasks Breakdown
### Task 1: Setup Environment (1-2 hours)
- Install Flutter SDK and set up a new project: `flutter create appraisal_app`.
- Install Python and create `backend/` folder.
- Install Python libraries: Create `requirements.txt` with:
  ```
  openai==1.2.0  # Or latest compatible
  requests==2.31.0
  flask==3.0.0   # For simple backend server
  ```
  Run `pip install -r requirements.txt`.
- Sign up for APIs:
  - OpenAI: Get API key from platform.openai.com (store in `.env` file).
  - eBay: Register at developer.ebay.com, get App ID (production key).
- Version control: Initialize Git repo and commit initial structure.

### Task 2: Build Mobile App UI (3-4 hours)
- In `lib/main.dart`:
  - Use `camera` package for photo capture (add to `pubspec.yaml`: `camera: ^0.10.0`).
  - Create a simple screen with button to take photo.
  - Convert photo to base64 string.
  - Send base64 to backend via HTTP POST (use `http` package: add `http: ^1.0.0` to `pubspec.yaml`).
  - Display results: Text fields for description, research, quicksell price, patient sell price.
- In `lib/api_client.dart`:
  - Function to call backend endpoint (e.g., `http://localhost:5000/process` with JSON payload `{ "image_base64": "..." }`).
- Test: Run app on emulator (`flutter run`), ensure photo capture works.

### Task 3: Implement GPT Interpreter (2-3 hours)
- File: `backend/gpt_interpreter.py`
- Functionality:
  - Take base64 image as input.
  - Use OpenAI API to analyze: Prompt like "Describe this item in detail, including type, age, material, and any historical/research notes. Focus on antiques or collectibles."
  - Model: `gpt-4o-mini` (cheaper/free tier).
  - Return JSON: `{ "description": "...", "research_notes": "..." }`.
- Code skeleton:
  ```python
  import os
  from openai import OpenAI
  import base64

  client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

  def interpret_image(image_base64):
      response = client.chat.completions.create(
          model="gpt-4o-mini",
          messages=[
              {"role": "user", "content": [
                  {"type": "text", "text": "Describe this item..."},  # Full prompt here
                  {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
              ]}
          ]
      )
      description = response.choices[0].message.content
      # Parse/extract description and notes
      return {"description": description, "research_notes": "Extracted notes..."}
  ```
- Error handling: Catch API errors, return fallback message.

### Task 4: Implement eBay Fetcher (2-3 hours)
- File: `backend/ebay_fetcher.py`
- Functionality:
  - Take item description as input.
  - Query eBay Browse API: Use `/buy/browse/v1/item_summary/search` with query=description, filter by FIXED_PRICE.
  - Get lowest Buy It Now for "quicksell", lowest overall for "patient sell".
  - Return JSON: `{ "quicksell_price": "XX.XX", "patient_sell_price": "YY.YY" }`.
- Code skeleton:
  ```python
  import requests
  import os

  EBAY_API_KEY = os.getenv("EBAY_API_KEY")

  def fetch_ebay_data(description):
      url = "https://api.ebay.com/buy/browse/v1/item_summary/search"
      headers = {"Authorization": f"Bearer {EBAY_API_KEY}"}
      params = {"q": description, "limit": 10, "sort": "price"}
      response = requests.get(url, headers=headers, params=params)
      data = response.json()
      # Extract prices: Find min FIXED_PRICE, min overall
      if "itemSummaries" in data:
          prices = [float(item["price"]["value"]) for item in data["itemSummaries"]]
          quicksell = min([p for p in prices if ...])  # Filter logic
          patient = min(prices)
          return {"quicksell_price": quicksell, "patient_sell_price": patient}
      return {"error": "No data found"}
  ```
- Note: Handle auth token (eBay requires OAuth—implement token fetch if needed).
- Error handling: API limits, invalid responses.

### Task 5: Integrate Backend (1-2 hours)
- File: `backend/run_backend.py`
- Use Flask to create a simple server:
  ```python
  from flask import Flask, request, jsonify
  from gpt_interpreter import interpret_image
  from ebay_fetcher import fetch_ebay_data

  app = Flask(__name__)

  @app.route('/process', methods=['POST'])
  def process_image():
      data = request.json
      image_base64 = data['image_base64']
      gpt_result = interpret_image(image_base64)
      ebay_result = fetch_ebay_data(gpt_result['description'])
      return jsonify({**gpt_result, **ebay_result})

  if __name__ == '__main__':
      app.run(port=5000)
  ```
- Run: `python run_backend.py` (localhost server).
- Connect from app: Update `api_client.dart` to POST to this endpoint.

### Task 6: Testing and Documentation (2-3 hours)
- Test end-to-end: Take photo, see results in app.
- Edge cases: Bad image, API failures.
- README.md: Explain setup, run instructions, API keys setup.
- For grade: Add comments in code, diagrams (e.g., flow chart in Markdown).

### Task 7: Polish and Submit (1 hour)
- Ensure separation: GPT and eBay in distinct files.
- Optimize for spendless: Monitor API calls (e.g., limit to 5-10 tests).
- Zip project and submit with this tasks file.

Total estimated time: 12-17 hours. Aim for clear, modular code to impress graders!