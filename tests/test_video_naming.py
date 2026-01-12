import unittest
from datetime import datetime
import re

class TestVideoNaming(unittest.TestCase):
    def test_naming_format(self):
        # Naming requirement: 年月日时分秒new.mp4 (no other symbols)
        # Format: %Y%m%d%H%M%Snew.mp4
        
        now = datetime(2026, 1, 12, 13, 30, 0)
        expected_filename = "20260112133000new.mp4"
        
        generated_filename = now.strftime("%Y%m%d%H%M%Snew.mp4")
        
        self.assertEqual(generated_filename, expected_filename)
        
        # Verify no symbols (except .mp4 which is extension, user said "中间不要有任何符号")
        # Check if it contains only digits before "new.mp4"
        prefix = generated_filename.replace("new.mp4", "")
        self.assertTrue(prefix.isdigit())
        
        # Verify length (YYYYMMDDHHMMSS = 14 chars)
        self.assertEqual(len(prefix), 14)

if __name__ == '__main__':
    unittest.main()
