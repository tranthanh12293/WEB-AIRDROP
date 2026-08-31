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

# 1. API CHECK X SIÊU TỐC QUA SYNDICATION ENGINE
@app.post("/check-x")
def check_x(req: XRequest):
    username = req.username.strip().lstrip("@")
    if not username:
        return {"status": "NOTFOUND", "username": username, "detail": "Username trống"}

    proxies = parse_proxy_string(req.proxy) if req.proxy else None
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*"
    }

    try:
        # Tầng 1: Check qua Syndication API (Cực nhanh, lấy Follower & Tên)
        synd_url = f"https://cdn.syndication.twimg.com/widgets/followbutton/info.json?screen_names={username}"
        r = requests.get(synd_url, headers=headers, proxies=proxies, timeout=8)
        
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list) and len(data) > 0:
                user_info = data[0]
                name = user_info.get("name", username)
                followers = user_info.get("followers_count", 0)
                return {
                    "status": "LIVE",
                    "username": username,
                    "detail": f"Tên: {name} | Follow: {followers:,}"
                }

        # Tầng 2: Kiểm tra lý do DIE / SUSPENDED nếu không tìm thấy ở Tầng 1
        prof_url = f"https://syndication.twitter.com/srv/timeline-profile/screen-name/{username}"
        r2 = requests.get(prof_url, headers=headers, proxies=proxies, timeout=8)
        
        if r2.status_code == 404 or "User not found" in r2.text:
            return {"status": "NOTFOUND", "username": username, "detail": "Tài khoản không tồn tại"}
        if "account is suspended" in r2.text.lower() or "suspended" in r2.text.lower():
            return {"status": "SUSPENDED", "username": username, "detail": "Tài khoản bị đình chỉ (Suspended)"}
            
        return {"status": "NOTFOUND", "username": username, "detail": "Không tìm thấy user"}

    except Exception as e:
        return {"status": "FAILED", "username": username, "detail": f"Timeout/Lỗi mạng ({str(e)[:25]})"}

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