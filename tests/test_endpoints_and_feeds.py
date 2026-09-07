import unittest
from keep_alive import app
from indicators import get_spot_gold_price, fetch_technical_data

class TestEndpointsAndFeeds(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_keep_alive_health(self):
        res = self.client.get('/health')
        self.assertEqual(res.status_code, 200)
        self.assertIn("I'm alive", res.text)

    def test_keep_alive_cron(self):
        res = self.client.get('/cron')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("status"), "ok")
        self.assertEqual(data.get("action"), "triggered_scan")

    def test_keep_alive_check(self):
        res = self.client.get('/check')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("status"), "online")

    def test_live_spot_gold_price(self):
        price = get_spot_gold_price()
        self.assertIsNotNone(price)
        self.assertGreater(price, 3000.0)

    def test_fetch_technical_data_15m(self):
        snapshot = fetch_technical_data("15m")
        self.assertIsNotNone(snapshot)
        self.assertEqual(snapshot.symbol, "XAUUSD")
        self.assertGreater(snapshot.close_price, 3000.0)
        self.assertIsNotNone(snapshot.rsi_14)
        self.assertIsNotNone(snapshot.sma_20)

if __name__ == '__main__':
    unittest.main()
