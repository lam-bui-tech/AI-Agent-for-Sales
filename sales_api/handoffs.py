import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
try:
    from .db import get_connection, log_audit
    from .notifications import send_telegram_alert
except (ImportError, ValueError):
    from db import get_connection, log_audit
    from notifications import send_telegram_alert

VALID_HANDOFF_REASONS = {
    "discount_pending": "Yêu cầu giảm giá / chiết khấu chờ quản lý duyệt",
    "discount_request": "Khách hàng yêu cầu giảm giá hoặc deal giá vượt quyền hạn của Agent",
    "migration": "Khách yêu cầu hỗ trợ chuyển dữ liệu cũ từ KiotViet/Sapo/Excel sang ThueDo.net",
    "hardware_setup": "Khách yêu cầu hỗ trợ kết nối thiết bị phần cứng (máy in hóa đơn/hợp đồng QR, máy quét mã vạch)",
    "live_demo": "Khách yêu cầu đặt lịch hẹn demo 1-1 trực tiếp qua Google Meet hoặc UltraViewer",
    "bulk_purchase": "Khách hàng chuỗi cửa hàng lớn cần gói giải pháp riêng",
    "invoice_request": "Khách hàng yêu cầu hỗ trợ hợp đồng và hóa đơn VAT đặc biệt",
    "complaint": "Khiếu nại về dịch vụ hoặc sự cố phần mềm cần kỹ thuật can thiệp",
    "product_not_found": "Không tìm thấy cấu hình hoặc gói cước phù hợp",
    "inventory_uncertain": "Trạng thái không chắc chắn hoặc hệ thống gặp sự cố tra cứu",
    "policy_exception": "Yêu cầu ngoại lệ về chính sách",
    "customer_requests_human": "Khách hàng chủ động yêu cầu nói chuyện trực tiếp với nhân viên",
    "agent_low_confidence": "Agent không đủ dữ liệu tin cậy để trả lời tiếp"
}

def handoff_to_human(
    conversation_id: str,
    reason: str,
    summary: str,
    priority: str = "medium",
    suggested_next_action: Optional[str] = None,
    preferred_contact_method: Optional[str] = None,
    status: str = "open"
) -> Dict[str, Any]:
    """
    Chuyển giao phiên tư vấn sang nhân viên kinh doanh / quản lý kèm tóm tắt ngữ cảnh.
    """
    clean_reason = reason.strip().lower()
    if clean_reason not in VALID_HANDOFF_REASONS:
        clean_reason = "customer_requests_human"

    clean_priority = priority.strip().lower()
    if clean_priority not in ["low", "medium", "high", "urgent"]:
        clean_priority = "medium"

    ticket_id = f"TICK-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    now_iso = datetime.now().isoformat()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO handoff_tickets (
        ticket_id, conversation_id, reason, priority, summary, suggested_next_action, preferred_contact_method, status, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        ticket_id,
        conversation_id,
        clean_reason,
        clean_priority,
        summary,
        suggested_next_action or "Nhân viên liên hệ và xử lý yêu cầu",
        preferred_contact_method,
        status or "open",
        now_iso
    ))
    conn.commit()
    conn.close()

    result = {
        "success": True,
        "ticket_id": ticket_id,
        "status": status if status != "open" else "handoff_created",
        "ticket_status": status or "open",
        "reason": clean_reason,
        "reason_description": VALID_HANDOFF_REASONS.get(clean_reason, ""),
        "priority": clean_priority,
        "summary": summary,
        "suggested_next_action": suggested_next_action,
        "preferred_contact_method": preferred_contact_method,
        "message": f"Yêu cầu đã được chuyển lên quản lý duyệt (Mã: {ticket_id}). Chuyên viên bên mình sẽ liên hệ hỗ trợ bạn sớm nhất ạ."
    }

    # Gửi thông báo tức thì về Telegram Sales nếu có cấu hình
    try:
        if clean_reason == "discount_request" or status == "discount_pending":
            alert_msg = (
                f"🏷️ <b>YÊU CẦU DEAL GIÁ (CHỜ DUYỆT - PENDING)</b>\n"
                f"🎫 <b>Mã yêu cầu:</b> <code>{ticket_id}</code>\n"
                f"💬 <b>Hội thoại:</b> {conversation_id}\n"
                f"📲 <b>Kênh liên hệ mong muốn:</b> {preferred_contact_method or 'Chưa rõ'}\n"
                f"📋 <b>Chi tiết yêu cầu & Liên hệ:</b>\n{summary}\n"
                f"👉 <b>Hành động tiếp theo:</b> {suggested_next_action or 'Quản lý xem xét duyệt giá và liên hệ lại'}"
            )
        else:
            alert_msg = (
                f"🚨 <b>YÊU CẦU CHUYỂN NHÂN VIÊN ({clean_priority.upper()})</b>\n"
                f"🎫 <b>Mã vé:</b> <code>{ticket_id}</code>\n"
                f"📌 <b>Lý do:</b> {VALID_HANDOFF_REASONS.get(clean_reason, clean_reason)}\n"
                f"💬 <b>Hội thoại:</b> {conversation_id}\n"
                f"📲 <b>Kênh liên hệ mong muốn:</b> {preferred_contact_method or 'Chưa rõ'}\n"
                f"📋 <b>Tóm tắt:</b> {summary}\n"
                f"👉 <b>Hành động tiếp theo:</b> {suggested_next_action or 'Chăm sóc khách hàng'}"
            )
        send_telegram_alert(alert_msg)
    except Exception as e:
        print(f"Error dispatching handoff alert: {e}")

    log_audit("handoff_to_human", {
        "conversation_id": conversation_id,
        "reason": clean_reason,
        "priority": clean_priority,
        "status": status,
        "preferred_contact_method": preferred_contact_method
    }, result, success=True)

    return result

def get_all_handoffs() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM handoff_tickets ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]
