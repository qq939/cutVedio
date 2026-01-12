import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import tempfile

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import comfy_utils
import app

class TestOBSFlow(unittest.TestCase):
    
    @patch('comfy_utils.requests.get')
    @patch('comfy_utils.client.upload_file')
    @patch('comfy_utils.queue_workflow_template')
    def test_submit_job_with_urls(self, mock_queue, mock_upload, mock_get):
        # Setup mocks
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"fake_content"
        mock_get.return_value = mock_response
        
        mock_upload.side_effect = [{'name': 'char.png'}, {'name': 'video.mp4'}]
        mock_queue.return_value = ('prompt_id_123', None)
        
        # Call the function
        char_url = "http://obs.example.com/char.png"
        video_url = "http://obs.example.com/video.mp4"
        
        # We need to implement this function in comfy_utils
        if hasattr(comfy_utils, 'submit_job_with_urls'):
            prompt_id, error = comfy_utils.submit_job_with_urls(char_url, video_url)
            
            # Verify
            self.assertEqual(prompt_id, 'prompt_id_123')
            self.assertIsNone(error)
            
            # Verify downloads happened
            self.assertEqual(mock_get.call_count, 2)
            mock_get.assert_any_call(char_url, stream=True)
            mock_get.assert_any_call(video_url, stream=True)
            
            # Verify uploads happened
            self.assertEqual(mock_upload.call_count, 2)
            
            # Verify queue called
            mock_queue.assert_called_once_with('char.png', 'video.mp4')
        else:
            self.fail("submit_job_with_urls not implemented yet")

if __name__ == '__main__':
    unittest.main()
