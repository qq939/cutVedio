# 加载环境变量（可选）
try:
    import dotenv
    dotenv.load_dotenv()
except ImportError:
    pass

# ========== 核心修复：兼容所有urllib3版本的编码方案 ==========
import os
import requests
import json
import time
import hmac
import hashlib
from urllib.parse import urlparse, urlencode, quote_plus
import base64

# ========== 核心配置（必须填真实值） ==========
VOLC_ACCESS_KEY = "你的真实AK"  # 替换根用户AK（纯ASCII字符）
VOLC_SECRET_KEY = "你的真实SK"  # 替换根用户SK（纯ASCII字符）
ENDPOINT = "https://visual.volcengineapi.com"

# ========== 火山引擎官方标准V4签名（无适配器依赖） ==========
def generate_official_authorization(ak, sk, method, url, headers, body):
    """火山引擎官方V4签名（确保Authorization头仅含ASCII字符）"""
    # 1. 解析URL
    parsed_url = urlparse(url)
    host = parsed_url.hostname
    path = parsed_url.path or "/"
    query = parsed_url.query

    # 2. 时间处理（官方格式）
    t = time.time()
    dt_utc = time.gmtime(t)
    amz_date = time.strftime("%Y%m%dT%H%M%SZ", dt_utc)
    date_str = time.strftime("%Y%m%d", dt_utc)

    # 3. 规范化请求头（仅ASCII字符）
    canonical_headers = {
        "content-type": headers.get("Content-Type", "").strip(),
        "host": host
    }
    sorted_headers = sorted(canonical_headers.items())
    canonical_header_str = "\n".join([f"{k}:{v}" for k, v in sorted_headers]) + "\n"
    signed_headers = ";".join([k for k, _ in sorted_headers])

    # 4. 规范化Query参数
    query_dict = {}
    if query:
        for kv in query.split("&"):
            if "=" in kv:
                k, v = kv.split("=", 1)
                query_dict[k] = v
    sorted_query = sorted(query_dict.items())
    canonical_query_str = "&".join([f"{quote_plus(k)}={quote_plus(v)}" for k, v in sorted_query])

    # 5. Body哈希
    body_bytes = body.encode("utf-8") if isinstance(body, str) else body
    payload_hash = hashlib.sha256(body_bytes).hexdigest()

    # 6. 规范化请求
    canonical_request = (
        f"{method.upper()}\n"
        f"{quote_plus(path)}\n"
        f"{canonical_query_str}\n"
        f"{canonical_header_str}\n"
        f"{signed_headers}\n"
        f"{payload_hash}"
    )

    # 7. 签名字符串
    credential_scope = f"{date_str}/cn-north-1/visual/volc_request"
    string_to_sign = (
        f"HMAC-SHA256\n"
        f"{amz_date}\n"
        f"{credential_scope}\n"
        f"{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"
    )

    # 8. 签名密钥（四级推导）
    def get_signing_key(key, date, region, service):
        k_date = hmac.new(("VOLC" + key).encode("utf-8"), date.encode("utf-8"), hashlib.sha256).digest()
        k_region = hmac.new(k_date, region.encode("utf-8"), hashlib.sha256).digest()
        k_service = hmac.new(k_region, service.encode("utf-8"), hashlib.sha256).digest()
        k_signing = hmac.new(k_service, b"volc_request", hashlib.sha256).digest()
        return k_signing

    signing_key = get_signing_key(sk, date_str, "cn-north-1", "visual")
    signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

    # 9. 构造Authorization头（核心：确保仅含ASCII字符）
    # 对AK进行URL编码，避免所有非ASCII字符
    ak_encoded = quote_plus(ak)
    authorization_header = (
        f"HMAC-SHA256 "
        f"Credential={ak_encoded}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, "
        f"Signature={signature}"
    )

    # 10. 返回请求头（所有值均为ASCII）
    headers["Authorization"] = authorization_header
    headers["X-Volc-Date"] = amz_date
    headers["X-Volc-Region"] = "cn-north-1"
    # 强制指定请求头编码为ASCII
    headers["Accept-Charset"] = "ASCII"
    return headers

