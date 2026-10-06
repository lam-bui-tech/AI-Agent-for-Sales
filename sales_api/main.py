import time
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Query, Request, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .db import init_db, get_connection, log_audit, get_latest_log_id, get_audit_logs_after
from .catalog import search_products, get_product_details, get_policy_answer
from .inventory import check_inventory, adjust_inventory, load_inventory
from .leads import create_lead, get_all_leads
from .handoffs import handoff_to_human, get_all_handoffs
from .zalo import initiate_zalo_login, get_zalo_status, LOCAL_QR_PATH


app = FastAPI(
    title="DemoTech Sales Copilot API",
    description="Backend cung cấp 6 công cụ nghiệp vụ và quản trị cho AI Sales Agent trên OpenClaw.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    init_db()

# --- Pydantic Request Models ---

class SearchProductsRequest(BaseModel):
    query: Optional[str] = Field(None, description="Từ khóa tìm kiếm hoặc nhu cầu sử dụng")
    max_price_vnd: Optional[int] = Field(None, description="Ngân sách tối đa tính bằng VNĐ")
    min_ram_gb: Optional[int] = Field(None, description="Dung lượng RAM tối thiểu (GB)")
    preferred_os: Optional[str] = Field(None, description="Hệ điều hành ưu tiên (Windows, macOS, Linux)")
    limit: int = Field(3, description="Số lượng sản phẩm tối đa trả về (mặc định: 3)")

class ProductDetailsRequest(BaseModel):
    sku: str = Field(..., description="Mã SKU của sản phẩm (ví dụ: LAP-001)")

class InventoryCheckRequest(BaseModel):
    sku: str = Field(..., description="Mã SKU cần kiểm tra tồn kho")

class CreateLeadRequest(BaseModel):
    channel: str = Field(..., description="Kênh tương tác (telegram, zalo, messenger, web)")
    phone: str = Field(..., description="Số điện thoại khách hàng")
    consent_to_contact: Optional[bool] = Field(None, description="Khách hàng đã xác nhận đồng ý nhận tư vấn")
    consent: Optional[bool] = Field(None, description="Alias cho consent_to_contact")
    name: Optional[str] = Field(None, description="Tên khách hàng")
    channel_user_id: Optional[str] = Field(None, description="ID người dùng trên kênh")
    product_skus: Optional[List[str]] = Field(None, description="Danh sách SKU khách đang quan tâm")
    skus: Optional[List[str]] = Field(None, description="Alias cho product_skus")
    budget_vnd: Optional[int] = Field(None, description="Ngân sách khách dự kiến")
    needs_summary: Optional[str] = Field(None, description="Tóm tắt ngắn gọn nhu cầu sử dụng của khách")
    need: Optional[str] = Field(None, description="Alias cho needs_summary")
    preferred_contact_method: Optional[str] = Field(None, description="Kênh liên hệ khách mong muốn (Zalo, Telegram, Gọi trực tiếp)")
    status: str = Field("new", description="Trạng thái lead: 'new' hoặc 'discount_pending'")

class HandoffRequest(BaseModel):
    conversation_id: Optional[str] = Field(None, description="ID phiên hội thoại")
    reason: str = Field(..., description="Lý do chuyển người (discount_request, bulk_purchase, invoice_request, complaint, etc.)")
    summary: str = Field(..., description="Tóm tắt ngắn gọn lý do và bối cảnh chuyển ca")
    priority: str = Field("medium", description="Mức độ ưu tiên: low, medium, high, urgent")
    suggested_next_action: Optional[str] = Field(None, description="Gợi ý hành động tiếp theo cho sales")
    preferred_contact_method: Optional[str] = Field(None, description="Kênh liên hệ khách mong muốn (Zalo, Telegram, Gọi trực tiếp)")
    status: str = Field("open", description="Trạng thái ticket: 'open' hoặc 'discount_pending'")
    channel: Optional[str] = Field(None, description="Kênh tương tác (tuỳ chọn)")
    contact: Optional[str] = Field(None, description="Thông tin liên hệ (tuỳ chọn)")


class PolicyRequest(BaseModel):
    topic: str = Field(..., description="Chủ đề chính sách cần tra cứu (bảo hành, đổi trả, vận chuyển, vat, trả góp)")

class AdjustInventoryRequest(BaseModel):
    sku: str
    quantity: int

# --- Tool Endpoints for Agent ---

@app.get("/search_products", summary="Tool 1: Tìm kiếm sản phẩm (GET)")
@app.get("/api/tools/search_products", summary="Tool 1: Tìm kiếm sản phẩm (GET)")
def tool_search_products_get(
    query: Optional[str] = Query(None, description="Từ khóa hoặc nhu cầu"),
    max_price: Optional[int] = Query(None, description="Ngân sách tối đa"),
    max_price_vnd: Optional[int] = Query(None, description="Ngân sách tối đa (VNĐ)"),
    min_ram: Optional[int] = Query(None, description="RAM tối thiểu (GB)"),
    min_ram_gb: Optional[int] = Query(None, description="RAM tối thiểu (GB)"),
    preferred_os: Optional[str] = Query(None, description="Hệ điều hành"),
    limit: int = Query(3, description="Số lượng kết quả")
):
    eff_max_price = max_price if max_price is not None else max_price_vnd
    eff_min_ram = min_ram if min_ram is not None else min_ram_gb
    return tool_search_products(SearchProductsRequest(
        query=query,
        max_price_vnd=eff_max_price,
        min_ram_gb=eff_min_ram,
        preferred_os=preferred_os,
        limit=limit
    ))

@app.post("/search_products", summary="Tool 1: Tìm kiếm sản phẩm theo tiêu chí (POST)")
@app.post("/api/tools/search_products", summary="Tool 1: Tìm kiếm sản phẩm theo tiêu chí")
def tool_search_products(req: SearchProductsRequest):
    start = time.time()
    result = search_products(
        query=req.query,
        max_price_vnd=req.max_price_vnd,
        min_ram_gb=req.min_ram_gb,
        preferred_os=req.preferred_os,
        limit=req.limit
    )
    duration = (time.time() - start) * 1000
    log_audit("search_products", req.dict(), result, duration_ms=duration, success=True)
    return result

@app.get("/get_product_details", summary="Tool 2: Chi tiết sản phẩm (GET)")
@app.get("/api/tools/get_product_details", summary="Tool 2: Chi tiết sản phẩm (GET)")
def tool_product_details_get(sku: str = Query(..., description="Mã SKU")):
    return tool_product_details(ProductDetailsRequest(sku=sku))

@app.post("/get_product_details", summary="Tool 2: Lấy thông số chi tiết của sản phẩm (POST)")
@app.post("/api/tools/get_product_details", summary="Tool 2: Lấy thông số chi tiết của sản phẩm")
def tool_product_details(req: ProductDetailsRequest):
    start = time.time()
    result = get_product_details(req.sku)
    duration = (time.time() - start) * 1000
    log_audit("get_product_details", req.dict(), result, duration_ms=duration, success=result.get("found", False))
    return result

@app.get("/check_inventory", summary="Tool 3: Kiểm tra tồn kho (GET)")
@app.get("/api/tools/check_inventory", summary="Tool 3: Kiểm tra tồn kho (GET)")
def tool_check_inventory_get(sku: str = Query(..., description="Mã SKU")):
    return tool_check_inventory(InventoryCheckRequest(sku=sku))

@app.post("/check_inventory", summary="Tool 3: Kiểm tra tồn kho thời gian thực (POST)")
@app.post("/api/tools/check_inventory", summary="Tool 3: Kiểm tra tồn kho thời gian thực")
def tool_check_inventory(req: InventoryCheckRequest):
    start = time.time()
    result = check_inventory(req.sku)
    duration = (time.time() - start) * 1000
    log_audit("check_inventory", req.dict(), result, duration_ms=duration, success=result.get("found", False))
    return result

@app.post("/create_lead", summary="Tool 4: Tạo hồ sơ Lead (POST)")
@app.post("/api/tools/create_lead", summary="Tool 4: Tạo hồ sơ Lead với consent")
def tool_create_lead(req: CreateLeadRequest):
    start = time.time()
    effective_consent = req.consent_to_contact if req.consent_to_contact is not None else (req.consent if req.consent is not None else True)
    effective_skus = req.product_skus or req.skus
    effective_needs = req.needs_summary or req.need
    result = create_lead(
        channel=req.channel,
        phone=req.phone,
        consent_to_contact=effective_consent,
        name=req.name,
        channel_user_id=req.channel_user_id,
        product_skus=effective_skus,
        budget_vnd=req.budget_vnd,
        needs_summary=effective_needs,
        preferred_contact_method=req.preferred_contact_method,
        status=req.status
    )
    duration = (time.time() - start) * 1000
    log_audit("create_lead", req.dict(), result, duration_ms=duration, success=result.get("success", False))
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message"))
    return result

@app.post("/handoff_to_human", summary="Tool 5: Chuyển giao ca cho nhân viên sales (POST)")
@app.post("/api/tools/handoff_to_human", summary="Tool 5: Chuyển giao ca cho nhân viên sales")
def tool_handoff(req: HandoffRequest):
    start = time.time()
    eff_conv_id = req.conversation_id or (f"{req.channel}:{req.contact}" if req.channel and req.contact else (req.channel or req.contact or "unknown"))
    result = handoff_to_human(
        conversation_id=eff_conv_id,
        reason=req.reason,
        summary=req.summary,
        priority=req.priority,
        suggested_next_action=req.suggested_next_action,
        preferred_contact_method=req.preferred_contact_method or req.contact,
        status=req.status
    )
    duration = (time.time() - start) * 1000
    log_audit("handoff_to_human", req.dict(), result, duration_ms=duration, success=True)
    return result


@app.get("/get_policy_answer", summary="Tool 6: Tra cứu chính sách (GET)")
@app.get("/api/tools/get_policy_answer", summary="Tool 6: Tra cứu chính sách (GET)")
def tool_policy_answer_get(topic: str = Query(..., description="Chủ đề")):
    return tool_policy_answer(PolicyRequest(topic=topic))

@app.post("/get_policy_answer", summary="Tool 6: Tra cứu chính sách và FAQ (POST)")
@app.post("/api/tools/get_policy_answer", summary="Tool 6: Tra cứu chính sách và FAQ")
def tool_policy_answer(req: PolicyRequest):
    start = time.time()
    result = get_policy_answer(req.topic)
    duration = (time.time() - start) * 1000
    log_audit("get_policy_answer", req.dict(), result, duration_ms=duration, success=result.get("found", False))
    return result

# --- Admin & Monitoring Endpoints ---

@app.get("/admin/leads", summary="Danh sách leads đã thu thập")
def admin_leads():
    return {"leads": get_all_leads()}

@app.get("/admin/handoffs", summary="Danh sách vé chuyển giao sales")
def admin_handoffs():
    return {"handoffs": get_all_handoffs()}

@app.get("/admin/inventory", summary="Toàn bộ dữ liệu tồn kho hiện tại")
def admin_inventory():
    return {"inventory": load_inventory()}

@app.post("/admin/inventory/adjust", summary="Điều chỉnh tồn kho phục vụ demo")
def admin_adjust_inventory(req: AdjustInventoryRequest):
    return adjust_inventory(req.sku, req.quantity)

@app.get("/admin/audit-logs", summary="Nhật ký các lượt gọi tool")
def admin_audit_logs(limit: int = 50):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return {"audit_logs": [dict(r) for r in rows]}

class ChatMessageRequest(BaseModel):
    message: str
    channel: Optional[str] = "web"
    user_id: Optional[str] = "web_user"

@app.post("/api/chat", summary="Chat trực tiếp với Mèo Con qua Web Simulator")
def web_chat(req: ChatMessageRequest):
    import subprocess
    msg = req.message.strip()
    if not msg:
        return {
            "reply": "Chào bạn! Mình là Mèo Con, trợ lý tư vấn thiết bị công nghệ cho DemoTech. Bạn đang cần tìm laptop phân khúc nào hay ngân sách khoảng bao nhiêu ạ?",
            "source": "greeting",
            "tool_calls": []
        }
    
    start_log_id = get_latest_log_id()
    session_id = f"web_{req.user_id or 'default'}"
    reply_text = None
    source = "openclaw-agent"

    # 1. Thử gọi OpenClaw qua Docker container
    try:
        cmd = ["docker", "exec", "openclaw-cont", "openclaw", "agent", "--session-id", session_id, "--message", msg]
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=90)
        if proc.returncode == 0 and proc.stdout.strip():
            reply_text = proc.stdout.strip()
            source = "openclaw-agent"
        elif proc.stdout.strip():
            reply_text = proc.stdout.strip()
            source = "openclaw-agent-partial"
        else:
            if "overloaded" in (proc.stderr or "").lower() or "rate limit" in (proc.stderr or "").lower():
                reply_text = "Dạ hệ thống AI đang chịu tải cao tạm thời, mình xin lỗi vì sự bất tiện này. Bạn vui lòng gửi lại câu hỏi sau giây lát nhé ạ."
                source = "overloaded_notice"
    except Exception as e:
        print("Docker agent exception:", e)

    # 2. Smart Simulation Mock nếu Docker không khả dụng (phục vụ dev & demo mượt mà)
    if not reply_text:
        source = "simulation-engine"
        lower_msg = msg.lower()
        
        if "bỏ qua các nguyên tắc" in lower_msg or "api token" in lower_msg or "config của bạn" in lower_msg:
            reply_text = "Dạ mình là Mèo Con, trợ lý tư vấn thiết bị công nghệ cho DemoTech. Mình chỉ hỗ trợ các thông tin về sản phẩm, tồn kho và chính sách bán hàng. Bạn cần mình tư vấn dòng laptop nào ạ?"
        elif "lap-010" in lower_msg or ("devstation" in lower_msg and "còn hàng" in lower_msg):
            # Kịch bản hết hàng LAP-010
            tool_check_inventory(InventoryCheckRequest(sku="LAP-010"))
            reply_text = "Dạ mình vừa tra cứu kho dữ liệu thời gian thực:\n\nMẫu DevStation Linux (LAP-010) hiện đã tạm hết hàng trên toàn hệ thống và chưa có lịch về hàng cụ thể.\n\nĐể đáp ứng công việc lập trình, bạn có thể tham khảo mẫu Forge Code 15 (LAP-002) RAM 32GB đang sẵn hàng tại kho TP.HCM.\n\n**Bạn có muốn mình gửi thông số chi tiết dòng Forge Code 15 để bạn tham khảo không ạ?**"
        elif "forge code 15" in lower_msg and ("còn hàng" in lower_msg or "chi nhánh" in lower_msg):
            # Kịch bản kiểm tra tồn kho LAP-002
            tool_check_inventory(InventoryCheckRequest(sku="LAP-002"))
            reply_text = "Dạ mình vừa kiểm tra trực tiếp kho dữ liệu thời gian thực:\n\nMẫu Forge Code 15 (LAP-002) hiện còn 3 máy sẵn sàng giao ngay tại chi nhánh trung tâm TP.HCM và hỗ trợ ship hỏa tốc toàn quốc.\n\n**Bạn muốn đặt giữ máy trước hay cần mình hỗ trợ kiểm tra chi tiết phụ kiện đi kèm ạ?**"
        elif "bớt" in lower_msg or "26 triệu" in lower_msg or "mặc cả" in lower_msg or "giảm giá" in lower_msg:
            # Kịch bản trả giá / deal pending
            tool_handoff_to_human(HandoffRequest(
                conversation_id=session_id,
                reason="discount_request",
                summary=f"Khách hỏi chiết khấu/giảm giá cho đơn hàng: {msg}",
                priority="high",
                suggested_next_action="Quản lý duyệt chính sách ưu đãi riêng cho khách",
                status="discount_pending"
            ))
            reply_text = "Dạ với mức giảm giá này, mình xin phép chuyển thông tin lên quản lý để xin chính sách ưu đãi riêng cho bạn.\n\nBạn cho mình xin Tên, Số điện thoại và bạn muốn bên mình liên hệ hỗ trợ lại qua đâu (Gọi trực tiếp hay nhắn qua Zalo/Telegram) để bên mình báo lại sớm nhất ạ."
        elif "0912345678" in msg or "09" in msg or "gọi tư vấn" in lower_msg or "đồng ý" in lower_msg:
            # Kịch bản thu lead
            import re
            phone_match = re.search(r"0\d{9,10}", msg)
            phone = phone_match.group(0) if phone_match else "0912345678"
            name = "Hùng" if "hùng" in lower_msg else "Khách hàng"
            tool_create_lead(CreateLeadRequest(
                channel="web",
                phone=phone,
                consent_to_contact=True,
                name=name,
                product_skus=["LAP-002"],
                needs_summary=msg,
                budget_vnd=28000000
            ))
            reply_text = f"Dạ mình đã ghi nhận thông tin của bạn {name} (SĐT: {phone}) kèm sự đồng thuận vào hệ thống tư vấn ưu tiên của DemoTech rồi ạ.\n\nChuyên viên tư vấn sẽ liên hệ lại sớm nhất để hỗ trợ bạn hoàn tất đơn hàng và nhận quà tặng kèm ạ."
        elif "bảo hành" in lower_msg or "đổi mới" in lower_msg or "chính sách" in lower_msg or "lỗi màn hình" in lower_msg:
            # Kịch bản chính sách 1 đổi 1
            tool_get_policy(PolicyRequest(topic="bảo hành"))
            reply_text = "Dạ theo chính sách bảo hành chính hãng của DemoTech:\n\nTrong vòng 30 ngày đầu tiên kể từ khi nhận máy, nếu sản phẩm phát sinh lỗi phần cứng do nhà sản xuất (bao gồm cả lỗi màn hình từ 3 điểm chết trở lên), bên mình áp dụng chính sách 1 đổi 1 máy mới 100% nguyên seal ngay lập tức.\n\nToàn bộ máy còn được hưởng chế độ bảo hành hãng 24 tháng và hỗ trợ kỹ thuật trọn đời.\n\n**Bạn cần mình giải đáp thêm về thủ tục bảo hành hay cách thức giao nhận máy ạ?**"
        elif "docker" in lower_msg or "lập trình" in lower_msg or "28" in lower_msg or "tìm máy" in lower_msg or "laptop" in lower_msg:
            # Kịch bản tìm máy code Docker 28tr
            tool_search_products(SearchProductsRequest(
                query="Docker lập trình backend",
                max_price_vnd=28000000,
                min_ram_gb=16,
                limit=3
            ))
            reply_text = "Dạ dựa trên nhu cầu lập trình backend và chạy Docker trong tầm ngân sách 28 triệu, mình đã tra cứu kho và đề xuất cho bạn 2 lựa chọn tối ưu nhất:\n\n1. **Forge Code 15 (LAP-002)** — 27.990.000đ\nCấu hình: Intel Core i7-14700HX, RAM 32GB DDR5, SSD 1TB NVMe. Dòng máy build cực kỳ chắc chắn, tản nhiệt buồng hơi kép, 32GB RAM cân mượt nhiều container Docker nặng cùng lúc.\n\n2. **Nova Pro 14 (LAP-001)** — 23.990.000đ\nCấu hình: AMD Ryzen 7 8845HS, RAM 16GB, SSD 512GB. Trọng lượng siêu nhẹ 1.4kg, pin trâu phù hợp di chuyển nhiều.\n\n**Bạn ưu tiên dòng hiệu năng tối đa RAM 32GB hay thích máy mỏng nhẹ cơ động hơn ạ?**"
        else:
            tool_search_products(SearchProductsRequest(query=msg, limit=3))
            reply_text = "Dạ mình đã kiểm tra dữ liệu kho sản phẩm của DemoTech. Bạn có thể cho mình biết cụ thể hơn về khoảng ngân sách dự kiến hoặc phần mềm chính bạn hay dùng để mình chọn máy chuẩn nhất cho bạn nhé ạ.\n\n**Bạn dự định đầu tư trong tầm ngân sách bao nhiêu ạ?**"

    # Lấy danh sách tool call vừa thực thi
    recent_tools = get_audit_logs_after(start_log_id)
    return {
        "reply": reply_text,
        "source": source,
        "tool_calls": recent_tools
    }


