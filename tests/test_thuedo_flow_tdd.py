import pytest
from pathlib import Path

# =========================================================================
# SLICE 1: PROMPT & BEHAVIOR CONTRACT SEAM (THUEDO.NET)
# =========================================================================

def test_identity_is_tro_ly_shop_for_thuedo():
    """Kiểm tra IDENTITY.md định danh là 'Trợ lý Shop' của ThueDo.net (Dion)."""
    root_dir = Path(__file__).parent.parent
    identity_content = (root_dir / "IDENTITY.md").read_text(encoding="utf-8")
    
    assert "Trợ lý Shop" in identity_content
    assert "ThueDo.net" in identity_content or "thuedo.net" in identity_content.lower()

def test_soul_and_agents_enforce_15_days_free_trial():
    """Kiểm tra chính sách trải nghiệm là dùng thử miễn phí 15 ngày."""
    root_dir = Path(__file__).parent.parent
    soul_content = (root_dir / "SOUL.md").read_text(encoding="utf-8")
    agents_content = (root_dir / "AGENTS.md").read_text(encoding="utf-8")
    skill_content = (root_dir / "skills" / "sales-advisor" / "SKILL.md").read_text(encoding="utf-8")

    for content in [soul_content, agents_content, skill_content]:
        assert "15 ngày" in content or "15 ngày miễn phí" in content
        assert "dùng thử" in content.lower()

def test_qualification_matrix_asks_both_scale_and_fashion_type():
    """Kiểm tra ma trận phân loại nhu cầu hỏi cả quy mô chi nhánh và loại hình trang phục."""
    root_dir = Path(__file__).parent.parent
    agents_content = (root_dir / "AGENTS.md").read_text(encoding="utf-8")
    skill_content = (root_dir / "skills" / "sales-advisor" / "SKILL.md").read_text(encoding="utf-8")

    for content in [agents_content, skill_content]:
        assert "chi nhánh" in content.lower()
        # Nhắc đến ít nhất 2 loại trang phục tiêu biểu
        assert "áo dài" in content.lower() or "váy cưới" in content.lower() or "đồ diễn" in content.lower()

def test_specialized_handoff_triggers_documented():
    """Kiểm tra quy định handoff cho 3 tình huống kỹ thuật: migration, hardware setup, live demo."""
    root_dir = Path(__file__).parent.parent
    soul_content = (root_dir / "SOUL.md").read_text(encoding="utf-8")
    agents_content = (root_dir / "AGENTS.md").read_text(encoding="utf-8")

    for content in [soul_content, agents_content]:
        # Migration (KiotViet/Sapo/Excel)
        assert "chuyển dữ liệu" in content.lower() or "migration" in content.lower() or "kiotviet" in content.lower()
        # Hardware setup (máy in/mã vạch)
        assert "máy in" in content.lower() or "phần cứng" in content.lower()
        # Live demo (Meet/UltraViewer)
        assert "demo" in content.lower() or "ultraviewer" in content.lower() or "meet" in content.lower()

def test_ux_rules_strictly_prohibit_markdown_tables_and_enforce_quick_view():
    """Đảm bảo các quy chuẩn UX: Không sinh bảng, 2 dòng Compact Quick-View, chỉ bôi đen câu chốt."""
    root_dir = Path(__file__).parent.parent
    soul_content = (root_dir / "SOUL.md").read_text(encoding="utf-8")
    agents_content = (root_dir / "AGENTS.md").read_text(encoding="utf-8")
    skill_content = (root_dir / "skills" / "sales-advisor" / "SKILL.md").read_text(encoding="utf-8")

    for content in [soul_content, agents_content, skill_content]:
        assert "không dùng bảng" in content.lower() or "không sinh bảng" in content.lower() or "tuyệt đối không" in content.lower()
        assert "compact quick-view" in content.lower() or "2 dòng" in content.lower()

# =========================================================================
# SLICE 2: CATALOG & PRICING CALCULATION SEAM
# =========================================================================

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "sales_api"))
from catalog import search_products, get_product_details, calculate_pricing

def test_catalog_contains_thuedo_saas_packages():
    """Kiểm tra danh mục sản phẩm chứa 3 gói phần mềm SaaS ThueDo.net."""
    res = search_products()
    assert res["matched_count"] >= 3
    skus = [p["sku"] for p in res["products"]]
    assert "PKG-STARTER" in skus
    assert "PKG-PRO" in skus
    assert "PKG-PREMIUM" in skus

def test_get_product_details_starter_and_pro():
    """Kiểm tra chi tiết gói Starter (189k) và gói Pro (339k)."""
    starter = get_product_details("PKG-STARTER")
    assert starter["found"] is True
    assert starter["product"]["price_vnd"] == 189000
    assert starter["product"]["max_branches"] == 1

    pro = get_product_details("PKG-PRO")
    assert pro["found"] is True
    assert pro["product"]["price_vnd"] == 339000
    assert pro["product"]["max_branches"] == 3

