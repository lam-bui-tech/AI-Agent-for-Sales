# Tools — ghi chú môi trường

## Sales API local
- Base URL (Agent chạy trong Docker container): `http://host.docker.internal:8000`
- Base URL (Test trực tiếp trên máy host Windows): `http://localhost:8000`
- Khi triển khai qua kênh cần webhook công khai (vd. sau này Zalo OA), dùng `ngrok http 8000` hoặc Cloudflare Tunnel để lấy URL public tạm thời — **không cần cho Telegram (dùng polling) hoặc Zalo cá nhân test nội bộ.**

## Endpoint và cách gọi

| Tool | Method | Endpoint | Tham số chính |
|---|---|---|---|
| `search_products` | GET | `/search_products` | `query`, `max_price` (tuỳ chọn) |
| `get_product_details` | GET | `/get_product_details` | `sku` |
| `check_inventory` | GET | `/check_inventory` | `sku` |
| `create_lead` | POST | `/create_lead` | `name`, `phone`, `channel`, `need`, `sku` (tuỳ chọn) |
| `handoff_to_human` | POST | `/handoff_to_human` | `reason`, `summary`, `channel`, `contact` (tuỳ chọn) |

## Quy tắc gọi tool
- Luôn gọi tool trước khi trả lời bất kỳ con số cụ thể nào (giá, tồn kho, mã sản phẩm).
- Nếu API trả lỗi (timeout, 5xx) → coi như "không xác minh được", báo cho khách, không đoán kết quả.
- `create_lead` chỉ gọi sau khi khách xác nhận đồng ý để lại thông tin.
