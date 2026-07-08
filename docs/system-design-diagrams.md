# 3.2.2 Thiet Ke Co So Du Lieu Va 3.2.3 Thiet Ke He Thong

Tai lieu nay mo ta thiet ke du lieu va thiet ke he thong cua ung dung **He thong quan ly kho hang**. Cac so do duoi day su dung cu phap Mermaid, co the dan vao Markdown, Mermaid Live Editor, draw.io hoac cac cong cu ho tro Mermaid de xuat thanh hinh.

## 3.2.2 Thiet Ke Co So Du Lieu

### ERD

```mermaid
erDiagram
    USERS {
        INTEGER id PK
        TEXT username UK
        TEXT password
        TEXT full_name
        TEXT role
        TEXT status
    }

    PRODUCTS {
        INTEGER id PK
        TEXT sku UK
        TEXT name
        TEXT category
        TEXT brand
        TEXT unit
        REAL import_price
        REAL sale_price
        TEXT barcode UK
        TEXT lot_number
        TEXT expiry_date
        TEXT image_url
        INTEGER min_stock
        TEXT location
        INTEGER stock_qty
        TEXT status
        TEXT created_at
    }

    SUPPLIERS {
        INTEGER id PK
        TEXT name
        TEXT address
        TEXT phone
        TEXT email
        TEXT contact_person
        TEXT status
        TEXT notes
        TEXT created_at
    }

    STOCK_RECEIPTS {
        INTEGER id PK
        TEXT code UK
        TEXT receipt_date
        INTEGER supplier_id FK
        TEXT note
        TEXT status
        TEXT created_by
    }

    STOCK_RECEIPT_ITEMS {
        INTEGER id PK
        INTEGER receipt_id FK
        INTEGER product_id FK
        INTEGER quantity
        REAL unit_price
    }

    ORDERS {
        INTEGER id PK
        TEXT code UK
        TEXT order_date
        TEXT customer_name
        TEXT channel
        TEXT status
        REAL total_amount
        TEXT note
        TEXT created_at
    }

    STOCK_ISSUES {
        INTEGER id PK
        TEXT code UK
        TEXT issue_date
        INTEGER order_id FK
        TEXT note
        TEXT status
        TEXT created_by
    }

    STOCK_ISSUE_ITEMS {
        INTEGER id PK
        INTEGER issue_id FK
        INTEGER product_id FK
        INTEGER quantity
        REAL unit_price
    }

    INVENTORY_CHECKS {
        INTEGER id PK
        TEXT code UK
        TEXT check_date
        TEXT note
        TEXT status
        TEXT created_by
    }

    INVENTORY_CHECK_ITEMS {
        INTEGER id PK
        INTEGER check_id FK
        INTEGER product_id FK
        INTEGER system_qty
        INTEGER actual_qty
        INTEGER difference
    }

    AUDIT_LOGS {
        INTEGER id PK
        TEXT action
        TEXT entity
        INTEGER entity_id
        TEXT message
        TEXT created_at
        INTEGER is_read
    }

    SUPPLIERS ||--o{ STOCK_RECEIPTS : supplies
    STOCK_RECEIPTS ||--|{ STOCK_RECEIPT_ITEMS : contains
    PRODUCTS ||--o{ STOCK_RECEIPT_ITEMS : received_product

    ORDERS ||--o{ STOCK_ISSUES : creates
    STOCK_ISSUES ||--|{ STOCK_ISSUE_ITEMS : contains
    PRODUCTS ||--o{ STOCK_ISSUE_ITEMS : issued_product

    INVENTORY_CHECKS ||--|{ INVENTORY_CHECK_ITEMS : contains
    PRODUCTS ||--o{ INVENTORY_CHECK_ITEMS : checked_product
```

Ghi chu: Quan he `STOCK_ISSUES.order_id -> ORDERS.id` dang duoc xu ly theo logic ung dung. Neu trien khai ban san pham that, nen khai bao foreign key truc tiep trong database.

### Data Dictionary

#### users

