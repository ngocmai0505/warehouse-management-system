# Hệ Thống Quản Lý Kho Hàng

## 1. Giới Thiệu Dự Án

**Hệ Thống Quản Lý Kho Hàng** là ứng dụng web hỗ trợ quản lý kho cho mô hình thương mại điện tử. Hệ thống giúp doanh nghiệp theo dõi sản phẩm, lô hàng, hạn sử dụng, tồn kho, nhà cung cấp, đơn hàng, phiếu nhập kho, phiếu xuất kho, kiểm kê và báo cáo doanh thu/vận hành kho.

Ứng dụng được xây dựng theo mô hình full-stack, gồm giao diện web React và backend FastAPI. Dữ liệu được lưu trong SQLite và được đóng gói bằng Docker để dễ cài đặt, chạy thử nghiệm và triển khai trên nhiều môi trường khác nhau.

## 2. Mục Tiêu Dự Án

- Xây dựng một hệ thống quản lý kho hàng trực quan, dễ sử dụng cho doanh nghiệp vừa và nhỏ.
- Hỗ trợ nghiệp vụ kho thương mại điện tử: nhập kho, xuất kho theo đơn hàng, quản lý lô hàng, hạn sử dụng và barcode/QR.
- Giảm sai sót khi theo dõi tồn kho bằng cách tự động cộng/trừ tồn sau mỗi giao dịch kho.
- Cung cấp báo cáo tổng quan về nhập kho, xuất kho, kiểm kê và doanh thu.
- Phân quyền người dùng theo vai trò: quản trị viên, quản lý kho và nhân viên kho.
- Đóng gói ứng dụng bằng Docker để đảm bảo chạy ổn định trên các máy khác nhau.

## 3. Chức Năng Chính

### 3.1 Đăng Nhập Và Phân Quyền

- Đăng nhập bằng tài khoản và mật khẩu.
- Hỗ trợ 3 vai trò:
  - Quản trị viên.
  - Quản lý kho.
  - Nhân viên kho.
- Giao diện hiển thị chức năng theo quyền của từng vai trò.
- Hỗ trợ chuyển đổi ngôn ngữ Việt/Anh.

### 3.2 Tổng Quan

- Hiển thị tổng số sản phẩm đang hoạt động.
- Hiển thị tổng tồn kho hiện tại.
- Hiển thị tổng đơn hàng.
- Hiển thị cảnh báo sản phẩm sắp hết hàng.
- Hiển thị tổng nhập kho và xuất kho.

### 3.3 Quản Lý Sản Phẩm

- Thêm, sửa và ngừng kinh doanh sản phẩm.
- Quản lý các thông tin:
  - SKU.
  - Tên sản phẩm.
  - Danh mục.
  - Thương hiệu.
  - Đơn vị tính.
  - Giá nhập.
  - Giá bán.
  - Barcode/QR.
  - Lô hàng.
  - Hạn sử dụng.
  - Vị trí lưu kho.
  - Tồn kho tối thiểu.
  - Hình ảnh sản phẩm.
- Tìm kiếm sản phẩm theo SKU, tên, danh mục, thương hiệu, barcode và lô hàng.

### 3.4 Quản Lý Nhà Cung Cấp

- Thêm, sửa và ngừng hợp tác nhà cung cấp.
- Quản lý thông tin liên hệ, địa chỉ, email, số điện thoại và ghi chú.
- Tìm kiếm nhà cung cấp.

### 3.5 Quản Lý Đơn Hàng

- Quản trị viên có thể thêm, sửa, xóa đơn hàng.
- Quản lý kho có thể xem và tìm kiếm đơn hàng để phục vụ việc xuất kho.
- Đơn hàng có các thông tin:
  - Mã đơn.
  - Ngày đặt hàng.
  - Tên khách hàng.
  - Kênh bán hàng.
  - Sản phẩm và số lượng mua.
  - Giá trị đơn hàng.
  - Trạng thái đơn hàng.
- Hỗ trợ tìm kiếm đơn hàng theo mã đơn, khách hàng, sản phẩm, ngày, kênh bán hàng và trạng thái.

### 3.6 Nhập Kho

- Tạo phiếu nhập kho theo từng sản phẩm.
- Gắn phiếu nhập với nhà cung cấp.
- Khi xác nhận phiếu nhập, hệ thống tự động cộng số lượng vào tồn kho.
- Phiếu nhập hiển thị tên sản phẩm, mã lô hàng và số lượng nhập.
- Ngày nhập kho được điều chỉnh phù hợp với tháng của lô hàng.
- Hỗ trợ tìm kiếm lịch sử nhập kho.

### 3.7 Xuất Kho

