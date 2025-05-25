import unittest
from unittest.mock import patch, MagicMock
import requests # Required for requests.exceptions
from alpha_vantage_client import get_daily_adjusted_stock_data, calculate_simple_insights
import logging

# Suppress logging output during tests by setting the level higher or to a NullHandler
# This is to keep test output clean.
# If you want to see logs during tests, you can comment this out or change the level.
logging.disable(logging.CRITICAL)


class TestAlphaVantageClient(unittest.TestCase):

    @patch('alpha_vantage_client.requests.get')
    def test_get_daily_adjusted_success(self, mock_get):
        mock_response_data = {"Time Series (Daily)": {"2023-01-01": {"4. close": "100"}}}
        mock_get.return_value.ok = True
        mock_get.return_value.json.return_value = mock_response_data
        
        result = get_daily_adjusted_stock_data("fake_api_key", "TEST")
        self.assertEqual(result, mock_response_data["Time Series (Daily)"])
        mock_get.assert_called_once()

    @patch('alpha_vantage_client.requests.get')
    def test_get_daily_adjusted_api_error(self, mock_get):
        mock_response_data = {"Error Message": "Invalid API key"}
        mock_get.return_value.ok = True
        mock_get.return_value.json.return_value = mock_response_data
        
        result = get_daily_adjusted_stock_data("fake_api_key", "TEST")
        self.assertIsNone(result)
        mock_get.assert_called_once()

    @patch('alpha_vantage_client.requests.get')
    def test_get_daily_adjusted_request_exception(self, mock_get):
        mock_get.side_effect = requests.exceptions.RequestException("Test network error")
        
        result = get_daily_adjusted_stock_data("fake_api_key", "TEST")
        self.assertIsNone(result)
        mock_get.assert_called_once()

    @patch('alpha_vantage_client.requests.get')
    def test_get_daily_adjusted_missing_key(self, mock_get):
        mock_response_data = {"SomeOtherKey": "SomeValue"}
        mock_get.return_value.ok = True
        mock_get.return_value.json.return_value = mock_response_data
        
        result = get_daily_adjusted_stock_data("fake_api_key", "TEST")
        self.assertIsNone(result)
        mock_get.assert_called_once()

    @patch('alpha_vantage_client.requests.get')
    def test_get_daily_adjusted_http_error(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Test HTTP Error")
        mock_get.return_value = mock_response
        
        result = get_daily_adjusted_stock_data("fake_api_key", "TEST")
        self.assertIsNone(result)
        mock_get.assert_called_once()
        mock_response.raise_for_status.assert_called_once()

    def test_calculate_insights_success(self):
        time_series_data = {
            "2023-01-05": {"1. open": "104", "2. high": "106", "3. low": "103", "4. close": "105.00", "5. adjusted close": "105.00", "6. volume": "1000", "7. dividend amount": "0.00", "8. split coefficient": "1.0"},
            "2023-01-04": {"1. open": "101", "2. high": "103", "3. low": "100", "4. close": "102.00", "5. adjusted close": "102.00", "6. volume": "1000", "7. dividend amount": "0.00", "8. split coefficient": "1.0"},
            "2023-01-03": {"1. open": "99",  "2. high": "101", "3. low": "98",  "4. close": "100.00", "5. adjusted close": "100.00", "6. volume": "1000", "7. dividend amount": "0.00", "8. split coefficient": "1.0"},
            "2023-01-02": {"1. open": "97",  "2. high": "99",  "3. low": "96",  "4. close": "98.00",  "5. adjusted close": "98.00",  "6. volume": "1000", "7. dividend amount": "0.00", "8. split coefficient": "1.0"},
            "2023-01-01": {"1. open": "94",  "2. high": "96",  "3. low": "93",  "4. close": "95.00",  "5. adjusted close": "95.00",  "6. volume": "1000", "7. dividend amount": "0.00", "8. split coefficient": "1.0"}
        }
        n_days = 3
        # Expected SMA: (105+102+100)/3 = 102.333...
        # Expected % change: ((105-100)/100)*100 = 5.0%
        # Note: closing_prices for calculation will be [105.0, 102.0, 100.0]
        # Most recent is 105.0, Nth day (3rd) is 100.0
        expected_sma = (105.00 + 102.00 + 100.00) / 3
        expected_percentage_change = ((105.00 - 100.00) / 100.00) * 100
        
        result = calculate_simple_insights(time_series_data, n_days)
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result["n_day_sma"], expected_sma, places=2)
        self.assertAlmostEqual(result["n_day_percentage_change"], expected_percentage_change, places=2)

    def test_calculate_insights_insufficient_data(self):
        time_series_data = {
            "2023-01-02": {"4. close": "98.00"},
            "2023-01-01": {"4. close": "95.00"}
        }
        n_days = 3
        result = calculate_simple_insights(time_series_data, n_days)
        self.assertIsNone(result)

    def test_calculate_insights_empty_data(self):
        time_series_data = {}
        n_days = 3
        result = calculate_simple_insights(time_series_data, n_days)
        self.assertIsNone(result)

    def test_calculate_insights_missing_close_price(self):
        time_series_data = {
            "2023-01-03": {"4. close": "100.00"},
            "2023-01-02": {"1. open": "98.00"}, # Missing '4. close'
            "2023-01-01": {"4. close": "95.00"}
        }
        n_days = 3
        result = calculate_simple_insights(time_series_data, n_days)
        self.assertIsNone(result)

    def test_calculate_insights_invalid_close_price(self):
        time_series_data = {
            "2023-01-03": {"4. close": "100.00"},
            "2023-01-02": {"4. close": "invalid_price"},
            "2023-01-01": {"4. close": "95.00"}
        }
        n_days = 3
        result = calculate_simple_insights(time_series_data, n_days)
        self.assertIsNone(result)

    def test_calculate_insights_zero_denominator_percentage_change(self):
        time_series_data = {
            "2023-01-03": {"4. close": "10.00"},
            "2023-01-02": {"4. close": "5.00"},
            "2023-01-01": {"4. close": "0.00"} # Nth day close is 0
        }
        n_days = 3
        # SMA: (10+5+0)/3 = 5
        # % change: (10-0)/0 -> inf
        expected_sma = (10.00 + 5.00 + 0.00) / 3
        
        result = calculate_simple_insights(time_series_data, n_days)
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result["n_day_sma"], expected_sma, places=2)
        self.assertEqual(result["n_day_percentage_change"], float('inf'))

    def test_calculate_insights_sorting_robustness(self):
        # Data not sorted by date (most recent not first)
        time_series_data = {
            "2023-01-01": {"4. close": "95.00"},
            "2023-01-03": {"4. close": "100.00"},
            "2023-01-02": {"4. close": "98.00"},
            "2023-01-05": {"4. close": "105.00"},
            "2023-01-04": {"4. close": "102.00"}
        }
        n_days = 3
        # After sorting, the latest 3 days are 05, 04, 03
        # Closing prices for calculation: [105.0, 102.0, 100.0]
        # Expected SMA: (105+102+100)/3 = 102.33
        # Expected % change: ((105-100)/100)*100 = 5.0%
        expected_sma = (105.00 + 102.00 + 100.00) / 3
        expected_percentage_change = ((105.00 - 100.00) / 100.00) * 100
        
        result = calculate_simple_insights(time_series_data, n_days)
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result["n_day_sma"], expected_sma, places=2)
        self.assertAlmostEqual(result["n_day_percentage_change"], expected_percentage_change, places=2)


if __name__ == '__main__':
    unittest.main()