| Truong | Kieu | Rang buoc | Mo ta |
|---|---|---|---|
| id | INTEGER | PK, AUTOINCREMENT | Ma nguoi dung |
| username | TEXT | UNIQUE, NOT NULL | Ten dang nhap |
| password | TEXT | NOT NULL | Mat khau dang nhap demo |
| full_name | TEXT | NOT NULL | Ho ten hien thi |
| role | TEXT | NOT NULL | Vai tro: Quan tri vien, Quan ly kho, Nhan vien kho |
| status | TEXT | DEFAULT active | Trang thai tai khoan |

#### products

| Truong | Kieu | Rang buoc | Mo ta |
|---|---|---|---|
| id | INTEGER | PK, AUTOINCREMENT | Ma san pham |
| sku | TEXT | UNIQUE, NOT NULL | Ma SKU |
| name | TEXT | NOT NULL | Ten san pham |
| category | TEXT | NOT NULL | Danh muc san pham |
| brand | TEXT | NOT NULL | Thuong hieu |
| unit | TEXT | NOT NULL | Don vi tinh |
| import_price | REAL | DEFAULT 0 | Gia nhap |
| sale_price | REAL | DEFAULT 0 | Gia ban |
| barcode | TEXT | UNIQUE | Ma vach/QR |
| lot_number | TEXT |  | Lo hang |
| expiry_date | TEXT |  | Han su dung |
| image_url | TEXT |  | Duong dan hinh anh |
| min_stock | INTEGER | DEFAULT 10 | Ton kho toi thieu |
| location | TEXT | DEFAULT Kho chinh | Vi tri luu kho |
| stock_qty | INTEGER | DEFAULT 0 | So luong ton hien tai |
| status | TEXT | DEFAULT Dang ban | Trang thai kinh doanh |
| created_at | TEXT | DEFAULT CURRENT_TIMESTAMP | Thoi diem tao |

#### suppliers

| Truong | Kieu | Rang buoc | Mo ta |
|---|---|---|---|
| id | INTEGER | PK, AUTOINCREMENT | Ma nha cung cap |
| name | TEXT | NOT NULL | Ten nha cung cap |
| address | TEXT |  | Dia chi |
| phone | TEXT |  | So dien thoai |
| email | TEXT |  | Email |
| contact_person | TEXT |  | Nguoi lien he |
| status | TEXT | DEFAULT Dang hop tac | Trang thai hop tac |
| notes | TEXT |  | Ghi chu |
| created_at | TEXT | DEFAULT CURRENT_TIMESTAMP | Thoi diem tao |

#### stock_receipts

| Truong | Kieu | Rang buoc | Mo ta |
|---|---|---|---|
| id | INTEGER | PK, AUTOINCREMENT | Ma phieu nhap |
| code | TEXT | UNIQUE, NOT NULL | So phieu nhap |
| receipt_date | TEXT | NOT NULL | Ngay nhap kho |
| supplier_id | INTEGER | FK -> suppliers.id | Nha cung cap |
| note | TEXT |  | Ghi chu |
| status | TEXT | DEFAULT Da xac nhan | Trang thai phieu |
| created_by | TEXT | DEFAULT system | Nguoi tao |

#### stock_receipt_items

| Truong | Kieu | Rang buoc | Mo ta |
|---|---|---|---|
| id | INTEGER | PK, AUTOINCREMENT | Ma dong chi tiet |
| receipt_id | INTEGER | FK -> stock_receipts.id | Phieu nhap |
| product_id | INTEGER | FK -> products.id | San pham nhap |
| quantity | INTEGER | NOT NULL | So luong nhap |
| unit_price | REAL | DEFAULT 0 | Don gia nhap |

#### orders

| Truong | Kieu | Rang buoc | Mo ta |
|---|---|---|---|
| id | INTEGER | PK, AUTOINCREMENT | Ma don hang |
| code | TEXT | UNIQUE, NOT NULL | So don hang |
| order_date | TEXT | NOT NULL | Ngay dat hang |
| customer_name | TEXT | NOT NULL | Ten khach hang |
| channel | TEXT | NOT NULL | Kenh ban hang: Website, Shopee, Lazada, TikTok Shop |
| status | TEXT | NOT NULL | Trang thai don |
| total_amount | REAL | DEFAULT 0 | Tong gia tri don hang |
| note | TEXT |  | Ghi chu |
| created_at | TEXT | DEFAULT CURRENT_TIMESTAMP | Thoi diem tao |

#### stock_issues