- Tạo phiếu xuất kho theo đơn hàng.
- Kiểm tra số lượng tồn trước khi xuất kho.
- Nếu tồn kho không đủ, hệ thống hiển thị lỗi và không cho xuất.
- Khi xác nhận phiếu xuất, hệ thống tự động trừ số lượng kho.
- Cập nhật trạng thái đơn hàng thành đã xuất kho.
- Hỗ trợ tìm kiếm phiếu xuất theo mã phiếu, ngày xuất, mã đơn, sản phẩm và trạng thái.

### 3.8 Tồn Kho

- Theo dõi tồn kho hiện tại của từng sản phẩm.
- Hiển thị vị trí lưu kho, lô hàng và hạn sử dụng.
- Cảnh báo sản phẩm hết hàng hoặc sắp hết hàng dựa trên tồn kho tối thiểu.
- Tồn kho là dữ liệu phát sinh từ sản phẩm, phiếu nhập, phiếu xuất và kiểm kê.

### 3.9 Kiểm Kê

- Tạo phiếu kiểm kê cho sản phẩm.
- Lấy số lượng hệ thống tại thời điểm kiểm kê.
- Nhập số lượng thực tế.
- Tính chênh lệch theo công thức:

```text
Chênh lệch = Số lượng hệ thống - Số lượng thực tế
```

- Nếu số lượng hệ thống thấp hơn số lượng thực tế thì chênh lệch âm.
- Nếu số lượng hệ thống cao hơn số lượng thực tế thì chênh lệch dương.
- Sau khi kiểm kê, tồn kho được cập nhật theo số lượng thực tế.

### 3.10 Báo Cáo

- Báo cáo nhập kho.
- Báo cáo xuất kho.
- Báo cáo kiểm kê.
- Báo cáo doanh thu theo ngày.
- Biểu đồ tổng quan nhập/xuất/kiểm kê.
- Xuất báo cáo dạng CSV.

### 3.11 Barcode/QR

- Tìm kiếm sản phẩm theo SKU hoặc barcode.
- Hỗ trợ mở camera để quét barcode/QR trên thiết bị có camera.
- Hiển thị thông tin sản phẩm sau khi quét:
  - Tên sản phẩm.
  - SKU.
  - Barcode.
  - Lô hàng.
  - Hạn sử dụng.
  - Tồn kho.
  - Vị trí lưu kho.

### 3.12 Hoạt Động Gần Đây

- Ghi nhận các thao tác quan trọng trong hệ thống.
- Hiển thị thông báo hoạt động chưa đọc.
- Cho phép đánh dấu đã đọc từng hoạt động hoặc tất cả hoạt động.
- Quản trị viên có thể xóa lịch sử hoạt động.

## 4. Phân Quyền Người Dùng

| Chức năng | Quản trị viên | Quản lý kho | Nhân viên kho |
| --- | --- | --- | --- |
| Tổng quan | Xem | Xem | Xem |
| Sản phẩm | Xem, thêm, sửa, ngừng kinh doanh | Xem, thêm, sửa, ngừng kinh doanh | Không xem |
| Nhà cung cấp | Xem, thêm, sửa, ngừng hợp tác | Xem, thêm, sửa, ngừng hợp tác | Không xem |
| Đơn hàng | Xem, tìm kiếm, thêm, sửa, xóa | Xem, tìm kiếm | Không xem |
| Nhập kho | Xem, tìm kiếm, tạo phiếu | Xem, tìm kiếm, tạo phiếu | Xem, tìm kiếm, tạo phiếu |
| Xuất kho | Xem, tìm kiếm, tạo phiếu | Xem, tìm kiếm, tạo phiếu | Xem, tìm kiếm, tạo phiếu |
| Tồn kho | Xem | Xem | Xem |
| Kiểm kê | Xem, tạo kiểm kê | Xem, tạo kiểm kê | Không xem |
| Báo cáo | Xem, xuất báo cáo | Xem, xuất báo cáo | Không xem |
| Barcode/QR | Quét/tìm sản phẩm | Quét/tìm sản phẩm | Quét/tìm sản phẩm |
| Hoạt động | Xem, đánh dấu đọc, xóa lịch sử | Xem, đánh dấu đọc | Xem, đánh dấu đọc |

## 5. Tài Khoản Demo

| Vai trò | Tài khoản | Mật khẩu |
| --- | --- | --- |
| Quản trị viên | `admin` | `admin123` |
| Quản lý kho | `warehouse` | `warehouse123` |
| Nhân viên kho | `staff` | `staff123` |

## 6. Công Nghệ Sử Dụng

### 6.1 Frontend

