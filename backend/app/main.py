from __future__ import annotations

import os
import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
DB_PATH = Path(os.getenv("DATABASE_URL", DATA_DIR / "goods.db"))
STATIC_DIR = Path(os.getenv("STATIC_DIR", BASE_DIR / "static"))

app = FastAPI(title="Goods Management System API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_conn() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def row_to_dict(row: Optional[sqlite3.Row]) -> Optional[dict[str, Any]]:
    return dict(row) if row else None


def fetch_all(query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with get_conn() as conn:
        return [dict(row) for row in conn.execute(query, params).fetchall()]


def fetch_one(query: str, params: tuple[Any, ...] = ()) -> Optional[dict[str, Any]]:
    with get_conn() as conn:
        return row_to_dict(conn.execute(query, params).fetchone())


def today_iso() -> str:
    return date.today().isoformat()


class LoginRequest(BaseModel):
    username: str
    password: str


class ProductIn(BaseModel):
    sku: str = Field(min_length=2)
    name: str = Field(min_length=2)
    category: str = "Khac"
    brand: str = "ActsOne"
    unit: str = "cai"
    import_price: float = 0
    sale_price: float = 0
    barcode: str = ""
    image_url: str = ""
    min_stock: int = 10
    location: str = "Kho chinh"
    status: str = "Dang ban"


class SupplierIn(BaseModel):
    name: str
    address: str = ""
    phone: str = ""
    email: str = ""
    contact_person: str = ""
    status: str = "Dang hop tac"
    notes: str = ""


class StockLineIn(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)
    unit_price: float = 0


class ReceiptIn(BaseModel):
    supplier_id: Optional[int] = None
    note: str = ""
    items: list[StockLineIn]


class IssueIn(BaseModel):
    order_id: Optional[int] = None
    note: str = ""
    items: list[StockLineIn]


class OrderIn(BaseModel):
    customer_name: str
    channel: str = "Website"
    status: str = "Cho xu ly"
    total_amount: float = 0
    note: str = ""


class InventoryCheckLineIn(BaseModel):
    product_id: int
    actual_qty: int = Field(ge=0)


class InventoryCheckIn(BaseModel):
    note: str = ""
    items: list[InventoryCheckLineIn]


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL,
  full_name TEXT NOT NULL,
  role TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'active'
);
CREATE TABLE IF NOT EXISTS products (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  sku TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  category TEXT NOT NULL,
  brand TEXT NOT NULL,
  unit TEXT NOT NULL,
  import_price REAL NOT NULL DEFAULT 0,
  sale_price REAL NOT NULL DEFAULT 0,
  barcode TEXT UNIQUE,
  image_url TEXT,
  min_stock INTEGER NOT NULL DEFAULT 10,
  location TEXT NOT NULL DEFAULT 'Kho chinh',
  stock_qty INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'Dang ban',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS suppliers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  address TEXT,
  phone TEXT,
  email TEXT,
  contact_person TEXT,
  status TEXT NOT NULL DEFAULT 'Dang hop tac',
  notes TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS stock_receipts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  code TEXT UNIQUE NOT NULL,
  receipt_date TEXT NOT NULL,
  supplier_id INTEGER,
  note TEXT,
  status TEXT NOT NULL DEFAULT 'Da xac nhan',
  created_by TEXT NOT NULL DEFAULT 'system',
  FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
);
CREATE TABLE IF NOT EXISTS stock_receipt_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  receipt_id INTEGER NOT NULL,
  product_id INTEGER NOT NULL,
  quantity INTEGER NOT NULL,
  unit_price REAL NOT NULL DEFAULT 0,
  FOREIGN KEY (receipt_id) REFERENCES stock_receipts(id) ON DELETE CASCADE,
  FOREIGN KEY (product_id) REFERENCES products(id)
);
CREATE TABLE IF NOT EXISTS stock_issues (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  code TEXT UNIQUE NOT NULL,
  issue_date TEXT NOT NULL,
  order_id INTEGER,
  note TEXT,
  status TEXT NOT NULL DEFAULT 'Da xac nhan',
  created_by TEXT NOT NULL DEFAULT 'system'
);
CREATE TABLE IF NOT EXISTS stock_issue_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  issue_id INTEGER NOT NULL,
  product_id INTEGER NOT NULL,
  quantity INTEGER NOT NULL,
  unit_price REAL NOT NULL DEFAULT 0,
  FOREIGN KEY (issue_id) REFERENCES stock_issues(id) ON DELETE CASCADE,
  FOREIGN KEY (product_id) REFERENCES products(id)
);
CREATE TABLE IF NOT EXISTS orders (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  code TEXT UNIQUE NOT NULL,
  order_date TEXT NOT NULL,
  customer_name TEXT NOT NULL,
  channel TEXT NOT NULL,
  status TEXT NOT NULL,
  total_amount REAL NOT NULL DEFAULT 0,
  note TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS inventory_checks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  code TEXT UNIQUE NOT NULL,
  check_date TEXT NOT NULL,
  note TEXT,
  status TEXT NOT NULL DEFAULT 'Da xac nhan',
  created_by TEXT NOT NULL DEFAULT 'system'
);
CREATE TABLE IF NOT EXISTS inventory_check_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  check_id INTEGER NOT NULL,
  product_id INTEGER NOT NULL,
  system_qty INTEGER NOT NULL,
  actual_qty INTEGER NOT NULL,
  difference INTEGER NOT NULL,
  FOREIGN KEY (check_id) REFERENCES inventory_checks(id) ON DELETE CASCADE,
  FOREIGN KEY (product_id) REFERENCES products(id)
);
CREATE TABLE IF NOT EXISTS audit_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  action TEXT NOT NULL,
  entity TEXT NOT NULL,
  entity_id INTEGER,
  message TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


