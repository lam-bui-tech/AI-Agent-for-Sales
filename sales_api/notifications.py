import os
import json
import urllib.request
import urllib.error
import subprocess
import ssl
from typing import Optional
from pathlib import Path

# Đọc cấu hình từ .env nếu có
ENV_PATH = Path(__file__).parent.parent / ".env"
if ENV_PATH.exists():
    with open(ENV_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8632970997:AAG9eoTriWBdtUAQMGwSJ-sUD836CoZOtfU")
TELEGRAM_SALES_CHAT_ID = os.getenv("TELEGRAM_SALES_CHAT_ID", "8182952988")

def send_telegram_alert(message: str, chat_id: Optional[str] = None) -> bool:
    """
    Gửi thông báo thời gian thực về Telegram của quản lý Sales (@lam_1342).
    Hỗ trợ cả Chat ID số lẫn username qua OpenClaw CLI.
    """
    token = TELEGRAM_BOT_TOKEN
    target = chat_id or TELEGRAM_SALES_CHAT_ID or "@lam_1342"
    
    if not target:
        return False

    # Cách 1: Nếu target là ID số (hoặc nhóm âm -100...) -> dùng Bot API trực tiếp
    if target.replace("-", "").isdigit():
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": target,
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
