# Tools — Ghi chú môi trường ThueDo.net

## Sales API local
- Base URL (Agent chạy trong Docker container): `http://host.docker.internal:8000`
- Base URL (Test trực tiếp trên máy host Windows): `http://localhost:8000`
- Khi triển khai qua kênh cần webhook công khai (Zalo OA, Webchat), dùng `ngrok http 8000` hoặc Cloudflare Tunnel để lấy URL public tạm thời — **không cần cho Telegram (dùng polling).**

## Endpoint và cách gọi

| Tool | Method | Endpoint | Tham số chính |
|---|---|---|---|
| `search_products` | GET | `/search_products` | `query`, `max_price_vnd`, `min_branches`, `limit` |
| `get_product_details` | GET | `/get_product_details` | `sku` (ví dụ: `PKG-STARTER`, `PKG-PRO`, `PKG-PREMIUM`) |
| `calculate_pricing` | GET / POST | `/calculate_pricing` | `sku`, `months` (3 tháng 0%, 6 tháng giảm 5%, 12 tháng giảm 10%) |
| `compare_packages` | GET / POST | `/compare_packages` | `sku1`, `sku2` (So sánh tính năng & quy mô định dạng 2 dòng) |
| `register_trial` | POST | `/register_trial` | `shop_name`, `fashion_type`, `name`, `phone`, `branches_count`, `preferred_contact_method` |
| `create_lead` | POST | `/create_lead` | `name`, `phone`, `channel`, `shop_name`, `fashion_type`, `branches_count`, `status` |
| `handoff_to_human` | POST | `/handoff_to_human` | `reason` (`discount_pending`, `migration`, `hardware_setup`, `live_demo`), `summary`, `channel`, `contact` |

## Quy tắc gọi tool
- Luôn gọi tool trước khi trả lời bất kỳ con số cụ thể nào (giá gói, tính năng, số tiền chiết khấu).
- Nếu API trả lỗi (timeout, 5xx) → coi như "không xác minh được", báo cho khách, không đoán kết quả.
- `register_trial` gọi ngay khi khách đồng ý kích hoạt trải nghiệm 15 ngày miễn phí.
- `create_lead` chỉ gọi sau khi khách xác nhận đồng ý để lại thông tin.
