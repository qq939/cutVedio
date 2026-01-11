
2026年 1月 11日 星期日
User: /overall接口不接受url了 ，改为接受视频文件video
Assistant: Updated the `/overall` endpoint in `app.py` to accept a video file upload instead of a JSON URL. The endpoint now saves the uploaded video and processes it using the standard pipeline (`_run_processing_pipeline`), ensuring consistent behavior with other upload endpoints. Added `tests/test_overall.py` to verify the new functionality.
