
import unittest
import json
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from comfy_utils import ComfyUIClient

class TestComfyCancellation(unittest.TestCase):
    def setUp(self):
        self.client = ComfyUIClient("127.0.0.1:8188")
        
    @patch('urllib.request.urlopen')
    def test_cancel_running_task(self, mock_urlopen):
        # Mock get_queue response to show task is RUNNING
        # ComfyUI queue format: 
        # queue_running: [[task_id, prompt_id, ...]]
        prompt_id = "test-prompt-id"
        queue_data = {
            "queue_pending": [],
            "queue_running": [["123", prompt_id, "extra"]]
        }
        
        # Mock responses
        # 1. delete queue (POST /queue)
        # 2. get queue (GET /queue) -> returns queue_data
        # 3. interrupt (POST /interrupt)
        
        mock_response_delete = MagicMock()
        mock_response_delete.read.return_value = b'{"success": true}'
        mock_response_delete.getcode.return_value = 200
        
        mock_response_queue = MagicMock()
        mock_response_queue.read.return_value = json.dumps(queue_data).encode('utf-8')
        mock_response_queue.getcode.return_value = 200
        
        mock_response_interrupt = MagicMock()
        mock_response_interrupt.read.return_value = b'{"success": true}'
        mock_response_interrupt.getcode.return_value = 200
        
        # Side effect to return different mocks
        def side_effect(req, *args, **kwargs):
            url = req if isinstance(req, str) else req.full_url
            
            response_mock = MagicMock()
            
            if "/queue" in url:
                if isinstance(req, str) or getattr(req, 'method', 'GET') == 'GET':
                     response_mock.read.return_value = json.dumps(queue_data).encode('utf-8')
                else: 
                     response_mock.read.return_value = b'{"success": true}'
            elif "/interrupt" in url:
                response_mock.read.return_value = b'{"success": true}'
            elif "/object_info" in url:
                response_mock.read.return_value = b'{}'
            else:
                response_mock.read.return_value = b'{}'
                
            response_mock.getcode.return_value = 200
            
            # Return a context manager that yields the response_mock
            cm = MagicMock()
            cm.__enter__.return_value = response_mock
            cm.__exit__.return_value = None
            return cm
            
        mock_urlopen.side_effect = side_effect
        
        # Act
        result = self.client.cancel_task(prompt_id)
        
        # Assert
        self.assertTrue(result)
        
        # Verify interrupt was called
        interrupt_called = False
        for call in mock_urlopen.call_args_list:
            args, _ = call
            req = args[0]
            url = req if isinstance(req, str) else req.full_url
            if "/interrupt" in url:
                interrupt_called = True
                break
        
        self.assertTrue(interrupt_called, "Interrupt should be called for running task")

    @patch('urllib.request.urlopen')
    def test_cancel_pending_task(self, mock_urlopen):
        # Mock get_queue response to show task is PENDING
        prompt_id = "test-prompt-id-pending"
        queue_data = {
            "queue_pending": [["124", prompt_id, "extra"]],
            "queue_running": []
        }
        
        mock_response_queue = MagicMock()
        mock_response_queue.read.return_value = json.dumps(queue_data).encode('utf-8')
        
        def side_effect(req, *args, **kwargs):
            url = req if isinstance(req, str) else req.full_url
            
            response_mock = MagicMock()
            
            if "/queue" in url:
                if isinstance(req, str) or getattr(req, 'method', 'GET') == 'GET':
                     response_mock.read.return_value = json.dumps(queue_data).encode('utf-8')
                else: # POST /queue (delete)
                     response_mock.read.return_value = b'{"success": true}'
            elif "/interrupt" in url:
                 response_mock.read.return_value = b'{"success": true}'
            elif "/object_info" in url:
                response_mock.read.return_value = b'{}'
            else:
                response_mock.read.return_value = b'{}'
                
            response_mock.getcode.return_value = 200
            
            cm = MagicMock()
            cm.__enter__.return_value = response_mock
            cm.__exit__.return_value = None
            return cm
            
        mock_urlopen.side_effect = side_effect
        
        # Act
        result = self.client.cancel_task(prompt_id)
        
        # Assert
        self.assertTrue(result)
        
        # Verify interrupt was NOT called
        interrupt_called = False
        for call in mock_urlopen.call_args_list:
            args, _ = call
            req = args[0]
            url = req if isinstance(req, str) else req.full_url
            if "/interrupt" in url:
                interrupt_called = True
                break
        
        self.assertFalse(interrupt_called, "Interrupt should NOT be called for pending task")

if __name__ == '__main__':
    unittest.main()
