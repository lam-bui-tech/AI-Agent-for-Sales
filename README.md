# DemoTech AI Sales Copilot — Hướng dẫn cài đặt, cấu hình & đóng gói triển khai

Hệ thống AI Sales Agent đa kênh chạy trên nền tảng **OpenClaw** tích hợp **Sales Demo Service (FastAPI)** thông qua giao thức **MCP (Model Context Protocol)** và REST API. Hệ thống hỗ trợ tư vấn bán hàng đa kênh (**Telegram, Zalo, Facebook Messenger, Web Simulator**), đảm bảo Agent tư vấn dựa trên dữ liệu thật, kiểm tra tồn kho thời gian thực, thu thập thông tin khách (Lead) có đồng thuận (Consent) và tự động chuyển giao nhân viên/quản lý (Handoff ticket + Alert) khi có yêu cầu giảm giá, mua sỉ hoặc khiếu nại.

---

## 1. Kiến trúc hệ thống (System Architecture)

```
[ Khách hàng ] ──> (Telegram / Zalo / Facebook Messenger / Web Simulator)
                              │
                              ▼
┌────────────────────────────────────────────────────────────────────────┐
│  KHỐI 1: OPENCLAW GATEWAY (Bộ não AI - Chạy qua Docker hoặc CLI)        │
│  - Điều phối mô hình ngôn ngữ lớn (Gemini 2.5 Flash, OpenRouter...)     │
│  - Định hình tính cách & quy chuẩn: SOUL.md, IDENTITY.md, AGENTS.md    │
│  - Kỹ năng bán hàng chuyên sâu: Skill sales-advisor (SKILL.md)         │
│  - Quản lý kênh chat: Telegram Polling, Zalo Userbot                   │
│  - Cầu nối công cụ: Giao thức MCP (Model Context Protocol)             │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │ (Gọi Tools qua MCP / HTTP)
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│  KHỐI 2: SALES DEMO SERVICE (FastAPI - Port 8000)                      │
│  - 6 Công cụ nghiệp vụ thực tế (Tools):                                 │
│    1. search_products     : Lọc sản phẩm theo ngân sách, RAM, OS, nhu cầu│
│    2. get_product_details : Xem thông số kỹ thuật chi tiết của SKU      │
│    3. check_inventory     : Kiểm tra tồn kho thời gian thực             │
│    4. create_lead         : Ghi nhận số điện thoại khi khách đồng ý     │
│    5. handoff_to_human    : Tạo phiếu chuyển giao sales + Bắn cảnh báo  │
│    6. get_policy_answer   : Tra cứu chính sách bảo hành, đổi trả, VAT   │
│  - Database: SQLite (sales_agent.db) lưu Lead, Vé Handoff, Audit Logs │
│  - Webhook Facebook Messenger (/api/webhooks/messenger)                │
│  - Trình tạo mã QR đăng nhập Zalo (/zalo)                              │
│  - Giao diện Web Simulator test trực tiếp (/index.html)                │
│  - Hệ thống thông báo Telegram Alert tới quản lý sales                 │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Cấu trúc thư mục dự án

```
ApplyOpenclaw/
├── .env                         # File cấu hình biến môi trường (Tokens, API URLs)
├── .env.example                 # File mẫu cấu hình biến môi trường
├── AGENTS.md                    # Quy trình xử lý hội thoại & checklist bắt buộc cho Agent
├── IDENTITY.md                  # Nhận diện của Agent (Tên: Mèo Con, biểu tượng 👨‍💻)
├── SOUL.md                      # Tính cách, tông giọng tự nhiên, chuẩn hiển thị 2 dòng
├── requirements.txt             # Danh sách thư viện Python cần thiết
├── sales_agent.db               # Cơ sở dữ liệu SQLite lưu Lead & Vé Handoff
├── sales_api/                   # Module backend FastAPI
│   ├── main.py                  # API endpoints, Webhooks, Router
│   ├── mcp_server.py            # Máy chủ MCP kết nối công cụ với OpenClaw
│   ├── catalog.py               # Xử lý tìm kiếm và tra cứu sản phẩm
│   ├── inventory.py             # Xử lý tra cứu & điều chỉnh tồn kho
│   ├── leads.py                 # Lưu trữ và kiểm tra Consent khách hàng
│   ├── handoffs.py              # Xử lý chuyển giao ca và phân loại ticket
│   ├── notifications.py         # Gửi thông báo Telegram Alert tới quản lý
│   ├── zalo.py                  # Điều khiển tiến trình QR login Zalo qua OpenClaw
│   └── static/                  # Giao diện Web Simulator & Zalo QR Login (Build output từ frontend/)
│       ├── index.html           # Web Chat Simulator & Admin Dashboard (Linear style)
│       └── zalo.html            # Trang quét mã QR Zalo
├── frontend/                    # Ứng dụng Next.js + Tailwind CSS + shadcn/ui + Lucide
│   ├── src/                     # Source code App Router, Components, Types, API client
│   └── package.json             # Scripts dev (npm run dev) và build & sync (npm run build:sync)
├── data/                        # Dữ liệu mẫu sản phẩm & tồn kho
│   ├── products.json            # Danh mục 12+ mẫu laptop thực tế
│   ├── inventory.json           # Dữ liệu tồn kho theo SKU
│   └── policies.md              # Dữ liệu chính sách bảo hành, đổi trả, VAT
├── skills/                      # Kỹ năng nạp vào OpenClaw
│   └── sales-advisor/           # Dạy Agent khi nào và cách gọi từng tool
│       └── SKILL.md
└── tests/                       # Bộ kiểm thử tự động
    ├── test_api.py              # Kiểm thử 8 chức năng API cốt lõi
    └── test_conversations.md    # 15 kịch bản hội thoại mẫu kiểm thử đa kênh
