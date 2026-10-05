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
    needs_summary: Optional[str] = None
) -> Dict[str, Any]:
    """
    Lưu thông tin khách hàng tiềm năng (Lead) sau khi có sự đồng ý (Consent) rõ ràng.
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
        channel, channel_user_id, name, phone, product_skus, budget_vnd, needs_summary, consent_to_contact, status, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        channel,
        channel_user_id or "unknown",
        name or "Khách hàng",
        phone.strip(),
        skus_json,
        budget_vnd,
        needs_summary or "",
        1 if consent_to_contact else 0,
        "new",
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
        "product_skus": product_skus or [],
        "needs_summary": needs_summary,
        "status": "new",
        "message": f"Đã ghi nhận thông tin thành công (Mã Lead: #{lead_id}). Chuyên viên tư vấn DemoTech sẽ liên hệ hỗ trợ bạn sớm nhất."
    }
    
    # Gửi thông báo tức thì về Telegram Sales nếu có cấu hình
    try:
        alert_msg = (
            f"🔥 <b>CÓ LEAD MỚI TỪ BOT!</b>\n"
            f"👤 <b>Khách hàng:</b> {name or 'Khách hàng'}\n"
            f"📞 <b>Số điện thoại:</b> <code>{phone}</code>\n"
            f"💻 <b>Quan tâm:</b> {', '.join(product_skus or []) if product_skus else 'Chưa chọn máy cụ thể'}\n"
            f"💰 <b>Ngân sách:</b> {f'{budget_vnd:,}đ' if budget_vnd else 'Chưa rõ'}\n"
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
        "skus": product_skus
    }, result, success=True)
    
    return result

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
