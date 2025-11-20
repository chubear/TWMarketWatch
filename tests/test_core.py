import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.measure_value import MeasureValue
from core.measure_score import MeasureScore
from core.config import Config

class TestCore(unittest.TestCase):
    def setUp(self):
        # Mock profile path
        self.profile_path = "data/measure_profile.json"
        # Ensure dummy profile exists or mock loading it
        
    @patch('core.base_measure.BaseMeasure._load_measure_profile')
    @patch('requests.get')
    def test_measure_value_fetch(self, mock_get, mock_load_profile):
        # Setup mock profile
        mock_load_profile.return_value = {
            "test_measure": {
                "name": "Test Measure",
                "func_value": "fetch_taiex_bias"
            }
        }
        
        # Setup mock API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "success",
            "data": {
                "TWA00": {
                    "data": [
                        {"日期": "2024-01-01", "價格_BIAS_67D": 10.5},
                        {"日期": "2024-01-02", "價格_BIAS_67D": -5.2}
                    ]
                }
            }
        }
        mock_get.return_value = mock_response
        
        mv = MeasureValue(self.profile_path)
        s = mv.compute_one("test_measure", "2024-01-01", "2024-01-02")
        
        self.assertIsInstance(s, pd.Series)
        self.assertEqual(len(s), 2)
        self.assertEqual(s.iloc[0], 10.5)
        self.assertEqual(s.iloc[1], -5.2)

    @patch('core.base_measure.BaseMeasure._load_measure_profile')
    @patch('requests.get')
    def test_measure_score_calc(self, mock_get, mock_load_profile):
        # Setup mock profile
        mock_load_profile.return_value = {
            "test_score": {
                "name": "Test Score",
                "func_score": "calc_score_taiex_bias"
            }
        }
        
        # Setup mock API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "success",
            "data": {
                "TWA00": {
                    "data": [
                        {"日期": "2024-01-01", "價格_BIAS_67D": 10.5},
                        {"日期": "2024-01-02", "價格_BIAS_67D": -5.2}
                    ]
                }
            }
        }
        mock_get.return_value = mock_response
        
        ms = MeasureScore(self.profile_path)
        s = ms.compute_one("test_score", "2024-01-01", "2024-01-02")
        
        self.assertIsInstance(s, pd.Series)
        self.assertEqual(len(s), 2)
        self.assertEqual(s.iloc[0], 1) # 10.5 > 0 -> 1
        self.assertEqual(s.iloc[1], 0) # -5.2 <= 0 -> 0

if __name__ == '__main__':
    unittest.main()
