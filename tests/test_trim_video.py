
import unittest
import os
import sys
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import app

class TestTrimVideo(unittest.TestCase):
    def setUp(self):
        self.client = app.app.test_client()
        self.video_path = "dummy_path.mp4"
        self.trimmed_path = "dummy_path_trimmed.mp4"

    @patch('subprocess.run')
    def test_trim_video_command(self, mock_run):
        # Setup mock to return success
        mock_run.return_value = MagicMock(returncode=0, stdout="success", stderr="")
        
        result = app.trim_video(self.video_path, self.trimmed_path, duration=9)
        
        self.assertTrue(result)
        
        # Verify subprocess.run was called with correct args
        mock_run.assert_called_once()
        args, _ = mock_run.call_args
        command = args[0]
        
        # Check if duration is 9
        self.assertIn('-t', command)
        t_index = command.index('-t')
        self.assertEqual(command[t_index + 1], '9')
        
        # Check input and output paths
        self.assertIn(self.video_path, command)
        self.assertIn(self.trimmed_path, command)

    @patch('app.trim_video')
    @patch('app.convert_and_upload_character')
    @patch('obs_utils.upload_file')
    @patch('comfy_utils.submit_job')
    @patch('cv2.VideoCapture')
    def test_pipeline_calls_trim(self, mock_cap, mock_submit, mock_upload, mock_convert, mock_trim):
        # Setup mocks
        mock_trim.return_value = True
        mock_convert.return_value = "http://char"
        mock_upload.return_value = "http://vid"
        mock_submit.return_value = ("123", None)
        
        # Mock video capture
        mock_cap_instance = MagicMock()
        mock_cap_instance.isOpened.return_value = True
        mock_cap_instance.get.return_value = 30 # fps
        mock_cap_instance.read.return_value = (False, None) # No frames to extract immediately
        mock_cap.return_value = mock_cap_instance
        
        # Call the pipeline directly
        # We need to mock os.path.exists if trim_video relies on it? 
        # But we are mocking trim_video itself, so it should be fine.
        
        result, code = app._run_processing_pipeline(self.video_path, "source")
        
        self.assertEqual(code, 200)
        mock_trim.assert_called_once()
        
        # Verify the path passed to trim_video matches expected logic
        # app.py logic:
        # dir_name = os.path.dirname(video_path)
        # base_name = os.path.basename(video_path)
        # name, ext = os.path.splitext(base_name)
        # trimmed_filename = f"{name}_trimmed{ext}"
        # trimmed_path = os.path.join(dir_name, trimmed_filename)
        
        # Check call args
        args, _ = mock_trim.call_args
        self.assertEqual(args[0], self.video_path)
        # The output path should contain "_trimmed"
        self.assertIn("_trimmed", args[1])

if __name__ == '__main__':
    unittest.main()
