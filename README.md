# Warehouse Management System + TikTok Shop Demo

Hệ thống quản lý kho hàng dành cho demo bán hàng thương mại điện tử. Ứng dụng gồm 2 service độc lập chạy bằng Docker Compose:

- `warehouse-management`: web quản lý kho nội bộ, chạy tại `http://localhost:8000`.
- `marketplace`: web sàn demo theo phong cách TikTok Shop, chạy tại `http://localhost:9000`.

Dữ liệu demo hiện tại dùng bộ sản phẩm **Bbia Official Store** từ file `product-list.csv`.

## Tính Năng Chính

### Web Quản Lý Kho

- Đăng nhập và phân quyền theo vai trò.
- Quản lý sản phẩm: thêm, sửa, ngừng kinh doanh, ảnh sản phẩm, SKU, barcode, lô hàng, hạn sử dụng, vị trí kho.
- Quản lý tồn kho:
  - Xem tồn kho theo SKU/tên sản phẩm.
  - Sửa trực tiếp số lượng tồn kho trong tab `Tồn kho`.
  - Đồng bộ số tồn mới sang TikTok Shop demo realtime.
  - Tự hiển thị trạng thái `An toàn`, `Sắp hết`, `Hết hàng`, `Ngừng kinh doanh`.
- Quản lý đơn hàng:
  - Đơn mới từ TikTok Shop được tạo ở trạng thái `Chờ xử lý`.
  - Đơn đã `Đã xuất kho` hoặc `Hủy đơn` sẽ bị khóa chỉnh sửa.
  - Khi hủy đơn trước khi xuất kho, tồn kho được cộng lại.
- Nhập kho, xuất kho, kiểm kê.
- Tạo phiếu xuất từ đơn hàng: khi chọn đơn, hệ thống tự lấy sản phẩm và số lượng theo đơn.
- Lịch sử xuất kho chỉ ghi nhận khi đơn thật sự được xác nhận `Đã xuất kho`.
- Realtime WebSocket cho đơn mới, cập nhật trạng thái đơn, đồng bộ tồn kho và log hoạt động.
- Báo cáo tổng quan và xuất báo cáo CSV.
- Quét/tìm sản phẩm bằng SKU hoặc barcode.
- Giao diện hỗ trợ tiếng Việt có dấu và tiếng Anh.

### TikTok Shop Demo

- Storefront demo cho **Bbia Official Store**.
- Tìm kiếm sản phẩm.
- Xem sản phẩm, ảnh, giá bán, số tồn khả dụng.
- Thêm giỏ hàng, mua ngay, thanh toán giỏ hàng.
- Chọn số lượng bằng nút `- / +` hoặc nhập trực tiếp.
- Tự disable sản phẩm khi:
  - Tồn kho bằng 0: hiển thị `Hết hàng`.
  - Sản phẩm ngừng kinh doanh: hiển thị `Ngừng kinh doanh`.
- Theo dõi đơn hàng trên sàn:
  - Đơn đang chờ xử lý.
  - Đơn đã xử lý/đã xuất kho.
  - Đơn đã hủy.
- Khách hàng có thể hủy đơn khi đơn chưa xuất kho; thao tác này đồng bộ về web quản lý kho và cộng tồn lại.

## Luồng Đồng Bộ Kho Và Sàn

### 1. Khách Mua Hàng Trên TikTok Shop Demo

1. Khách chọn sản phẩm và số lượng.
2. TikTok Shop demo gọi API về `warehouse-management`.
3. Web quản lý kho tạo đơn hàng mới trạng thái `Chờ xử lý`.
4. Tồn kho sản phẩm bị trừ ngay để tránh bán vượt tồn.
5. Tab `Đơn hàng`, `Tồn kho`, `Sản phẩm` và dữ liệu sàn được cập nhật realtime.

### 2. Công Ty Xác Nhận Xuất Kho

1. Nhân viên vào tab `Xuất kho`.
2. Chọn đơn hàng cần xử lý.
3. Hệ thống tự điền sản phẩm và số lượng theo đơn.
4. Khi lưu phiếu xuất, đơn chuyển sang `Đã xuất kho`.
5. Lịch sử xuất kho hiển thị phiếu đã xác nhận.
6. Trạng thái đơn bên TikTok Shop demo hiển thị kiện hàng đã được xuất đi.

