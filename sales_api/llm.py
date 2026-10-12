import os
import re
import json
import time
from typing import Dict, Any, List, Optional
from pathlib import Path
import requests

try:
    from .db import log_audit, get_latest_log_id, get_audit_logs_after
    from .catalog import search_products, get_product_details, get_policy_answer, calculate_pricing, compare_packages
    from .inventory import check_inventory
    from .leads import register_trial, create_lead
    from .handoffs import handoff_to_human
except (ImportError, ValueError):
    from db import log_audit, get_latest_log_id, get_audit_logs_after
    from catalog import search_products, get_product_details, get_policy_answer, calculate_pricing, compare_packages
    from inventory import check_inventory
    from leads import register_trial, create_lead
    from handoffs import handoff_to_human

def get_config_var(key: str, default: str = "") -> str:
    # 1. Thử đọc từ /app/.env hoặc parent/.env hoặc local .env
    for p in [Path("/app/.env"), Path(__file__).parent.parent / ".env", Path(__file__).parent / ".env"]:
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith(f"{key}="):
                            val = line.split("=", 1)[1].strip()
                            if val:
                                return val
            except Exception:
                pass
    return os.getenv(key, default)

def get_dion_base_url() -> str:
    return get_config_var("DION_LLM_BASE_URL", "https://ai.dion.vn/api/v1").rstrip("/")

def get_dion_api_key() -> str:
    return get_config_var("DION_LLM_API_KEY", "")

def get_dion_model() -> str:
    return get_config_var("DION_LLM_MODEL", "balanced")

# Bộ nhớ hội thoại theo phiên (session memory)
SESSION_CONVERSATIONS: Dict[str, List[Dict[str, str]]] = {}
MAX_SESSION_HISTORY = 8

SYSTEM_PROMPT = """Bạn là Trợ lý Shop — AI Agent tư vấn bán hàng của ThueDo.net (Hệ sinh thái phần mềm quản lý cho thuê trang phục chuyên nghiệp: áo dài, váy cưới, đồ biểu diễn, dạ hội).

DANH MỤC GÓI PHẦN MỀM THUEDO.NET:
- Gói Starter (189.000đ/tháng): 1 chi nhánh, 1 kho, 1 Admin + 3 NV, quản lý thuê - cọc - trả cơ bản, mẫu hợp đồng cơ bản, hỗ trợ giờ hành chính. Phù hợp cửa hàng nhỏ khởi nghiệp.
- Gói Pro (339.000đ/tháng): Tối đa 3 chi nhánh, 3 kho, 1 Admin + 5 NV, in hợp đồng mã QR tùy chỉnh, xuất HĐĐT (Viettel/VNPT/Misa), Mobile App iOS/Android, hỗ trợ 24/7. Phù hợp studio áo cưới, tiệm áo dài phát triển.
- Gói Premium (489.000đ/tháng): Không giới hạn chi nhánh và kho, không giới hạn nhân viên, mẫu hợp đồng cao cấp, hotline riêng 5 phút, miễn phí 100% chuyển dữ liệu. Phù hợp chuỗi cửa hàng lớn.

CHÍNH SÁCH THANH TOÁN & ƯU ĐÃI:
- Thanh toán 3 tháng: nguyên giá.
- Thanh toán 6 tháng: giảm 5%.
- Thanh toán 12 tháng: giảm 10%.
- DÙNG THỬ MIỄN PHÍ: Tặng 15 ngày dùng thử miễn phí đầy đủ tính năng cho mọi gói, không cần thanh toán trước.

THIẾT BỊ PHẦN CỨNG BÁN KÈM:
- DEV-PRINTER-QR: Máy in nhiệt hóa đơn & hợp đồng mã QR Xprinter K80 (1.850.000đ), khổ 80mm, cổng USB/LAN.
- DEV-SCANNER-2D: Máy quét mã vạch 2D / QR không dây (1.250.000đ), kết nối 50m, quét mã trên vải/điện thoại.
- DEV-POS-TOUCH: Máy POS bán hàng cảm ứng 15.6 inch (6.900.000đ).
- DEV-CASH-DRAWER: Ngăn kéo đựng tiền thu ngân tự động (850.000đ).

HỖ TRỢ CHUYỂN ĐỔI DỮ LIỆU:
- Miễn phí 100% chuyển dữ liệu tồn kho, danh mục, khách hàng từ KiotViet, Sapo, Pos365 hoặc Excel sang ThueDo.net.

QUY TẮC BẮT BUỘC KHI PHẢN HỒI:
1. Trình bày danh sách gói cước theo định dạng So sánh nhanh 2 dòng (Compact Quick-View), cách nhau 1 dòng trống. TUYỆT ĐỐI KHÔNG DÙNG BẢNG KẺ CỘT Markdown (|---|---|) vì gây vỡ giao diện trên điện thoại.
2. Bôi đen (**) DUY NHẤT câu hỏi chốt nhu cầu hoặc câu gợi mở ở cuối tin nhắn. Không bôi đen tràn lan giữa bài.
3. Luôn chủ động mời khách kích hoạt gói Dùng thử miễn phí 15 ngày để trải nghiệm app và web.
4. Tông giọng nhã nhặn, chuyên nghiệp, xưng "mình" - "bạn", kết thúc bằng "ạ" hoặc "sớm nhất ạ" (tránh dùng "nha!", không cợt nhả).
5. Xử lý deal giá / xin chiết khấu riêng:
   - Lượt 1: Báo chuyển lên quản lý xin ưu đãi riêng, xin Tên, Số điện thoại và Kênh liên hệ mong muốn (Gọi trực tiếp hay nhắn Zalo/Telegram).
   - Lượt 2: Khi khách để lại SĐT, cảm ơn và xác nhận yêu cầu đang được quản lý duyệt.
6. Nếu khách hỏi quy mô chưa rõ, hỏi ngắn gọn câu Qualification Matrix:
   **"Shop mình hiện có mấy chi nhánh và đang kinh doanh dòng trang phục nào (như áo dài, váy cưới hay đồ biểu diễn) để mình tư vấn gói phù hợp nhất cho bạn ạ?"**
"""