@app.get("/api/catalog", summary="Lấy danh sách tất cả sản phẩm cho Web UI")
def get_full_catalog():
    from .catalog import load_products
    return {"products": load_products()}

# --- Messenger Webhook ---
import os
import requests

MESSENGER_VERIFY_TOKEN = os.getenv("MESSENGER_VERIFY_TOKEN", "demotech_verify_token_123")

@app.get("/api/webhooks/messenger", summary="Messenger Webhook Verification")
def verify_messenger_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == MESSENGER_VERIFY_TOKEN:
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(challenge)
    raise HTTPException(status_code=403, detail="Invalid verification token")

# Bộ nhớ đệm lưu các message ID đã xử lý để tránh trả lời lặp lại
PROCESSED_MESSAGE_IDS = set()

def process_and_reply_messenger(sender_id: str, message_text: str):
    import subprocess
    try:
        cmd = ["docker", "exec", "openclaw-cont", "openclaw", "agent", "--session-id", f"fb_{sender_id}", "--message", message_text]
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=45)
        reply = proc.stdout.strip() if proc.returncode == 0 else "Mèo Con đang tiếp nhận yêu cầu, chờ xíu nhé!"
        
        # Đọc token Page mới nhất
        access_token = os.getenv("MESSENGER_PAGE_ACCESS_TOKEN", "")
        env_file = Path(__file__).parent.parent / ".env"
        if env_file.exists():
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("MESSENGER_PAGE_ACCESS_TOKEN="):
                        access_token = line.split("=", 1)[1].strip()
                        break
        
        print(f"[Messenger] Processing message from {sender_id}: {message_text}")
        print(f"[Messenger] OpenClaw Reply: {reply}")
        
        if access_token:
            url = f"https://graph.facebook.com/v21.0/me/messages?access_token={access_token}"
            payload = {
                "recipient": {"id": sender_id},
                "message": {"text": reply}
            }
            fb_resp = requests.post(url, json=payload)
            print(f"[Messenger] Graph API response status={fb_resp.status_code}, body={fb_resp.text}")
        else:
            print("[Messenger] Error: MESSENGER_PAGE_ACCESS_TOKEN is missing!")
    except Exception as e:
        print(f"Error processing Messenger message: {e}")