def test_calculate_pricing_cycles_with_discounts():
    """Kiểm tra tính giá theo chu kỳ 3 tháng (0%), 6 tháng (5%), 12 tháng (10%)."""
    # Gói Starter 189.000đ/tháng
    calc_3m = calculate_pricing("PKG-STARTER", months=3)
    assert calc_3m["success"] is True
    assert calc_3m["original_total_vnd"] == 189000 * 3
    assert calc_3m["discount_percent"] == 0
    assert calc_3m["final_total_vnd"] == 189000 * 3

    calc_6m = calculate_pricing("PKG-STARTER", months=6)
    assert calc_6m["success"] is True
    assert calc_6m["discount_percent"] == 5
    expected_original = 189000 * 6
    expected_discount = int(expected_original * 0.05)
    assert calc_6m["final_total_vnd"] == expected_original - expected_discount

    calc_12m = calculate_pricing("PKG-PRO", months=12)
    assert calc_12m["success"] is True
    assert calc_12m["discount_percent"] == 10
    expected_pro_orig = 339000 * 12
    expected_pro_disc = int(expected_pro_orig * 0.10)
    assert calc_12m["final_total_vnd"] == expected_pro_orig - expected_pro_disc

def test_calculate_pricing_invalid_sku():
    """Kiểm tra calculate_pricing với SKU không tồn tại."""
    res = calculate_pricing("UNKNOWN-SKU", months=6)
    assert res["success"] is False
    assert "không tìm thấy" in res["error"].lower()

# =========================================================================
# SLICE 3: PACKAGE COMPARISON SEAM (compare_packages)
# =========================================================================

from catalog import compare_packages

def test_compare_packages_starter_vs_pro():
    """Kiểm tra so sánh giữa gói Starter và gói Pro."""
    res = compare_packages("PKG-STARTER", "PKG-PRO")
    assert res["success"] is True
    assert res["pkg1"]["sku"] == "PKG-STARTER"
    assert res["pkg2"]["sku"] == "PKG-PRO"
    
    # Kiểm tra chỉ ra các điểm khác biệt then chốt
    diffs = res["differences"]
    assert "branches" in diffs
    assert "mobile_app" in diffs
    assert "e_invoice" in diffs
    assert "contract_qr" in diffs
    
    # Đảm bảo có đoạn text tóm tắt 2 dòng không dùng bảng markdown
    summary_text = res["quick_view_summary"]
    assert "|" not in summary_text
    assert "PKG-STARTER" in summary_text
    assert "PKG-PRO" in summary_text

def test_compare_packages_pro_vs_premium():
    """Kiểm tra so sánh giữa gói Pro và gói Premium."""
    res = compare_packages("PKG-PRO", "PKG-PREMIUM")
    assert res["success"] is True
    diffs = res["differences"]
    assert diffs["branches"]["pkg2"] == "Không giới hạn" or diffs["branches"]["pkg2"] == 999

def test_compare_packages_invalid_sku():
    """Kiểm tra compare_packages báo lỗi khi truyền SKU không hợp lệ."""
    res = compare_packages("PKG-STARTER", "NON-EXISTENT")
    assert res["success"] is False
    assert "không tìm thấy" in res["error"].lower()

# =========================================================================
# SLICE 4: TRIAL REGISTRATION & B2B LEADS SEAM
# =========================================================================

from db import init_db
from leads import register_trial, create_lead, get_all_leads

@pytest.fixture(autouse=True)
def setup_db():
    init_db()

def test_register_trial_creates_lead_with_15_days():
    """Kiểm tra đăng ký dùng thử 15 ngày cho shop với đầy đủ thông tin nâng cao."""
    res = register_trial(
        shop_name="Áo Dài Nàng Thơ",
        fashion_type="Áo dài truyền thống & kỷ yếu",
        name="Chị Hương",
        phone="0987654321",
        branches_count=2,
        channel="telegram",
        preferred_contact_method="Zalo"
    )
    assert res["success"] is True
    assert res["trial_days"] == 15
    assert "Áo Dài Nàng Thơ" in res["message"]
    
    # Kiểm tra trong DB có lưu đúng thông tin
    leads = get_all_leads()
    found = any(l.get("shop_name") == "Áo Dài Nàng Thơ" and l["status"] == "trial_pending" for l in leads)
    assert found is True

def test_register_trial_validates_phone():
    """Kiểm tra register_trial từ chối số điện thoại không hợp lệ."""
    res = register_trial(
        shop_name="Studio Váy Cưới Paris",
        fashion_type="Váy cưới & vest",
        name="Anh Nam",
        phone="12345",  # Sai số
        channel="telegram"
    )
    assert res["success"] is False
    assert "INVALID_PHONE" in res["error"]