| Truong | Kieu | Rang buoc | Mo ta |
|---|---|---|---|
| id | INTEGER | PK, AUTOINCREMENT | Ma phieu xuat |
| code | TEXT | UNIQUE, NOT NULL | So phieu xuat |
| issue_date | TEXT | NOT NULL | Ngay xuat kho |
| order_id | INTEGER | FK logic -> orders.id | Don hang lien quan |
| note | TEXT |  | Ghi chu |
| status | TEXT | DEFAULT Da xac nhan | Trang thai phieu |
| created_by | TEXT | DEFAULT system | Nguoi tao |

#### stock_issue_items

| Truong | Kieu | Rang buoc | Mo ta |
|---|---|---|---|
| id | INTEGER | PK, AUTOINCREMENT | Ma dong chi tiet |
| issue_id | INTEGER | FK -> stock_issues.id | Phieu xuat |
| product_id | INTEGER | FK -> products.id | San pham xuat |
| quantity | INTEGER | NOT NULL | So luong xuat |
| unit_price | REAL | DEFAULT 0 | Don gia xuat |

#### inventory_checks

| Truong | Kieu | Rang buoc | Mo ta |
|---|---|---|---|
| id | INTEGER | PK, AUTOINCREMENT | Ma phieu kiem ke |
| code | TEXT | UNIQUE, NOT NULL | So phieu kiem ke |
| check_date | TEXT | NOT NULL | Ngay kiem ke |
| note | TEXT |  | Ghi chu |
| status | TEXT | DEFAULT Da xac nhan | Trang thai phieu |
| created_by | TEXT | DEFAULT system | Nguoi tao |

#### inventory_check_items

| Truong | Kieu | Rang buoc | Mo ta |
|---|---|---|---|
| id | INTEGER | PK, AUTOINCREMENT | Ma dong chi tiet |
| check_id | INTEGER | FK -> inventory_checks.id | Phieu kiem ke |
| product_id | INTEGER | FK -> products.id | San pham kiem ke |
| system_qty | INTEGER | NOT NULL | Ton kho tren he thong |
| actual_qty | INTEGER | NOT NULL | Ton kho thuc te |
| difference | INTEGER | NOT NULL | Chenh lech ton kho, tinh bang system_qty - actual_qty |

#### audit_logs

| Truong | Kieu | Rang buoc | Mo ta |
|---|---|---|---|
| id | INTEGER | PK, AUTOINCREMENT | Ma nhat ky |
| action | TEXT | NOT NULL | Hanh dong thuc hien |
| entity | TEXT | NOT NULL | Doi tuong bi tac dong |
| entity_id | INTEGER |  | Ma doi tuong |
| message | TEXT | NOT NULL | Noi dung hoat dong |
| created_at | TEXT | DEFAULT CURRENT_TIMESTAMP | Thoi gian ghi nhan |
| is_read | INTEGER | DEFAULT 0 | Trang thai da doc/chua doc |

## 3.2.3 Thiet Ke He Thong

### Use Case Diagram

```mermaid
flowchart LR
    Admin[Quan tri vien]
    Manager[Quan ly kho]
    Staff[Nhan vien kho]

    UC_Login((Dang nhap))
    UC_Dashboard((Xem tong quan))
    UC_Product((Quan ly san pham))
    UC_Supplier((Quan ly nha cung cap))
    UC_Order((Quan ly don hang))
    UC_ViewOrder((Xem va tim kiem don hang))
    UC_Receipt((Tao phieu nhap kho))
    UC_Issue((Tao phieu xuat kho))
    UC_Inventory((Xem ton kho))
    UC_Check((Kiem ke kho))
    UC_Report((Xem va xuat bao cao))
    UC_Scan((Quet Barcode/QR))
    UC_Activity((Quan ly hoat dong))

    Admin --> UC_Login
    Admin --> UC_Dashboard
    Admin --> UC_Product
    Admin --> UC_Supplier
    Admin --> UC_Order
    Admin --> UC_Receipt
    Admin --> UC_Issue
    Admin --> UC_Inventory
    Admin --> UC_Check
    Admin --> UC_Report
    Admin --> UC_Scan
    Admin --> UC_Activity

    Manager --> UC_Login
    Manager --> UC_Dashboard
    Manager --> UC_Product
    Manager --> UC_Supplier
    Manager --> UC_ViewOrder
    Manager --> UC_Receipt
    Manager --> UC_Issue
    Manager --> UC_Inventory
    Manager --> UC_Check
    Manager --> UC_Report
    Manager --> UC_Scan
    Manager --> UC_Activity

    Staff --> UC_Login
    Staff --> UC_Dashboard
    Staff --> UC_Receipt
    Staff --> UC_Issue
    Staff --> UC_Inventory
    Staff --> UC_Scan
    Staff --> UC_Activity
```

