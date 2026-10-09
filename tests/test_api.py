import pytest
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "sales_api"))

from catalog import search_products, get_product_details, get_policy_answer
from inventory import check_inventory, adjust_inventory
from leads import create_lead, get_all_leads
from handoffs import handoff_to_human, get_all_handoffs
from db import init_db, get_connection

@pytest.fixture(autouse=True)
def setup_db():
    init_db()

def test_search_products_budget():
    # Tìm gói phần mềm dưới 400.000đ
    res = search_products(query="áo dài", max_price_vnd=400000, limit=3)
    assert res["matched_count"] > 0
    assert len(res["products"]) <= 3
    for p in res["products"]:
        assert p["price_vnd"] <= 400000

def test_search_products_branches_filter():
    # Tìm gói hỗ trợ từ 3 chi nhánh trở lên
    res = search_products(min_branches=3, limit=5)
    assert res["matched_count"] >= 2
    for p in res["products"]:
        assert p["max_branches"] >= 3

def test_get_product_details():
    res = get_product_details("PKG-STARTER")
    assert res["found"] is True
    assert res["product"]["name"] == "Gói Starter"
    assert res["product"]["price_vnd"] == 189000

    not_found = get_product_details("UNKNOWN-999")
    assert not_found["found"] is False

def test_check_inventory():
    # PKG-STARTER luôn sẵn sàng (cloud active)
    stock = check_inventory("PKG-STARTER")
    assert stock["found"] is True
    assert stock["available"] is True
    assert stock["quantity"] > 0

def test_create_lead_requires_consent():
    # Khi không có consent -> Bắt buộc từ chối
    res_no_consent = create_lead(
        channel="telegram",
        phone="0912345678",
        consent_to_contact=False,
        name="Anh Nam"
    )
    assert res_no_consent["success"] is False
    assert res_no_consent["error"] == "CONSENT_REQUIRED"

def test_create_lead_success():
    # Khi có consent hợp lệ -> Lưu thành công vào DB
    res = create_lead(
        channel="telegram",
        phone="0987654321",
        consent_to_contact=True,
        name="Lâm Dev",
        product_skus=["PKG-PRO"],
        budget_vnd=28000000,
        needs_summary="Studio váy cưới 3 chi nhánh, cần in hợp đồng QR"
    )
    assert res["success"] is True
    assert "lead_id" in res

    # Kiểm tra DB
    leads = get_all_leads()
    found = any(l["phone"] == "0987654321" for l in leads)
    assert found is True

def test_handoff_to_human():
    res = handoff_to_human(
        conversation_id="telegram:test_user_123",
        reason="discount_request",
        priority="high",
        summary="Khách hỏi chiết khấu 15% khi thanh toán 2 năm Gói Pro",
        suggested_next_action="Quản lý liên hệ duyệt ưu đãi riêng"
    )
    assert res["success"] is True
    assert res["status"] == "handoff_created"
    assert res["ticket_id"].startswith("TICK-")

    # Kiểm tra trong DB
    tickets = get_all_handoffs()
    assert any(t["ticket_id"] == res["ticket_id"] for t in tickets)

def test_policy_lookup():
    res_warranty = get_policy_answer("bảo hành")
    assert res_warranty["found"] is True
    assert "bảo hành" in res_warranty["content"].lower()

    res_vat = get_policy_answer("hóa đơn vat")
    assert res_vat["found"] is True
    assert "vat" in res_vat["content"].lower()
