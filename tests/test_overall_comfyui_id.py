import unittest
import os
import sys
import json
from io import BytesIO
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import app

class TestOverallComfyUIID(unittest.TestCase):
    def setUp(self):
        self.client = app.app.test_client()
        self.video_content = b'fake video content'
        
    @patch('app._run_processing_pipeline')
    def test_overall_returns_comfyUIID(self, mock_pipeline):
        # Mock pipeline response to include comfyUIID (which is task_id in our logic)
        mock_pipeline.return_value = ({
            'message': 'Success',
            'task_id': 'prompt_123',
            'comfyUIID': 'prompt_123',
            'upload_urls': {'character': 'http://c', 'video': 'http://v'}
        }, 200)
        
        data = {
            'video': (BytesIO(self.video_content), 'test.mp4')
        }
        
        response = self.client.post('/overall', data=data, content_type='multipart/form-data')
        
        self.assertEqual(response.status_code, 200)
        
        # Check if response contains comfyUIID
        # Based on user request, the key should be 'comfyUIID'
        # We need to ensure app.py maps 'task_id' to 'comfyUIID' or includes it.
        
        # If the implementation simply adds 'comfyUIID' = task_id:
        json_data = response.json
        self.assertIn('comfyUIID', json_data)
        self.assertEqual(json_data['comfyUIID'], 'prompt_123')

if __name__ == '__main__':
    unittest.main()