### DFD Muc 0 - Context Diagram

```mermaid
flowchart LR
    Admin[Quan tri vien]
    Manager[Quan ly kho]
    Staff[Nhan vien kho]
    System((He thong quan ly kho hang))
    DB[(Co so du lieu SQLite)]

    Admin -->|Dang nhap, quan tri du lieu, xem bao cao| System
    Manager -->|Quan ly kho, theo doi don, xuat/nhap, kiem ke| System
    Staff -->|Nhap kho, xuat kho, quet ma, xem ton| System

    System -->|Ket qua xu ly, danh sach, bao cao, thong bao| Admin
    System -->|Du lieu kho, don hang, bao cao| Manager
    System -->|Du lieu thao tac kho| Staff

    System <--> DB
```

### DFD Muc 1

```mermaid
flowchart TB
    User[Nguoi dung]
    P1[1.0 Xac thuc nguoi dung]
    P2[2.0 Quan ly danh muc]
    P3[3.0 Xu ly nhap kho]
    P4[4.0 Xu ly xuat kho]
    P5[5.0 Kiem ke va ton kho]
    P6[6.0 Bao cao va hoat dong]

    D1[(users)]
    D2[(products)]
    D3[(suppliers)]
    D4[(orders)]
    D5[(stock_receipts)]
    D6[(stock_issues)]
    D7[(inventory_checks)]
    D8[(audit_logs)]

    User -->|Thong tin dang nhap| P1
    P1 <--> D1
    P1 -->|Thong tin tai khoan/quyen| User

    User -->|Them/sua/xoa san pham, NCC| P2
    P2 <--> D2
    P2 <--> D3
    P2 --> D8

    User -->|Tao phieu nhap| P3
    P3 <--> D2
    P3 <--> D3
    P3 <--> D5
    P3 --> D8

    User -->|Tao phieu xuat theo don| P4
    P4 <--> D2
    P4 <--> D4
    P4 <--> D6
    P4 --> D8

    User -->|Xem ton, tao kiem ke| P5
    P5 <--> D2
    P5 <--> D7
    P5 --> D8

    User -->|Xem bao cao, danh dau hoat dong| P6
    P6 --> D2
    P6 --> D4
    P6 --> D5
    P6 --> D6
    P6 --> D7
    P6 <--> D8
    P6 -->|Bao cao tong hop| User
```

### Activity Diagram - Dang Nhap Va Dieu Huong Theo Quyen

```mermaid
flowchart TD
    A([Bat dau]) --> B[Nguoi dung nhap username/password]
    B --> C{Thong tin hop le?}
    C -- Khong --> D[Thong bao loi dang nhap]
    D --> B
    C -- Co --> E[Lay thong tin nguoi dung va vai tro]
    E --> F{Vai tro}
    F -- Quan tri vien --> G[Hien tat ca chuc nang]
    F -- Quan ly kho --> H[Hien quan ly kho, don hang, bao cao]
    F -- Nhan vien kho --> I[Hien tong quan, ton kho, nhap/xuat, scan, hoat dong]
    G --> J([Su dung he thong])
    H --> J
    I --> J
```

### Activity Diagram - Quy Trinh Nhap Kho

```mermaid
flowchart TD
    A([Bat dau]) --> B[Chon chuc nang Nhap kho]
    B --> C[Chon nha cung cap]
    C --> D[Chon san pham va so luong]
    D --> E{Du lieu hop le?}
    E -- Khong --> F[Thong bao loi va yeu cau nhap lai]
    F --> D
    E -- Co --> G[Tao phieu nhap kho]
    G --> H[Luu chi tiet phieu nhap]
    H --> I[Cong stock_qty cho san pham]
    I --> J[Ghi audit log]
    J --> K[Cap nhat danh sach nhap kho va ton kho]
    K --> L([Ket thuc])
```

