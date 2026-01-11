
import unittest
import os
import sys
import json
from io import BytesIO
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import app

class TestOverall(unittest.TestCase):
    def setUp(self):
        self.client = app.app.test_client()
        self.video_content = b'fake video content'
        
    @patch('app._run_processing_pipeline')
    def test_overall_upload_success(self, mock_pipeline):
        # Mock pipeline response
        mock_pipeline.return_value = ({
            'message': 'Success',
            'task_id': '123',
            'upload_urls': {'character': 'http://c', 'video': 'http://v'}
        }, 200)
        
        data = {
            'video': (BytesIO(self.video_content), 'test.mp4')
        }
        
        response = self.client.post('/overall', data=data, content_type='multipart/form-data')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['task_id'], '123')
        
        # Verify pipeline was called
        mock_pipeline.assert_called_once()
        
    def test_overall_missing_file(self):
        response = self.client.post('/overall', data={}, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)
        self.assertIn('No video file provided', response.json['error'])

if __name__ == '__main__':
    unittest.main()
