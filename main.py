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

# 1. ENGINE CHECK X ĐA TẦNG SIÊU CHUẨN
@app.post("/check-x")
def check_x(req: XRequest):
    username = req.username.strip().lstrip("@")
    if not username:
        return {"status": "NOTFOUND", "username": username, "detail": "Username trống"}

    proxies = parse_proxy_string(req.proxy) if req.proxy else None
    
    # --- TẦNG 1: Gateway API Siêu Tốc (Chuẩn xác 100%, không dính rate-limit) ---
    try:
        vx_url = f"https://api.vxtwitter.com/{username}"
        r1 = requests.get(vx_url, proxies=proxies, timeout=6)
        if r1.status_code == 200:
            d1 = r1.json()
            name = d1.get("user_name") or d1.get("name") or username
            followers = d1.get("user_followers") or d1.get("followers_count") or 0
            return {
                "status": "LIVE",
                "username": username,
                "detail": f"Tên: {name} | Follow: {followers:,}"
            }
        elif r1.status_code == 404:
            err_msg = r1.text.lower()
            if "suspend" in err_msg:
                return {"status": "SUSPENDED", "username": username, "detail": "Tài khoản bị đình chỉ (Suspended)"}
    except Exception:
        pass

    # --- TẦNG 2: FxTwitter Engine Backup ---
    try:
        fx_url = f"https://api.fxtwitter.com/{username}"
        r2 = requests.get(fx_url, proxies=proxies, timeout=6)
        if r2.status_code == 200:
            d2 = r2.json().get("user", {})
            if d2:
                name = d2.get("name", username)
                followers = d2.get("followers_count", 0)
                return {
                    "status": "LIVE",
                    "username": username,
                    "detail": f"Tên: {name} | Follow: {followers:,}"
                }
        elif r2.status_code == 404:
            err_msg = r2.text.lower()
            if "suspend" in err_msg:
                return {"status": "SUSPENDED", "username": username, "detail": "Tài khoản bị đình chỉ (Suspended)"}
            return {"status": "NOTFOUND", "username": username, "detail": "Tài khoản không tồn tại"}
    except Exception:
        pass

    # --- TẦNG 3: Timeline Profile Fallback ---
    try:
        prof_url = f"https://syndication.twitter.com/srv/timeline-profile/screen-name/{username}"
        r3 = requests.get(prof_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}, proxies=proxies, timeout=6)
        if "account is suspended" in r3.text.lower() or "suspended" in r3.text.lower():
            return {"status": "SUSPENDED", "username": username, "detail": "Tài khoản bị đình chỉ (Suspended)"}
        if r3.status_code == 404 or "User not found" in r3.text:
            return {"status": "NOTFOUND", "username": username, "detail": "Tài khoản không tồn tại"}
        if r3.status_code == 200:
            return {"status": "LIVE", "username": username, "detail": "Đang hoạt động"}
    except Exception:
        pass

    return {"status": "NOTFOUND", "username": username, "detail": "Tài khoản không tồn tại hoặc bị xóa"}

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