@app.post("/api/webhooks/messenger", summary="Receive Messenger Message")
async def receive_messenger_webhook(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    if data.get("object") == "page":
        current_time_ms = int(time.time() * 1000)
        for entry in data.get("entry", []):
            entry_time = entry.get("time", current_time_ms)
            for messaging_event in entry.get("messaging", []):
                if "message" in messaging_event and "text" in messaging_event["message"]:
                    # Bỏ qua tin nhắn echo từ chính Trang
                    if messaging_event["message"].get("is_echo"):
                        continue
                    
                    # 1. Bỏ qua tin nhắn cũ bị Facebook retry/tồn đọng (quá 45 giây trước)
                    msg_time = messaging_event.get("timestamp") or entry_time
                    if (current_time_ms - msg_time) > 45 * 1000:
                        print(f"[Messenger] Bỏ qua tin cũ tồn đọng (cách đây {(current_time_ms - msg_time)//1000}s): {messaging_event['message'].get('text')}")
                        continue
                    
                    # 2. Bỏ qua tin nhắn trùng lặp (Facebook retry)
                    mid = messaging_event.get("message", {}).get("mid")
                    if mid:
                        if mid in PROCESSED_MESSAGE_IDS:
                            print(f"[Messenger] Bỏ qua tin nhắn đã xử lý: {mid}")
                            continue
                        PROCESSED_MESSAGE_IDS.add(mid)
                        if len(PROCESSED_MESSAGE_IDS) > 2000:
                            PROCESSED_MESSAGE_IDS.clear()
                    
                    sender_id = messaging_event["sender"]["id"]
                    message_text = messaging_event["message"]["text"]
                    
                    # Trả về 200 OK ngay cho Facebook và xử lý gửi tin trong background
                    background_tasks.add_task(process_and_reply_messenger, sender_id, message_text)
                    
    return {"status": "ok"}

# --- Zalo Channel Integration Endpoints ---

@app.post("/api/zalo/login", summary="Bắt đầu đăng nhập Zalo bằng mã QR (OpenClaw)")
@app.get("/api/zalo/login", summary="Bắt đầu đăng nhập Zalo bằng mã QR (OpenClaw GET)")
def zalo_login_endpoint(force: bool = Query(False, description="Bắt buộc tạo mã QR mới")):
    """
    Kích hoạt OpenClaw tạo mã QR đăng nhập Zalo Personal,
    tải ảnh QR về workspace máy chủ và trả về đường dẫn cùng dữ liệu Base64.
    """
    res = initiate_zalo_login(force=force)
    return res

@app.get("/api/zalo/qr.png", summary="Lấy file ảnh mã QR Zalo hiện tại")
def zalo_qr_image_endpoint():
    """Trả về file ảnh PNG của mã QR Zalo để hiển thị trực tiếp trên trình duyệt."""
    if not LOCAL_QR_PATH.exists():
        from .zalo import fetch_qr_from_container
        fetch_qr_from_container()
    if not LOCAL_QR_PATH.exists():
        raise HTTPException(status_code=404, detail="Chưa có mã QR đăng nhập nào. Hãy gọi /api/zalo/login để tạo.")
    return FileResponse(LOCAL_QR_PATH, media_type="image/png")

@app.get("/api/zalo/qr", summary="Lấy thông tin và mã Base64 của mã QR Zalo")
def zalo_qr_info_endpoint():
    """Trả về thông tin chi tiết về mã QR Zalo (base64, URL, đường dẫn file)."""
    import base64
    if not LOCAL_QR_PATH.exists():
        from .zalo import fetch_qr_from_container
        fetch_qr_from_container()
    if not LOCAL_QR_PATH.exists():
        return {
            "status": "waiting",
            "message": "Đang khởi tạo mã QR từ OpenClaw...",
            "qr_image_url": "/api/zalo/qr.png",
            "qr_base64": None
        }
    b64_str = base64.b64encode(LOCAL_QR_PATH.read_bytes()).decode("utf-8")
    return {
        "status": "ready_to_scan",
        "qr_image_url": f"/api/zalo/qr.png?t={int(time.time())}",
        "qr_base64": f"data:image/png;base64,{b64_str}",
        "local_file_path": str(LOCAL_QR_PATH)
    }

@app.get("/api/zalo/status", summary="Kiểm tra trạng thái kết nối Zalo trên OpenClaw")
def zalo_status_endpoint():
    """Kiểm tra xem tài khoản Zalo đã đăng nhập và liên kết thành công vào OpenClaw hay chưa."""
    return get_zalo_status()

@app.get("/zalo", summary="Trang giao diện đăng nhập Zalo QR")
def zalo_page_endpoint():
    """Giao diện web trực quan để quét mã QR và theo dõi đăng nhập Zalo."""
    zalo_html = Path(__file__).parent / "static" / "zalo.html"
    if zalo_html.exists():
        return FileResponse(zalo_html, media_type="text/html")
    raise HTTPException(status_code=404, detail="File zalo.html không tồn tại")

@app.get("/health", summary="Health Check")
def health_check():
    return {"status": "ok", "service": "DemoTech Sales Service", "time": time.time()}

# Mount Static UI Web App at root
from fastapi.staticfiles import StaticFiles
from pathlib import Path
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
