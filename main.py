from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
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

def parse_proxy_url(raw_proxy: str):
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
        return f"http://{user}:{pwd}@{host}:{port}"
    return f"http://{host}:{port}"

@app.get("/")
def root():
    return {"status": "online", "message": "Async Backend Trần Thành 1202 is running"}

# 1. API CHECK X ASYNC SIÊU MƯỢT (CHỐNG NGHẼN LUỒNG)
@app.post("/check-x")
async def check_x(req: XRequest):
    username = req.username.strip().lstrip("@")
    if not username:
        return {"status": "NOTFOUND", "username": username, "detail": "Username trống"}

    proxy_url = parse_proxy_url(req.proxy) if req.proxy else None
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*"
    }

    async with httpx.AsyncClient(proxy=proxy_url, timeout=7.0, follow_redirects=True) as client:
        # Tầng 1: vx API Gateway
        try:
            r1 = await client.get(f"https://api.vxtwitter.com/{username}", headers=headers)
            if r1.status_code == 200:
                d1 = r1.json()
                name = d1.get("user_name") or d1.get("name") or username
                followers = d1.get("user_followers") or d1.get("followers_count") or 0
                return {
                    "status": "LIVE",
                    "username": username,
                    "detail": f"Tên: {name} | Follow: {followers:,}"
                }
            elif r1.status_code == 404 and "suspend" in r1.text.lower():
                return {"status": "SUSPENDED", "username": username, "detail": "Tài khoản bị đình chỉ (Suspended)"}
        except Exception:
            pass

        # Tầng 2: fx API Gateway
        try:
            r2 = await client.get(f"https://api.fxtwitter.com/{username}", headers=headers)
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
                if "suspend" in r2.text.lower():
                    return {"status": "SUSPENDED", "username": username, "detail": "Tài khoản bị đình chỉ (Suspended)"}
                return {"status": "NOTFOUND", "username": username, "detail": "Tài khoản không tồn tại"}
        except Exception:
            pass

        # Tầng 3: Timeline Profile Fallback
        try:
            r3 = await client.get(f"https://syndication.twitter.com/srv/timeline-profile/screen-name/{username}", headers=headers)
            if "suspended" in r3.text.lower():
                return {"status": "SUSPENDED", "username": username, "detail": "Tài khoản bị đình chỉ (Suspended)"}
            if r3.status_code == 404 or "User not found" in r3.text:
                return {"status": "NOTFOUND", "username": username, "detail": "Tài khoản không tồn tại"}
            if r3.status_code == 200:
                return {"status": "LIVE", "username": username, "detail": "Đang hoạt động"}
        except Exception:
            pass

    return {"status": "NOTFOUND", "username": username, "detail": "Tài khoản không tồn tại hoặc bị xóa"}

# 2. API CHECK PROXY ASYNC
@app.post("/check-proxy")
async def check_proxy(req: ProxyRequest):
    raw_proxy = req.proxy.strip()
    if not raw_proxy:
        return {"status": "DIE", "ip_out": "--", "avg_ping": -1, "jitter": -1, "loss": 100}

    proxy_url = parse_proxy_url(raw_proxy)
    host = raw_proxy.split(":")[0].replace("http://", "").replace("https://", "")

    t0 = time.time()
    try:
        async with httpx.AsyncClient(proxy=proxy_url, timeout=5.0) as client:
            r = await client.get("http://ip-api.com/json/?fields=status,query")
            t_ping = int((time.time() - t0) * 1000)
            if r.status_code == 200 and r.json().get("status") == "success":
                out_ip = r.json().get("query", host)
                status = "FAST" if t_ping < 2000 else ("MEDIUM" if t_ping < 5000 else "LAG")
                return {
                    "status": status,
                    "proxy": raw_proxy,
                    "ip_out": out_ip,
                    "avg_ping": t_ping,
                    "jitter": 5,
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