import json
import re
from datetime import datetime
from typing import Dict, Any, List, Optional
try:
    from .db import get_connection, log_audit
    from .notifications import send_telegram_alert
except (ImportError, ValueError):
    from db import get_connection, log_audit
    from notifications import send_telegram_alert

def validate_phone(phone: str) -> bool:
    """Kiểm tra số điện thoại Việt Nam hợp lệ (10 số, bắt đầu bằng 03, 05, 07, 08, 09)"""
    cleaned = re.sub(r'[\s\.\-\(\)]', '', phone)
    pattern = r'^(0|\+84)(3|5|7|8|9)[0-9]{8}$'
    return bool(re.match(pattern, cleaned))

def create_lead(
    channel: str,
    phone: str,
    consent_to_contact: bool,
    name: Optional[str] = None,
    channel_user_id: Optional[str] = None,
    product_skus: Optional[List[str]] = None,
    budget_vnd: Optional[int] = None,
    needs_summary: Optional[str] = None,
    preferred_contact_method: Optional[str] = None,
    status: str = "new",
    shop_name: Optional[str] = None,
    fashion_type: Optional[str] = None,
    branches_count: Optional[int] = 1
) -> Dict[str, Any]:
    """
    Lưu thông tin khách hàng tiềm năng (Lead) sau khi có sự đồng ý (Consent) rõ ràng.
    Hỗ trợ các trường B2B nâng cao: shop_name, fashion_type, branches_count.
    """
    # 1. Bắt buộc kiểm tra Consent
    if not consent_to_contact:
        return {
            "success": False,
            "error": "CONSENT_REQUIRED",
            "message": "Không thể lưu thông tin liên hệ khi khách hàng chưa chủ động đồng ý nhận cuộc gọi tư vấn."
        }
        
    # 2. Kiểm tra số điện thoại
    if not phone or not validate_phone(phone):
        return {
            "success": False,
            "error": "INVALID_PHONE",
            "message": f"Số điện thoại '{phone}' không đúng định dạng liên hệ hợp lệ tại Việt Nam."
        }

    now_iso = datetime.now().isoformat()
    skus_json = json.dumps(product_skus or [], ensure_ascii=False)
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO leads (
        channel, channel_user_id, name, phone, product_skus, budget_vnd, needs_summary,
        preferred_contact_method, consent_to_contact, status, shop_name, fashion_type, branches_count, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        channel,
        channel_user_id or "unknown",
        name or "Khách hàng",
        phone.strip(),
        skus_json,
        budget_vnd,
        needs_summary or "",
        preferred_contact_method,
        1 if consent_to_contact else 0,
        status or "new",
        shop_name,
        fashion_type,
        branches_count or 1,
        now_iso
    ))
    lead_id = cursor.lastrowid
    conn.commit()
    conn.close()

    result = {
        "success": True,
        "lead_id": lead_id,
        "customer_name": name or "Khách hàng",
        "phone": phone,
        "shop_name": shop_name,
        "fashion_type": fashion_type,
        "branches_count": branches_count or 1,
        "product_skus": product_skus or [],
        "needs_summary": needs_summary,
        "preferred_contact_method": preferred_contact_method,
        "status": status or "new",
        "message": f"Đã ghi nhận thông tin thành công (Mã Lead: #{lead_id}). Chuyên viên tư vấn ThueDo.net sẽ liên hệ hỗ trợ bạn sớm nhất ạ."
    }
    
    # Gửi thông báo tức thì về Telegram Sales nếu có cấu hình
    try:
        if status == "trial_pending":
            alert_msg = (
                f"🎉 <b>CÓ ĐĂNG KÝ DÙNG THỬ 15 NGÀY THUEDO.NET!</b>\n"
                f"🏪 <b>Shop:</b> {shop_name or 'Chưa rõ'}\n"
                f"👗 <b>Mặt hàng:</b> {fashion_type or 'Cho thuê trang phục'}\n"
                f"📍 <b>Số chi nhánh:</b> {branches_count or 1}\n"
                f"👤 <b>Người liên hệ:</b> {name or 'Chủ shop'}\n"
                f"📞 <b>Số điện thoại:</b> <code>{phone}</code>\n"
                f"📲 <b>Kênh ưu tiên:</b> {preferred_contact_method or 'Zalo'}\n"
                f"📱 <b>Nguồn:</b> {channel}"
            )
        elif status == "discount_pending":
            alert_msg = (
                f"🏷️ <b>CÓ LEAD DEAL GIÁ (CHỜ DUYỆT - PENDING)!</b>\n"
                f"🏪 <b>Shop:</b> {shop_name or 'Chưa rõ'}\n"
                f"👤 <b>Người liên hệ:</b> {name or 'Khách hàng'}\n"
                f"📞 <b>Số điện thoại:</b> <code>{phone}</code>\n"
                f"📲 <b>Kênh liên hệ:</b> {preferred_contact_method or 'Gọi trực tiếp'}\n"
                f"📦 <b>Gói quan tâm:</b> {', '.join(product_skus or []) if product_skus else 'Chưa chọn'}\n"
                f"📝 <b>Yêu cầu:</b> {needs_summary or 'Xin giá ưu đãi'}\n"
                f"📱 <b>Nguồn:</b> {channel}"
            )
        else:
            alert_msg = (
                f"🔥 <b>CÓ LEAD MỚI TỪ BOT!</b>\n"
                f"🏪 <b>Shop:</b> {shop_name or 'Chưa rõ'}\n"
                f"👤 <b>Khách hàng:</b> {name or 'Khách hàng'}\n"
                f"📞 <b>Số điện thoại:</b> <code>{phone}</code>\n"
                f"📲 <b>Kênh:</b> {preferred_contact_method or 'Gọi trực tiếp'}\n"
                f"📦 <b>Gói:</b> {', '.join(product_skus or []) if product_skus else 'Tư vấn chung'}\n"
                f"📝 <b>Nhu cầu:</b> {needs_summary or 'Cần tư vấn'}\n"
                f"📱 <b>Kênh:</b> {channel}"
            )
        send_telegram_alert(alert_msg)
    except Exception as e:
        print(f"Error dispatching alert: {e}")

    log_audit("create_lead", {
        "channel": channel,
        "phone": phone,
        "consent": consent_to_contact,
        "skus": product_skus,
        "status": status,
        "shop_name": shop_name,
        "preferred_contact_method": preferred_contact_method
    }, result, success=True)
    
    return result

