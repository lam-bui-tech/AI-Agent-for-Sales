# DemoTech Sales Copilot Context

Hệ thống AI Sales Agent đa kênh hỗ trợ tư vấn thiết bị công nghệ, tra cứu catalog/tồn kho có kiểm soát, thu thập lead bán hàng có đồng thuận và chuyển tiếp nhân viên bán hàng khi vượt thẩm quyền.

## Language

**Product**:
Một thiết bị công nghệ (laptop hoặc phụ kiện) cụ thể có mã định danh, thông số kỹ thuật và giá niêm yết trong hệ thống.
_Avoid_: Item, hàng hóa, thiết bị chung

**SKU**:
Mã định danh duy nhất (Stock Keeping Unit) cho từng cấu hình sản phẩm cụ thể trong catalog (ví dụ: `LAP-001`).
_Avoid_: Mã hàng, serial number, barcode

**Inventory**:
Dữ liệu trạng thái tồn kho thời gian thực của một SKU bao gồm số lượng khả dụng và thời điểm cập nhật.
_Avoid_: Stockpile, kho hàng, số lượng dự kiến

**Qualification**:
Quá trình agent hỏi 1–3 câu ngắn gọn để làm rõ ngân sách, mục đích sử dụng và các tiêu chí ưu tiên của khách trước khi lọc danh mục.
_Avoid_: Khảo sát, phỏng vấn, thẩm vấn

**Lead**:
Hồ sơ nhu cầu khách hàng có cấu trúc bao gồm kênh liên hệ, thông tin liên lạc tối thiểu, sản phẩm quan tâm và sự đồng ý cho phép liên hệ.
_Avoid_: Prospect, contact, khách tiềm năng chưa xác nhận

**Consent**:
Sự đồng thuận rõ ràng, chủ động từ phía khách hàng cho phép cửa hàng lưu số điện thoại và nhân viên liên hệ tư vấn.
_Avoid_: Opt-in ngầm, mặc định cho phép

**Handoff Ticket**:
Bản ghi chuyển giao cuộc hội thoại sang nhân viên bán hàng kèm phân loại lý do, mức độ ưu tiên và bản tóm tắt ngắn gọn toàn bộ ngữ cảnh.
_Avoid_: Escalation đơn thuần, complaint ticket, transfer call
