import unittest
from unittest.mock import patch, MagicMock
import threading
import time
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import app

class TestBackgroundMonitor(unittest.TestCase):
    
    @patch('app.comfy_utils.check_status')
    @patch('app.comfy_utils.download_result')
    @patch('app.obs_utils.upload_file')
    @patch('time.sleep')
    def test_monitor_task_success(self, mock_sleep, mock_upload, mock_download, mock_check_status):
        # Setup mocks
        # First call PENDING, second call SUCCEEDED
        mock_check_status.side_effect = [
            ('PENDING', None),
            ('SUCCEEDED', {'filename': 'test.mp4', 'subfolder': '', 'type': 'output'})
        ]
        
        mock_download.return_value = "/tmp/test.mp4"
        mock_upload.return_value = "http://obs/test.mp4"
        
        # We need to verify that monitor_task calls these functions
        # Since monitor_task runs in a thread, testing it directly calling it is easier for unit test
        # We can test the function logic itself without spawning a real thread, or spawn one and join.
        
        # Let's call the logic function directly (assuming we extract it or expose it)
        # We'll use app.monitor_task_logic(task_id) if we define it, 
        # or just test the function that will be the target of the thread.
        
        # For this test, I'll assume we add a function `monitor_task_status(task_id)` to app.py
        
        task_id = "123"
        
        # Call the function (synchronously for test)
        # Note: We need to make sure the loop breaks. 
        # In the real code, it breaks on SUCCEEDED or FAILED.
        app.monitor_task_status(task_id)
        
        # Verify check_status called twice
        self.assertEqual(mock_check_status.call_count, 2)
        
        # Verify download called once
        mock_download.assert_called_once()
        
        # Verify upload called once
        mock_upload.assert_called_once()
        
        # Verify naming convention in upload
        args, _ = mock_upload.call_args
        uploaded_filename = args[1]
        # Check format YYYYMMDDHHMMSSnew.mp4
        import re
        self.assertTrue(re.match(r'\d{14}new\.mp4', uploaded_filename))

    @patch('app.comfy_utils.check_status')
    @patch('app.obs_utils.upload_file')
    @patch('time.sleep')
    def test_monitor_task_failure(self, mock_sleep, mock_upload, mock_check_status):
        mock_check_status.return_value = ('FAILED', 'Error message')
        
        app.monitor_task_status("456")
        
        # Should stop after failure
        mock_check_status.assert_called_once()
        mock_upload.assert_not_called()

if __name__ == '__main__':
    unittest.main()