def next_code(conn: sqlite3.Connection, table: str, prefix: str) -> str:
    row = conn.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()
    return f"{prefix}{row['count'] + 1:05d}"


def log(conn: sqlite3.Connection, action: str, entity: str, entity_id: Optional[int], message: str) -> None:
    conn.execute(
        "INSERT INTO audit_logs(action, entity, entity_id, message) VALUES (?, ?, ?, ?)",
        (action, entity, entity_id, message),
    )


def normalize_demo_data(conn: sqlite3.Connection) -> None:
    demo_products = [
        ("Son m\u00f4i Velvet Tint", "c\u00e2y", "K\u1ec7 A1", "SK001"),
        ("Kem ch\u1ed1ng n\u1eafng Aqua", "tu\u00fdp", "K\u1ec7 B2", "SK002"),
        ("M\u1eb7t n\u1ea1 d\u01b0\u1ee1ng \u1ea9m", "h\u1ed9p", "K\u1ec7 C1", "SK003"),
        ("N\u01b0\u1edbc t\u1ea9y trang Green Tea", "chai", "K\u1ec7 B1", "SK004"),
    ]
    conn.executemany("UPDATE products SET name=?, unit=?, location=? WHERE sku=?", demo_products)
    demo_orders = [
        ("L\u00ea Minh Anh", "ORD00001"),
        ("Tr\u1ea7n Gia H\u00e2n", "ORD00002"),
        ("Ph\u1ea1m Qu\u1ed1c B\u1ea3o", "ORD00003"),
    ]
    conn.executemany("UPDATE orders SET customer_name=? WHERE code=?", demo_orders)
    demo_users = [
        ("Qu\u1ea3n tr\u1ecb h\u1ec7 th\u1ed1ng", "Qu\u1ea3n tr\u1ecb vi\u00ean", "admin"),
        ("Qu\u1ea3n l\u00fd kho", "Qu\u1ea3n l\u00fd kho", "warehouse"),
        ("Nh\u00e2n vi\u00ean kho", "Nh\u00e2n vi\u00ean kho", "staff"),
    ]
    conn.executemany("UPDATE users SET full_name=?, role=? WHERE username=?", demo_users)


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(SCHEMA)
        if conn.execute("SELECT COUNT(*) AS count FROM users").fetchone()["count"] == 0:
            conn.executemany(
                "INSERT INTO users(username, password, full_name, role) VALUES (?, ?, ?, ?)",
                [
                    ("admin", "admin123", "Qu\u1ea3n tr\u1ecb h\u1ec7 th\u1ed1ng", "Qu\u1ea3n tr\u1ecb vi\u00ean"),
                    ("warehouse", "warehouse123", "Qu\u1ea3n l\u00fd kho", "Qu\u1ea3n l\u00fd kho"),
                    ("staff", "staff123", "Nh\u00e2n vi\u00ean kho", "Nh\u00e2n vi\u00ean kho"),
                ],
            )
        if conn.execute("SELECT COUNT(*) AS count FROM suppliers").fetchone()["count"] == 0:
            conn.executemany(
                "INSERT INTO suppliers(name, address, phone, email, contact_person, status, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
                [
                    ("ActsOne Korea", "Seoul, Korea", "+82 02 1000 2000", "supply@actsone.kr", "Kim Hana", "Dang hop tac", "Nha cung cap my pham Han Quoc"),
                    ("Beauty Logistics VN", "TP. Ho Chi Minh", "0909000111", "ops@beautylog.vn", "Nguyen An", "Dang hop tac", "Doi tac logistics noi dia"),
                ],
            )
        if conn.execute("SELECT COUNT(*) AS count FROM products").fetchone()["count"] == 0:
            conn.executemany(
                """
                INSERT INTO products(sku, name, category, brand, unit, import_price, sale_price, barcode, image_url, min_stock, location, stock_qty, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    ("SK001", "Son môi Velvet Tint", "Makeup", "ActsOne", "cây", 85000, 159000, "880000000001", "https://images.unsplash.com/photo-1586495777744-4413f21062fa?auto=format&fit=crop&w=400&q=80", 50, "Kệ A1", 500, "Dang ban"),
                    ("SK002", "Kem chống nắng Aqua", "Skincare", "ActsOne", "tuýp", 120000, 249000, "880000000002", "https://images.unsplash.com/photo-1556228578-8c89e6adf883?auto=format&fit=crop&w=400&q=80", 40, "Kệ B2", 35, "Dang ban"),
                    ("SK003", "Mặt nạ dưỡng ẩm", "Skincare", "K-Beauty", "hộp", 65000, 129000, "880000000003", "https://images.unsplash.com/photo-1598440947619-2c35fc9aa908?auto=format&fit=crop&w=400&q=80", 30, "Kệ C1", 8, "Dang ban"),
                    ("SK004", "Nước tẩy trang Green Tea", "Skincare", "ActsOne", "chai", 90000, 189000, "880000000004", "https://images.unsplash.com/photo-1608248543803-ba4f8c70ae0b?auto=format&fit=crop&w=400&q=80", 25, "Kệ B1", 0, "Tam ngung"),
                ],
            )
        if conn.execute("SELECT COUNT(*) AS count FROM orders").fetchone()["count"] == 0:
            conn.executemany(
                "INSERT INTO orders(code, order_date, customer_name, channel, status, total_amount, note) VALUES (?, ?, ?, ?, ?, ?, ?)",
                [
                    ("ORD00001", today_iso(), "Lê Minh Anh", "Shopee", "Cho xu ly", 408000, "Don uu tien"),
                    ("ORD00002", today_iso(), "Trần Gia Hân", "Website", "Dang dong goi", 159000, ""),
                    ("ORD00003", today_iso(), "Phạm Quốc Bảo", "TikTok Shop", "Da xuat kho", 249000, ""),
                ],
            )
        normalize_demo_data(conn)
        conn.commit()


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "time": datetime.utcnow().isoformat()}


@app.post("/api/auth/login")
def login(payload: LoginRequest) -> dict[str, Any]:
    user = fetch_one(
        "SELECT id, username, full_name, role, status FROM users WHERE username = ? AND password = ? AND status = 'active'",
        (payload.username, payload.password),
    )
    if not user:
        raise HTTPException(status_code=401, detail="Tai khoan hoac mat khau khong dung")
    return {"token": f"demo-token-{user['id']}", "user": user}


@app.get("/api/products")
def list_products(q: str = "") -> list[dict[str, Any]]:
    like = f"%{q.lower()}%"
    return fetch_all(
        """
        SELECT * FROM products
        WHERE lower(sku) LIKE ? OR lower(name) LIKE ? OR lower(category) LIKE ? OR lower(brand) LIKE ? OR lower(coalesce(barcode, '')) LIKE ?
        ORDER BY created_at DESC, id DESC
        """,
        (like, like, like, like, like),
    )


@app.post("/api/products", status_code=201)
def create_product(payload: ProductIn) -> dict[str, Any]:
    with get_conn() as conn:
        try:
            cursor = conn.execute(
                """
                INSERT INTO products(sku, name, category, brand, unit, import_price, sale_price, barcode, image_url, min_stock, location, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (payload.sku, payload.name, payload.category, payload.brand, payload.unit, payload.import_price, payload.sale_price, payload.barcode or None, payload.image_url, payload.min_stock, payload.location, payload.status),
            )
            log(conn, "create", "product", cursor.lastrowid, f"Tao san pham {payload.sku}")
            conn.commit()
        except sqlite3.IntegrityError as exc:
            raise HTTPException(status_code=409, detail="SKU hoac barcode da ton tai") from exc
        return fetch_one("SELECT * FROM products WHERE id = ?", (cursor.lastrowid,))


@app.put("/api/products/{product_id}")
def update_product(product_id: int, payload: ProductIn) -> dict[str, Any]:
    with get_conn() as conn:
        current = conn.execute("SELECT id FROM products WHERE id = ?", (product_id,)).fetchone()
        if not current:
            raise HTTPException(status_code=404, detail="Khong tim thay san pham")
        try:
            conn.execute(
                """
                UPDATE products SET sku=?, name=?, category=?, brand=?, unit=?, import_price=?, sale_price=?, barcode=?, image_url=?, min_stock=?, location=?, status=?
                WHERE id=?
                """,
                (payload.sku, payload.name, payload.category, payload.brand, payload.unit, payload.import_price, payload.sale_price, payload.barcode or None, payload.image_url, payload.min_stock, payload.location, payload.status, product_id),
            )
            log(conn, "update", "product", product_id, f"Cap nhat san pham {payload.sku}")
            conn.commit()
        except sqlite3.IntegrityError as exc:
            raise HTTPException(status_code=409, detail="SKU hoac barcode da ton tai") from exc
    return fetch_one("SELECT * FROM products WHERE id = ?", (product_id,))


@app.delete("/api/products/{product_id}")
def deactivate_product(product_id: int) -> dict[str, str]:
    with get_conn() as conn:
        conn.execute("UPDATE products SET status = 'Ngung kinh doanh' WHERE id = ?", (product_id,))
        log(conn, "deactivate", "product", product_id, "Vo hieu hoa san pham")
        conn.commit()
    return {"message": "Da vo hieu hoa san pham"}


@app.get("/api/suppliers")
def list_suppliers(q: str = "") -> list[dict[str, Any]]:
    like = f"%{q.lower()}%"
    return fetch_all(
        "SELECT * FROM suppliers WHERE lower(name) LIKE ? OR lower(coalesce(email,'')) LIKE ? OR lower(coalesce(phone,'')) LIKE ? ORDER BY id DESC",
        (like, like, like),
    )


@app.post("/api/suppliers", status_code=201)
def create_supplier(payload: SupplierIn) -> dict[str, Any]:
    with get_conn() as conn:
        cursor = conn.execute(
            "INSERT INTO suppliers(name, address, phone, email, contact_person, status, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (payload.name, payload.address, payload.phone, payload.email, payload.contact_person, payload.status, payload.notes),
        )
        log(conn, "create", "supplier", cursor.lastrowid, f"Tao nha cung cap {payload.name}")
        conn.commit()
    return fetch_one("SELECT * FROM suppliers WHERE id = ?", (cursor.lastrowid,))


@app.put("/api/suppliers/{supplier_id}")
def update_supplier(supplier_id: int, payload: SupplierIn) -> dict[str, Any]:
    with get_conn() as conn:
        conn.execute(
            "UPDATE suppliers SET name=?, address=?, phone=?, email=?, contact_person=?, status=?, notes=? WHERE id=?",
            (payload.name, payload.address, payload.phone, payload.email, payload.contact_person, payload.status, payload.notes, supplier_id),
        )
        log(conn, "update", "supplier", supplier_id, f"Cap nhat nha cung cap {payload.name}")
        conn.commit()
    supplier = fetch_one("SELECT * FROM suppliers WHERE id = ?", (supplier_id,))
    if not supplier:
        raise HTTPException(status_code=404, detail="Khong tim thay nha cung cap")
    return supplier


@app.delete("/api/suppliers/{supplier_id}")
def delete_supplier(supplier_id: int) -> dict[str, str]:
    with get_conn() as conn:
        conn.execute("UPDATE suppliers SET status = 'Ngung hop tac' WHERE id = ?", (supplier_id,))
        log(conn, "deactivate", "supplier", supplier_id, "Ngung hop tac nha cung cap")
        conn.commit()
    return {"message": "Da xoa nha cung cap"}


@app.get("/api/inventory")
def inventory(q: str = "", low_stock: bool = False) -> list[dict[str, Any]]:
    like = f"%{q.lower()}%"
    rows = fetch_all(
        """
        SELECT *,
          CASE
            WHEN stock_qty <= 0 THEN 'Het hang'
            WHEN stock_qty <= min_stock THEN 'Sap het'
            ELSE 'An toan'
          END AS inventory_status
        FROM products
        WHERE (lower(sku) LIKE ? OR lower(name) LIKE ? OR lower(category) LIKE ?)
        ORDER BY stock_qty ASC, name ASC
        """,
        (like, like, like),
    )
    return [row for row in rows if not low_stock or row["stock_qty"] <= row["min_stock"]]


@app.get("/api/receipts")
def list_receipts() -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT r.*, s.name AS supplier_name, COALESCE(SUM(i.quantity), 0) AS total_quantity, COALESCE(SUM(i.quantity * i.unit_price), 0) AS total_value
        FROM stock_receipts r
        LEFT JOIN suppliers s ON s.id = r.supplier_id
        LEFT JOIN stock_receipt_items i ON i.receipt_id = r.id
        GROUP BY r.id
        ORDER BY r.id DESC
        """
    )


@app.post("/api/receipts", status_code=201)
def create_receipt(payload: ReceiptIn) -> dict[str, Any]:
    if not payload.items:
        raise HTTPException(status_code=400, detail="Phieu nhap can co it nhat mot san pham")
    with get_conn() as conn:
        code = next_code(conn, "stock_receipts", "RCP")
        cursor = conn.execute(
            "INSERT INTO stock_receipts(code, receipt_date, supplier_id, note) VALUES (?, ?, ?, ?)",
            (code, today_iso(), payload.supplier_id, payload.note),
        )
        receipt_id = cursor.lastrowid
        for item in payload.items:
            product = conn.execute("SELECT id FROM products WHERE id = ?", (item.product_id,)).fetchone()
            if not product:
                raise HTTPException(status_code=404, detail=f"Khong tim thay san pham #{item.product_id}")
            conn.execute(
                "INSERT INTO stock_receipt_items(receipt_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
                (receipt_id, item.product_id, item.quantity, item.unit_price),
            )
            conn.execute("UPDATE products SET stock_qty = stock_qty + ? WHERE id = ?", (item.quantity, item.product_id))
        log(conn, "confirm", "receipt", receipt_id, f"Xac nhan phieu nhap {code}")
        conn.commit()
    return fetch_one("SELECT * FROM stock_receipts WHERE id = ?", (receipt_id,))


@app.get("/api/issues")
def list_issues() -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT i.*, o.code AS order_code, COALESCE(SUM(ii.quantity), 0) AS total_quantity, COALESCE(SUM(ii.quantity * ii.unit_price), 0) AS total_value
        FROM stock_issues i
        LEFT JOIN orders o ON o.id = i.order_id
        LEFT JOIN stock_issue_items ii ON ii.issue_id = i.id
        GROUP BY i.id
        ORDER BY i.id DESC
        """
    )