```

---

## 3. Hướng dẫn cài đặt & Cấu hình OpenClaw

OpenClaw đóng vai trò là Gateway AI đa kênh. Có thể chạy OpenClaw thông qua Docker Container hoặc cài trực tiếp trên máy chủ.

### Cách 1: Sử dụng Docker Container (Khuyên dùng)
```bash
# Khởi động container OpenClaw
docker start openclaw-cont

# Kiểm tra trạng thái Gateway, kênh kết nối và model AI
docker exec openclaw-cont openclaw status
```

### File cấu hình OpenClaw (`/root/.openclaw/openclaw.json`):
```json
{
  "agents": {
    "defaults": {
      "workspace": "/root/.openclaw/workspace",
      "model": {
        "primary": "your-model",
        "fallbacks": ["your-fallback-model"]
      }
    }
  },
  "gateway": {
    "port": 18789,
    "bind": "loopback"
  },
  "channels": {
    "telegram": {
      "enabled": true,
      "botToken": "your_bot_token"
    }
  },
  "plugins": {
    "entries": {
      "telegram": { "enabled": true },
      "zalouser": { "enabled": true },
      "google": { "enabled": true },
      "openrouter": { "enabled": true }
    }
  },
  "mcp": {
    "servers": {
      "sales-tools": {
        "command": "python3",
        "args": ["/root/.openclaw/workspace/sales_api/mcp_server.py"]
      }
    }
  }
}
```

---

## 4. Hướng dẫn khởi chạy Sales API Backend

### Bước 1: Chuẩn bị môi trường Python
```bash
# Tạo môi trường ảo venv
python -m venv venv

# Kích hoạt venv:
# Trên Windows:
.\venv\Scripts\activate
# Trên Linux/macOS:
source venv/bin/activate

# Cài đặt các gói phụ thuộc
pip install -r requirements.txt
```

### Bước 2: Thiết lập file môi trường `.env`
Sao chép `.env.example` thành `.env` và điền các tham số:
```ini
# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_SALES_CHAT_ID=your_chat_id

# Sales API Configuration
SALES_API_URL=http://localhost:8000