### Activity Diagram - Quy Trinh Xuat Kho

```mermaid
flowchart TD
    A([Bat dau]) --> B[Chon chuc nang Xuat kho]
    B --> C[Chon don hang lien quan neu co]
    C --> D[Chon san pham va so luong xuat]
    D --> E{Ton kho co du?}
    E -- Khong --> F[Thong bao san pham khong du ton]
    F --> D
    E -- Co --> G[Tao phieu xuat kho]
    G --> H[Luu chi tiet phieu xuat]
    H --> I[Tru stock_qty cua san pham]
    I --> J[Cap nhat trang thai don hang Da xuat kho]
    J --> K[Ghi audit log]
    K --> L[Cap nhat danh sach xuat kho va ton kho]
    L --> M([Ket thuc])
```

### Activity Diagram - Quy Trinh Kiem Ke

```mermaid
flowchart TD
    A([Bat dau]) --> B[Chon chuc nang Kiem ke]
    B --> C[Chon san pham can kiem ke]
    C --> D[He thong lay so luong ton he thong]
    D --> E[Nguoi dung nhap so luong thuc te]
    E --> F[Tinh chenh lech = he thong - thuc te]
    F --> G[Luu phieu kiem ke]
    G --> H[Cap nhat stock_qty theo so luong thuc te]
    H --> I[Ghi audit log]
    I --> J([Ket thuc])
```

### Kien Truc He Thong

```mermaid
flowchart TB
    subgraph Client["Client"]
        Browser["Trinh duyet web\nReact + Vite"]
    end

    subgraph Container["Docker container: warehouse-management-system"]
        Static["Static frontend files\n/app/static"]
        API["FastAPI backend\nUvicorn port 8000"]
        SQLite["SQLite database\n/app/data/warehouse.db"]
    end

    Browser -->|HTTP localhost:8000| API
    API -->|Tra ve SPA| Static
    API -->|Doc/ghi du lieu| SQLite
    API -->|JSON REST API| Browser
```

### Component Diagram

```mermaid
flowchart LR
    UI[React UI]
    Auth[Auth/Login]
    Product[Product Module]
    Supplier[Supplier Module]
    Order[Order Module]
    Receipt[Stock Receipt Module]
    Issue[Stock Issue Module]
    Inventory[Inventory/Check Module]
    Report[Report Module]
    Activity[Activity Log Module]
    Scan[Barcode/QR Module]
    API[FastAPI REST API]
    DB[(SQLite)]

    UI --> Auth
    UI --> Product
    UI --> Supplier
    UI --> Order
    UI --> Receipt
    UI --> Issue
    UI --> Inventory
    UI --> Report
    UI --> Activity
    UI --> Scan

    Auth --> API
    Product --> API
    Supplier --> API
    Order --> API
    Receipt --> API
    Issue --> API
    Inventory --> API
    Report --> API
    Activity --> API
    Scan --> API
    API --> DB
```

### Ma Tran Phan Quyen

| Chuc nang | Quan tri vien | Quan ly kho | Nhan vien kho |
|---|---|---|---|
| Tong quan | Xem | Xem | Xem |
| San pham | Xem, them, sua, ngung kinh doanh | Xem, them, sua, ngung kinh doanh | Khong xem |
| Nha cung cap | Xem, them, sua, ngung hop tac | Xem, them, sua, ngung hop tac | Khong xem |
| Don hang | Xem, tim kiem, them, sua, xoa | Xem, tim kiem | Khong xem |
| Nhap kho | Xem, tim kiem, tao phieu | Xem, tim kiem, tao phieu | Xem, tim kiem, tao phieu |
| Xuat kho | Xem, tim kiem, tao phieu | Xem, tim kiem, tao phieu | Xem, tim kiem, tao phieu |
| Ton kho | Xem | Xem | Xem |
| Kiem ke | Xem, tao kiem ke | Xem, tao kiem ke | Khong xem |
| Bao cao | Xem, xuat bao cao | Xem, xuat bao cao | Khong xem |
| Barcode/QR | Quet/tim san pham | Quet/tim san pham | Quet/tim san pham |
| Hoat dong | Xem, danh dau doc, xoa lich su | Xem, danh dau doc | Xem, danh dau doc |