def test_create_lead_supports_b2b_fields():
    """Kiểm tra create_lead hỗ trợ thêm các trường B2B shop_name, fashion_type, branches_count."""
    res = create_lead(
        channel="telegram",
        phone="0912345678",
        consent_to_contact=True,
        name="Chị Mai",
        shop_name="Mai Wedding",
        fashion_type="Váy cưới",
        branches_count=1,
        product_skus=["PKG-PRO"],
        status="discount_pending"
    )
    assert res["success"] is True
    lead_id = res["lead_id"]
    
    leads = get_all_leads()
    lead = next(l for l in leads if l["id"] == lead_id)
    assert lead["shop_name"] == "Mai Wedding"
    assert lead["fashion_type"] == "Váy cưới"
    assert lead["branches_count"] == 1
    assert lead["status"] == "discount_pending"

# =========================================================================
# SLICE 5: SPECIALIZED HANDOFF TRIGGERS SEAM
# =========================================================================

from handoffs import handoff_to_human, get_all_handoffs, VALID_HANDOFF_REASONS

def test_handoff_reasons_contain_thuedo_specialized_triggers():
    """Kiểm tra danh sách lý do handoff có đủ 3 tình huống kỹ thuật và deal giá."""
    assert "migration" in VALID_HANDOFF_REASONS
    assert "hardware_setup" in VALID_HANDOFF_REASONS
    assert "live_demo" in VALID_HANDOFF_REASONS
    assert "discount_pending" in VALID_HANDOFF_REASONS or "discount_request" in VALID_HANDOFF_REASONS

def test_handoff_migration_ticket_creation():
    """Kiểm tra tạo handoff ticket khi khách yêu cầu chuyển dữ liệu từ KiotViet/Sapo."""
    res = handoff_to_human(
        conversation_id="conv-mig-123",
        reason="migration",
        summary="Shop Áo Dài Minh Châu có 2000 mẫu đồ trên KiotViet muốn chuyển sang ThueDo.net",
        preferred_contact_method="Zalo",
        priority="high"
    )
    assert res["success"] is True
    assert res["reason"] == "migration"
    assert res["priority"] == "high"
    assert "TICK-" in res["ticket_id"]

def test_handoff_hardware_setup_and_live_demo():
    """Kiểm tra tạo handoff ticket cho cài đặt máy in và hẹn demo 1-1."""
    hw_res = handoff_to_human(
        conversation_id="conv-hw-456",
        reason="hardware_setup",
        summary="Cần hỗ trợ kết nối máy in hóa đơn nhiệt Xprinter và máy quét mã vạch",
        preferred_contact_method="Gọi trực tiếp"
    )
    assert hw_res["success"] is True
    assert hw_res["reason"] == "hardware_setup"

    demo_res = handoff_to_human(
        conversation_id="conv-demo-789",
        reason="live_demo",
        summary="Chủ chuỗi váy cưới muốn demo tính năng lịch hẹn thử đồ qua Google Meet",
        preferred_contact_method="Zalo"
    )
    assert demo_res["success"] is True
    assert demo_res["reason"] == "live_demo"

# =========================================================================
# SLICE 6: FASTAPI ENDPOINT INTEGRATION SEAM
# =========================================================================

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_api_calculate_pricing_get_and_post():
    """Kiểm tra endpoint /calculate_pricing qua cả GET và POST."""
    # GET
    res_get = client.get("/calculate_pricing?sku=PKG-STARTER&months=6")
    assert res_get.status_code == 200
    data_get = res_get.json()
    assert data_get["success"] is True
    assert data_get["discount_percent"] == 5

    # POST
    res_post = client.post("/calculate_pricing", json={"sku": "PKG-PRO", "months": 12})
    assert res_post.status_code == 200
    data_post = res_post.json()
    assert data_post["success"] is True
    assert data_post["discount_percent"] == 10

def test_api_compare_packages_get_and_post():
    """Kiểm tra endpoint /compare_packages qua cả GET và POST."""
    # GET
    res_get = client.get("/compare_packages?sku1=PKG-STARTER&sku2=PKG-PRO")
    assert res_get.status_code == 200
    data_get = res_get.json()
    assert data_get["success"] is True
    assert "differences" in data_get
    assert "quick_view_summary" in data_get

    # POST
    res_post = client.post("/compare_packages", json={"sku1": "PKG-PRO", "sku2": "PKG-PREMIUM"})
    assert res_post.status_code == 200
    data_post = res_post.json()
    assert data_post["success"] is True

def test_api_register_trial_post():
    """Kiểm tra endpoint /register_trial kích hoạt dùng thử 15 ngày qua API."""
    payload = {
        "shop_name": "Studio Cưới Bella",
        "fashion_type": "Váy cưới & Dạ hội",
        "name": "Chị Linh",
        "phone": "0934567890",
        "branches_count": 2,
        "channel": "telegram",
        "preferred_contact_method": "Zalo"
    }
    res = client.post("/register_trial", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["trial_days"] == 15
    assert "Studio Cưới Bella" in data["message"]





