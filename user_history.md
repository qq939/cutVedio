
2026年 1月 6日 星期二 10时45分20秒 CST
User: 模型就要用wan2.2-animate-mix，参考是这个！ `https://bailian.console.aliyun.com/?tab=api#/api/?type=model&url=2982219` Terminal#157-162 现在统一退回到第一版，我们使用http://obs.dimond.top来存储视频和图片。检索项目里的所有存储工具和应用，所有的cloudflare存储都要改成dimond存储。
Assistant: Reverted storage backend to OBS (obs.dimond.top). Updated `app.py` to use `obs_utils.py` for uploads. Updated `video_change_face_demo.py` to use `wan2.2-animate-mix` model with the specific parameter structure requested by the user. Removed `r2_utils.py` and updated frontend to reflect OBS storage.
