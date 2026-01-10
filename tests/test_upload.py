
import unittest
import os
import sys
import shutil
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import obs_utils
import app

class TestUpload(unittest.TestCase):
    def setUp(self):
        # Create dummy video file
        self.video_dir = os.path.join(os.path.dirname(__file__), '..', 'tmp', 'video')
        if not os.path.exists(self.video_dir):
            os.makedirs(self.video_dir)
        self.dummy_video = os.path.join(self.video_dir, 'test_video.mp4')
        with open(self.dummy_video, 'wb') as f:
            f.write(b'dummy content')

    def tearDown(self):
        if os.path.exists(self.dummy_video):
            os.remove(self.dummy_video)

    def test_obs_upload_failure(self):
        """Test upload failure logging"""
        # Mock subprocess.run to simulate failure
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stderr="Curl connection error", stdout="")
            
            # Capture stdout
            from io import StringIO
            captured_output = StringIO()
            sys.stdout = captured_output
            
            try:
                result = obs_utils.upload_file(self.dummy_video, 'test.mp4')
                self.assertIsNone(result)
                
                output = captured_output.getvalue()
                # print(f"Captured output: {output}") 
                
                self.assertIn("DEBUG: Upload failed with exit code 1", output)
                self.assertIn("DEBUG: Curl stderr: Curl connection error", output)
            finally:
                sys.stdout = sys.__stdout__

    def test_app_manual_upload_failure(self):
        """Test app endpoint behavior on upload failure"""
        with patch('obs_utils.upload_file') as mock_upload:
            mock_upload.return_value = None
            
            with app.app.test_client() as client:
                # Mock glob to find the file
                with patch('glob.glob') as mock_glob:
                    mock_glob.return_value = [self.dummy_video]
                    
                    # Capture stdout
                    from io import StringIO
                    captured_output = StringIO()
                    sys.stdout = captured_output
                    
                    try:
                        response = client.post('/manual_upload/video')
                        output = captured_output.getvalue()
                        
                        self.assertEqual(response.status_code, 500)
                        self.assertIn("Failed to upload video. Check logs.", response.json['error'])
                        self.assertIn("DEBUG: Upload failed (returned None/False).", output)
                    finally:
                        sys.stdout = sys.__stdout__

if __name__ == '__main__':
    unittest.main()
