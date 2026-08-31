from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import time
import socket

app = FastAPI()

# Mở CORS để website tranthanh1202.online gọi được API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class XRequest(BaseModel):
    username: str

class ProxyRequest(BaseModel):
    proxy: str

# 1. API CHECK X NGUYÊN BẢN PYTHON
@app.post("/check-x")
def check_x(req: XRequest):
    username = req.username.strip().lstrip("@")
    if not username:
        return {"status": "NOTFOUND", "username": username, "detail": "Username trống"}

    session = requests.Session()
    session.headers.update({
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "accept-language": "en-US,en;q=0.9"
    })

    try:
        # Lấy Guest Token
        r = session.get("https://x.com/", timeout=10)
        gt = r.cookies.get("gt")
        if not gt and 'document.cookie="gt=' in r.text:
            gt = r.text.split('document.cookie="gt=')[1].split('";')[0]

        if not gt:
            # Fallback lấy qua API
            bearer = "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"
            r_act = session.post("https://api.twitter.com/1.1/guest/activate.json", headers={"authorization": bearer}, timeout=10)
            if r_act.status_code == 200:
                gt = r_act.json().get("guest_token")

        if not gt:
            return {"status": "FAILED", "username": username, "detail": "Không lấy được Guest Token"}

        bearer = "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"
        q_url = f"https://x.com/i/api/graphql/k5X_OmflwGekW9W0hucqCA/UserByScreenName"
        params = {
            "variables": f'{{"screen_name":"{username}"}}',
            "features": '{"hidden_profile_subscriptions_enabled":true,"profile_label_improvements_pcf_label_in_post_enabled":true,"rweb_tipjar_consumption_enabled":true,"responsive_web_graphql_exclude_directive_enabled":true,"verified_phone_label_enabled":false,"highlights_tweets_tab_ui_enabled":true,"responsive_web_twitter_article_notes_tab_enabled":true,"creator_subscriptions_tweet_preview_api_enabled":true,"responsive_web_graphql_skip_user_profile_image_extensions_enabled":false,"responsive_web_graphql_timeline_navigation_enabled":true}',
            "fieldToggles": '{"withAuxiliaryUserLabels":false}'
        }
        headers = {
            "authorization": bearer,
            "x-guest-token": gt,
            "cookie": f"gt={gt};",
            "x-twitter-active-user": "yes"
        }
        res = session.get(q_url, headers=headers, params=params, timeout=10)
        
        if res.status_code == 404:
            return {"status": "NOTFOUND", "username": username, "detail": "Tài khoản không tồn tại"}
        if res.status_code != 200:
            return {"status": "FAILED", "username": username, "detail": f"HTTP {res.status_code}"}

        data = res.json().get("data", {}).get("user", {}).get("result", {})
        if not data:
            return {"status": "NOTFOUND", "username": username, "detail": "Không tìm thấy user"}

        if data.get("reason") == "Suspended" or data.get("__typename") == "UserUnavailable":
            return {"status": "SUSPENDED", "username": username, "detail": "Đã bị đình chỉ"}
        
        name = data.get("legacy", {}).get("name", "N/A")
        followers = data.get("legacy", {}).get("followers_count", 0)
        return {"status": "LIVE", "username": username, "detail": f"Tên: {name} | Follow: {followers}"}

    except Exception as e:
        return {"status": "FAILED", "username": username, "detail": str(e)[:40]}

# 2. API CHECK PROXY NGUYÊN BẢN PYTHON
@app.post("/check-proxy")
def check_proxy(req: ProxyRequest):
    raw_proxy = req.proxy.strip()
    if not raw_proxy:
        return {"status": "DIE", "ip_out": "--", "avg_ping": -1, "jitter": -1, "loss": 100}

    # Bóc tách định dạng host:port:user:pass hoặc user:pass@host:port
    clean = raw_proxy.replace("http://", "").replace("https://", "").replace("socks5://", "")
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

    # Format proxy cho requests
    if user and pwd:
        proxy_url = f"http://{user}:{pwd}@{host}:{port}"
    else:
        proxy_url = f"http://{host}:{port}"

    proxies = {"http": proxy_url, "https": proxy_url}
    
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
                "jitter": 8,
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