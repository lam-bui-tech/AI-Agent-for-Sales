import time
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Query, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .db import init_db, get_connection, log_audit
from .catalog import search_products, get_product_details, get_policy_answer
from .inventory import check_inventory, adjust_inventory, load_inventory
from .leads import create_lead, get_all_leads
from .handoffs import handoff_to_human, get_all_handoffs

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
    consent_to_contact: bool = Field(..., description="Khách hàng đã xác nhận đồng ý nhận tư vấn")
    name: Optional[str] = Field(None, description="Tên khách hàng")
    channel_user_id: Optional[str] = Field(None, description="ID người dùng trên kênh")
    product_skus: Optional[List[str]] = Field(None, description="Danh sách SKU khách đang quan tâm")
    budget_vnd: Optional[int] = Field(None, description="Ngân sách khách dự kiến")
    needs_summary: Optional[str] = Field(None, description="Tóm tắt ngắn gọn nhu cầu sử dụng của khách")
    preferred_contact_method: Optional[str] = Field(None, description="Kênh liên hệ khách mong muốn (Zalo, Telegram, Gọi trực tiếp)")
    status: str = Field("new", description="Trạng thái lead: 'new' hoặc 'discount_pending'")

class HandoffRequest(BaseModel):
    conversation_id: str = Field(..., description="ID phiên hội thoại")
    reason: str = Field(..., description="Lý do chuyển người (discount_request, bulk_purchase, invoice_request, complaint, etc.)")
    summary: str = Field(..., description="Tóm tắt ngắn gọn lý do và bối cảnh chuyển ca")
    priority: str = Field("medium", description="Mức độ ưu tiên: low, medium, high, urgent")
    suggested_next_action: Optional[str] = Field(None, description="Gợi ý hành động tiếp theo cho sales")
    preferred_contact_method: Optional[str] = Field(None, description="Kênh liên hệ khách mong muốn (Zalo, Telegram, Gọi trực tiếp)")
    status: str = Field("open", description="Trạng thái ticket: 'open' hoặc 'discount_pending'")

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
    result = create_lead(
        channel=req.channel,
        phone=req.phone,
        consent_to_contact=req.consent_to_contact,
        name=req.name,
        channel_user_id=req.channel_user_id,
        product_skus=req.product_skus,
        budget_vnd=req.budget_vnd,
        needs_summary=req.needs_summary,
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
    result = handoff_to_human(
        conversation_id=req.conversation_id,
        reason=req.reason,
        summary=req.summary,
        priority=req.priority,
        suggested_next_action=req.suggested_next_action,
        preferred_contact_method=req.preferred_contact_method,
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
        return {"reply": "Chào bạn! Mình là Mèo Con 👨‍💻 — bạn cần tìm laptop phục vụ nhu cầu gì hay mức ngân sách bao nhiêu ạ?"}
    
    try:
        cmd = ["docker", "exec", "openclaw-cont", "openclaw", "agent", "--message", msg]
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=45)
        if proc.returncode == 0 and proc.stdout.strip():
            return {"reply": proc.stdout.strip(), "source": "openclaw-agent"}
        else:
            print("Docker agent err:", proc.stderr)
    except Exception as e:
        print("Exception executing docker agent:", e)
        
    return {"reply": "Mèo Con đang tiếp nhận yêu cầu, bạn có thể thử hỏi lại hoặc bấm các nút kịch bản mẫu bên dưới nhé!", "source": "fallback"}

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

@app.get("/health", summary="Health Check")
def health_check():
    return {"status": "ok", "service": "DemoTech Sales Service", "time": time.time()}

# Mount Static UI Web App at root
from fastapi.staticfiles import StaticFiles
from pathlib import Path
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
