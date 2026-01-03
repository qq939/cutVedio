import datetime
import json
import re
from typing import Optional
from urllib.parse import quote, urlencode

import httpx
import requests
from pydantic import BaseModel
from abogus import ABogus

DOUYIN_DOMAIN = "https://www.douyin.com"

def get_timestamp(unit: str = "milli"):
    now = datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)
    if unit == "milli":
        return int(now.total_seconds() * 1000)
    elif unit == "sec":
        return int(now.total_seconds())
    elif unit == "min":
        return int(now.total_seconds() / 60)
    else:
        raise ValueError("Unsupported time unit")

class DouyinConfig:
    HEADERS = {
        "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
        "Referer": "https://www.douyin.com/",
        "Cookie": None
    }
    
    MS_TOKEN = {
        "url": "https://mssdk.bytedance.com/web/report",
        "magic": 538969122,
        "version": 1,
        "dataType": 8,
        "strData": "fWOdJTQR3/jwmZqBBsPO6tdNEc1jX7YTwPg0Z8CT+j3HScLFbj2Zm1XQ7/lqgSutntVKLJWaY3Hc/+vc0h+So9N1t6EqiImu5jKyUa+S4NPy6cNP0x9CUQQgb4+RRihCgsn4QyV8jivEFOsj3N5zFQbzXRyOV+9aG5B5EAnwpn8C70llsWq0zJz1VjN6y2KZiBZRyonAHE8feSGpwMDeUTllvq6BG3AQZz7RrORLWNCLEoGzM6bMovYVPRAJipuUML4Hq/568bNb5vqAo0eOFpvTZjQFgbB7f/CtAYYmnOYlvfrHKBKvb0TX6AjYrw2qmNNEer2ADJosmT5kZeBsogDui8rNiI/OOdX9PVotmcSmHOLRfw1cYXTgwHXr6cJeJveuipgwtUj2FNT4YCdZfUGGyRDz5bR5bdBuYiSRteSX12EktobsKPksdhUPGGv99SI1QRVmR0ETdWqnKWOj/7ujFZsNnfCLxNfqxQYEZEp9/U01CHhWLVrdzlrJ1v+KJH9EA4P1Wo5/2fuBFVdIz2upFqEQ11DJu8LSyD43qpTok+hFG3Moqrr81uPYiyPHnUvTFgwA/TIE11mTc/pNvYIb8IdbE4UAlsR90eYvPkI+rK9KpYN/l0s9ti9sqTth12VAw8tzCQvhKtxevJRQntU3STeZ3coz9Dg8qkvaSNFWuBDuyefZBGVSgILFdMy33//l/eTXhQpFrVc9OyxDNsG6cvdFwu7trkAENHU5eQEWkFSXBx9Ml54+fa3LvJBoacfPViyvzkJworlHcYYTG392L4q6wuMSSpYUconb+0c5mwqnnLP6MvRdm/bBTaY2Q6RfJcCxyLW0xsJMO6fgLUEjAg/dcqGxl6gDjUVRWbCcG1NAwPCfmYARTuXQYbFc8LO+r6WQTWikO9Q7Cgda78pwH07F8bgJ8zFBbWmyrghilNXENNQkyIzBqOQ1V3w0WXF9+Z3vG3aBKCjIENqAQM9qnC14WMrQkfCHosGbQyEH0n/5R2AaVTE/ye2oPQBWG1m0Gfcgs/96f6yYrsxbDcSnMvsA+okyd6GfWsdZYTIK1E97PYHlncFeOjxySjPpfy6wJc4UlArJEBZYmgveo1SZAhmXl3pJY3yJa9CmYImWkhbpwsVkSmG3g11JitJXTGLIfqKXSAhh+7jg4HTKe+5KNir8xmbBI/DF8O/+diFAlD+BQd3cV0G4mEtCiPEhOvVLKV1pE+fv7nKJh0t38wNVdbs3qHtiQNN7JhY4uWZAosMuBXSjpEtoNUndI+o0cjR8XJ8tSFnrAY8XihiRzLMfeisiZxWCvVwIP3kum9MSHXma75cdCQGFBfFRj0jPn1JildrTh2vRgwG+KeDZ33BJ2VGw9PgRkztZ2l/W5d32jc7H91FftFFhwXil6sA23mr6nNp6CcrO7rOblcm5SzXJ5MA601+WVicC/g3p6A0lAnhjsm37qP+xGT+cbCFOfjexDYEhnqz0QZm94CCSnilQ9B/HBLhWOddp9GK0SABIk5i3xAH701Xb4HCcgAulvfO5EK0RL2eN4fb+CccgZQeO1Zzo4qsMHc13UG0saMgBEH8SqYlHz2S0CVHuDY5j1MSV0nsShjM01vIynw6K0T8kmEyNjt1eRGlleJ5lvE8vonJv7rAeaVRZ06rlYaxrMT6cK3RSHd2liE50Z3ik3xezwWoaY6zBXvCzljyEmqjNFgAPU3gI+N1vi0MsFmwAwFzYqqWdk3jwRoWLp//FnawQX0g5T64CnfAe/o2e/8o5/bvz83OsAAwZoR48GZzPu7KCIN9q4GBjyrePNx5Csq2srblifmzSKwF5MP/RLYsk6mEE15jpCMKOVlHcu0zhJybNP3AKMVllF6pvn+HWvUnLXNkt0A6zsfvjAva/tbLQiiiYi6vtheasIyDz3HpODlI+BCkV6V8lkTt7m8QJ1IcgTfqjQBummyjYTSwsQji3DdNCnlKYd13ZQa54"
    }

