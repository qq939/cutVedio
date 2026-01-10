
2026年 1月 11日 星期日
User: 手动提交生成任务时候，如果之前的任务还在running状态，向comfyUI提交终止之前 自动提交的任务。
Assistant: Verified and refined the task cancellation logic. Created `tests/test_cancel_task.py` to confirm that `cancel_task` correctly attempts to delete pending tasks and interrupt running tasks. Updated `app.py` to log the result of the cancellation attempt.
