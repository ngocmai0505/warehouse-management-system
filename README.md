# Goods Management System

## English

Goods Management System is a full-stack application for managing products, warehouse stock, suppliers, orders, stock counts, and operational reports for e-commerce teams.

### Technology Stack
- Frontend: React, TypeScript, Vite, lucide-react.
- Backend: Python FastAPI.
- Database: SQLite for demo; can be replaced by PostgreSQL/MySQL in production.
- Deployment: Docker multi-stage image and Docker Compose.
- UI: bilingual English/Vietnamese, modern responsive layout, card-based product view, subtle animation.

### Key Features
- Clean login screen with VI/EN language switch.
- Dashboard for products, stock, orders, low-stock alerts, and monthly inbound/outbound quantities.
- Product CRUD: create, edit, and deactivate/delete from the management view.
- Supplier CRUD and order CRUD.
- Stock receipts increase inventory after confirmation.
- Stock issues validate available stock before decreasing inventory.
- Inventory is derived from products and warehouse transactions, so it is not directly deleted.
- Reports are generated from stock receipts, stock issues, and stock counts, with CSV export.
- Barcode/QR lookup by SKU or barcode.

### Run With Docker
```bash
docker compose up -d --build
```

Application: http://localhost:8000  
API docs: http://localhost:8000/docs

### Demo Accounts
| Username | Password | Role |
| --- | --- | --- |
| `admin` | `admin123` | Admin |
| `warehouse` | `warehouse123` | Warehouse Manager |
| `staff` | `staff123` | Warehouse Staff |

## Tiếng Việt

Goods Management System là ứng dụng full-stack dùng để quản lý hàng hóa, kho, nhà cung cấp, đơn hàng, kiểm kê và báo cáo cho vận hành thương mại điện tử.

### Công nghệ
- Frontend: React, TypeScript, Vite, lucide-react.
- Backend: Python FastAPI.
- Database: SQLite cho demo; có thể thay bằng PostgreSQL/MySQL khi lên production.
- Triển khai: Docker multi-stage image và Docker Compose.
- Giao diện: song ngữ Anh/Việt, responsive, hiện đại, có animation nhẹ.

### Chức năng chính
- Màn hình đăng nhập gọn gàng, không tự điền tài khoản.
- Dashboard tổng quan sản phẩm, tồn kho, đơn hàng, cảnh báo hàng sắp hết và nhập/xuất trong tháng.
- Quản lý sản phẩm: thêm, sửa, xóa/ngừng kinh doanh.
- Quản lý nhà cung cấp và đơn hàng: thêm, sửa, xóa/hủy.
- Nhập kho tự động cộng tồn; xuất kho kiểm tra số lượng trước khi trừ tồn.
- Tồn kho là dữ liệu phát sinh từ sản phẩm và giao dịch kho, không xóa trực tiếp.
- Báo cáo lấy dữ liệu từ phiếu nhập, phiếu xuất và kiểm kê; có nút xuất CSV.
- Tra cứu barcode/QR theo SKU hoặc mã vạch.

### Chạy bằng Docker
```bash
docker compose up -d --build
```

Ứng dụng: http://localhost:8000  
Tài liệu API: http://localhost:8000/docs

### Tài khoản demo
| Tài khoản | Mật khẩu | Vai trò |
| --- | --- | --- |
| `admin` | `admin123` | Admin |
| `warehouse` | `warehouse123` | Quản lý kho |
| `staff` | `staff123` | Nhân viên kho |
