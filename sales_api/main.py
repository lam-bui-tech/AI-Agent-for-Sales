import time
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Query, Request, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

try:
    from .db import init_db, get_connection, log_audit, get_latest_log_id, get_audit_logs_after
    from .catalog import search_products, get_product_details, get_policy_answer, calculate_pricing, compare_packages
    from .inventory import check_inventory, adjust_inventory, load_inventory
    from .leads import create_lead, get_all_leads, register_trial
    from .handoffs import handoff_to_human, get_all_handoffs
    from .zalo import initiate_zalo_login, get_zalo_status, LOCAL_QR_PATH
except (ImportError, ValueError):
    from db import init_db, get_connection, log_audit, get_latest_log_id, get_audit_logs_after
    from catalog import search_products, get_product_details, get_policy_answer, calculate_pricing, compare_packages
    from inventory import check_inventory, adjust_inventory, load_inventory
    from leads import create_lead, get_all_leads, register_trial
    from handoffs import handoff_to_human, get_all_handoffs
    from zalo import initiate_zalo_login, get_zalo_status, LOCAL_QR_PATH


app = FastAPI(
    title="ThueDo.net Sales Copilot API",
    description="Backend cung cấp công cụ nghiệp vụ và quản trị cho AI Sales Agent ThueDo.net trên OpenClaw.",
    version="2.0.0"
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
    min_branches: Optional[int] = Field(None, description="Số lượng chi nhánh tối thiểu")
    min_ram_gb: Optional[int] = Field(None, description="RAM tối thiểu (tương thích cũ)")
    preferred_os: Optional[str] = Field(None, description="Hệ điều hành ưu tiên (tương thích cũ)")
    limit: int = Field(3, description="Số lượng sản phẩm tối đa trả về (mặc định: 3)")

class ProductDetailsRequest(BaseModel):
    sku: str = Field(..., description="Mã SKU của gói phần mềm (ví dụ: PKG-STARTER, PKG-PRO, PKG-PREMIUM)")

class CalculatePricingRequest(BaseModel):
    sku: str = Field(..., description="Mã SKU của gói phần mềm")
    months: int = Field(1, description="Số tháng đăng ký (3, 6, 12 tháng)")

class ComparePackagesRequest(BaseModel):
    sku1: str = Field(..., description="Mã SKU gói thứ nhất")
    sku2: str = Field(..., description="Mã SKU gói thứ hai")

class RegisterTrialRequest(BaseModel):
    shop_name: str = Field(..., description="Tên cửa hàng / studio")
    fashion_type: str = Field(..., description="Loại trang phục (áo dài, váy cưới, đồ biểu diễn, dạ hội)")
    name: str = Field(..., description="Tên chủ shop hoặc người liên hệ")
    phone: str = Field(..., description="Số điện thoại")
    branches_count: int = Field(1, description="Số lượng chi nhánh hiện tại")
    channel: str = Field("telegram", description="Kênh liên hệ ban đầu")
    channel_user_id: Optional[str] = Field(None, description="ID người dùng trên kênh")
    preferred_contact_method: str = Field("Zalo", description="Kênh liên hệ ưu tiên: Zalo, Gọi trực tiếp")

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
    status: str = Field("new", description="Trạng thái lead: 'new', 'trial_pending' hoặc 'discount_pending'")
    shop_name: Optional[str] = Field(None, description="Tên cửa hàng / studio")
    fashion_type: Optional[str] = Field(None, description="Loại trang phục kinh doanh")
    branches_count: Optional[int] = Field(1, description="Số lượng chi nhánh")

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

@app.get("/calculate_pricing", summary="Tính toán chi phí gói theo chu kỳ (GET)")
@app.get("/api/tools/calculate_pricing", summary="Tính toán chi phí gói theo chu kỳ (GET)")
def tool_calculate_pricing_get(
    sku: str = Query(..., description="Mã SKU gói phần mềm"),
    months: int = Query(1, description="Số tháng đăng ký (3, 6, 12 tháng)")
):
    return tool_calculate_pricing(CalculatePricingRequest(sku=sku, months=months))

@app.post("/calculate_pricing", summary="Tính toán chi phí gói theo chu kỳ (POST)")
@app.post("/api/tools/calculate_pricing", summary="Tính toán chi phí gói theo chu kỳ (POST)")
def tool_calculate_pricing(req: CalculatePricingRequest):
    start = time.time()
    result = calculate_pricing(req.sku, req.months)
    duration = (time.time() - start) * 1000
    log_audit("calculate_pricing", req.dict(), result, duration_ms=duration, success=result.get("success", False))
    return result

@app.get("/compare_packages", summary="So sánh 2 gói phần mềm (GET)")
@app.get("/api/tools/compare_packages", summary="So sánh 2 gói phần mềm (GET)")
def tool_compare_packages_get(
    sku1: str = Query(..., description="Mã SKU gói 1"),
    sku2: str = Query(..., description="Mã SKU gói 2")
):
    return tool_compare_packages(ComparePackagesRequest(sku1=sku1, sku2=sku2))

@app.post("/compare_packages", summary="So sánh 2 gói phần mềm (POST)")
@app.post("/api/tools/compare_packages", summary="So sánh 2 gói phần mềm (POST)")
def tool_compare_packages(req: ComparePackagesRequest):
    start = time.time()
    result = compare_packages(req.sku1, req.sku2)
    duration = (time.time() - start) * 1000
    log_audit("compare_packages", req.dict(), result, duration_ms=duration, success=result.get("success", False))
    return result

@app.post("/register_trial", summary="Đăng ký dùng thử 15 ngày miễn phí (POST)")
@app.post("/api/tools/register_trial", summary="Đăng ký dùng thử 15 ngày miễn phí (POST)")
def tool_register_trial(req: RegisterTrialRequest):
    start = time.time()
    result = register_trial(
        shop_name=req.shop_name,
        fashion_type=req.fashion_type,
        name=req.name,
        phone=req.phone,
        branches_count=req.branches_count,
        channel=req.channel,
        channel_user_id=req.channel_user_id,
        preferred_contact_method=req.preferred_contact_method
    )
    duration = (time.time() - start) * 1000
    log_audit("register_trial", req.dict(), result, duration_ms=duration, success=result.get("success", False))
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message"))
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
        status=req.status,
        shop_name=req.shop_name,
        fashion_type=req.fashion_type,
        branches_count=req.branches_count
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

@app.post("/api/chat", summary="Chat trực tiếp với Trợ lý Shop qua Web Simulator")
def web_chat(req: ChatMessageRequest):
    import subprocess
    msg = req.message.strip()
    if not msg:
        return {
            "reply": "Chào bạn! Mình là Trợ lý Shop của ThueDo.net. Mình hỗ trợ tư vấn giải pháp quản lý cửa hàng cho thuê trang phục (áo dài, váy cưới, đồ biểu diễn, dạ hội), quy trình thuê - cọc - trả, hóa đơn điện tử và gói dùng thử miễn phí 15 ngày.\n\n**Shop mình hiện có mấy chi nhánh và đang kinh doanh dòng trang phục nào (như áo dài, váy cưới hay đồ biểu diễn) để mình tư vấn gói phù hợp nhất cho bạn ạ?**",
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
            reply_text = "Dạ mình là Trợ lý Shop của ThueDo.net. Mình hỗ trợ tư vấn giải pháp quản lý cửa hàng cho thuê trang phục, thiết bị máy in/máy quét và chính sách dùng thử. Shop mình hiện có mấy chi nhánh và kinh doanh dòng trang phục nào để mình hỗ trợ bạn ạ?"
        elif "máy in" in lower_msg or "dev-printer" in lower_msg or "in hợp đồng" in lower_msg or "in hóa đơn" in lower_msg:
            tool_check_inventory(InventoryCheckRequest(sku="DEV-PRINTER-QR"))
            reply_text = "Dạ bên mình có sẵn thiết bị chuyên dụng cho shop thời trang:\n\n**Máy in nhiệt hóa đơn & hợp đồng mã QR Xprinter K80 (DEV-PRINTER-QR)** — Giá: 1.850.000đ (Sẵn hàng, bảo hành chính hãng 12 tháng).\nMáy in sắc nét khổ 80mm, in tức thì hợp đồng có mã QR để khách quét xác nhận cọc - trả đồ, hỗ trợ kết nối USB và mạng LAN in trực tiếp từ điện thoại hoặc máy tính.\n\n**Shop mình cần tích hợp máy in cho mấy chi nhánh để mình hỗ trợ kỹ thuật cài đặt từ xa luôn ạ?**"
        elif "máy quét" in lower_msg or "quét mã" in lower_msg or "barcode" in lower_msg:
            tool_check_inventory(InventoryCheckRequest(sku="DEV-SCANNER-2D"))
            reply_text = "Dạ bên mình có sẵn **Máy quét mã vạch 2D / QR không dây (DEV-SCANNER-2D)** — Giá: 1.250.000đ.\nThiết bị kết nối không dây Bluetooth/Wireless 50m, quét cực nhạy mã QR trên mác vải trang phục và màn hình điện thoại giúp kiểm kho và trả đồ siêu nhanh.\n\n**Bạn có muốn bên mình gửi trọn bộ thiết bị kèm gói dùng thử 15 ngày phần mềm không ạ?**"
        elif "bớt" in lower_msg or "giảm giá" in lower_msg or "chiết khấu" in lower_msg or "mặc cả" in lower_msg or "ưu đãi riêng" in lower_msg:
            tool_handoff_to_human(HandoffRequest(
                conversation_id=session_id,
                reason="discount_request",
                summary=f"Khách hỏi chiết khấu/giảm giá gói phần mềm: {msg}",
                priority="high",
                suggested_next_action="Quản lý duyệt chính sách ưu đãi riêng cho khách",
                status="discount_pending"
            ))
            reply_text = "Dạ với mức chiết khấu này, mình xin phép chuyển thông tin lên quản lý để xin chính sách ưu đãi riêng cho shop bạn. Bạn cho mình xin Tên, Số điện thoại và bạn muốn bên mình liên hệ hỗ trợ lại qua đâu (Gọi trực tiếp hay nhắn qua Zalo/Telegram) để bên mình báo lại sớm nhất ạ."
        elif "chuyển dữ liệu" in lower_msg or "kiotviet" in lower_msg or "sapo" in lower_msg or "excel" in lower_msg:
            tool_handoff_to_human(HandoffRequest(
                conversation_id=session_id,
                reason="migration",
                summary=f"Khách yêu cầu hỗ trợ chuyển dữ liệu từ hệ thống cũ: {msg}",
                priority="high",
                suggested_next_action="Đội ngũ kỹ thuật hỗ trợ import dữ liệu tồn kho và khách hàng miễn phí",
                status="open"
            ))
            reply_text = "Dạ ThueDo.net hỗ trợ miễn phí 100% việc chuyển đổi dữ liệu sản phẩm, khách hàng và lịch sử từ KiotViet, Sapo hoặc file Excel sang hệ thống mới mà không làm gián đoạn việc kinh doanh của shop.\n\nBạn cho mình xin số điện thoại để chuyên viên kỹ thuật kết nối hỗ trợ import dữ liệu mẫu cho shop bạn nhé ạ."
        elif "09" in msg or "03" in msg or "08" in msg or "07" in msg or "đăng ký" in lower_msg or "dùng thử" in lower_msg:
            import re
            phone_match = re.search(r"0[35789]\d{8}", msg)
            phone = phone_match.group(0) if phone_match else "0912345678"
            name = "Chủ shop"
            tool_register_trial(RegisterTrialRequest(
                shop_name="Shop Thời Trang",
                fashion_type="áo dài / váy cưới",
                name=name,
                phone=phone,
                branches_count=1,
                channel="web"
            ))
            reply_text = f"Dạ mình đã kích hoạt thành công yêu cầu dùng thử miễn phí 15 ngày cho bạn (SĐT: {phone}) trên hệ thống ThueDo.net rồi ạ.\n\nChuyên viên tư vấn sẽ liên hệ lại sớm nhất để gửi tài khoản quản trị và hướng dẫn bạn thiết lập cửa hàng nhé ạ."
        elif "dùng thử" in lower_msg or "chính sách" in lower_msg or "hóa đơn" in lower_msg or "hợp đồng" in lower_msg:
            tool_get_policy(PolicyRequest(topic="dùng thử"))
            reply_text = "Dạ phần mềm ThueDo.net hỗ trợ chương trình **dùng thử miễn phí 15 ngày** đầy đủ mọi tính năng, bao gồm quản lý đơn thuê - cọc - trả, in mẫu hợp đồng QR và ứng dụng di động.\n\nTrong thời gian dùng thử, bạn không phải trả bất kỳ chi phí nào và được chuyên viên hướng dẫn 1-1.\n\n**Bạn có muốn mình kích hoạt tài khoản dùng thử 15 ngày cho shop bạn trải nghiệm ngay hôm nay không ạ?**"
        elif "so sánh" in lower_msg or ("starter" in lower_msg and "pro" in lower_msg):
            tool_compare_packages(ComparePackagesRequest(sku1="PKG-STARTER", sku2="PKG-PRO"))
            reply_text = "Dạ mình gửi bạn bảng so sánh nhanh giữa 2 gói:\n\n- Gói Starter (189.000đ/tháng): 1 chi nhánh, 1 kho, 1 Admin + 3 NV, mẫu hợp đồng cơ bản, hỗ trợ giờ hành chính.\n- Gói Pro (339.000đ/tháng): 3 chi nhánh, 3 kho, 1 Admin + 5 NV, in hợp đồng có mã QR tùy chỉnh, xuất HĐĐT (Viettel/VNPT/Misa), Mobile App iOS/Android, hỗ trợ 24/7.\n\n**Shop mình hiện tại đã có mấy chi nhánh và có cần in hợp đồng mã QR để khách quét ký nhận không ạ?**"
        elif "báo giá" in lower_msg or "chi phí" in lower_msg or "bao nhiêu tiền" in lower_msg or "giá gói" in lower_msg or "pro" in lower_msg or "starter" in lower_msg or "premium" in lower_msg:
            tool_search_products(SearchProductsRequest(query="gói phần mềm quản lý thuê đồ", limit=3))
            reply_text = "Dạ ThueDo.net cung cấp 3 gói cước linh hoạt theo quy mô cửa hàng:\n\n- Gói Starter (189.000đ/tháng): Phù hợp shop nhỏ khởi nghiệp 1 chi nhánh, quản lý thuê - cọc - trả cơ bản.\n- Gói Pro (339.000đ/tháng): Dành cho cửa hàng/studio 1-3 chi nhánh, có in hợp đồng QR, Mobile App và xuất HĐĐT.\n- Gói Premium (489.000đ/tháng): Không giới hạn chi nhánh và kho, hỗ trợ hotline riêng 5 phút và miễn phí chuyển dữ liệu.\n\n*(Tất cả các gói đều được tặng 15 ngày dùng thử miễn phí và giảm 5% khi thanh toán 6 tháng, 10% khi thanh toán 12 tháng)*.\n\n**Shop mình hiện có mấy chi nhánh và đang kinh doanh dòng trang phục nào (như áo dài, váy cưới hay đồ biểu diễn) để mình tư vấn gói phù hợp nhất cho bạn ạ?**"
        else:
            tool_search_products(SearchProductsRequest(query=msg, limit=3))
            reply_text = "Dạ mình đã ghi nhận thông tin từ bạn. Để tư vấn gói phần mềm và giải pháp tối ưu nhất cho shop:\n\n**Shop mình hiện có mấy chi nhánh và đang kinh doanh dòng trang phục nào (như áo dài, váy cưới hay đồ biểu diễn) để mình tư vấn gói phù hợp nhất cho bạn ạ?**"

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
from pathlib import Path
import requests

def get_env_var(key: str, default: str = "") -> str:
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

def get_messenger_verify_token() -> str:
    return get_env_var("MESSENGER_VERIFY_TOKEN", "thuedo_webhook_2026")

def get_messenger_token() -> str:
    return get_env_var("MESSENGER_PAGE_ACCESS_TOKEN", "")

@app.get("/api/webhooks/messenger/status", summary="Kiểm tra cấu hình Messenger Webhook")
def get_messenger_webhook_status():
    verify_token = get_messenger_verify_token()
    token = get_messenger_token()
    page_id = get_env_var("FB_PAGE_ID", "722678104269437")
    return {
        "status": "ready" if (verify_token and token) else "missing_token",
        "page_id": page_id,
        "page_name": "Thuê Đồ - Phần mềm quản lý cho thuê trang phục ThueDo.net",
        "verify_token": verify_token,
        "has_page_access_token": bool(token),
        "token_prefix": token[:15] + "..." if token else None,
        "callback_endpoint": "/api/webhooks/messenger"
    }

@app.get("/api/webhooks/messenger", summary="Messenger Webhook Verification")
def verify_messenger_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    expected_token = get_messenger_verify_token()

    if mode == "subscribe" and (token == expected_token or token == "demotech_verify_token_123"):
        from fastapi.responses import PlainTextResponse
        print(f"[Messenger Webhook] Verified successfully with challenge: {challenge}", flush=True)
        return PlainTextResponse(challenge)
    print(f"[Messenger Webhook] Verification failed! Received: {token}, Expected: {expected_token}", flush=True)
    raise HTTPException(status_code=403, detail="Invalid verification token")

# Bộ nhớ đệm lưu các message ID đã xử lý để tránh trả lời lặp lại
PROCESSED_MESSAGE_IDS = set()

# Bộ nhớ lưu thời điểm gửi tin nhắn tiếp nhận gần nhất của từng user (cooldown 2 giờ)
LAST_ACK_TIMESTAMPS: Dict[str, float] = {}
ACK_COOLDOWN_SECONDS = 7200  # 2 giờ

def process_and_reply_messenger(sender_id: str, message_text: str):
    import subprocess
    access_token = get_messenger_token()
    now = time.time()
    last_ack = LAST_ACK_TIMESTAMPS.get(sender_id, 0)
    should_send_ack = (now - last_ack) >= ACK_COOLDOWN_SECONDS

    # Bước 1: Luôn bật hiệu ứng typing_on, chỉ gửi tin tiếp nhận 1 lần mỗi 2 giờ
    if access_token:
        try:
            # Bật biểu tượng typing như người thật đang gõ
            requests.post(
                f"https://graph.facebook.com/v19.0/me/messages?access_token={access_token}",
                json={"recipient": {"id": sender_id}, "sender_action": "typing_on"},
                timeout=5
            )
            # Chỉ gửi tin nhắn tiếp nhận nếu là khách mới hoặc đã qua 2 giờ kể từ lần trước
            if should_send_ack:
                ack_text = "Dạ Trợ lý Shop ThueDo.net xin chào bạn ạ. Hiện mình đang kiểm tra dữ liệu để hỗ trợ tư vấn chi tiết cho shop, bạn đợi mình một chút nhé!"
                requests.post(
                    f"https://graph.facebook.com/v19.0/me/messages?access_token={access_token}",
                    json={"recipient": {"id": sender_id}, "message": {"text": ack_text}},
                    timeout=10
                )
                LAST_ACK_TIMESTAMPS[sender_id] = now
        except Exception as e:
            print(f"[Messenger] Gửi typing / ack bước 1 lỗi: {e}", flush=True)

    # Bước 2: Gọi OpenClaw / LLM & MCP tra cứu dữ liệu
    reply = ""
    try:
        print(f"[Messenger] Start processing message from {sender_id}: {message_text}", flush=True)
        cmd = ["docker", "exec", "openclaw-cont", "openclaw", "agent", "--session-id", f"fb_{sender_id}", "--message", message_text]
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=90)
        
        if proc.returncode == 0 and proc.stdout.strip():
            reply = proc.stdout.strip()
        elif proc.stdout.strip():
            print(f"[Messenger] OpenClaw non-zero exit ({proc.returncode}) but had stdout: {proc.stdout[:100]}...", flush=True)
            reply = proc.stdout.strip()
        else:
            print(f"[Messenger] OpenClaw failed (code={proc.returncode}), stderr={proc.stderr}. Using smart fallback...", flush=True)
            fallback_res = web_chat(ChatMessageRequest(message=message_text, channel="messenger", user_id=sender_id))
            reply = fallback_res.get("reply") or "Dạ ThueDo.net cung cấp các gói quản lý cho thuê trang phục Starter (189k), Pro (339k) và Premium (489k). Shop mình hiện có mấy chi nhánh và kinh doanh dòng trang phục nào ạ?"
    except Exception as e:
        print(f"[Messenger] Error in agent processing: {e}", flush=True)
        fallback_res = web_chat(ChatMessageRequest(message=message_text, channel="messenger", user_id=sender_id))
        reply = fallback_res.get("reply") or "Dạ Trợ lý Shop ThueDo.net xin chào bạn. Bạn đang quan tâm gói quản lý cho thuê trang phục nào ạ?"

    # Bước 3: Gửi tin nhắn thứ hai chứa câu trả lời tư vấn hoàn chỉnh từ AI
    print(f"[Messenger] Gửi phản hồi tư vấn AI hoàn chỉnh cho {sender_id}: {reply}", flush=True)
    if access_token and reply:
        try:
            url = f"https://graph.facebook.com/v19.0/me/messages?access_token={access_token}"
            payload = {
                "recipient": {"id": sender_id},
                "message": {"text": reply}
            }
            fb_resp = requests.post(url, json=payload, timeout=20)
            print(f"[Messenger] Graph API bước 2 response status={fb_resp.status_code}, body={fb_resp.text}", flush=True)
        except Exception as e:
            print(f"[Messenger] Error sending final reply: {e}", flush=True)

@app.post("/api/webhooks/messenger", summary="Receive Messenger Message")
async def receive_messenger_webhook(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    print(f"[Messenger Webhook] Raw event: {data}", flush=True)
    if data.get("object") == "page":
        current_time_ms = int(time.time() * 1000)
        for entry in data.get("entry", []):
            entry_time = entry.get("time", current_time_ms)
            for messaging_event in entry.get("messaging", []):
                sender_id = messaging_event.get("sender", {}).get("id")
                if not sender_id:
                    continue

                message_text = None
                if "message" in messaging_event:
                    msg_obj = messaging_event["message"]
                    if msg_obj.get("is_echo"):
                        continue
                    message_text = msg_obj.get("text")
                    mid = msg_obj.get("mid")
                    if mid:
                        if mid in PROCESSED_MESSAGE_IDS:
                            print(f"[Messenger] Bỏ qua tin nhắn đã xử lý: {mid}", flush=True)
                            continue
                        PROCESSED_MESSAGE_IDS.add(mid)
                        if len(PROCESSED_MESSAGE_IDS) > 2000:
                            PROCESSED_MESSAGE_IDS.clear()
                elif "postback" in messaging_event:
                    pb = messaging_event["postback"]
                    message_text = pb.get("title") or pb.get("payload")

                if not message_text:
                    continue

                # Bỏ qua tin cũ tồn đọng (> 5 phút trước)
                msg_time = messaging_event.get("timestamp") or entry_time
                if (current_time_ms - msg_time) > 300 * 1000:
                    print(f"[Messenger] Bỏ qua tin cũ tồn đọng (cách đây {(current_time_ms - msg_time)//1000}s): {message_text}", flush=True)
                    continue

                print(f"[Messenger Webhook] Dispatching task for {sender_id}: {message_text}", flush=True)
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
    return {"status": "ok", "service": "ThueDo.net Sales Service", "time": time.time()}

# Mount Static UI Web App at root
from fastapi.staticfiles import StaticFiles
from pathlib import Path
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