def call_dion_chat_completions(messages: List[Dict[str, Any]], max_tokens: int = 800, timeout: int = 40) -> Optional[str]:
    """
    Gọi trực tiếp API Dion AI (POST https://ai.dion.vn/api/v1/chat/completions)
    với Model alias 'balanced' sử dụng Bearer API Key bí mật.
    """
    api_key = get_dion_api_key()
    base_url = get_dion_base_url()
    model = get_dion_model()

    if not api_key:
        print("[Dion LLM] Warning: DION_LLM_API_KEY is not configured", flush=True)
        return None

    endpoint = f"{base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens
    }

    try:
        t0 = time.time()
        resp = requests.post(endpoint, headers=headers, json=payload, timeout=timeout)
        duration_ms = (time.time() - t0) * 1000

        if resp.status_code == 200:
            data = resp.json()
            choices = data.get("choices", [])
            if choices and "message" in choices[0]:
                content = choices[0]["message"].get("content", "").strip()
                print(f"[Dion LLM] Success in {duration_ms:.0f}ms (model: {data.get('model', model)})", flush=True)
                return content
        else:
            print(f"[Dion LLM] API returned HTTP {resp.status_code}: {resp.text}", flush=True)
    except Exception as e:
        print(f"[Dion LLM] Request exception: {e}", flush=True)

    return None

def execute_intent_tools(user_message: str, session_id: str, channel: str = "web") -> List[Dict[str, Any]]:
    """
    Phân tích từ khóa nghiệp vụ để chủ động gọi tool backend tương ứng,
    ghi lại audit log và phục vụ dữ liệu cho phiên chat.
    """
    lower_msg = user_message.lower()
    recent_tools = []

    # 1. Khách để lại SĐT hoặc đăng ký dùng thử 15 ngày
    phone_match = re.search(r"0[35789]\d{8}", user_message)
    if phone_match or "dùng thử" in lower_msg or "đăng ký" in lower_msg:
        if phone_match:
            phone = phone_match.group(0)
            res = register_trial(
                shop_name="Shop Thời Trang",
                fashion_type="áo dài / váy cưới",
                name="Chủ shop",
                phone=phone,
                branches_count=1,
                channel=channel,
                channel_user_id=session_id
            )
            log_audit("register_trial", {"phone": phone, "channel": channel}, res, duration_ms=10, success=res.get("success", True))

    # 2. Khách xin giảm giá / chiết khấu
    if any(k in lower_msg for k in ["giảm giá", "chiết khấu", "bớt", "ưu đãi riêng", "mặc cả"]):
        res = handoff_to_human(
            conversation_id=session_id,
            reason="discount_request",
            summary=f"Khách hỏi chiết khấu/giảm giá: {user_message}",
            priority="high",
            suggested_next_action="Quản lý duyệt chính sách ưu đãi riêng cho shop",
            preferred_contact_method=channel,
            status="discount_pending"
        )
        log_audit("handoff_to_human", {"reason": "discount_request"}, res, duration_ms=10, success=True)

    # 3. Khách hỏi chuyển dữ liệu
    elif any(k in lower_msg for k in ["chuyển dữ liệu", "kiotviet", "sapo", "pos365", "excel"]):
        res = handoff_to_human(
            conversation_id=session_id,
            reason="migration",
            summary=f"Khách yêu cầu chuyển đổi dữ liệu từ hệ thống cũ: {user_message}",
            priority="high",
            suggested_next_action="Kỹ thuật hỗ trợ import dữ liệu tồn kho miễn phí",
            preferred_contact_method=channel,
            status="open"
        )
        log_audit("handoff_to_human", {"reason": "migration"}, res, duration_ms=10, success=True)

    # 4. Khách hỏi phần cứng máy in / máy quét
    elif "máy in" in lower_msg or "dev-printer" in lower_msg:
        res = check_inventory("DEV-PRINTER-QR")
        log_audit("check_inventory", {"sku": "DEV-PRINTER-QR"}, res, duration_ms=10, success=res.get("found", True))
    elif "máy quét" in lower_msg or "dev-scanner" in lower_msg:
        res = check_inventory("DEV-SCANNER-2D")
        log_audit("check_inventory", {"sku": "DEV-SCANNER-2D"}, res, duration_ms=10, success=res.get("found", True))

    # 5. Khách hỏi so sánh
    elif "so sánh" in lower_msg or ("starter" in lower_msg and "pro" in lower_msg):
        res = compare_packages("PKG-STARTER", "PKG-PRO")
        log_audit("compare_packages", {"sku1": "PKG-STARTER", "sku2": "PKG-PRO"}, res, duration_ms=10, success=res.get("success", True))

    # 6. Khách hỏi giá / gói
    elif any(k in lower_msg for k in ["giá", "gói", "chi phí", "bao nhiêu", "starter", "pro", "premium"]):
        res = search_products(query=user_message, limit=3)
        log_audit("search_products", {"query": user_message}, res, duration_ms=10, success=True)

    return recent_tools