- **React**: xây dựng giao diện người dùng theo component.
- **TypeScript**: tăng tính an toàn kiểu dữ liệu, giúp mã nguồn dễ bảo trì hơn.
- **Vite**: công cụ build frontend nhanh, phù hợp cho phát triển React.
- **lucide-react**: thư viện icon giúp giao diện trực quan và đồng bộ.
- **CSS responsive**: tối ưu hiển thị trên laptop và điện thoại.

### 6.2 Backend

- **Python**: ngôn ngữ lập trình chính cho phần server.
- **FastAPI**: xây dựng REST API nhanh, gọn, có sẵn OpenAPI docs.
- **Uvicorn**: ASGI server dùng để chạy ứng dụng FastAPI.
- **Pydantic**: kiểm tra và validate dữ liệu request.

### 6.3 Cơ Sở Dữ Liệu

- **SQLite**: cơ sở dữ liệu nhẹ, phù hợp cho demo, học tập và triển khai cục bộ.
- Dữ liệu được lưu trong Docker volume tại `/app/data` để không bị mất khi container khởi động lại.
- Khi cần mở rộng thành sản phẩm thực tế, có thể thay SQLite bằng PostgreSQL hoặc MySQL.

### 6.4 Triển Khai

- **Docker**: đóng gói frontend, backend và runtime vào một image.
- **Docker Compose**: cấu hình build, run container, map port và volume dữ liệu.

## 7. Mục Đích Sử Dụng Docker Trong Dự Án

Docker được sử dụng trong dự án này nhằm:

- **Đóng gói môi trường chạy ứng dụng**: tất cả thành phần cần thiết như Python, FastAPI, Node.js build frontend và static files được đóng gói trong image.
- **Đảm bảo tính nhất quán giữa các máy**: ứng dụng chạy giống nhau trên máy lập trình, máy chấm điểm, máy demo hoặc server.
- **Giảm lỗi cài đặt thủ công**: người dùng không cần tự cài Python, Node.js, npm package hay cấu hình môi trường phức tạp.
- **Dễ khởi động ứng dụng**: chỉ cần sử dụng Docker Compose để build và run.
- **Quản lý dữ liệu bằng volume**: database SQLite được lưu trong Docker volume `warehouse-data`, giúp dữ liệu vẫn còn sau khi container được recreate.
- **Tách biệt ứng dụng khỏi hệ điều hành**: tránh xung đột phiên bản thư viện giữa các dự án khác nhau.
- **Phù hợp demo và bảo vệ môi trường máy tính**: dễ chạy, dừng, xóa container mà không ảnh hưởng nhiều đến hệ thống chính.

## 8. Kiến Trúc Docker Của Dự Án

Dự án sử dụng Dockerfile multi-stage:

1. **Stage frontend-builder**
   - Sử dụng image `node:22-alpine`.
   - Cài đặt package frontend.
   - Build ứng dụng React/Vite thành static files.

2. **Stage runtime**
   - Sử dụng image `python:3.12-slim`.
   - Cài đặt thư viện backend từ `backend/requirements.txt`.
   - Copy source backend vào `/app/app`.
   - Copy frontend đã build vào `/app/static`.
   - Chạy FastAPI bằng Uvicorn tại port `8000`.

Docker Compose cấu hình:

- Image: `warehouse-management-system:v1.0`
- Container: `warehouse-management-system`
- Port: `8000:8000`
- Volume: `warehouse-data:/app/data`
- Restart policy: `unless-stopped`

## 9. Hướng Dẫn Chạy Dự Án

### 9.1 Yêu Cầu

- Đã cài Docker Desktop.
- Docker Desktop đang chạy.

### 9.2 Build Và Chạy Ứng Dụng

```bash
docker compose up -d --build
```

Sau khi chạy thành công:

- Ứng dụng web: http://localhost:8000
- API docs: http://localhost:8000/docs

### 9.3 Dừng Ứng Dụng

```bash
docker compose down
```

### 9.4 Xem Log

```bash
docker compose logs -f
```

## 10. Cấu Trúc Thư Mục

```text
warehouse-management-system/
├── backend/
│   ├── app/
│   │   └── main.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   └── styles.css
│   ├── index.html
│   ├── package.json
│   └── package-lock.json
├── docs/
│   ├── requirements.md
│   └── system-design-diagrams.md
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
└── README.md
```

## 11. Tài Liệu Thiết Kế

Tài liệu sơ đồ hệ thống nằm tại:

```text
docs/system-design-diagrams.md
```

File này bao gồm:

- ERD.
- Data Dictionary.
- Use Case Diagram.
- DFD mức 0 và mức 1.
- Activity Diagram.
- Kiến trúc hệ thống.
- Component Diagram.
- Ma trận phân quyền.
