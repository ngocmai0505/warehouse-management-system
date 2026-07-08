# Requirements / Yêu cầu dự án

## English

### Objective
Build a warehouse management system for e-commerce operations, covering product catalog, suppliers, warehouse transactions, inventory visibility, orders, stock counts, reporting, and barcode/QR lookup.

### Technology Requirements
- Frontend: React + TypeScript + Vite.
- Backend: Python FastAPI.
- Database: SQLite for demo, replaceable by PostgreSQL/MySQL for production.
- Packaging: Docker image `warehouse-management-system:v1.0` and Docker Compose.
- UI language: English and Vietnamese with a VI/EN switch.
- Encoding: Vietnamese text must render correctly in browser and generated files.
- UX/UI: modern e-commerce operations style, professional font, responsive layout, product card grid, subtle transitions/animations, no outdated split marketing login page.

### Functional Requirements
1. Authentication with demo roles.
2. Product management: create, edit, deactivate/delete; SKU, category, brand, unit, prices, barcode/QR, lot number, expiry date, image, minimum stock, location, status.
3. Supplier management: create, edit, deactivate/delete.
4. Order management: create, edit, cancel/delete; channel, customer, status, total amount, note.
5. Stock receipt: create confirmed inbound documents and increase product stock.
6. Stock issue: create confirmed outbound documents, validate available stock, and decrease product stock.
7. Inventory: read-only stock view derived from products plus warehouse transactions; direct deletion is not allowed.
8. Stock count: record actual quantity, variance, and update stock after confirmation.
9. Dashboard: operational KPIs, low-stock alerts, and recent activity.
10. Reports: summarize receipts, issues, stock count variance, and export CSV.
11. Barcode/QR lookup by SKU or barcode.
12. Responsive warehouse workflow for both laptop operations and mobile barcode scanning.

### Acceptance Criteria
- Docker image `warehouse-management-system:v1.0` builds successfully.
- Container serves the app at http://localhost:8000.
- API health, login, dashboard, products, and report export endpoints work.
- Login form is empty by default and does not display demo account hints.
- Product demo data displays Vietnamese accents correctly.
- UI language switch works without page reload.

## Tiếng Việt

### Mục tiêu
Xây dựng hệ thống quản lý kho hàng cho vận hành thương mại điện tử, bao gồm danh mục sản phẩm, nhà cung cấp, giao dịch kho, tồn kho, đơn hàng, kiểm kê, báo cáo và barcode/QR.

### Yêu cầu công nghệ
- Frontend: React + TypeScript + Vite.
- Backend: Python FastAPI.
- Database: SQLite cho demo, có thể thay bằng PostgreSQL/MySQL khi production.
- Đóng gói: Docker image `warehouse-management-system:v1.0` và Docker Compose.
- Ngôn ngữ: Anh/Việt, chuyển bằng nút VI/EN.
- Encoding: tiếng Việt phải hiển thị đúng dấu trên browser và trong tài liệu.
- UX/UI: phong cách vận hành thương mại điện tử, font chuyên nghiệp, responsive, grid card cho sản phẩm, animation nhẹ, không dùng login split marketing kiểu cũ.

### Yêu cầu chức năng
1. Đăng nhập theo vai trò demo.
2. Quản lý sản phẩm: thêm, sửa, xóa/ngừng kinh doanh; quản lý SKU, danh mục, thương hiệu, đơn vị, giá, barcode/QR, lô hàng, hạn sử dụng, hình ảnh, ngưỡng tồn, vị trí, trạng thái.
3. Quản lý nhà cung cấp: thêm, sửa, xóa/ngừng hợp tác.
4. Quản lý đơn hàng: thêm, sửa, xóa/hủy; quản lý kênh bán, khách hàng, trạng thái, tổng tiền, ghi chú.
5. Nhập kho: tạo phiếu đã xác nhận và cộng tồn kho.
6. Xuất kho: tạo phiếu đã xác nhận, kiểm tra tồn khả dụng và trừ tồn kho.
7. Tồn kho: chỉ xem dữ liệu phát sinh từ sản phẩm và giao dịch kho; không cho xóa trực tiếp.
8. Kiểm kê: ghi nhận số lượng thực tế, chênh lệch và cập nhật tồn sau xác nhận.
9. Dashboard: KPI vận hành, cảnh báo tồn kho và hoạt động gần đây.
10. Báo cáo: tổng hợp nhập kho, xuất kho, chênh lệch kiểm kê và xuất CSV.
11. Tra cứu barcode/QR theo SKU hoặc mã vạch.
12. Giao diện responsive cho thao tác trên laptop và quét mã bằng điện thoại.

### Tiêu chí nghiệm thu
- Docker image `warehouse-management-system:v1.0` build thành công.
- Container phục vụ ứng dụng tại http://localhost:8000.
- API health, login, dashboard, products và export report hoạt động.
- Form đăng nhập không tự điền và không hiển thị gợi ý tài khoản demo.
- Dữ liệu demo sản phẩm hiển thị tiếng Việt có dấu.
- Chuyển ngôn ngữ không cần reload trang.
