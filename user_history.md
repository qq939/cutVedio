
User: 自动提交给ComfyUI后，后端要每隔30秒检查生成状态，视频生成后按照命名规则上传至OBS
Assistant: Implemented background task monitoring in `app.py`. Created `monitor_task_status` thread that checks status every 30 seconds. Upon success, it automatically downloads the result, renames it to `YYYYMMDDHHMMSSnew.mp4`, and uploads it to OBS. Refactored `api_task_status` to reuse the shared `handle_task_completion` logic. Created `tests/test_background_monitor.py` to verify this behavior.
