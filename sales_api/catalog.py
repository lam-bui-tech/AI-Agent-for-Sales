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
        return []
    with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def search_products(
    query: Optional[str] = None,
    max_price_vnd: Optional[int] = None,
    min_ram_gb: Optional[int] = None,
    preferred_os: Optional[str] = None,
    limit: int = 3
) -> Dict[str, Any]:
    """
    Tìm danh mục sản phẩm theo tiêu chí ngân sách, RAM, hệ điều hành và nhu cầu sử dụng.
    """
    products = load_products()
    results = []
    
    query_terms = []
    if query:
        # Tách các từ khóa tìm kiếm (bỏ các từ nối thông dụng)
        cleaned = re.sub(r'[^\w\s]', ' ', query.lower())
        query_terms = [t for t in cleaned.split() if len(t) > 1 and t not in ["cần", "mua", "tìm", "cho", "máy", "laptop", "khoảng", "tầm", "có", "không"]]

    for p in products:
        # 1. Lọc giá trần
        if max_price_vnd is not None and p.get("price_vnd", 0) > max_price_vnd:
            continue
            
        # 2. Lọc RAM tối thiểu
        if min_ram_gb is not None and p.get("ram_gb", 0) < min_ram_gb:
            continue
            
        # 3. Lọc hệ điều hành
        if preferred_os:
            os_clean = preferred_os.strip().lower()
            product_os = p.get("os", "").lower()
            if os_clean == "mac" or os_clean == "macos" or os_clean == "apple":
                if "mac" not in product_os:
                    continue
            elif os_clean == "windows":
                if "windows" not in product_os:
                    continue
            elif os_clean == "linux" or os_clean == "ubuntu":
                if "linux" not in product_os and "ubuntu" not in product_os:
                    continue

        # 4. Tính điểm phù hợp theo query
        score = 0
        if query_terms:
            searchable_text = " ".join([
                p.get("name", ""),
                p.get("brand", ""),
                p.get("cpu", ""),
                p.get("gpu", ""),
                p.get("summary", ""),
                " ".join(p.get("use_cases", []))
            ]).lower()
            
            for term in query_terms:
                if term in searchable_text:
                    score += 1
            # Nếu có query mà không khớp từ khóa nào thì chỉ lấy nếu query rất ngắn
            if len(query_terms) >= 2 and score == 0:
                continue

        p_summary = {
            "sku": p["sku"],
            "name": p["name"],
            "brand": p["brand"],
            "price_vnd": p["price_vnd"],
            "cpu": p["cpu"],
            "ram_gb": p["ram_gb"],
            "storage_gb": p["storage_gb"],
            "gpu": p["gpu"],
            "screen": p["screen"],
            "weight_kg": p["weight_kg"],
            "os": p["os"],
            "use_cases": p.get("use_cases", []),
            "summary": p["summary"],
            "warranty_months": p.get("warranty_months", 12),
            "match_score": score
        }
        results.append(p_summary)

    # Sắp xếp theo match_score giảm dần, sau đó theo giá hợp lý
    results.sort(key=lambda x: (-x["match_score"], x["price_vnd"]))
    
    top_matches = results[:limit]
    
    # Loại bỏ match_score nội bộ trước khi trả ra client/agent
    for item in top_matches:
        item.pop("match_score", None)

    return {
        "products": top_matches,
        "matched_count": len(results),
        "total_catalog_count": len(products),
        "filter_applied": {
            "query": query,
            "max_price_vnd": max_price_vnd,
            "min_ram_gb": min_ram_gb,
            "preferred_os": preferred_os,
            "limit": limit
        }
    }

def get_product_details(sku: str) -> Dict[str, Any]:
    """
    Trả về thông số chi tiết đầy đủ của một SKU cụ thể.
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
        "message": f"Không tìm thấy sản phẩm có SKU '{sku}' trong danh mục.",
        "sku": sku
    }

def get_policy_answer(topic: str) -> Dict[str, Any]:
    """
    Tra cứu chính sách bảo hành, đổi trả, vận chuyển, xuất hóa đơn VAT, hoặc FAQ.
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
    
    # Tìm đoạn văn bản phù hợp nhất
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