def generate_sales_reply(user_message: str, session_id: str = "default", channel: str = "web") -> Dict[str, Any]:
    """
    Sinh câu trả lời tư vấn bán hàng hoàn chỉnh cho Trợ lý Shop ThueDo.net:
    1. Chủ động thực thi tool backend tương ứng.
    2. Gọi Dion LLM API với Session History và Domain System Prompt.
    3. Nếu LLM phản hồi chậm hoặc lỗi, áp dụng bộ phản hồi dự phòng chuẩn quy tắc SOUL/AGENTS.
    """
    start_log_id = get_latest_log_id()

    # 1. Kích hoạt tool backend theo intent
    execute_intent_tools(user_message, session_id, channel)

    # 2. Quản lý lịch sử hội thoại session
    if session_id not in SESSION_CONVERSATIONS:
        SESSION_CONVERSATIONS[session_id] = []
    
    history = SESSION_CONVERSATIONS[session_id]
    history.append({"role": "user", "content": user_message})

    # Giới hạn số lượt lịch sử
    if len(history) > MAX_SESSION_HISTORY * 2:
        history = history[-(MAX_SESSION_HISTORY * 2):]
        SESSION_CONVERSATIONS[session_id] = history

    messages_payload = [{"role": "system", "content": SYSTEM_PROMPT}] + history

    # 3. Gọi trực tiếp Dion LLM API
    llm_reply = call_dion_chat_completions(messages_payload, max_tokens=850, timeout=35)

    source = "dion-llm"
    reply_text = llm_reply

    # 4. Fallback Rule-based nếu mạng/API gặp sự cố
    if not reply_text:
        source = "simulation-engine"
        lower_msg = user_message.lower()

        if "bớt" in lower_msg or "giảm giá" in lower_msg or "chiết khấu" in lower_msg or "mặc cả" in lower_msg or "ưu đãi riêng" in lower_msg:
            reply_text = "Dạ với mức chiết khấu này, mình xin phép chuyển thông tin lên quản lý để xin chính sách ưu đãi riêng cho shop bạn. Bạn cho mình xin Tên, Số điện thoại và bạn muốn bên mình liên hệ hỗ trợ lại qua đâu (Gọi trực tiếp hay nhắn qua Zalo/Telegram) để bên mình báo lại sớm nhất ạ."
        elif "máy in" in lower_msg or "dev-printer" in lower_msg or "in hợp đồng" in lower_msg or "in hóa đơn" in lower_msg:
            reply_text = "Dạ bên mình có sẵn thiết bị chuyên dụng cho shop thời trang:\n\n**Máy in nhiệt hóa đơn & hợp đồng mã QR Xprinter K80 (DEV-PRINTER-QR)** — Giá: 1.850.000đ (Sẵn hàng, bảo hành chính hãng 12 tháng).\nMáy in sắc nét khổ 80mm, in tức thì hợp đồng có mã QR để khách quét xác nhận cọc - trả đồ, hỗ trợ kết nối USB và mạng LAN in trực tiếp từ điện thoại hoặc máy tính.\n\n**Shop mình cần tích hợp máy in cho mấy chi nhánh để mình hỗ trợ kỹ thuật cài đặt từ xa luôn ạ?**"
        elif "máy quét" in lower_msg or "quét mã" in lower_msg or "barcode" in lower_msg:
            reply_text = "Dạ bên mình có sẵn **Máy quét mã vạch 2D / QR không dây (DEV-SCANNER-2D)** — Giá: 1.250.000đ.\nThiết bị kết nối không dây Bluetooth/Wireless 50m, quét cực nhạy mã QR trên mác vải trang phục và màn hình điện thoại giúp kiểm kho và trả đồ siêu nhanh.\n\n**Bạn có muốn bên mình gửi trọn bộ thiết bị kèm gói dùng thử 15 ngày phần mềm không ạ?**"
        elif "chuyển dữ liệu" in lower_msg or "kiotviet" in lower_msg or "sapo" in lower_msg or "excel" in lower_msg:
            reply_text = "Dạ ThueDo.net hỗ trợ miễn phí 100% việc chuyển đổi dữ liệu sản phẩm, khách hàng và lịch sử từ KiotViet, Sapo hoặc file Excel sang hệ thống mới mà không làm gián đoạn việc kinh doanh của shop.\n\n**Bạn cho mình xin số điện thoại để chuyên viên kỹ thuật kết nối hỗ trợ import dữ liệu mẫu cho shop bạn nhé ạ?**"
        elif "09" in user_message or "03" in user_message or "08" in user_message or "07" in user_message:
            phone_match = re.search(r"0[35789]\d{8}", user_message)
            phone = phone_match.group(0) if phone_match else "số điện thoại bạn vừa gửi"
            reply_text = f"Dạ mình đã kích hoạt thành công yêu cầu dùng thử miễn phí 15 ngày cho bạn (SĐT: {phone}) trên hệ thống ThueDo.net rồi ạ.\n\nChuyên viên tư vấn sẽ liên hệ lại sớm nhất để gửi tài khoản quản trị và hướng dẫn bạn thiết lập cửa hàng nhé ạ."
        elif "so sánh" in lower_msg or ("starter" in lower_msg and "pro" in lower_msg):
            reply_text = "Dạ mình gửi bạn bảng so sánh nhanh giữa 2 gói:\n\n- Gói Starter (189.000đ/tháng): 1 chi nhánh, 1 kho, 1 Admin + 3 NV, mẫu hợp đồng cơ bản, hỗ trợ giờ hành chính.\n\n- Gói Pro (339.000đ/tháng): 3 chi nhánh, 3 kho, 1 Admin + 5 NV, in hợp đồng có mã QR tùy chỉnh, xuất HĐĐT (Viettel/VNPT/Misa), Mobile App iOS/Android, hỗ trợ 24/7.\n\n**Shop mình hiện tại đã có mấy chi nhánh và có cần in hợp đồng mã QR để khách quét ký nhận không ạ?**"
        elif "báo giá" in lower_msg or "chi phí" in lower_msg or "bao nhiêu tiền" in lower_msg or "giá gói" in lower_msg or "pro" in lower_msg or "starter" in lower_msg or "premium" in lower_msg:
            reply_text = "Dạ ThueDo.net cung cấp 3 gói cước linh hoạt theo quy mô cửa hàng:\n\n- Gói Starter (189.000đ/tháng): Phù hợp shop nhỏ khởi nghiệp 1 chi nhánh, quản lý thuê - cọc - trả cơ bản.\n\n- Gói Pro (339.000đ/tháng): Dành cho cửa hàng/studio 1-3 chi nhánh, có in hợp đồng QR, Mobile App và xuất HĐĐT.\n\n- Gói Premium (489.000đ/tháng): Không giới hạn chi nhánh và kho, hỗ trợ hotline riêng 5 phút và miễn phí chuyển dữ liệu.\n\n*(Tất cả các gói đều được tặng 15 ngày dùng thử miễn phí và giảm 5% khi thanh toán 6 tháng, 10% khi thanh toán 12 tháng)*.\n\n**Shop mình hiện có mấy chi nhánh và đang kinh doanh dòng trang phục nào (như áo dài, váy cưới hay đồ biểu diễn) để mình tư vấn gói phù hợp nhất cho bạn ạ?**"
        else:
            reply_text = "Dạ mình đã ghi nhận thông tin từ bạn. Để tư vấn gói phần mềm và giải pháp tối ưu nhất cho shop:\n\n**Shop mình hiện có mấy chi nhánh và đang kinh doanh dòng trang phục nào (như áo dài, váy cưới hay đồ biểu diễn) để mình tư vấn gói phù hợp nhất cho bạn ạ?**"

    # Lưu lại câu trả lời vào lịch sử session
    if reply_text:
        history.append({"role": "assistant", "content": reply_text})

    recent_tools = get_audit_logs_after(start_log_id)
    return {
        "reply": reply_text,
        "source": source,
        "tool_calls": recent_tools
    }