@app.post("/api/issues", status_code=201)
def create_issue(payload: IssueIn) -> dict[str, Any]:
    if not payload.items:
        raise HTTPException(status_code=400, detail="Phieu xuat can co it nhat mot san pham")
    with get_conn() as conn:
        for item in payload.items:
            product = conn.execute("SELECT stock_qty, name FROM products WHERE id = ?", (item.product_id,)).fetchone()
            if not product:
                raise HTTPException(status_code=404, detail=f"Khong tim thay san pham #{item.product_id}")
            if product["stock_qty"] < item.quantity:
                raise HTTPException(status_code=409, detail=f"San pham {product['name']} khong du ton kho")
        code = next_code(conn, "stock_issues", "ISS")
        cursor = conn.execute(
            "INSERT INTO stock_issues(code, issue_date, order_id, note) VALUES (?, ?, ?, ?)",
            (code, today_iso(), payload.order_id, payload.note),
        )
        issue_id = cursor.lastrowid
        for item in payload.items:
            conn.execute(
                "INSERT INTO stock_issue_items(issue_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
                (issue_id, item.product_id, item.quantity, item.unit_price),
            )
            conn.execute("UPDATE products SET stock_qty = stock_qty - ? WHERE id = ?", (item.quantity, item.product_id))
        if payload.order_id:
            conn.execute("UPDATE orders SET status = 'Da xuat kho' WHERE id = ?", (payload.order_id,))
        log(conn, "confirm", "issue", issue_id, f"Xac nhan phieu xuat {code}")
        conn.commit()
    return fetch_one("SELECT * FROM stock_issues WHERE id = ?", (issue_id,))