# Facebook Messenger Configuration
MESSENGER_VERIFY_TOKEN=demotech_verify_token_123
MESSENGER_PAGE_ACCESS_TOKEN=your_facebook_page_access_token_here
```

### Bước 3: Chạy máy chủ Uvicorn
```bash
python -m uvicorn sales_api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Bước 4: Kiểm tra các cổng dịch vụ
- **Tài liệu Swagger API**: `http://localhost:8000/docs`
- **Giao diện Web Simulator**: `http://localhost:8000/`
- **Giao diện đăng nhập Zalo**: `http://localhost:8000/zalo`
- **Xem danh sách Lead**: `http://localhost:8000/admin/leads`
- **Xem danh sách Vé Handoff**: `http://localhost:8000/admin/handoffs`

---

## 5. Kết nối OpenClaw với Sales API qua MCP

OpenClaw giao tiếp với các công cụ bán hàng thông qua chuẩn giao thức **Model Context Protocol (MCP)** tại file `sales_api/mcp_server.py`.

1. **Đồng bộ mã nguồn vào Workspace OpenClaw**:
   Thư mục mã nguồn được liên kết hoặc copy vào `/root/.openclaw/workspace/` (gồm `sales_api/`, `data/`, `SOUL.md`, `AGENTS.md`, `skills/`).
2. **Cơ chế gọi dự phòng (Fallback Resilience)**:
   - `mcp_server.py` ưu tiên gọi sang endpoint HTTP của FastAPI (`http://host.docker.internal:8000` hoặc `http://localhost:8000`).
   - Nếu Sales API chưa khởi động hoặc gặp sự cố mạng, `mcp_server.py` tự động kích hoạt logic cục bộ (Direct Python invocation), đảm bảo Agent không bao giờ bị gián đoạn.

---

## 6. Hướng dẫn thiết lập từng kênh tương tác

### Kênh 1: Telegram Bot (Không cần IP công khai)
- **Cơ chế**: Sử dụng cơ chế Long-polling qua Telegram Bot API (chạy được cả ở localhost, không cần mở port mạng).
- **Cách tạo Bot**:
  1. Mở Telegram, nhắn tin cho **`@BotFather`**, gõ `/newbot`.
  2. Đặt tên và username cho bot -> Nhận chuỗi `botToken`.
  3. Lấy Chat ID của quản lý: Nhắn tin cho **`@userinfobot`** để lấy `Id` số của bạn.
  4. Điền `botToken` vào `openclaw.json` (phần `channels.telegram`) và file `.env`.
  5. Khởi động lại OpenClaw Gateway. Chat trực tiếp với bot để kiểm tra.

### Kênh 2: Zalo cá nhân (Quét mã QR qua OpenClaw)
- **Cơ chế**: Sử dụng plugin `zalouser` tích hợp sẵn trong OpenClaw.
- **Cách kết nối**:
  1. Mở trình duyệt vào trang: `http://localhost:8000/zalo`.
  2. Bấm **Bắt đầu đăng nhập** để hệ thống tạo mã QR.
  3. Mở ứng dụng Zalo trên điện thoại, chọn **Quét mã QR** và xác nhận đăng nhập.
  4. Sau khi quét thành công, tài khoản Zalo cá nhân sẽ tự động phản hồi tin nhắn của bạn bè/khách hàng theo đúng kịch bản của shop.

