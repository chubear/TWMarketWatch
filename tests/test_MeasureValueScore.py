import unittest
import pandas as pd
import os
import sys
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.measure_value import MeasureValue
from core.measure_score import MeasureScore

class TestMeasureValueScore(unittest.TestCase):
    def setUp(self):
        # Use the real profile path
        # Assuming the test is run from project root or tests/ directory
        # We try to locate the file relative to this script
        self.profile_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/measure_profile.json'))
        
        if not os.path.exists(self.profile_path):
            self.skipTest(f"Profile not found at {self.profile_path}")
            
    def test_MeasureValue(self):

        mv = MeasureValue(self.profile_path)
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)        
           
        test_measure_id = list(mv.measure_profile.keys())[0]
        print(f"Testing measure: {test_measure_id}")
        
        try:
            s = mv.compute_one(test_measure_id, start_date, end_date)

            if not s.empty:
                print("Head of data:")
                print(s.head())
            
            if s.empty:
                print("Warning: Returned series is empty. Check if the API has data for this period.")
            
        except Exception as e:
            self.fail(f"Real API connection failed: {e}")

    def test_MeasureScore(self):

        ms = MeasureScore(self.profile_path)
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)        
           
        test_measure_id = list(ms.measure_profile.keys())[0]
        print(f"Testing measure: {test_measure_id}")
        
        try:
            s = ms.compute_one(test_measure_id, start_date, end_date)

            if not s.empty:
                print("Head of data:")
                print(s.head())
            
            if s.empty:
                print("Warning: Returned series is empty. Check if the API has data for this period.")
            
        except Exception as e:
            self.fail(f"Real API connection failed: {e}")

if __name__ == '__main__':
    unittest.main()
