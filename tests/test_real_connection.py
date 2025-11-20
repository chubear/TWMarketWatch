import unittest
import pandas as pd
import os
import sys
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.measure_value import MeasureValue

class TestRealConnection(unittest.TestCase):
    def setUp(self):
        # Use the real profile path
        # Assuming the test is run from project root or tests/ directory
        # We try to locate the file relative to this script
        self.profile_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/measure_profile.json'))
        
        if not os.path.exists(self.profile_path):
            self.skipTest(f"Profile not found at {self.profile_path}")
            
    def test_real_api_connection(self):
        """Test fetching real data from the API using the actual profile."""
        print(f"\nTesting real connection with profile: {self.profile_path}")
        
        mv = MeasureValue(self.profile_path)
        
        # Define a recent date range (e.g., last 180 days to ensure we get data)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)
        
        # Pick a measure to test (e.g., 加權指數乖離率_id)
        # We pick the first key from the profile to be dynamic
        if not mv.measure_profile:
            self.fail("Measure profile is empty")
            
        first_measure_id = list(mv.measure_profile.keys())[0]
        print(f"Testing measure: {first_measure_id}")
        
        try:
            s = mv.compute_one(first_measure_id, start_date, end_date)
            
            print(f"Successfully fetched {len(s)} data points.")
            if not s.empty:
                print("Head of data:")
                print(s.head())
            
            self.assertIsInstance(s, pd.Series)
            # We don't strictly assert not empty because the API might return no data for specific dates/stocks
            # but usually it should return something for 180 days.
            if s.empty:
                print("Warning: Returned series is empty. Check if the API has data for this period.")
            
        except Exception as e:
            self.fail(f"Real API connection failed: {e}")

if __name__ == '__main__':
    unittest.main()
