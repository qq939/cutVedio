import unittest
import os
import sys
from unittest.mock import patch, MagicMock
from io import BytesIO
from PIL import Image

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import app

class TestUploadLulu(unittest.TestCase):
    def setUp(self):
        self.client = app.app.test_client()
        
    @patch('obs_utils.upload_file')
    @patch('os.remove')
    def test_upload_lulu_png(self, mock_remove, mock_upload):
        # Create a dummy image
        img = Image.new('RGB', (100, 100), color = 'red')
        img_io = BytesIO()
        img.save(img_io, 'JPEG')
        img_io.seek(0)
        
        mock_upload.return_value = "http://obs.dimond.top/lulu.png"
        
        response = self.client.post(
            '/manual_upload/character_image', 
            data={'image': (img_io, 'test.jpg')},
            content_type='multipart/form-data'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('url', response.json)
        self.assertEqual(response.json['url'], "http://obs.dimond.top/lulu.png")
        
        # Verify OBS upload called with lulu.png
        mock_upload.assert_called_once()
        args, kwargs = mock_upload.call_args
        # Check filename arg (2nd arg)
        self.assertEqual(args[1], 'lulu.png')
        # Check mime type
        self.assertEqual(kwargs.get('mime_type'), 'image/png')
        
        # Verify local file is cleaned up or not persistent in face/
        # The current implementation saves to face/lulu.webp.
        # We want to verify it doesn't leave junk, or uses a temp file.
        # If we use temp file, we expect os.remove to be called.
        # But if we assume the code changes to use tempfile or cleanup, we check logic.
        
if __name__ == '__main__':
    unittest.main()
