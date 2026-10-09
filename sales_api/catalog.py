import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

DATA_DIR = Path(__file__).parent.parent / "data"
PRODUCTS_FILE = DATA_DIR / "products.json"
POLICIES_FILE = DATA_DIR / "policies.md"
FAQ_FILE = DATA_DIR / "faq.md"

def load_products() -> List[Dict[str, Any]]:
    if not PRODUCTS_FILE.exists():
        # Fallback to root products.json if data/products.json not found
        root_file = Path(__file__).parent.parent / "products.json"
        if root_file.exists():
            with open(root_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return []
    with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def search_products(
    query: Optional[str] = None,
    max_price_vnd: Optional[int] = None,
    min_branches: Optional[int] = None,
    min_ram_gb: Optional[int] = None,
    preferred_os: Optional[str] = None,
    limit: int = 3
) -> Dict[str, Any]:
    """
    Tìm kiếm gói phần mềm ThueDo.net theo từ khóa nhu cầu, ngân sách và quy mô chi nhánh.
    """
    products = load_products()
    results = []
    
    query_terms = []
    if query:
        cleaned = re.sub(r'[^\w\s]', ' ', query.lower())
        query_terms = [t for t in cleaned.split() if len(t) > 1 and t not in ["cần", "tìm", "gói", "cho", "phần", "mềm", "shop", "khoảng", "có", "không"]]

    for p in products:
        # 1. Lọc giá trần
        if max_price_vnd is not None and p.get("price_vnd", 0) > max_price_vnd:
            continue
            
        # 2. Lọc số chi nhánh tối thiểu
        if min_branches is not None and p.get("max_branches", 1) < min_branches:
            continue

        # 3. Tính điểm phù hợp theo query
        score = 0
        if query_terms:
            searchable_text = " ".join([
                p.get("name", ""),
                p.get("sku", ""),
                p.get("audience", ""),
                p.get("summary", ""),
                " ".join(p.get("suitable_fashion", [])),
                " ".join(p.get("features", []))
            ]).lower()
            
            for term in query_terms:
                if term in searchable_text:
                    score += 1
            if len(query_terms) >= 2 and score == 0:
                continue

        p_summary = {
            "sku": p["sku"],
            "name": p["name"],
            "category": p.get("category", "software_package"),
            "price_vnd": p["price_vnd"],
            "billing_cycle": p.get("billing_cycle", "tháng"),
            "trial_days": p.get("trial_days", 15),
            "max_branches": p.get("max_branches", 1),
            "max_warehouses": p.get("max_warehouses", 1),
            "max_admin_accounts": p.get("max_admin_accounts", 1),
            "max_staff_accounts": p.get("max_staff_accounts", 3),
            "has_mobile_app": p.get("has_mobile_app", False),
            "has_e_invoice": p.get("has_e_invoice", False),
            "has_custom_contract_qr": p.get("has_custom_contract_qr", False),
            "suitable_fashion": p.get("suitable_fashion", []),
            "features": p.get("features", []),
            "summary": p.get("summary", ""),
            "match_score": score
        }
        results.append(p_summary)

    # Sắp xếp theo match_score giảm dần, ưu tiên gói phần mềm cốt lõi SaaS, sau đó theo giá
    results.sort(key=lambda x: (-x["match_score"], 0 if x.get("category") == "software_package" else 1, x["price_vnd"]))
    
    top_matches = results[:limit]
    for item in top_matches:
        item.pop("match_score", None)

    return {
        "products": top_matches,
        "matched_count": len(results),
        "total_catalog_count": len(products),
        "filter_applied": {
            "query": query,
            "max_price_vnd": max_price_vnd,
            "min_branches": min_branches,
            "limit": limit
        }
    }

def get_product_details(sku: str) -> Dict[str, Any]:
    """
    Trả về thông tin chi tiết đầy đủ của gói phần mềm theo mã SKU (ví dụ: PKG-STARTER, PKG-PRO, PKG-PREMIUM).
    """
    clean_sku = sku.strip().upper()
    products = load_products()
    for p in products:
        if p.get("sku", "").upper() == clean_sku:
            return {
                "found": True,
                "product": p
            }
    return {
        "found": False,
        "message": f"Không tìm thấy gói phần mềm có SKU '{sku}' trong danh mục.",
        "sku": sku
    }

def calculate_pricing(sku: str, months: int = 1) -> Dict[str, Any]:
    """
    Tính chính xác chi phí gói cước ThueDo.net theo chu kỳ thanh toán:
    - 3 tháng: Nguyên giá (0% chiết khấu)
    - 6 tháng: Giảm 5%
    - 12 tháng: Giảm 10%
    """
    details = get_product_details(sku)
    if not details.get("found"):
        return {
            "success": False,
            "error": f"Không tìm thấy gói phần mềm với mã SKU: {sku}"
        }

    p = details["product"]
    months = max(1, int(months))
    monthly_price = p["price_vnd"]
    original_total = monthly_price * months

    discount_percent = 0
    if months >= 12:
        discount_percent = 10
    elif months >= 6:
        discount_percent = 5
    elif months >= 3:
        discount_percent = 0

    discount_amount = int(original_total * (discount_percent / 100))
    final_total = original_total - discount_amount

    return {
        "success": True,
        "sku": p["sku"],
        "package_name": p["name"],
        "monthly_price_vnd": monthly_price,
        "months": months,
        "original_total_vnd": original_total,
        "discount_percent": discount_percent,
        "discount_amount_vnd": discount_amount,
        "final_total_vnd": final_total,
        "message": f"Chi phí gói {p['name']} cho {months} tháng: {final_total:,.0f}đ (Tiết kiệm {discount_amount:,.0f}đ nhờ ưu đãi {discount_percent}%)."
    }

def compare_packages(sku1: str, sku2: str) -> Dict[str, Any]:
    """
    So sánh chi tiết các tính năng và giới hạn giữa 2 gói phần mềm ThueDo.net:
    Trả về khác biệt về quy mô chi nhánh, hợp đồng QR, hóa đơn điện tử, mobile app
    kèm tóm tắt văn bản 2 dòng không dùng bảng kẻ cột Markdown.
    """
    p1_res = get_product_details(sku1)
    p2_res = get_product_details(sku2)
    if not p1_res.get("found"):
        return {"success": False, "error": f"Không tìm thấy gói phần mềm với mã: {sku1}"}
    if not p2_res.get("found"):
        return {"success": False, "error": f"Không tìm thấy gói phần mềm với mã: {sku2}"}
    
    p1 = p1_res["product"]
    p2 = p2_res["product"]

    def format_branches(val):
        return "Không giới hạn" if val >= 999 else f"{val} chi nhánh"

    differences = {
        "price_per_month": {
            "pkg1": f"{p1['price_vnd']:,}đ/tháng",
            "pkg2": f"{p2['price_vnd']:,}đ/tháng"
        },
        "branches": {
            "pkg1": format_branches(p1.get("max_branches", 1)),
            "pkg2": format_branches(p2.get("max_branches", 1))
        },
        "mobile_app": {
            "pkg1": "Không hỗ trợ" if not p1.get("has_mobile_app") else "iOS & Android",
            "pkg2": "Không hỗ trợ" if not p2.get("has_mobile_app") else "iOS & Android"
        },
        "e_invoice": {
            "pkg1": "Không tích hợp" if not p1.get("has_e_invoice") else "Tích hợp Viettel/VNPT/MISA",
            "pkg2": "Không tích hợp" if not p2.get("has_e_invoice") else "Tích hợp Viettel/VNPT/MISA"
        },
        "contract_qr": {
            "pkg1": "Mẫu mặc định" if not p1.get("has_custom_contract_qr") else "Tùy chỉnh có mã QR & watermark",
            "pkg2": "Mẫu mặc định" if not p2.get("has_custom_contract_qr") else "Tùy chỉnh có mã QR & watermark"
        }
    }

    quick_view_summary = (
        f"1. {p1['name']} ({p1['sku']}) — {p1['price_vnd']:,}đ/tháng\n"
        f"{p1.get('summary', '')}\n\n"
        f"2. {p2['name']} ({p2['sku']}) — {p2['price_vnd']:,}đ/tháng\n"
        f"{p2.get('summary', '')}"
    )

    return {
        "success": True,
        "pkg1": {"sku": p1["sku"], "name": p1["name"], "price_vnd": p1["price_vnd"]},
        "pkg2": {"sku": p2["sku"], "name": p2["name"], "price_vnd": p2["price_vnd"]},
        "differences": differences,
        "quick_view_summary": quick_view_summary
    }

def get_policy_answer(topic: str) -> Dict[str, Any]:
    """
    Tra cứu chính sách dịch vụ ThueDo.net: Dùng thử 15 ngày, hóa đơn điện tử, hợp đồng, hoàn tiền, hỗ trợ 24/7.
    """
    clean_topic = topic.strip().lower()
    
    policies_text = ""
    if POLICIES_FILE.exists():
        with open(POLICIES_FILE, "r", encoding="utf-8") as f:
            policies_text = f.read()
            
    faq_text = ""
    if FAQ_FILE.exists():
        with open(FAQ_FILE, "r", encoding="utf-8") as f:
            faq_text = f.read()

    combined_text = policies_text + "\n\n" + faq_text
    paragraphs = combined_text.split("## ")
    matched_sections = []
    
    terms = clean_topic.split()
    for p in paragraphs:
        p_clean = p.lower()
        if any(term in p_clean for term in terms if len(term) > 2):
            matched_sections.append("## " + p.strip())

    if matched_sections:
        return {
            "found": True,
            "topic": topic,
            "content": "\n\n".join(matched_sections[:2])
        }
        
    return {
        "found": False,
        "topic": topic,
        "message": f"Chưa có thông tin chính sách khớp cho chủ đề '{topic}'. Vui lòng handoff nhân viên tư vấn."
    }
