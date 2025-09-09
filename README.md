# Advanced Reliability and Resilience Features

## Outlier Detection for Price Reliability
For both "quicksell" (lowest Buy It Now) and "patient sell" (lowest listing) price proxies, implement outlier detection using statistical methods such as the Interquartile Range (IQR). This helps filter out anomalous prices and improves reliability:

- Collect all relevant prices from eBay API results.
- Calculate Q1 (25th percentile) and Q3 (75th percentile).
- Compute IQR = Q3 - Q1.
- Filter out prices outside [Q1 - 1.5*IQR, Q3 + 1.5*IQR].
- Use the minimum of the filtered set for "quicksell" and the overall minimum for "patient sell".

## Average Duration Posted (Time-to-Sell)
To estimate "average duration posted," use sold listings' time-to-sell data, now accessible via eBay API extensions:

- Query sold listings for similar items.
- Calculate the average time between listing and sale for these items.
- Display this as a proxy for expected time-to-sell.

## API Rate Limiting and Caching
Enhance backend resilience and speed by handling API rate limits and caching frequent queries:

- Detect eBay/OpenAI API rate limit responses and implement exponential backoff or retry logic.
- Use a caching layer (e.g., Redis) to store results for frequent queries, reducing latency and API usage.
- Cache can be keyed by item description or image hash.

## Example Python Snippet for IQR Filtering
```python
import numpy as np
def filter_outliers(prices):
	q1 = np.percentile(prices, 25)
	q3 = np.percentile(prices, 75)
	iqr = q3 - q1
	filtered = [p for p in prices if (q1 - 1.5*iqr) <= p <= (q3 + 1.5*iqr)]
	return filtered
```

## Example Python Snippet for Redis Caching
```python
import redis
cache = redis.Redis()
def get_cached_result(key):
	result = cache.get(key)
	if result:
		return result
	# ...fetch from API, then cache...
	cache.set(key, api_result)
	return api_result
```

## Example: Handling API Rate Limits
```python
import time
def call_api_with_retry(api_func, *args, **kwargs):
	for attempt in range(5):
		try:
			return api_func(*args, **kwargs)
		except RateLimitError:
			time.sleep(2 ** attempt)
	raise Exception('API rate limit exceeded')
```
# Simplified Inherited Item Appraisal App

See project_tasks.md for full instructions.

## Running the Backend and Flutter App (with Mock eBay Data)

1. Create a virtual environment and install Python dependencies:
   ```bash
   cd backend
   python3 -m venv backend_venv
   source backend_venv/bin/activate
   pip install -r requirements.txt
   ```

2. Set up your OpenAI API key in the `.env` file:
   ```bash
   # Edit backend/.env and replace the placeholder with your actual API key
   OPENAI_API_KEY=your-actual-openai-api-key-here
   ```

3. Start the backend server:
   ```bash
   cd backend
   source backend_venv/bin/activate
   python run_backend.py
   ```
   - The backend will use mock data for eBay prices ("N/A") if the eBay API is unavailable.
   - Server will run on http://127.0.0.1:5000

4. Install Flutter dependencies:
   ```bash
   cd appraisal_app
   flutter pub get
   ```
5. Run the Flutter app:
   ```bash
   flutter run
   ```
   - Use an emulator or physical device. The app will display results from the backend, including mock eBay prices.

## Testing

### Backend Endpoint Test (Flask)
You can test the backend endpoint using curl or Postman:
```bash
curl -X POST http://localhost:5000/process \
  -H "Content-Type: application/json" \
  -d '{"image_base64": "<your_base64_image>"}'
```
Expected response:
```
{
  "description": "...",
  "research_notes": "...",
  "quicksell_price": "N/A",
  "patient_sell_price": "N/A",
  "error": "eBay API unavailable; using mock data."
}
```

### Flutter API Client Unit Test Example
Add this to `test/api_client_test.dart`:
```dart
import 'package:flutter_test/flutter_test.dart';
import 'package:appraisal_app/api_client.dart';

void main() {
  test('processImage returns expected keys', () async {
    // Use a dummy base64 string
    final result = await ApiClient.processImage('dGVzdA==');
    expect(result.containsKey('description'), true);
    expect(result.containsKey('research_notes'), true);
    expect(result.containsKey('quicksell_price'), true);
    expect(result.containsKey('patient_sell_price'), true);
  });
}
```

### Backend Unit Test Example
Add this to `backend/test_backend.py`:
```python
import unittest
import run_backend

class BackendTestCase(unittest.TestCase):
    def setUp(self):
        run_backend.app.testing = True
        self.client = run_backend.app.test_client()

    def test_process_image(self):
        response = self.client.post('/process', json={"image_base64": "dGVzdA=="})
        data = response.get_json()
        self.assertIn("description", data)
        self.assertIn("research_notes", data)
        self.assertIn("quicksell_price", data)
        self.assertIn("patient_sell_price", data)

if __name__ == '__main__':
    unittest.main()
```
