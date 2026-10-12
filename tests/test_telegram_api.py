import pytest
import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "sales_api"))

from main import app
from notifications import (
    get_telegram_bot_info,
    send_telegram_alert,
    get_env_var
)

@pytest.fixture
def client():
    return TestClient(app)

def test_telegram_config():
    """Kiểm tra cấu hình Telegram Bot Token"""
    token = get_env_var("TELEGRAM_BOT_TOKEN")
    sales_chat_id = get_env_var("TELEGRAM_SALES_CHAT_ID")

    if token:
        assert ":" in token
    if sales_chat_id:
        assert len(sales_chat_id) > 0

def test_telegram_status_endpoint(client):
    """Kiểm tra endpoint GET /api/telegram/status"""
    response = client.get("/api/telegram/status")
    assert response.status_code == 200
    data = response.json()

    assert data.get("status") in ["connected", "error", "unreachable", "missing_token"]
    if data.get("status") == "connected":
        assert data.get("bot_id") is not None
        assert data.get("username") == "pmthuedo_bot"
        assert data.get("sales_chat_id") is not None
        assert "t.me/pmthuedo_bot" in data.get("bot_url", "")

    # Đảm bảo không làm lộ bí mật bot token nguyên bản trong response
    token = get_env_var("TELEGRAM_BOT_TOKEN")
    if token:
        assert token not in str(data)

def test_telegram_bot_info_mock():
    """Kiểm tra logic phân giải bot info qua mock"""
    fake_data = {
        "ok": True,
        "result": {
            "id": 1234567890,
            "first_name": "Phan Mem Thue Do",
            "username": "pmthuedo_bot"
        }
    }
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps(fake_data).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        info = get_telegram_bot_info()
        assert info["status"] == "connected"
        assert info["bot_id"] == 1234567890
        assert info["username"] == "pmthuedo_bot"
        assert info["bot_name"] == "Phan Mem Thue Do"

def test_send_telegram_alert_mock():
    """Kiểm tra hàm send_telegram_alert gửi tin nhắn thông báo"""
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        success = send_telegram_alert("Thông báo thử nghiệm đơn hàng mới")
        assert success is True
