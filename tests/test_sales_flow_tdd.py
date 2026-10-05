import pytest
import sys
import re
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "sales_api"))

from db import init_db, get_connection
from catalog import search_products, get_product_details, get_policy_answer
from inventory import check_inventory
from leads import create_lead, get_all_leads, validate_phone
from handoffs import handoff_to_human, get_all_handoffs
from mcp_server import TOOLS_DEFINITIONS

@pytest.fixture(autouse=True)
def setup_db():
    init_db()

# =========================================================================
# 1. QUY TRÌNH TƯ VẤN SẢN PHẨM & ĐỊNH DẠNG (UX / FORMATTING RULES)
# =========================================================================

def test_prompt_rules_strictly_prohibit_markdown_tables():
    """Quy tắc SOUL.md và AGENTS.md phải cấm tuyệt đối sinh bảng markdown |---|---|."""
    root_dir = Path(__file__).parent.parent
    soul_content = (root_dir / "SOUL.md").read_text(encoding="utf-8")
    agents_content = (root_dir / "AGENTS.md").read_text(encoding="utf-8")
    skill_content = (root_dir / "skills" / "sales-advisor" / "SKILL.md").read_text(encoding="utf-8")

    # Kiểm tra cấm bảng
    assert "KHÔNG dùng bảng" in soul_content or "không dùng bảng" in soul_content.lower()
    assert "KHÔNG sinh bảng Markdown" in agents_content or "không dùng bảng" in agents_content.lower()
    assert "KHÔNG tạo bảng Markdown" in skill_content or "không dùng bảng" in skill_content.lower()

    # Kiểm tra quy chuẩn 2 dòng Compact Quick-View
    assert "Compact Quick-View" in soul_content
    assert "Compact Quick-View" in agents_content
    assert "Compact Quick-View" in skill_content

def test_prompt_rules_enforce_tone_and_closing_bold_only():
    """Kiểm tra quy định giọng nói không thảo mai ('sớm nhất ạ') và chỉ bôi đen câu hỏi chốt."""
    root_dir = Path(__file__).parent.parent
    soul_content = (root_dir / "SOUL.md").read_text(encoding="utf-8")
    agents_content = (root_dir / "AGENTS.md").read_text(encoding="utf-8")

    # Kiểm tra giọng điệu
    assert "sớm nhất ạ" in soul_content
    assert "sớm nhất ạ" in agents_content
    assert "thảo mai" in soul_content
    assert "nha!" in soul_content  # Cấm nha!

    # Kiểm tra quy tắc bôi đen
    assert "bôi đen" in soul_content.lower()
    assert "câu hỏi chốt" in soul_content.lower()
    assert "bôi đen" in agents_content.lower()

# =========================================================================
# 2. QUY TRÌNH XỬ LÝ DEAL GIÁ / GIẢM GIÁ (2-TURN DEAL QUALIFICATION)
# =========================================================================

def test_deal_turn_1_qualification_rules():
    """Lượt 1: Phải có quy định hỏi đủ 3 thông tin: Tên, SĐT, Kênh liên hệ mong muốn."""
    root_dir = Path(__file__).parent.parent
    soul_content = (root_dir / "SOUL.md").read_text(encoding="utf-8")
    agents_content = (root_dir / "AGENTS.md").read_text(encoding="utf-8")

    expected_kw = ["Tên", "Số điện thoại", "Zalo"]
    for kw in expected_kw:
        assert kw in soul_content
        assert kw in agents_content

def test_deal_turn_2_lead_creation_with_status_and_contact_method():
    """
    Lượt 2: Khi khách để lại thông tin deal giá, create_lead phải lưu được:
    - status = 'discount_pending' (thay vì 'new')
    - preferred_contact_method (Zalo/Telegram/Call)
    """
    res = create_lead(
        channel="telegram",
        phone="0918234567",
        consent_to_contact=True,
        name="Chị Hương",
        product_skus=["LAP-002"],
        budget_vnd=26000000,
        needs_summary="Khách xin giảm giá LAP-002 từ 27.99M xuống 26M",
        status="discount_pending",
        preferred_contact_method="Zalo"
    )
    assert res["success"] is True
    assert res.get("status") == "discount_pending"
    assert res.get("preferred_contact_method") == "Zalo"

    # Kiểm tra lưu trong DB
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT status, preferred_contact_method FROM leads WHERE id = ?", (res["lead_id"],))
    row = cursor.fetchone()
    conn.close()
    assert row is not None
    assert row["status"] == "discount_pending"
    assert row["preferred_contact_method"] == "Zalo"

