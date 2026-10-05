import pytest
import sys
from pathlib import Path
from starlette.testclient import TestClient

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "sales_api"))

from sales_api.main import app
from sales_api.zalo import LOCAL_QR_PATH, get_zalo_status

@pytest.fixture
def client():
    return TestClient(app)

def test_zalo_status_endpoint(client):
    response = client.get("/api/zalo/status")
    assert response.status_code == 200
    data = response.json()
    assert "is_authenticated" in data
    assert "status" in data
    assert "login_in_progress" in data
    assert "qr_available" in data

def test_zalo_qr_info_endpoint(client):
    if LOCAL_QR_PATH.exists():
        response = client.get("/api/zalo/qr")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready_to_scan"
        assert "qr_base64" in data
        assert data["qr_base64"].startswith("data:image/png;base64,")
        assert data["qr_image_url"] == "/api/zalo/qr.png"

def test_zalo_qr_image_endpoint(client):
    if LOCAL_QR_PATH.exists():
        response = client.get("/api/zalo/qr.png")
        assert response.status_code == 200
        assert "image/png" in response.headers["content-type"]
        assert len(response.content) > 0
