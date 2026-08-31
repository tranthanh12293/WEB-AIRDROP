from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import time
from typing import Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class XRequest(BaseModel):
    username: str
    proxy: Optional[str] = ""

class ProxyRequest(BaseModel):
    proxy: str

BEARER_TOKEN = "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"

def parse_proxy_string(raw_proxy: str):
    if not raw_proxy:
        return None
    clean = raw_proxy.strip().replace("http://", "").replace("https://", "").replace("socks5://", "")
    host, port, user, pwd = "", "80", "", ""
    if "@" in clean:
        auth, hp = clean.split("@")
        user, pwd = auth.split(":") if ":" in auth else (auth, "")
        host, port = hp.split(":") if ":" in hp else (hp, "80")
    else:
        parts = clean.split(":")
        if len(parts) >= 4:
            if parts[1].isdigit():
                host, port, user, pwd = parts[0], parts[1], parts[2], parts[3]
            else:
                user, pwd, host, port = parts[0], parts[1], parts[2], parts[3]
        elif len(parts) == 2:
            host, port = parts[0], parts[1]
        else:
            host = parts[0]
    
    if user and pwd:
        proxy_url = f"http://{user}:{pwd}@{host}:{port}"
    else:
        proxy_url = f"http://{host}:{port}"
    return {"http": proxy_url, "https": proxy_url}

@app.get("/")
def root():
    return {"status": "online", "message": "Backend Trần Thành 1202 is running"}

# 1. API CHECK X THEO CHUẨN PYTHON GRAPHQL
@app.post("/check-x")
def check_x(req: XRequest):
    username = req.username.strip().lstrip("@")
    if not username:
        return {"status": "NOTFOUND", "username": username, "detail": "Username trống"}

    proxies = parse_proxy_string(req.proxy) if req.proxy else None
    
    session = requests.Session()
    session.headers.update({
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "accept-language": "en-US,en;q=0.9"
    })

    guest_token = None

    # Bước 1: Kích hoạt Guest Token chính thức
    try:
        act_headers = {
            "authorization": BEARER_TOKEN,
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
        }
        r_act = session.post("https://api.twitter.com/1.1/guest/activate.json", headers=act_headers, proxies=proxies, timeout=7)
        if r_act.status_code == 200:
            guest_token = r_act.json().get("guest_token")
    except Exception:
        pass

    # Bước 2: Dự phòng lấy từ HTML nếu activate API bị rate limit
    if not guest_token:
        try:
            r_main = session.get("https://x.com/?lang=en", proxies=proxies, timeout=7)
            guest_token = r_main.cookies.get("gt")
            if not guest_token and 'document.cookie="gt=' in r_main.text:
                guest_token = r_main.text.split('document.cookie="gt=')[1].split('";')[0]
        except Exception:
            pass

    if not guest_token:
        return {"status": "FAILED", "username": username, "detail": "Không thể lấy Guest Token"}

    # Bước 3: Gọi GraphQL Endpoint
    q_url = "https://x.com/i/api/graphql/k5X_OmflwGekW9W0hucqCA/UserByScreenName"
    params = {
        "variables": f'{{"screen_name":"{username}"}}',
        "features": '{"hidden_profile_subscriptions_enabled":true,"profile_label_improvements_pcf_label_in_post_enabled":true,"rweb_tipjar_consumption_enabled":true,"responsive_web_graphql_exclude_directive_enabled":true,"verified_phone_label_enabled":false,"highlights_tweets_tab_ui_enabled":true,"responsive_web_twitter_article_notes_tab_enabled":true,"creator_subscriptions_tweet_preview_api_enabled":true,"responsive_web_graphql_skip_user_profile_image_extensions_enabled":false,"responsive_web_graphql_timeline_navigation_enabled":true}',
        "fieldToggles": '{"withAuxiliaryUserLabels":false}'
    }
    headers = {
        "authorization": BEARER_TOKEN,
        "x-guest-token": str(guest_token),
        "cookie": f"gt={guest_token};",
        "x-twitter-active-user": "yes"
    }

    try:
        res = session.get(q_url, headers=headers, params=params, proxies=proxies, timeout=9)
        
        if res.status_code == 404:
            return {"status": "NOTFOUND", "username": username, "detail": "Tài khoản không tồn tại"}
        if res.status_code == 429:
            return {"status": "FAILED", "username": username, "detail": "Rate Limit (Thử lại sau ít phút)"}
        if res.status_code != 200:
            return {"status": "FAILED", "username": username, "detail": f"HTTP {res.status_code}"}

        json_data = res.json()
        user_res = json_data.get("data", {}).get("user", {}).get("result", {})
        
        if not user_res:
            return {"status": "NOTFOUND", "username": username, "detail": "Không tìm thấy dữ liệu user"}

        # Phân loại trạng thái
        if user_res.get("reason") == "Suspended" or user_res.get("__typename") == "UserUnavailable":
            return {"status": "SUSPENDED", "username": username, "detail": "Tài khoản bị đình chỉ (Suspended)"}
        
        legacy = user_res.get("legacy", {})
        if legacy.get("profile_interstitial_type") == "fake_account":
            return {"status": "CAPTCHA", "username": username, "detail": "Tài khoản dính Captcha/Khóa tạm thời"}

        name = legacy.get("name", "N/A")
        followers = legacy.get("followers_count", 0)
        return {
            "status": "LIVE",
            "username": username,
            "detail": f"Tên: {name} | Follow: {followers:,}"
        }

    except Exception as e:
        return {"status": "FAILED", "username": username, "detail": str(e)[:35]}

# 2. API CHECK PROXY
@app.post("/check-proxy")
def check_proxy(req: ProxyRequest):
    raw_proxy = req.proxy.strip()
    if not raw_proxy:
        return {"status": "DIE", "ip_out": "--", "avg_ping": -1, "jitter": -1, "loss": 100}

    proxies = parse_proxy_string(raw_proxy)
    host = raw_proxy.split(":")[0].replace("http://", "").replace("https://", "")

    t0 = time.time()
    try:
        r = requests.get("http://ip-api.com/json/?fields=status,query", proxies=proxies, timeout=6)
        t_ping = int((time.time() - t0) * 1000)
        if r.status_code == 200 and r.json().get("status") == "success":
            out_ip = r.json().get("query", host)
            status = "FAST" if t_ping < 2000 else ("MEDIUM" if t_ping < 5000 else "LAG")
            return {
                "status": status,
                "proxy": raw_proxy,
                "ip_out": out_ip,
                "avg_ping": t_ping,
                "jitter": 6,
                "loss": 0
            }
    except Exception:
        pass

    return {
        "status": "DIE",
        "proxy": raw_proxy,
        "ip_out": host,
        "avg_ping": -1,
        "jitter": -1,
        "loss": 100
    }