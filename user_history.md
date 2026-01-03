# User History

## 2026-01-04
**User**: 创建一个flask应用，风格参考http://teacher.dimond.top 中间有一个输入行和提交按钮。当你把一个视频的url链接提交的时候，下面以及/tmp/vedio里就会每隔1秒把视频帧提取出来保存为图片。参考一下 `https://github.com/qq939/cutVedio.git`

**Action**: 
1.  Initialized Git repository.
2.  Created Python virtual environment using `uv`.
3.  Implemented Flask application (`app.py`) with OpenCV for video frame extraction.
4.  Created frontend (`templates/index.html`) with requested styling.
5.  Configured project rules and documentation.

**User**: 你要参考ref.txt里面的做法，因为视频url不一定能下载视频，完成以后你告诉我你用了什么方法达到了目的。

**Action**:
1.  Read `ref.txt` (found `https://github.com/JefferyHcool/BiliNote.git`).
2.  Cloned and analyzed `BiliNote` repository.
3.  Identified that `BiliNote` uses `yt-dlp` for video downloading.
4.  Updated `app.py` to use `yt-dlp` to download video from URL first, then extract frames using OpenCV.
5.  Updated `requirements.txt` to include `yt-dlp`.
6.  Updated project rules and tips.

**User**: 错误: ERROR: [Douyin] ... Fresh cookies (not necessarily logged in) are needed ... 可使用 yt-dlp 的 --cookies-from-browser chrome 参数（需安装对应依赖），自动从浏览器读取 Cookie：

**Action**:
1.  Updated `app.py` to include `'cookiesfrombrowser': ('chrome',)` in `yt-dlp` options.
2.  Added `pycryptodomex` to `requirements.txt` to support cookie decryption from the browser.
3.  Reinstalled dependencies.