class BaseRequestModel(BaseModel):
    device_platform: str = "webapp"
    aid: str = "6383"
    channel: str = "channel_pc_web"
    pc_client_type: int = 1
    version_code: str = "290100"
    version_name: str = "29.1.0"
    cookie_enabled: str = "true"
    screen_width: int = 1920
    screen_height: int = 1080
    browser_language: str = "zh-CN"
    browser_platform: str = "Win32"
    browser_name: str = "Chrome"
    browser_version: str = "130.0.0.0"
    browser_online: str = "true"
    engine_name: str = "Blink"
    engine_version: str = "130.0.0.0"
    os_name: str = "Windows"
    os_version: str = "10"
    cpu_core_num: int = 12
    device_memory: int = 8
    platform: str = "PC"
    downlink: str = "10"
    effective_type: str = "4g"
    from_user_page: str = "1"
    locate_query: str = "false"
    need_time_list: str = "1"
    pc_libra_divert: str = "Windows"
    publish_video_strategy_type: str = "2"
    round_trip_time: str = "0"
    show_live_replay_strategy: str = "1"
    time_list_query: str = "0"
    whale_cut_token: str = ""
    update_version_code: str = "170400"
    msToken: str = None

class DouyinUtils:
    def __init__(self):
        self.headers_config = DouyinConfig.HEADERS.copy()
        # Remove Cookie if None to avoid httpx error
        if self.headers_config.get("Cookie") is None:
            self.headers_config.pop("Cookie", None)
        self.ms_token_config = DouyinConfig.MS_TOKEN.copy()
        self.ttwid_config = {
            "url": "https://ttwid.bytedance.com/ttwid/union/register/",
            "data": '{"region":"cn","aid":1768,"needFid":false,"service":"www.ixigua.com","migrate_info":{"ticket":"","source":"node"},"cbUrlProtocol":"https","union":true}'
        }

    @staticmethod
    def find_url(string: str) -> list:
        url = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', string)
        return url

    def extract_video_id(self, url: str) -> str:
        video_url = self.find_url(url)
        if len(video_url):
            video_url = video_url[0]
            try:
                response = requests.head(video_url, allow_redirects=True)
                url = response.url
            except Exception as e:
                return ""
        patterns = [
            r'video/(\d+)',
            r'aweme_id=(\d+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return ""

    def gen_real_msToken(self) -> str:
        try:
            payload = json.dumps(
                {
                    "magic": self.ms_token_config["magic"],
                    "version": self.ms_token_config["version"],
                    "dataType": self.ms_token_config["dataType"],
                    "strData": self.ms_token_config["strData"],
                    "tspFromClient": get_timestamp(),
                }
            )
            headers = {
                "User-Agent": self.headers_config["User-Agent"],
                "Content-Type": "application/json",
            }
            transport = httpx.HTTPTransport(retries=5)
            with httpx.Client(transport=transport) as client:
                try:
                    response = client.post(
                        self.ms_token_config["url"], content=payload, headers=headers
                    )
                    response.raise_for_status()

                    msToken = str(httpx.Cookies(response.cookies).get("msToken"))
                    if len(msToken) not in [120, 128]:
                         # Fallback if generation fails, return empty or mock? 
                         # Actually for now let's just proceed, usually it works or we catch error
                         pass
                    return msToken
                except Exception as e:
                    print(f"Douyin msToken API failed: {e}")
                    return ""
        except Exception as e:
            print(f"Douyin msToken API error: {e}")
            return ""

    def gen_ttwid(self) -> str:
        try:
            headers = {
                "User-Agent": self.headers_config["User-Agent"],
                "Content-Type": "application/json",
            }
            with httpx.Client() as client:
                response = client.post(
                    self.ttwid_config["url"], content=self.ttwid_config["data"], headers=headers
                )
                response.raise_for_status()
                ttwid = str(httpx.Cookies(response.cookies).get("ttwid"))
                return ttwid
        except Exception as e:
            print(f"Generate ttwid failed: {e}")
            return ""

    def get_video_url(self, video_url: str) -> str:
        try:
            aweme_id = self.extract_video_id(video_url)
            if not aweme_id:
                return None
                
            base_params = BaseRequestModel().model_dump()
            base_params["msToken"] = self.gen_real_msToken()
            base_params["aweme_id"] = aweme_id
            
            bogus = ABogus()
            ab_value = bogus.get_value(base_params)
            a_bogus = quote(ab_value, safe='')
            
            query_str = urlencode(base_params)
            full_url = f"{DOUYIN_DOMAIN}/aweme/v1/web/aweme/detail/?{query_str}&a_bogus={a_bogus}"
            
            headers = self.headers_config.copy()
            # Important: Referer is needed
            headers['Referer'] = 'https://www.douyin.com/'
            
            # Add cookies
            cookies = {}
            ttwid = self.gen_ttwid()
            if ttwid:
                cookies['ttwid'] = ttwid
            
            # Combine with existing cookies if any
            if 'Cookie' in headers:
                # simple parsing if needed, but here we likely have None or empty
                pass
            
            # Construct cookie string
            cookie_str = "; ".join([f"{k}={v}" for k, v in cookies.items()])
            if cookie_str:
                headers['Cookie'] = cookie_str
            
            with httpx.Client() as client:
                response = client.get(full_url, headers=headers)
                print(f"Response status: {response.status_code}")
                # print(f"Response text: {response.text[:500]}") # Print first 500 chars
                if response.status_code == 200:
                    try:
                        data = response.json()
                    except json.JSONDecodeError:
                        print("Failed to decode JSON. Response might be HTML.")
                        return None
                    # Try to get highest quality video
                    try:
                        video_list = data['aweme_detail']['video']['bit_rate']
                        # Find url_list in one of the bit_rates, or directly from video.play_addr
                        # Usually play_addr has url_list
                        uri = data['aweme_detail']['video']['play_addr']['uri']
                        # Construct real play url (sometimes need to replace playwm with play)
                        # But typically the url_list in play_addr works
                        url_list = data['aweme_detail']['video']['play_addr']['url_list']
                        if url_list:
                            return url_list[-1] # Return the last one (usually highest quality or CDN)
                    except KeyError:
                         # Fallback to other structure
                         pass
            return None

        except Exception as e:
            print(f"Fetch video info failed: {e}")
            return None
