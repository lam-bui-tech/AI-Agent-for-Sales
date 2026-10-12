import os
import json
import urllib.request
import urllib.error
import subprocess
import ssl
from typing import Optional, Dict, Any
from pathlib import Path

def get_env_var(key: str, default: str = "") -> str:
    for p in [Path("/app/.env"), Path(__file__).parent.parent / ".env", Path(__file__).parent / ".env"]:
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith(f"{key}="):
                            val = line.split("=", 1)[1].strip()
                            if val:
                                return val
            except Exception:
                pass
    return os.getenv(key, default)

TELEGRAM_BOT_TOKEN = get_env_var("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_SALES_CHAT_ID = get_env_var("TELEGRAM_SALES_CHAT_ID", "")

def get_telegram_bot_info() -> Dict[str, Any]:
    """
    Kiểm tra trạng thái kết nối của Telegram Bot thông qua getMe API.
    Không làm lộ toàn bộ token trong response.
    """
    token = get_env_var("TELEGRAM_BOT_TOKEN", TELEGRAM_BOT_TOKEN)
    sales_chat_id = get_env_var("TELEGRAM_SALES_CHAT_ID", TELEGRAM_SALES_CHAT_ID)
    
    if not token:
        return {
            "status": "missing_token",
            "bot_id": None,
            "bot_name": None,
            "username": None,
            "sales_chat_id": sales_chat_id
        }

    url = f"https://api.telegram.org/bot{token}/getMe"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ThueDoBot/1.0"})
        ctx = ssl._create_unverified_context()
        with urllib.request.urlopen(req, timeout=8, context=ctx) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                if data.get("ok"):
                    res = data.get("result", {})
                    return {
                        "status": "connected",
                        "bot_id": res.get("id"),
                        "bot_name": res.get("first_name"),
                        "username": res.get("username"),
                        "sales_chat_id": sales_chat_id,
                        "bot_url": f"https://t.me/{res.get('username')}"
                    }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "sales_chat_id": sales_chat_id
        }

    return {
        "status": "unreachable",
        "sales_chat_id": sales_chat_id
    }

def send_telegram_alert(message: str, chat_id: Optional[str] = None) -> bool:
    """
    Gửi thông báo thời gian thực về Telegram của quản lý Sales (@lam_1342).
    Hỗ trợ cả Chat ID số lẫn username qua OpenClaw CLI.
    """
    token = get_env_var("TELEGRAM_BOT_TOKEN", TELEGRAM_BOT_TOKEN)
    target = chat_id or get_env_var("TELEGRAM_SALES_CHAT_ID", TELEGRAM_SALES_CHAT_ID) or "@lam_1342"
    
    if not target:
        return False

    # Cách 1: Nếu target là ID số (hoặc nhóm âm -100...) -> dùng Bot API trực tiếp
    if str(target).replace("-", "").isdigit():
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": str(target),
            "text": message,
            "parse_mode": "HTML"
        }
        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            ctx = ssl._create_unverified_context()
            with urllib.request.urlopen(req, timeout=5, context=ctx) as response:
                return response.status == 200
        except Exception as e:
            print(f"Telegram Bot API alert error: {e}")

    # Cách 2: Gửi thông qua OpenClaw CLI trong container (hỗ trợ resolve @username)
    try:
        cmd = [
            "docker", "exec", "openclaw-cont",
            "openclaw", "message", "send",
            "--channel", "telegram",
            "--target", str(target),
            "--message", message
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if proc.returncode == 0:
            return True
        else:
            print(f"OpenClaw message send warning: {proc.stderr.strip()}")
    except Exception as e:
        print(f"Subprocess alert dispatch error: {e}")

    return False