@app.get("/api/orders")
def list_orders() -> list[dict[str, Any]]:
    return fetch_all("SELECT * FROM orders ORDER BY id DESC")


@app.post("/api/orders", status_code=201)
def create_order(payload: OrderIn) -> dict[str, Any]:
    with get_conn() as conn:
        code = next_code(conn, "orders", "ORD")
        cursor = conn.execute(
            "INSERT INTO orders(code, order_date, customer_name, channel, status, total_amount, note) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (code, today_iso(), payload.customer_name, payload.channel, payload.status, payload.total_amount, payload.note),
        )
        log(conn, "create", "order", cursor.lastrowid, f"Tao don hang {code}")
        conn.commit()
    return fetch_one("SELECT * FROM orders WHERE id = ?", (cursor.lastrowid,))


@app.put("/api/orders/{order_id}")
def update_order(order_id: int, payload: OrderIn) -> dict[str, Any]:
    with get_conn() as conn:
        current = conn.execute("SELECT id FROM orders WHERE id = ?", (order_id,)).fetchone()
        if not current:
            raise HTTPException(status_code=404, detail="Khong tim thay don hang")
        conn.execute(
            "UPDATE orders SET customer_name=?, channel=?, status=?, total_amount=?, note=? WHERE id=?",
            (payload.customer_name, payload.channel, payload.status, payload.total_amount, payload.note, order_id),
        )
        log(conn, "update", "order", order_id, f"Cap nhat don hang #{order_id}")
        conn.commit()
    return fetch_one("SELECT * FROM orders WHERE id = ?", (order_id,))


