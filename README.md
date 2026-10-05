# DemoTech AI Sales Copilot (Vertical Slice MVP)

Hệ thống AI Sales Agent đa kênh chạy trên nền tảng **OpenClaw** (Docker) kết nối **Telegram Bot** (`@lamOpclw_bot`) và chuẩn bị mở rộng sang Zalo. Hệ thống được tích hợp với **Sales Demo Service** thông qua chuẩn giao thức **MCP (Model Context Protocol)** và REST API, đảm bảo Agent tư vấn dựa trên dữ liệu thật, không hallucinate, kiểm tra tồn kho thời gian thực, thu lead có đồng thuận (consent) và tự động chuyển giao nhân viên bán hàng (handoff).

---

## 1. Kiến trúc hệ thống

```
Khách hàng (Telegram / Zalo)
         │
         ▼
OpenClaw Gateway (Container: openclaw-cont)
         │
         ├── Đọc AGENTS.md + SOUL.md + IDENTITY.md ("Mèo Con 👨‍💻")
         ├── Kích hoạt Skill sales-advisor (SKILL.md)
         └── Gọi Tool Call qua MCP Server (mcp_server.py)
                     │
                     ▼ (HTTP / Local)
        Sales Demo Service (http://localhost:8000)
         ├── /search_products       (Lọc theo ngân sách, RAM, OS, use-case)
         ├── /get_product_details   (Xem full thông số kỹ thuật)
         ├── /check_inventory       (Tra tồn kho & chi nhánh thời gian thực)
         ├── /create_lead           (Lưu Lead vào SQLite khi có Consent)
         ├── /handoff_to_human      (Tạo ticket chuyển ca + Alert Telegram)
         └── /get_policy_answer     (Tra cứu bảo hành 1-đổi-1, đổi trả, VAT)
                     │
                     ▼
          data/sales.db (SQLite) + data/products.json + data/inventory.json
```

---

## 2. Danh mục 6 công cụ (Tools)

1. **`search_products`**: Tìm kiếm 1–3 sản phẩm phù hợp nhất theo ngân sách, RAM tối thiểu, hệ điều hành ưu tiên và từ khóa nhu cầu.
2. **`get_product_details`**: Tra cứu toàn bộ thông số chi tiết của SKU để giải thích hoặc so sánh.
3. **`check_inventory`**: Bắt buộc gọi khi khách hỏi "còn hàng không?", kiểm tra số lượng thực tế tại các kho.
4. **`create_lead`**: Ghi nhận thông tin khách hàng vào SQLite. **Chỉ gọi khi khách đồng ý (Consent)**.
5. **`handoff_to_human`**: Tự động chuyển ca cho nhân viên sales khi khách hỏi giảm giá, mua sỉ B2B, xuất hóa đơn VAT đặc biệt, khiếu nại, hoặc vượt thẩm quyền.
6. **`get_policy_answer`**: Tra cứu chính sách bảo hành 24 tháng, 1 đổi 1 trong 30 ngày, chính sách VAT, vận chuyển.

---

## 3. Cách khởi chạy & Kiểm thử

### Bước 1: Khởi động Sales Demo Service
```bash
# Tại thư mục gốc c:\Users\OS\Downloads\ApplyOpenclaw
python -m uvicorn sales_api.main:app --host 0.0.0.0 --port 8000
```
- Swagger UI tài liệu API: `http://localhost:8000/docs`
- Dashboard xem Lead: `http://localhost:8000/admin/leads`
- Dashboard xem Handoff: `http://localhost:8000/admin/handoffs`

### Bước 2: Chạy kiểm thử tự động
```bash
pytest tests/test_api.py -v
```

### Bước 3: Chat trực tiếp trên Telegram
- Mở ứng dụng Telegram và tìm bot: **`@lamOpclw_bot`**
- Thử các kịch bản mẫu từ tài liệu [tests/test_conversations.md](file:///c:/Users/OS/Downloads/ApplyOpenclaw/tests/test_conversations.md):
  1. *"Tôi cần laptop lập trình backend Docker khoảng 28 triệu"* -> Bot gọi `search_products`, đề xuất `Forge Code 15 (LAP-002)` giá 27.990.000đ.
  2. *"Bớt cho mình 2 triệu con này được không?"* -> Bot từ chối giảm giá, gọi `handoff_to_human` tạo mã vé `TICK-...`.
  3. *"Nhờ nhân viên gọi tư vấn giúp, mình đồng ý cho shop lưu số 0912345678, mình tên Hùng"* -> Bot gọi `create_lead` tạo mã Lead.