### 3. Hủy Đơn

- Nếu khách hoặc công ty hủy đơn khi đơn còn `Chờ xử lý`, hệ thống:
  - Chuyển đơn sang `Hủy đơn`.
  - Cộng lại tồn kho đã trừ.
  - Đồng bộ realtime sang cả web quản lý và TikTok Shop demo.
- Đơn đã `Đã xuất kho` hoặc `Hủy đơn` không được chỉnh sửa/hủy lại.

### 4. Sửa Tồn Kho Thủ Công

- Khi sửa số lượng trong tab `Tồn kho`, backend cập nhật trực tiếp `products.stock_qty`.
- Sau đó hệ thống gọi API sang TikTok Shop demo để cập nhật số tồn hiển thị trên sàn.

## Tài Khoản Demo

| Vai trò | Tài khoản | Mật khẩu |
| --- | --- | --- |
| Quản trị viên | `admin` | `admin123` |
| Quản lý kho | `warehouse` | `warehouse123` |
| Nhân viên kho | `staff` | `staff123` |

## Phân Quyền Tổng Quan

| Chức năng | Admin | Warehouse | Staff |
| --- | --- | --- | --- |
| Tổng quan | Xem | Xem | Xem |
| Sản phẩm | Xem, thêm, sửa, ngừng kinh doanh | Xem, thêm, sửa, ngừng kinh doanh | Không xem |
| Nhà cung cấp | Xem, thêm, sửa, ngừng hợp tác | Xem, thêm, sửa, ngừng hợp tác | Không xem |
| Đơn hàng | Xem, thêm, sửa, hủy | Xem | Không xem |
| Nhập kho | Xem, tạo phiếu | Xem, tạo phiếu | Xem, tạo phiếu |
| Xuất kho | Xem, tạo phiếu | Xem, tạo phiếu | Xem, tạo phiếu |
| Tồn kho | Xem, sửa số lượng | Xem, sửa số lượng | Xem |
| Kiểm kê | Xem, tạo phiếu | Xem, tạo phiếu | Không xem |
| Đồng bộ sàn | Xem, retry | Xem, retry | Xem |
| Báo cáo | Xem, xuất CSV | Xem, xuất CSV | Không xem |
| Barcode/QR | Quét/tìm | Quét/tìm | Quét/tìm |
| Hoạt động | Xem, đánh dấu đọc, xóa | Xem, đánh dấu đọc | Xem, đánh dấu đọc |

## Công Nghệ Sử Dụng

### Backend

- Python 3.12
- FastAPI
- Uvicorn
- SQLite
- Pydantic
- httpx
- WebSocket realtime

### Frontend

- React
- TypeScript
- Vite
- lucide-react
- CSS responsive

### Triển Khai

- Docker
- Docker Compose
- SQLite bind mount ra thư mục `./data`

## Cấu Trúc Dự Án

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
├── marketplace/
│   ├── app/
│   │   ├── main.py
│   │   └── storefront.html
│   ├── Dockerfile
│   └── requirements.txt
├── data/
│   └── warehouse.db
├── docs/
├── product-list.csv
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Dữ Liệu

Ứng dụng dùng SQLite. File database nằm trong:

```text
data/warehouse.db
```

Trong `docker-compose.yml`, thư mục này được mount ra ngoài container:

```yaml
volumes:
  - ./data:/app/data
```

Vì vậy khi container bị recreate, dữ liệu vẫn còn. Khi triển khai sang laptop khác, chỉ cần đem theo cả thư mục dự án, đặc biệt là:

- `docker-compose.yml`
- `product-list.csv`
- thư mục `data/`

Sau đó chạy `docker compose up -d`.

### Seed Sản Phẩm BBIA

File `product-list.csv` chứa danh sách sản phẩm Bbia Official Store, bao gồm SKU, tên sản phẩm, danh mục, giá, ảnh và tồn kho.

