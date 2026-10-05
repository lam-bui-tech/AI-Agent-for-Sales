import pytest
from fastapi.testclient import TestClient
from sales_api.main import app
from sales_api.handoffs import get_all_handoffs

client = TestClient(app)

def test_handoff_without_conversation_id_repro():
    """
    Test repro: OpenClaw calls handoff_to_human without conversation_id,
    passing only reason, summary, channel, contact (as per TOOLS.md).
    Before fix: Returns 422 Unprocessable Entity, fails to save ticket.
    After fix: Returns 200 OK, saves ticket to DB.
    """
    payload = {
        "reason": "warranty_check",
        "summary": "Khách Huynh Nguyễn (SĐT: 0342395067) muốn tra cứu bảo hành cho laptop đã mua trước đó. Cần nhân viên kiểm tra lịch sử đơn hàng và trạng thái bảo hành.",
        "channel": "zalouser",
        "contact": "0342395067"
    }

    response = client.post("/api/tools/handoff_to_human", json=payload)
    assert response.status_code == 200, f"Expected 200 but got {response.status_code}: {response.text}"
    data = response.json()
    assert data["success"] is True
    ticket_id = data["ticket_id"]

    # Verify it was saved to DB and appears in /admin/handoffs
    admin_resp = client.get("/admin/handoffs")
    assert admin_resp.status_code == 200
    handoffs = admin_resp.json()["handoffs"]
    assert any(h["ticket_id"] == ticket_id for h in handoffs)

def test_create_lead_with_consent_alias():
    payload = {
        "channel": "zalouser",
        "phone": "0342395067",
        "name": "Huynh Nguyễn",
        "consent": True
    }
    response = client.post("/api/tools/create_lead", json=payload)
    assert response.status_code == 200