### Kênh 3: Facebook Messenger Webhook (Yêu cầu HTTPS)
- **Cơ chế**: Meta gửi HTTP POST request đến Webhook của hệ thống mỗi khi có tin nhắn mới tới Fanpage.
- **Cách cài đặt trên Meta for Developers**:
  1. Truy cập [Meta for Developers](https://developers.facebook.com/), tạo App và thêm sản phẩm **Messenger**.
  2. Liên kết Fanpage và tạo **Page Access Token** -> Dán vào `MESSENGER_PAGE_ACCESS_TOKEN` trong `.env`.
  3. Trong phần Webhooks, nhấn **Add Callback URL**:
     - **URL gọi lại**: `https://<ten-mien-hoac-ip-server>/api/webhooks/messenger`
     - **Mã xác minh (Verify Token)**: Điền giá trị `MESSENGER_VERIFY_TOKEN` (mặc định: `demotech_verify_token_123`).
  4. Đăng ký nhận sự kiện (Subscribe): Chọn `messages` và `messaging_postbacks`.
  5. Khi khách nhắn tin vào Fanpage, hệ thống sẽ tiếp nhận, đưa qua OpenClaw Agent và tự động trả lời qua Facebook Graph API.

### Kênh 4: Giao diện Web Simulator
- Truy cập trực tiếp tại `http://localhost:8000/`.
- Hỗ trợ đầy đủ các kịch bản test nhanh:
  * Nhu cầu lập trình Docker / Máy mỏng nhẹ / Đồ họa.
  * Mặc cả deal giá -> Hệ thống kích hoạt quy trình hỏi thông tin liên hệ và tạo vé Handoff chờ duyệt.
  * Xem trực tiếp trạng thái kho, danh sách Lead và Handoff ticket ngay trên giao diện.

---

## 7. Hướng dẫn đóng gói & Đẩy lên Server (Server Deployment)

Khi triển khai lên máy chủ VPS / Cloud (Ubuntu 22.04 LTS hoặc 24.04 LTS), toàn bộ hệ thống được đóng gói thành **Docker Compose**.

### Cấu trúc triển khai đề xuất trên Server:

```
                  ┌───────────────────────────────────────────┐
                  │                 SERVER                    │
                  │                                           │
  Internet ───> Nginx / Reverse Proxy (SSL Certbot HTTPS)    │
                       │               │                      │
                       │:8000          │:18789                │
                       ▼               ▼                      │
             ┌────────────────┐ ┌───────────────────────────┐ │
             │ Sales API App  │ │ OpenClaw Gateway Service  │ │
             │ (FastAPI)      │ │ (Container openclaw-cont) │ │
             └───────┬────────┘ └─────────────┬─────────────┘ │
                     │                        │               │
                     └─────── MCP Tools ──────┘               │
                                                              │
                  └───────────────────────────────────────────┘
```

### Các bước đóng gói & chuẩn bị đưa lên Server:
1. **Gom mã nguồn**:
   Đảm bảo toàn bộ thư mục dự án gồm các file cấu hình, mã nguồn `sales_api/`, `data/`, `skills/` và các file tài liệu nhân cách (`SOUL.md`, `AGENTS.md`) được đẩy lên Git repo hoặc nén thành file archive.
2. **Cài đặt môi trường trên Server**:
   ```bash
   # Cài Docker & Docker Compose trên Ubuntu
   sudo apt update && sudo apt install -y docker.io docker-compose git
   sudo systemctl enable --now docker
   ```
3. **Cấu hình Nginx & Chứng chỉ SSL (HTTPS)**:
   Để phục vụ Webhook Facebook Messenger, máy chủ cần cấu hình Nginx trỏ cổng `8000` và kích hoạt SSL miễn phí qua Certbot:
   ```bash
   sudo apt install -y certbot python3-certbot-nginx
   sudo certbot --nginx -d yourdomain.com
   ```
   *(Trường hợp máy chủ chưa có Domain/IP tĩnh, có thể sử dụng Cloudflare Tunnel để tạo đường dẫn HTTPS miễn phí ra Internet).*

---

## 8. Chạy kiểm thử tự động (Automated Testing)

Chạy bộ kiểm thử để đảm bảo 100% các công cụ nghiệp vụ và quy tắc an toàn hoạt động chính xác trước khi đưa lên môi trường thật:

```bash
pytest tests/test_api.py -v
```

**Kết quả kiểm thử đạt chuẩn (8/8 Passed):**
- `test_search_products_budget`: Lọc sản phẩm chính xác theo ngân sách tối đa.
- `test_search_products_os_filter`: Lọc đúng hệ điều hành (macOS / Windows).
- `test_get_product_details`: Xem đầy đủ thông số kỹ thuật của SKU.
- `test_check_inventory`: Kiểm tra tồn kho thời gian thực chính xác.
- `test_create_lead_requires_consent`: Bắt buộc từ chối lưu số điện thoại nếu khách chưa đồng ý (Consent).
- `test_create_lead_success`: Lưu Lead thành công vào SQLite khi có xác nhận.
- `test_handoff_to_human`: Tạo vé chuyển ca Handoff kèm mã vé `TICK-...` và cảnh báo quản lý.
- `test_policy_lookup`: Tra cứu chính xác chính sách bảo hành 24 tháng, 1 đổi 1 và hóa đơn VAT.
