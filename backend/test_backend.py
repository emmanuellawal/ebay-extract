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