def test_deal_turn_2_handoff_with_status_and_contact_method():
    """
    Handoff ticket khi deal giá phải hỗ trợ:
    - reason = 'discount_request'
    - status = 'discount_pending' (hoặc 'pending')
    - preferred_contact_method (Zalo/Telegram/Call)
    """
    res = handoff_to_human(
        conversation_id="telegram:5960520836",
        reason="discount_request",
        priority="high",
        summary="Khách Huỳnh Nguyễn (0983256720) xin giảm giá SwiftGo 14 AI còn 19.5M. Kênh: Zalo",
        suggested_next_action="Quản lý duyệt giá ưu đãi và phản hồi qua Zalo",
        status="discount_pending",
        preferred_contact_method="Zalo"
    )
    assert res["success"] is True
    assert res.get("status") == "discount_pending"
    assert res.get("preferred_contact_method") == "Zalo"

    # Kiểm tra lưu trong DB
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT status, preferred_contact_method FROM handoff_tickets WHERE ticket_id = ?", (res["ticket_id"],))
    row = cursor.fetchone()
    conn.close()
    assert row is not None
    assert row["status"] == "discount_pending"
    assert row["preferred_contact_method"] == "Zalo"

# =========================================================================
# 3. KIỂM TRA ĐỊNH DẠNG SỐ ĐIỆN THOẠI & CONSENT
# =========================================================================

def test_phone_validation_formats():
    """Kiểm tra hàm validate_phone với các dạng nhập liệu thực tế của khách hàng."""
    valid_numbers = [
        "0987654321",
        "+84987654321",
        "032 123 4567",
        "098-765-4321",
        "(098) 765 4321",
        "0868.123.456",
        "+84 912 345 678"
    ]
    for p in valid_numbers:
        assert validate_phone(p) is True, f"Failed on valid phone: {p}"

    invalid_numbers = [
        "12345",
        "098765432",        # 9 số
        "09876543210",       # 11 số (đầu 09)
        "01234567890",       # 11 số cũ
        "abcdefghij",
        "",
        "02838123456"        # Số bàn cố định TP.HCM (không phải di động)
    ]
    for p in invalid_numbers:
        assert validate_phone(p) is False, f"Failed on invalid phone: {p}"

def test_lead_rejection_without_consent():
    """Khách chưa đồng ý cung cấp SĐT -> Tuyệt đối không lưu lead."""
    res = create_lead(
        channel="telegram",
        phone="0987654321",
        consent_to_contact=False,
        name="Khách Hàng"
    )
    assert res["success"] is False
    assert res["error"] == "CONSENT_REQUIRED"

# =========================================================================
# 4. KIỂM TRA TỒN KHO & CHÍNH SÁCH BÁN HÀNG
# =========================================================================

def test_check_inventory_returns_location():
    """Kiểm tra thông tin tồn kho phải có số lượng và chi tiết kho hàng."""
    res = check_inventory("LAP-002")
    assert res["found"] is True
    assert res["available"] is True
    assert res["quantity"] > 0
    assert "warehouse" in res or "warehouses" in res

def test_policy_lookup_key_topics():
    """Kiểm tra đầy đủ các chính sách trọng yếu."""
    for topic in ["bảo hành", "đổi trả", "vận chuyển", "vat", "trả góp"]:
        res = get_policy_answer(topic)
        assert res["found"] is True, f"Policy for '{topic}' not found"
        assert len(res["content"]) > 10

# =========================================================================
# 5. KIỂM TRA KHỚP NỐI SCHEMA CỦA MCP SERVER & FASTAPI
# =========================================================================

def test_mcp_server_exposes_preferred_contact_method_and_status():
    """MCP Server định nghĩa tool create_lead và handoff_to_human phải có tham số preferred_contact_method và status."""
    tool_map = {t["name"]: t for t in TOOLS_DEFINITIONS}
    
    assert "create_lead" in tool_map
    lead_props = tool_map["create_lead"]["inputSchema"]["properties"]
    assert "preferred_contact_method" in lead_props, "create_lead missing preferred_contact_method in MCP schema"
    assert "status" in lead_props, "create_lead missing status in MCP schema"

    assert "handoff_to_human" in tool_map
    handoff_props = tool_map["handoff_to_human"]["inputSchema"]["properties"]
    assert "preferred_contact_method" in handoff_props, "handoff_to_human missing preferred_contact_method in MCP schema"
    assert "status" in handoff_props, "handoff_to_human missing status in MCP schema"
