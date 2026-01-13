
User: /overall端口要返回comfyUIID
Assistant: Updated the `/overall` endpoint in `app.py` to include the `comfyUIID` field in the response JSON, mapping it from the internal `task_id`. Created `tests/test_overall_comfyui_id.py` to verify that the response correctly contains the `comfyUIID`.