# ========== 核心调用函数（无适配器，彻底解决编码问题） ==========
def create_jimeng_task(image_url: str, video_url: str):
    """无适配器依赖，确保所有请求头仅含ASCII字符"""
    # 1. 基础校验
    if not VOLC_ACCESS_KEY or not VOLC_SECRET_KEY:
        print("❌ 请填写真实AK/SK！", flush=True)
        return None
    if not (image_url.startswith("https://") and video_url.startswith("https://")):
        print("❌ URL必须是HTTPS！", flush=True)
        return None

    # 2. 构造参数（确保无中文，仅ASCII）
    query_params = {
        "Action": "ImageMotionMimic",
        "Version": "2024-01-01",
        "Region": "cn-north-1"
    }
    payload = {
        "ImageUrl": image_url,
        "VideoUrl": video_url,
        "Style": "Cartoon",
        "OutputFormat": "mp4",
        "Resolution": "720p"
    }
    # 生成JSON（确保输出为ASCII）
    payload_str = json.dumps(payload, separators=(',', ':'), ensure_ascii=True)

    # 3. 基础请求头（仅ASCII字符）
    headers = {
        "Content-Type": "application/json; charset=ASCII",  # 强制ASCII
        "Host": "visual.volcengineapi.com",
        "Accept": "application/json; charset=ASCII"
    }

    # 4. 拼接URL并生成签名
    query_str = urlencode(query_params, quote_via=quote_plus)
    final_url = f"{ENDPOINT}?{query_str}"
    headers = generate_official_authorization(
        ak=VOLC_ACCESS_KEY,
        sk=VOLC_SECRET_KEY,
        method="POST",
        url=final_url,
        headers=headers,
        body=payload_str
    )

    # 5. 发送请求（无自定义适配器，原生requests）
    try:
        print(f"✅ 发送官方请求：{final_url}", flush=True)
        
        # 原生requests发送，无适配器依赖
        response = requests.post(
            url=final_url,
            headers=headers,
            data=payload_str.encode("ASCII"),  # 强制ASCII编码
            timeout=60,
            verify=True
        )

        # 解析响应
        print(f"📝 状态码：{response.status_code}", flush=True)
        # 用UTF-8解码响应（兼容返回内容）
        response_text = response.content.decode("utf-8", errors="ignore")
        print(f"📝 响应：{response_text}", flush=True)

        resp_json = json.loads(response_text) if response_text else {}
        if response.status_code == 200 and ("Result" in resp_json or "data" in resp_json):
            # Check for TaskId in Result or data
            result_data = resp_json.get("Result") or resp_json.get("data")
            task_id = result_data.get("TaskId") or result_data.get("task_id")
            
            if task_id:
                print(f"\n🎉 成功！TaskId：{task_id}")
                return task_id
            else:
                print("\n❌ 无TaskId")
                return None
        else:
            error_msg = resp_json.get("ResponseMetadata", {}).get("Error", {}).get("Message", "未知错误")
            print(f"\n❌ 失败：{error_msg}")
            return None

    except Exception as e:
        print(f"\n❌ 异常：{str(e)}")
        import traceback
        print(f"❌ 详情：{traceback.format_exc()}")
        return None

def check_task_status(task_id):
    """
    Checks the status of a Jimeng task.
    Uses manual signing.
    """
    if not VOLC_ACCESS_KEY or not VOLC_SECRET_KEY:
        return 'FAILED', 'Missing API Key'

    query_params = {
        "Action": "GetVisualTask", # Assuming this is the correct action for polling
        "Version": "2024-01-01",
        "Region": "cn-north-1"
    }
    
    # Payload
    payload = {
        "TaskId": task_id
    }
    payload_str = json.dumps(payload, separators=(',', ':'), ensure_ascii=True)
    
    # Headers
    headers = {
        "Content-Type": "application/json; charset=ASCII",
        "Host": "visual.volcengineapi.com",
        "Accept": "application/json; charset=ASCII"
    }
    
    # Sign
    query_str = urlencode(query_params, quote_via=quote_plus)
    final_url = f"{ENDPOINT}?{query_str}"
    
    try:
        headers = generate_official_authorization(
            ak=VOLC_ACCESS_KEY,
            sk=VOLC_SECRET_KEY,
            method="POST",
            url=final_url,
            headers=headers,
            body=payload_str
        )
        
        response = requests.post(
            url=final_url,
            headers=headers,
            data=payload_str.encode("ASCII"),
            timeout=60,
            verify=True
        )
        
        response_text = response.content.decode("utf-8", errors="ignore")
        resp_json = json.loads(response_text) if response_text else {}
        
        if response.status_code == 200:
            # Structure might be data -> status
            data = resp_json.get("data") or resp_json.get("Result")
            if data:
                status = data.get("status") or data.get("Status")
                
                if status == "ProcessSuccess" or status == "SUCCEEDED":
                    res_data = data.get("resp_data") or data.get("ResultData")
                    if isinstance(res_data, str):
                        try:
                            res_data = json.loads(res_data)
                        except:
                            pass
                    
                    video_url = None
                    if isinstance(res_data, dict):
                        video_url = res_data.get("video_url") or res_data.get("VideoUrl")
                    
                    return 'SUCCEEDED', video_url
                elif status == "ProcessFail" or status == "FAILED":
                    return 'FAILED', data.get("fail_reason", "Unknown failure")
                else:
                    return 'RUNNING', None
            else:
                return 'UNKNOWN', str(resp_json)
        else:
            return 'UNKNOWN', str(resp_json)
            
    except Exception as e:
        print(f"Check status error: {e}")
        return 'UNKNOWN', str(e)