Khi database trống, backend sẽ seed sản phẩm từ file này. Nếu `data/warehouse.db` đã tồn tại và có dữ liệu, hệ thống sẽ ưu tiên dữ liệu hiện có trong database.

Muốn làm mới dữ liệu demo hoàn toàn thì dừng container, xóa hoặc đổi tên `data/warehouse.db`, sau đó chạy lại Docker Compose để seed lại từ `product-list.csv`.

## Docker Compose Hiện Tại

`docker-compose.yml` đang chạy 2 service:

| Service | Image | Container | Port |
| --- | --- | --- | --- |
| `warehouse-management` | `warehouse-management-system:v1.3` | `warehouse-management-system` | `8000:8000` |
| `marketplace` | `tiktokshop_demo:v1.3` | `tiktokshop_demo` | `9000:9000` |

Biến môi trường chính:

| Service | Biến | Ý nghĩa |
| --- | --- | --- |
| `warehouse-management` | `DATA_DIR=/app/data` | Nơi lưu SQLite trong container |
| `warehouse-management` | `STATIC_DIR=/app/static` | Nơi serve frontend React đã build |
| `warehouse-management` | `MARKETPLACE_BASE_URL=http://marketplace:9000` | URL nội bộ để gọi TikTok Shop demo |
| `marketplace` | `WAREHOUSE_BASE_URL=http://warehouse-management:8000` | URL nội bộ để gọi web quản lý kho |

## Hướng Dẫn Chạy

### Yêu Cầu

- Docker Desktop đã được cài.
- Docker Desktop đang chạy.

### Build Và Chạy

```bash
docker compose up -d --build
```

Sau khi chạy:

- Web quản lý kho: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- TikTok Shop demo: `http://localhost:9000`

### Dừng Ứng Dụng

```bash
docker compose down
```

### Xem Log

```bash
docker compose logs -f
```

### Build Lại Sau Khi Sửa Code

```bash
docker compose up -d --build
```

## Một Vài API Quan Trọng

### Warehouse Management

- `POST /api/auth/login`: đăng nhập.
- `GET /api/products`: danh sách sản phẩm.
- `PUT /api/products/{id}`: sửa thông tin sản phẩm.
- `PUT /api/products/{id}/stock`: sửa trực tiếp số lượng tồn kho.
- `DELETE /api/products/{id}`: ngừng kinh doanh sản phẩm.
- `GET /api/orders`: danh sách đơn hàng.
- `PUT /api/orders/{id}`: cập nhật đơn hàng.
- `DELETE /api/orders/{id}`: hủy đơn hàng.
- `POST /api/issues`: tạo phiếu xuất kho.
- `GET /api/channels`: trạng thái kênh TikTok Shop.
- `GET /api/channel-syncs`: lịch sử đồng bộ tồn kho.
- `POST /api/webhooks/orders`: webhook nhận đơn từ TikTok Shop demo.
- `GET /ws/realtime`: websocket realtime cho frontend.

### TikTok Shop Demo

- `GET /api/listings`: danh sách sản phẩm đang bán trên sàn.
- `POST /api/listings/{sku}/buy`: mua sản phẩm.
- `GET /api/orders`: theo dõi đơn hàng của khách.
- `DELETE /api/orders/{id}`: khách hủy đơn.
- `PUT /api/mock/{channel_code}/products/{sku}/stock`: endpoint mock nhận đồng bộ tồn kho từ warehouse.

## Ghi Chú Demo

- Đây là hệ thống demo cục bộ, mật khẩu demo đang lưu dạng đơn giản trong SQLite.
- TikTok Shop demo là service mock để mô phỏng luồng seller/sàn, chưa phải tích hợp TikTok Shop Partner Center thật.
- Nếu muốn tích hợp thật, cần thay `MARKETPLACE_BASE_URL`, bổ sung xác thực API, chữ ký request và mapping endpoint theo tài liệu chính thức của nền tảng.

## Tài Liệu Thiết Kế

Một số tài liệu thiết kế nằm trong thư mục:

```text
docs/
```

Bao gồm sơ đồ ERD, use case và tài liệu mô tả hệ thống nếu đã được xuất kèm trong dự án.