@app.delete("/api/orders/{order_id}")
def delete_order(order_id: int) -> dict[str, str]:
    with get_conn() as conn:
        conn.execute("UPDATE orders SET status = 'Huy don' WHERE id = ?", (order_id,))
        log(conn, "cancel", "order", order_id, f"Huy don hang #{order_id}")
        conn.commit()
    return {"message": "Da huy don hang"}


@app.get("/api/inventory-checks")
def list_inventory_checks() -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT c.*, COALESCE(SUM(ABS(i.difference)), 0) AS total_difference
        FROM inventory_checks c
        LEFT JOIN inventory_check_items i ON i.check_id = c.id
        GROUP BY c.id
        ORDER BY c.id DESC
        """
    )


@app.post("/api/inventory-checks", status_code=201)
def create_inventory_check(payload: InventoryCheckIn) -> dict[str, Any]:
    if not payload.items:
        raise HTTPException(status_code=400, detail="Phieu kiem ke can co it nhat mot san pham")
    with get_conn() as conn:
        code = next_code(conn, "inventory_checks", "CHK")
        cursor = conn.execute(
            "INSERT INTO inventory_checks(code, check_date, note) VALUES (?, ?, ?)",
            (code, today_iso(), payload.note),
        )
        check_id = cursor.lastrowid
        for item in payload.items:
            product = conn.execute("SELECT stock_qty FROM products WHERE id = ?", (item.product_id,)).fetchone()
            if not product:
                raise HTTPException(status_code=404, detail=f"Khong tim thay san pham #{item.product_id}")
            diff = item.actual_qty - product["stock_qty"]
            conn.execute(
                "INSERT INTO inventory_check_items(check_id, product_id, system_qty, actual_qty, difference) VALUES (?, ?, ?, ?, ?)",
                (check_id, item.product_id, product["stock_qty"], item.actual_qty, diff),
            )
            conn.execute("UPDATE products SET stock_qty = ? WHERE id = ?", (item.actual_qty, item.product_id))
        log(conn, "confirm", "inventory_check", check_id, f"Xac nhan phieu kiem ke {code}")
        conn.commit()
    return fetch_one("SELECT * FROM inventory_checks WHERE id = ?", (check_id,))


@app.get("/api/dashboard")
def dashboard() -> dict[str, Any]:
    stats = fetch_one(
        """
        SELECT
          COUNT(*) AS total_products,
          COALESCE(SUM(stock_qty), 0) AS total_stock,
          SUM(CASE WHEN stock_qty <= min_stock THEN 1 ELSE 0 END) AS low_stock_products
        FROM products
        """
    ) or {}
    order_stats = fetch_one("SELECT COUNT(*) AS today_orders FROM orders WHERE order_date = ?", (today_iso(),)) or {}
    month = today_iso()[:7]
    receipt_stats = fetch_one("SELECT COALESCE(SUM(i.quantity), 0) AS month_receipts FROM stock_receipts r JOIN stock_receipt_items i ON i.receipt_id = r.id WHERE substr(r.receipt_date, 1, 7) = ?", (month,)) or {}
    issue_stats = fetch_one("SELECT COALESCE(SUM(i.quantity), 0) AS month_issues FROM stock_issues s JOIN stock_issue_items i ON i.issue_id = s.id WHERE substr(s.issue_date, 1, 7) = ?", (month,)) or {}
    low_stock = inventory(low_stock=True)[:6]
    activities = fetch_all("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 8")
    return {**stats, **order_stats, **receipt_stats, **issue_stats, "low_stock": low_stock, "activities": activities}


@app.get("/api/reports/summary")
def report_summary() -> dict[str, Any]:
    receipts = fetch_all(
        "SELECT receipt_date AS date, COUNT(*) AS documents, COALESCE(SUM(i.quantity), 0) AS quantity FROM stock_receipts r LEFT JOIN stock_receipt_items i ON i.receipt_id = r.id GROUP BY receipt_date ORDER BY receipt_date DESC LIMIT 12"
    )
    issues = fetch_all(
        "SELECT issue_date AS date, COUNT(*) AS documents, COALESCE(SUM(i.quantity), 0) AS quantity FROM stock_issues s LEFT JOIN stock_issue_items i ON i.issue_id = s.id GROUP BY issue_date ORDER BY issue_date DESC LIMIT 12"
    )
    checks = fetch_all(
        "SELECT c.check_date AS date, c.code, COALESCE(SUM(ABS(i.difference)), 0) AS total_difference FROM inventory_checks c LEFT JOIN inventory_check_items i ON i.check_id = c.id GROUP BY c.id ORDER BY c.id DESC LIMIT 12"
    )
    return {"receipts": receipts, "issues": issues, "checks": checks}


@app.get("/api/reports/export")
def export_report() -> Response:
    rows = fetch_all(
        """
        SELECT 'receipt' AS type, r.code AS code, r.receipt_date AS date, COALESCE(s.name, '') AS ref,
               COALESCE(SUM(i.quantity), 0) AS quantity, COALESCE(SUM(i.quantity * i.unit_price), 0) AS value
        FROM stock_receipts r
        LEFT JOIN suppliers s ON s.id = r.supplier_id
        LEFT JOIN stock_receipt_items i ON i.receipt_id = r.id
        GROUP BY r.id
        UNION ALL
        SELECT 'issue' AS type, si.code AS code, si.issue_date AS date, COALESCE(o.code, '') AS ref,
               COALESCE(SUM(ii.quantity), 0) AS quantity, COALESCE(SUM(ii.quantity * ii.unit_price), 0) AS value
        FROM stock_issues si
        LEFT JOIN orders o ON o.id = si.order_id
        LEFT JOIN stock_issue_items ii ON ii.issue_id = si.id
        GROUP BY si.id
        ORDER BY date DESC
        """
    )
    lines = ["type,code,date,reference,quantity,value"]
    for row in rows:
        lines.append(f"{row['type']},{row['code']},{row['date']},{row['ref']},{row['quantity']},{row['value']}")
    csv = "\ufeff" + "\n".join(lines)
    return Response(
        content=csv,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=goods-report.csv"},
    )


@app.get("/api/scan/{code}")
def scan_product(code: str) -> dict[str, Any]:
    product = fetch_one("SELECT * FROM products WHERE barcode = ? OR sku = ?", (code, code))
    if not product:
        raise HTTPException(status_code=404, detail="Khong tim thay san pham tu ma quet")
    product["inventory_status"] = "Het hang" if product["stock_qty"] <= 0 else "Sap het" if product["stock_qty"] <= product["min_stock"] else "An toan"
    return product


if STATIC_DIR.exists():
    assets_dir = STATIC_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_spa(full_path: str) -> FileResponse:
        target = STATIC_DIR / full_path
        if full_path and target.exists() and target.is_file():
            return FileResponse(target)
        return FileResponse(STATIC_DIR / "index.html")