def register_trial(
    shop_name: str,
    fashion_type: str,
    name: str,
    phone: str,
    branches_count: int = 1,
    channel: str = "telegram",
    channel_user_id: Optional[str] = None,
    preferred_contact_method: str = "Zalo"
) -> Dict[str, Any]:
    """
    Tiếp nhận đăng ký dùng thử 15 ngày phần mềm ThueDo.net cho cửa hàng thời trang.
    """
    if not phone or not validate_phone(phone):
        return {
            "success": False,
            "error": "INVALID_PHONE",
            "message": f"Số điện thoại '{phone}' không đúng định dạng liên hệ hợp lệ tại Việt Nam."
        }

    res = create_lead(
        channel=channel,
        phone=phone,
        consent_to_contact=True,
        name=name,
        channel_user_id=channel_user_id,
        shop_name=shop_name,
        fashion_type=fashion_type,
        branches_count=branches_count,
        preferred_contact_method=preferred_contact_method,
        needs_summary=f"Đăng ký dùng thử 15 ngày ThueDo.net cho shop {shop_name} ({fashion_type}, {branches_count} chi nhánh).",
        status="trial_pending"
    )
    if res.get("success"):
        res["trial_days"] = 15
        res["message"] = f"Dạ mình đã ghi nhận đăng ký dùng thử 15 ngày cho shop {shop_name}. Chuyên viên ThueDo.net sẽ liên hệ qua {preferred_contact_method} để hỗ trợ kích hoạt tài khoản sớm nhất ạ."
    return res

def get_all_leads() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM leads ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    
    leads = []
    for r in rows:
        d = dict(r)
        if d.get("product_skus"):
            try:
                d["product_skus"] = json.loads(d["product_skus"])
            except:
                pass
        leads.append(d)
    return leads
