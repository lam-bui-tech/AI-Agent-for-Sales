# ThueDo.net Sales Copilot Context

Hệ thống AI Sales Agent đa kênh hỗ trợ tư vấn giải pháp phần mềm quản lý cho thuê trang phục ThueDo.net (thuộc Digital Innovation - Dion), tra cứu gói cước, tính toán chi phí chu kỳ, so sánh tính năng nghiệp vụ thuê – cọc – trả, tiếp nhận đăng ký dùng thử miễn phí 15 ngày và chuyển tiếp chuyên viên kỹ thuật khi cần.

## Domain Language

**Package (Gói phần mềm)**:
Một gói cước phần mềm SaaS có mã SKU, cấu hình giới hạn (chi nhánh, kho, tài khoản nhân viên), danh mục tính năng và giá niêm yết theo tháng.
_Avoid_: Sản phẩm bán lẻ, thiết bị phần cứng, máy móc

**SKU**:
Mã định danh duy nhất cho từng gói giải pháp trong hệ thống (ví dụ: `PKG-STARTER`, `PKG-PRO`, `PKG-PREMIUM`).
_Avoid_: Mã hàng, serial number, barcode

**Rental Lifecycle (Vòng đời thuê)**:
Nghiệp vụ cốt lõi quản lý xuyên suốt: Nhận đơn -> Ghi nhận cọc -> Theo dõi đồ (đang thuê/đã trả/cần giặt ủi/cần sửa chữa/trễ hạn) -> Trả đồ và hoàn cọc.

**Qualification**:
Quá trình agent hỏi ngắn gọn kết hợp 2 tiêu chí: quy mô chi nhánh/nhân sự và dòng trang phục kinh doanh (áo dài, váy cưới, đồ biểu diễn, dạ hội) trước khi gợi ý gói giải pháp tối ưu.
_Avoid_: Khảo sát, phỏng vấn, tra khảo

**Free Trial (Dùng thử miễn phí)**:
Chương trình cấp tài khoản trải nghiệm thực tế toàn bộ tính năng trên Web và Mobile App (iOS/Android) trong vòng 15 ngày miễn phí.

**Lead**:
Hồ sơ nhu cầu khách hàng có cấu trúc bao gồm Tên chủ shop, Số điện thoại, Tên cửa hàng, Loại hình trang phục, Số lượng chi nhánh và kênh liên hệ mong muốn.

**Handoff Ticket**:
Bản ghi chuyển giao cuộc hội thoại sang nhân viên phụ trách với phân loại lý do rõ ràng: `discount_pending` (xin giảm giá), `migration` (chuyển dữ liệu cũ từ KiotViet/Sapo/Excel), `hardware_setup` (kết nối máy in/mã vạch), `live_demo` (hẹn demo 1-1 qua Meet/UltraViewer), hoặc `complaint`.
