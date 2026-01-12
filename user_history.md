
2026年 1月 12日 星期一
User: 本地不把图片和视频存储到video和face文件夹了，直接推送到OBS上，然后再从OBS下载下来推送到ComfyUI上
Assistant: Modified the workflow to avoid persistent local storage of uploaded videos. Implemented `submit_job_with_urls` in `comfy_utils.py` to handle downloading files from OBS URLs and uploading them to ComfyUI. Updated `app.py` to upload processed videos directly to OBS, use OBS URLs for ComfyUI submission, and clean up local video files after processing. Created `tests/test_obs_flow.py` to verify the new OBS-based workflow using TDD.
