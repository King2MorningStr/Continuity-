import unittest
import requests
import time
import threading
import json
from dimensional_cortex.udac_listener import start_udac_listener, get_udac_stats, _state

class TestUDACListener(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Start listener on a non-default port for testing
        cls.port = 7014
        cls.thread = start_udac_listener(port=cls.port)
        # Give it a moment to start
        time.sleep(1)

    def setUp(self):
        # Reset state for each test if possible, but _state is global.
        # We can just check increments or specific values.
        pass

    def test_event_reception(self):
        url = f"http://127.0.0.1:{self.port}/udac/event"
        payload = {
            "text": "Hello World",
            "source_app": "com.example.app",
            "event_type": 1,
            "timestamp": 123456789
        }

        response = requests.post(url, json=payload)
        self.assertEqual(response.status_code, 200)

        # Allow some time for the thread to process (it's synchronous in handler but running in thread)
        time.sleep(0.1)

        stats = get_udac_stats()
        self.assertEqual(stats["last_text"], "Hello World")
        self.assertEqual(stats["last_source"], "com.example.app")
        self.assertGreater(stats["total_events"], 0)
        self.assertIn("com.example.app", stats["platform_counts"])

    def test_invalid_payload(self):
        url = f"http://127.0.0.1:{self.port}/udac/event"
        response = requests.post(url, data="Not JSON")
        self.assertEqual(response.status_code, 400)

    def test_wrong_endpoint(self):
        url = f"http://127.0.0.1:{self.port}/wrong/path"
        response = requests.post(url, json={})
        self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
    unittest.main()
