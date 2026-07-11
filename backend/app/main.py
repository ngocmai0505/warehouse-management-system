from __future__ import annotations

import csv
import os
import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional

import httpx
from fastapi import BackgroundTasks, FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
DB_PATH = Path(os.getenv("DATABASE_URL", DATA_DIR / "warehouse.db"))
STATIC_DIR = Path(os.getenv("STATIC_DIR", BASE_DIR / "static"))
MARKETPLACE_BASE_URL = os.getenv("MARKETPLACE_BASE_URL", "http://localhost:9000")
PRODUCT_CSV_PATH = os.getenv("PRODUCT_CSV_PATH", "")

app = FastAPI(title="Warehouse Management System API", version="1.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RealtimeHub:
    """Keeps track of connected dashboard clients and broadcasts live events
    (stock changes, channel sync results) so every open tab updates instantly."""

    def __init__(self) -> None:
        self.connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self.connections.append(ws)

    def disconnect(self, ws: WebSocket) -> None:
        if ws in self.connections:
            self.connections.remove(ws)

    async def broadcast(self, event: dict[str, Any]) -> None:
        dead: list[WebSocket] = []
        for ws in self.connections:
            try:
                await ws.send_json(event)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


hub = RealtimeHub()


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


PRODUCT_FIELDS = "id, sku, name, category, brand, unit, import_price, sale_price, barcode, lot_number, expiry_date, image_url, min_stock, location, stock_qty, status, created_at"


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
    lot_number: str = ""
    expiry_date: str = ""
    image_url: str = ""
    min_stock: int = 10
    location: str = "Kho chinh"
    status: str = "Dang ban"


class ProductStockIn(BaseModel):
    stock_qty: int = Field(ge=0)


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
    items: list[StockLineIn] = []


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
  lot_number TEXT,
  expiry_date TEXT,
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
  stock_deducted INTEGER NOT NULL DEFAULT 0,
  note TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS order_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  order_id INTEGER NOT NULL,
  product_id INTEGER NOT NULL,
  quantity INTEGER NOT NULL,
  unit_price REAL NOT NULL DEFAULT 0,
  FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
  FOREIGN KEY (product_id) REFERENCES products(id)
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
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  is_read INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS sales_channels (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  code TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  api_base_url TEXT NOT NULL,
  is_connected INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS channel_stock_syncs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  product_id INTEGER NOT NULL,
  channel_id INTEGER NOT NULL,
  trigger_type TEXT NOT NULL,
  order_id INTEGER,
  old_qty INTEGER NOT NULL,
  new_qty INTEGER NOT NULL,
  status TEXT NOT NULL,
  message TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (product_id) REFERENCES products(id),
  FOREIGN KEY (channel_id) REFERENCES sales_channels(id)
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


def ensure_product_columns(conn: sqlite3.Connection) -> None:
    existing = {row["name"] for row in conn.execute("PRAGMA table_info(products)").fetchall()}
    for name, definition in {
        "lot_number": "TEXT",
        "expiry_date": "TEXT",
    }.items():
        if name not in existing:
            conn.execute(f"ALTER TABLE products ADD COLUMN {name} {definition}")


def ensure_audit_columns(conn: sqlite3.Connection) -> None:
    existing = {row["name"] for row in conn.execute("PRAGMA table_info(audit_logs)").fetchall()}
    if "is_read" not in existing:
        conn.execute("ALTER TABLE audit_logs ADD COLUMN is_read INTEGER NOT NULL DEFAULT 0")


def ensure_order_columns(conn: sqlite3.Connection) -> None:
    existing = {row["name"] for row in conn.execute("PRAGMA table_info(orders)").fetchall()}
    if "stock_deducted" not in existing:
        conn.execute("ALTER TABLE orders ADD COLUMN stock_deducted INTEGER NOT NULL DEFAULT 0")


def ensure_channel_urls(conn: sqlite3.Connection) -> None:
    """Keeps sales_channels.api_base_url pointed at the current MARKETPLACE_BASE_URL even for a
    database volume that was seeded by an older version with a different (or fake) URL."""
    conn.execute("UPDATE sales_channels SET api_base_url = ?", (MARKETPLACE_BASE_URL,))


def ensure_tiktok_shop_channel(conn: sqlite3.Connection) -> None:
    """The demo models one marketplace only: TikTok Shop for Bbia Official Store."""
    conn.execute("DELETE FROM channel_stock_syncs WHERE channel_id IN (SELECT id FROM sales_channels WHERE code != 'tiktok')")
    conn.execute("DELETE FROM sales_channels WHERE code != 'tiktok'")
    channel = conn.execute("SELECT id FROM sales_channels WHERE code = 'tiktok'").fetchone()
    if channel:
        conn.execute(
            "UPDATE sales_channels SET name = 'TikTok Shop', api_base_url = ?, is_connected = 1 WHERE code = 'tiktok'",
            (MARKETPLACE_BASE_URL,),
        )
    else:
        conn.execute(
            "INSERT INTO sales_channels(code, name, api_base_url, is_connected) VALUES (?, ?, ?, ?)",
            ("tiktok", "TikTok Shop", MARKETPLACE_BASE_URL, 1),
        )


def normalize_demo_data(conn: sqlite3.Connection) -> None:
    demo_products = [
        ("Son tint bóng căng mọng, trong trẻo BBIA Glow Tint", "cây", "Kệ A1", "BBIA001"),
        ("Son kem nhung thuần chay, nhẹ môi BBIA Last Velvet Tint V Edition 5g", "cây", "Kệ A2", "BBIA002"),
        ("[LIVESTREAM] Son tint bóng căng mọng, trong trẻo BBIA Glow Tint", "cây", "Kệ A3", "BBIA003"),
        ("Má hồng kem mỏng nhẹ, bền màu BBIA Ready To Wear Downy Cheek 3.5g", "hộp", "Kệ B1", "BBIA004"),
        ("[BÁN CHẠY] Bảng Phấn Mắt 6 ô dễ tán và bám màu tốt BBIA Ready To Wear Eye Palette 5g", "bảng", "Kệ B2", "BBIA005"),
        ("Son tint lì lâu trôi, bền màu BBIA Air Fit Tint 4g", "cây", "Kệ B3", "BBIA006"),
        ("Son bóng mượt mà BBIA Over Glaze 4.5g", "cây", "Kệ C1", "BBIA007"),
        ("[LIVESTREAM] Má hồng kem mỏng nhẹ, bền màu BBIA Ready To Wear Downy Cheek 3.5g", "hộp", "Kệ C2", "BBIA008"),
        ("Mascara dày mi, chống lem BBIA Never Die Mascara 7g", "cây", "Kệ C3", "BBIA009"),
        ("Kem che khuyết điểm BBIA Eau Stay Concealer Eau Edition 8.5g", "tuýp", "Kệ D1", "BBIA010"),
        ("Kẻ mắt dạng gel thuần chay, chống nước tuyệt đỉnh BBIA Last Auto Gel Eyeliner 0.3g", "cây", "Kệ D2", "BBIA011"),
        ("[MUA 2 GIÁ 299K] Son tint bóng lâu trôi, bền màu BBIA Water Fit Tint 4g", "cây", "Kệ D3", "BBIA012"),
        ("Mascara tơi mi, không lem trôi BBIA Never Die Mascara Slim 3ml", "cây", "Kệ E1", "BBIA013"),
        ("Son thỏi tint bóng căng mọng, dưỡng ẩm mềm mịn BBIA Ready To Wear Water Lipstick 3g", "thỏi", "Kệ E2", "BBIA014"),
        ("[LIVESTREAM] Son kem nhung thuần chay, nhẹ môi BBIA Last Velvet Tint V Edition 5g", "cây", "Kệ E3", "BBIA015"),
        ("Phấn má hồng mịn lì, đa năng BBIA Last Blush 4g", "hộp", "Kệ F1", "BBIA016"),
        ("Son tint bóng lâu trôi, dưỡng ẩm, màu trong veo BBIA L'eau Tint 4.5g", "cây", "Kệ F2", "BBIA017"),
        ("Kẻ mắt nước đều màu, chống nước, dễ tẩy trang BBIA Last Pen Eyeliner 0.6g", "cây", "Kệ F3", "BBIA018"),
        ("Bảng phấn mắt 10 ô dễ tán và bám màu tốt BBIA Essential Eye Palette 8.5g", "bảng", "Kệ G1", "BBIA019"),
        ("[LIVESTREAM] Son bóng mượt mà, không bết dính BBIA Over Glaze 4.5g", "cây", "Kệ G2", "BBIA020"),
    ]
    conn.executemany("UPDATE products SET name=?, unit=?, location=? WHERE sku=?", demo_products)
    demo_users = [
        ("Qu\u1ea3n tr\u1ecb h\u1ec7 th\u1ed1ng", "Qu\u1ea3n tr\u1ecb vi\u00ean", "admin"),
        ("Qu\u1ea3n l\u00fd kho", "Qu\u1ea3n l\u00fd kho", "warehouse"),
        ("Nh\u00e2n vi\u00ean kho", "Nh\u00e2n vi\u00ean kho", "staff"),
    ]
    conn.executemany("UPDATE users SET full_name=?, role=? WHERE username=?", demo_users)


def load_products_from_csv() -> list[tuple[Any, ...]]:
    candidates = []
    if PRODUCT_CSV_PATH:
        candidates.append(Path(PRODUCT_CSV_PATH))
    candidates.extend([BASE_DIR / "product-list.csv", BASE_DIR.parent / "product-list.csv"])
    csv_path = next((path for path in candidates if path.exists()), None)
    if not csv_path:
        return []

    def as_float(value: str, default: float = 0) -> float:
        try:
            return float(str(value or "").replace(",", "").strip())
        except ValueError:
            return default

    def as_int(value: str, default: int = 0) -> int:
        try:
            return int(float(str(value or "").replace(",", "").strip()))
        except ValueError:
            return default

    rows: list[tuple[Any, ...]] = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            sku = (row.get("SKU") or "").strip()
            name = (row.get("Tên sản phẩm") or "").strip()
            if not sku or not name:
                continue
            rows.append(
                (
                    sku,
                    name,
                    (row.get("Danh mục") or "Makeup").strip(),
                    (row.get("Thương hiệu") or "Bbia").strip(),
                    (row.get("Đơn vị") or "sản phẩm").strip(),
                    as_float(row.get("Giá nhập", "")),
                    as_float(row.get("Giá bán", "")),
                    (row.get("Barcode") or "").strip(),
                    (row.get("Lô hàng") or "").strip(),
                    (row.get("Hạn sử dụng") or "").strip(),
                    (row.get("Link ảnh") or "").strip(),
                    as_int(row.get("Tồn tối thiểu", ""), 10),
                    (row.get("Vị trí") or "Kệ B1").strip(),
                    as_int(row.get("Tồn kho", ""), 100),
                    (row.get("Trạng thái") or "Dang ban").strip(),
                )
            )
    return rows


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(SCHEMA)
        ensure_product_columns(conn)
        ensure_audit_columns(conn)
        ensure_order_columns(conn)
        ensure_channel_urls(conn)
        ensure_tiktok_shop_channel(conn)
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
        product_rows = load_products_from_csv()
        if conn.execute("SELECT COUNT(*) AS count FROM products").fetchone()["count"] == 0 and product_rows:
            conn.executemany(
                """
                INSERT INTO products(sku, name, category, brand, unit, import_price, sale_price, barcode, lot_number, expiry_date, image_url, min_stock, location, stock_qty, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                product_rows,
            )
        elif conn.execute("SELECT COUNT(*) AS count FROM products").fetchone()["count"] == 0:
            conn.executemany(
                """
                INSERT INTO products(sku, name, category, brand, unit, import_price, sale_price, barcode, lot_number, expiry_date, image_url, min_stock, location, stock_qty, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    ("BBIA001", "Son tint bóng căng mọng, trong trẻo BBIA Glow Tint", "Lip Makeup", "BBIA", "cay", 76000, 169000, "880960000001", "BBIA-2026-01", "2028-12-31", "https://down-vn.img.susercontent.com/file/vn-11134258-81ztc-mmpn5o534ft15b", 50, "Ke A1", 420, "Dang ban"),
                    ("BBIA002", "Son kem nhung thuần chay, nhẹ môi BBIA Last Velvet Tint V Edition 5g", "Lip Makeup", "BBIA", "cay", 85000, 189000, "880960000002", "BBIA-2026-02", "2028-11-30", "https://images.unsplash.com/photo-1586495777744-4413f21062fa?auto=format&fit=crop&w=500&q=80", 45, "Ke A2", 310, "Dang ban"),
                    ("BBIA003", "[LIVESTREAM] Son tint bóng căng mọng, trong trẻo BBIA Glow Tint", "Lip Makeup", "BBIA", "cay", 90000, 200000, "880960000003", "BBIA-2026-03", "2028-10-31", "https://images.unsplash.com/photo-1585652757141-8837d676fac8?auto=format&fit=crop&w=500&q=80", 40, "Ke A3", 275, "Dang ban"),
                    ("BBIA004", "Má hồng kem mỏng nhẹ, bền màu BBIA Ready To Wear Downy Cheek 3.5g", "Face Makeup", "BBIA", "hop", 69000, 154000, "880960000004", "BBIA-2026-04", "2028-09-30", "https://images.unsplash.com/photo-1612817288484-6f916006741a?auto=format&fit=crop&w=500&q=80", 35, "Ke B1", 360, "Dang ban"),
                    ("BBIA005", "[BÁN CHẠY] Bảng Phấn Mắt 6 ô dễ tán và bám màu tốt BBIA Ready To Wear Eye Palette 5g", "Eye Makeup", "BBIA", "bang", 130000, 289000, "880960000005", "BBIA-2026-05", "2028-08-31", "https://images.unsplash.com/photo-1522338242992-e1a54906a8da?auto=format&fit=crop&w=500&q=80", 35, "Ke B2", 185, "Dang ban"),
                    ("BBIA006", "Son tint lì lâu trôi, bền màu BBIA Air Fit Tint 4g", "Lip Makeup", "BBIA", "cay", 74000, 165000, "880960000006", "BBIA-2026-06", "2028-07-31", "https://images.unsplash.com/photo-1625093742435-6fa192b6fb10?auto=format&fit=crop&w=500&q=80", 35, "Ke B3", 440, "Dang ban"),
                    ("BBIA007", "Son bóng mượt mà BBIA Over Glaze 4.5g", "Lip Makeup", "BBIA", "cay", 77000, 170050, "880960000007", "BBIA-2026-07", "2028-06-30", "https://images.unsplash.com/photo-1608248543803-ba4f8c70ae0b?auto=format&fit=crop&w=500&q=80", 40, "Ke C1", 390, "Dang ban"),
                    ("BBIA008", "[LIVESTREAM] Má hồng kem mỏng nhẹ, bền màu BBIA Ready To Wear Downy Cheek 3.5g", "Face Makeup", "BBIA", "hop", 74000, 164000, "880960000008", "BBIA-2026-08", "2028-05-31", "https://images.unsplash.com/photo-1556228724-4f5d027f1b86?auto=format&fit=crop&w=500&q=80", 35, "Ke C2", 155, "Dang ban"),
                    ("BBIA009", "Mascara dày mi, chống lem BBIA Never Die Mascara 7g", "Eye Makeup", "BBIA", "cay", 89000, 198000, "880960000009", "BBIA-2026-09", "2028-04-30", "https://images.unsplash.com/photo-1631214540242-3cd8c9e88a76?auto=format&fit=crop&w=500&q=80", 30, "Ke C3", 225, "Dang ban"),
                    ("BBIA010", "Kem che khuyết điểm BBIA Eau Stay Concealer Eau Edition 8.5g", "Base Makeup", "BBIA", "tuyp", 111000, 247000, "880960000010", "BBIA-2026-10", "2028-03-31", "https://images.unsplash.com/photo-1571781926291-c477ebfd024b?auto=format&fit=crop&w=500&q=80", 35, "Ke D1", 475, "Dang ban"),
                    ("BBIA011", "Kẻ mắt dạng gel thuần chay, chống nước tuyệt đỉnh BBIA Last Auto Gel Eyeliner 0.3g", "Eye Makeup", "BBIA", "cay", 45000, 100000, "880960000011", "BBIA-2026-11", "2028-02-28", "https://images.unsplash.com/photo-1512496015851-a90fb38ba796?auto=format&fit=crop&w=500&q=80", 35, "Ke D2", 500, "Dang ban"),
                    ("BBIA012", "[MUA 2 GIÁ 299K] Son tint bóng lâu trôi, bền màu BBIA Water Fit Tint 4g", "Lip Makeup", "BBIA", "cay", 72000, 159000, "880960000012", "BBIA-2026-12", "2028-01-31", "https://images.unsplash.com/photo-1598440947619-2c35fc9aa908?auto=format&fit=crop&w=500&q=80", 25, "Ke D3", 120, "Dang ban"),
                    ("BBIA013", "Mascara tơi mi, không lem trôi BBIA Never Die Mascara Slim 3ml", "Eye Makeup", "BBIA", "cay", 72000, 159000, "880960000013", "BBIA-2027-01", "2028-12-20", "https://images.unsplash.com/photo-1631214540242-3cd8c9e88a76?auto=format&fit=crop&w=500&q=80", 25, "Ke E1", 330, "Dang ban"),
                    ("BBIA014", "Son thỏi tint bóng căng mọng, dưỡng ẩm mềm mịn BBIA Ready To Wear Water Lipstick 3g", "Lip Makeup", "BBIA", "thoi", 79000, 176000, "880960000014", "BBIA-2027-02", "2028-11-20", "https://images.unsplash.com/photo-1515688594390-b649af70d282?auto=format&fit=crop&w=500&q=80", 25, "Ke E2", 260, "Dang ban"),
                    ("BBIA015", "[LIVESTREAM] Son kem nhung thuần chay, nhẹ môi BBIA Last Velvet Tint V Edition 5g", "Lip Makeup", "BBIA", "cay", 90000, 200000, "880960000015", "BBIA-2027-03", "2028-10-20", "https://images.unsplash.com/photo-1586495777744-4413f21062fa?auto=format&fit=crop&w=500&q=80", 30, "Ke E3", 145, "Dang ban"),
                    ("BBIA016", "Phấn má hồng mịn lì, đa năng BBIA Last Blush 4g", "Face Makeup", "BBIA", "hop", 67000, 149000, "880960000016", "BBIA-2027-04", "2028-09-20", "https://images.unsplash.com/photo-1612817288484-6f916006741a?auto=format&fit=crop&w=500&q=80", 30, "Ke F1", 410, "Dang ban"),
                    ("BBIA017", "Son tint bóng lâu trôi, dưỡng ẩm, màu trong veo BBIA L'eau Tint 4.5g", "Lip Makeup", "BBIA", "cay", 87000, 194000, "880960000017", "BBIA-2027-05", "2028-08-20", "https://images.unsplash.com/photo-1608248543803-ba4f8c70ae0b?auto=format&fit=crop&w=500&q=80", 30, "Ke F2", 205, "Dang ban"),
                    ("BBIA018", "Kẻ mắt nước đều màu, chống nước, dễ tẩy trang BBIA Last Pen Eyeliner 0.6g", "Eye Makeup", "BBIA", "cay", 59000, 132000, "880960000018", "BBIA-2027-06", "2028-07-20", "https://images.unsplash.com/photo-1512496015851-a90fb38ba796?auto=format&fit=crop&w=500&q=80", 25, "Ke F3", 370, "Dang ban"),
                    ("BBIA019", "Bảng phấn mắt 10 ô dễ tán và bám màu tốt BBIA Essential Eye Palette 8.5g", "Eye Makeup", "BBIA", "bang", 202000, 448000, "880960000019", "BBIA-2027-07", "2028-06-20", "https://images.unsplash.com/photo-1522338242992-e1a54906a8da?auto=format&fit=crop&w=500&q=80", 30, "Ke G1", 295, "Dang ban"),
                    ("BBIA020", "[LIVESTREAM] Son bóng mượt mà, không bết dính BBIA Over Glaze 4.5g", "Lip Makeup", "BBIA", "cay", 97000, 216000, "880960000020", "BBIA-2027-08", "2028-05-20", "https://images.unsplash.com/photo-1592945403244-b3fbafd7f539?auto=format&fit=crop&w=500&q=80", 25, "Ke G2", 135, "Dang ban"),
                ],
            )
        if conn.execute("SELECT COUNT(*) AS count FROM sales_channels").fetchone()["count"] == 0:
            conn.execute(
                "INSERT INTO sales_channels(code, name, api_base_url, is_connected) VALUES (?, ?, ?, ?)",
                ("tiktok", "TikTok Shop", MARKETPLACE_BASE_URL, 1),
            )
        normalize_demo_data(conn)
        conn.commit()


@app.on_event("startup")
def on_startup() -> None:
    init_db()


async def call_channel_platform_api(channel_code: str, api_base_url: str, sku: str, quantity: int, status: str = "Dang ban") -> tuple[bool, str]:
    """Fires the outbound stock-update call to a connected sales channel over the network.

    `sales_channels.api_base_url` points at the standalone `marketplace` service (a separate
    process/container simulating TikTok Shop) so this is a genuine cross-service HTTP call, not
    an in-process shortcut. Pointing it at the real TikTok Shop Partner Center base URL (with an
    auth header) turns this into a production sync with no other code changes.
    """
    async with httpx.AsyncClient(base_url=api_base_url, timeout=5) as client:
        try:
            response = await client.put(f"/api/mock/{channel_code}/products/{sku}/stock", json={"quantity": quantity, "status": status})
        except httpx.HTTPError as exc:
            return False, f"Loi ket noi toi {channel_code}: {exc}"
    if response.status_code == 200:
        return True, response.json().get("message", "Da dong bo")
    return False, response.json().get("detail", response.text)


async def sync_stock_to_channels(trigger_type: str, order_id: Optional[int], items: list[tuple[int, int, int]], only_channel_id: Optional[int] = None) -> None:
    """Broadcasts the new stock level of each affected product to every connected sales channel.

    Runs as a FastAPI background task so the triggering request (xac nhan phieu xuat/nhap/kiem ke)
    returns immediately; sync results stream to clients afterwards over the /ws/realtime socket,
    which is what keeps overselling risk low without blocking warehouse staff. Pass
    `only_channel_id` to retry a single previously-failed channel instead of resyncing all of them.
    """
    if not items:
        return
    with get_conn() as conn:
        query = "SELECT * FROM sales_channels WHERE is_connected = 1"
        params: tuple[Any, ...] = ()
        if only_channel_id is not None:
            query += " AND id = ?"
            params = (only_channel_id,)
        channels = [dict(row) for row in conn.execute(query, params).fetchall()]
        placeholders = ",".join("?" * len(items))
        products = {
            row["id"]: dict(row)
            for row in conn.execute(f"SELECT id, sku, name, status FROM products WHERE id IN ({placeholders})", tuple(i[0] for i in items)).fetchall()
        }
    for product_id, old_qty, new_qty in items:
        product = products.get(product_id)
        if not product:
            continue
        for channel in channels:
            ok, message = await call_channel_platform_api(channel["code"], channel["api_base_url"], product["sku"], new_qty, product["status"])
            status = "success" if ok else "failed"
            with get_conn() as conn:
                cursor = conn.execute(
                    "INSERT INTO channel_stock_syncs(product_id, channel_id, trigger_type, order_id, old_qty, new_qty, status, message) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (product_id, channel["id"], trigger_type, order_id, old_qty, new_qty, status, message),
                )
                sync_id = cursor.lastrowid
                conn.commit()
            await hub.broadcast(
                {
                    "type": "channel_sync",
                    "id": sync_id,
                    "product_id": product_id,
                    "sku": product["sku"],
                    "product_name": product["name"],
                    "channel_code": channel["code"],
                    "channel_name": channel["name"],
                    "trigger_type": trigger_type,
                    "old_qty": old_qty,
                    "new_qty": new_qty,
                    "status": status,
                    "message": message,
                }
            )
    await hub.broadcast({"type": "stock_changed", "trigger_type": trigger_type})


@app.websocket("/ws/realtime")
async def realtime_socket(websocket: WebSocket) -> None:
    await hub.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        hub.disconnect(websocket)


class WebhookOrderIn(BaseModel):
    channel_code: str
    sku: str
    quantity: int = Field(gt=0)
    customer_name: str = "Khach le"


@app.post("/api/webhooks/orders", status_code=201)
async def receive_channel_order(payload: WebhookOrderIn) -> dict[str, Any]:
    """Inbound webhook called by an external sales channel (the `marketplace` service) whenever
    a customer places an order there, mirroring how TikTok Shop pushes new orders to a seller's
    system. Creates a pending order, deducts sellable stock immediately to reserve inventory,
    and waits until the order is shipped before creating a stock issue document."""
    sync_items: list[tuple[int, int, int]] = []
    with get_conn() as conn:
        channel = conn.execute("SELECT * FROM sales_channels WHERE code = ?", (payload.channel_code,)).fetchone()
        if not channel:
            raise HTTPException(status_code=404, detail=f"Khong tim thay kenh ban hang {payload.channel_code}")
        product = conn.execute("SELECT id, name, sale_price, stock_qty FROM products WHERE sku = ?", (payload.sku,)).fetchone()
        if not product:
            raise HTTPException(status_code=404, detail=f"Khong tim thay san pham {payload.sku}")
        if product["stock_qty"] < payload.quantity:
            raise HTTPException(status_code=409, detail=f"San pham {product['name']} chi con {product['stock_qty']} trong kho")
        code = next_code(conn, "orders", "ORD")
        cursor = conn.execute(
            "INSERT INTO orders(code, order_date, customer_name, channel, status, total_amount, stock_deducted, note) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (code, today_iso(), payload.customer_name, channel["name"], "Cho xu ly", product["sale_price"] * payload.quantity, 1, f"Đơn từ {channel['name']}: {payload.sku} x{payload.quantity}"),
        )
        order_id = cursor.lastrowid
        conn.execute(
            "INSERT INTO order_items(order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
            (order_id, product["id"], payload.quantity, product["sale_price"]),
        )
        conn.execute("UPDATE products SET stock_qty = stock_qty - ? WHERE id = ?", (payload.quantity, product["id"]))
        sync_items.append((product["id"], product["stock_qty"], product["stock_qty"] - payload.quantity))
        log(conn, "create", "order", order_id, f"Nhận đơn hàng mới từ {channel['name']} ({code})")
        conn.commit()
        order = row_to_dict(conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone())
    await hub.broadcast({"type": "new_order", "order": order, "channel_name": channel["name"], "sku": payload.sku, "quantity": payload.quantity})
    await sync_stock_to_channels("marketplace_order", order["id"], sync_items, channel["id"])
    return order


@app.get("/api/channels")
def list_channels() -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT c.*,
          (SELECT COUNT(*) FROM channel_stock_syncs s WHERE s.channel_id = c.id AND s.status = 'failed'
             AND s.id > COALESCE((SELECT MAX(id) FROM channel_stock_syncs WHERE channel_id = c.id AND status = 'success'), 0)) AS pending_failures,
          (SELECT MAX(created_at) FROM channel_stock_syncs s WHERE s.channel_id = c.id) AS last_synced_at
        FROM sales_channels c
        ORDER BY c.name ASC
        """
    )


@app.get("/api/channel-syncs")
def list_channel_syncs(limit: int = Query(50, le=200)) -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT s.*, p.sku, p.name AS product_name, c.name AS channel_name, c.code AS channel_code
        FROM channel_stock_syncs s
        JOIN products p ON p.id = s.product_id
        JOIN sales_channels c ON c.id = s.channel_id
        ORDER BY s.id DESC
        LIMIT ?
        """,
        (limit,),
    )


@app.post("/api/channel-syncs/{sync_id}/retry")
async def retry_channel_sync(sync_id: int, background_tasks: BackgroundTasks) -> dict[str, Any]:
    row = fetch_one("SELECT * FROM channel_stock_syncs WHERE id = ?", (sync_id,))
    if not row:
        raise HTTPException(status_code=404, detail="Khong tim thay ban ghi dong bo")
    product = fetch_one("SELECT stock_qty FROM products WHERE id = ?", (row["product_id"],))
    if not product:
        raise HTTPException(status_code=404, detail="Khong tim thay san pham")
    background_tasks.add_task(sync_stock_to_channels, row["trigger_type"], row["order_id"], [(row["product_id"], row["old_qty"], product["stock_qty"])], row["channel_id"])
    return {"message": "Dang dong bo lai"}


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
        f"""
        SELECT {PRODUCT_FIELDS} FROM products
        WHERE (lower(sku) LIKE ? OR lower(name) LIKE ? OR lower(category) LIKE ? OR lower(brand) LIKE ? OR lower(coalesce(barcode, '')) LIKE ? OR lower(coalesce(lot_number, '')) LIKE ?)
        ORDER BY created_at DESC, id DESC
        """,
        (like, like, like, like, like, like),
    )


@app.get("/api/marketplace/listings")
def marketplace_listings() -> list[dict[str, Any]]:
    return fetch_all(
        f"""
        SELECT {PRODUCT_FIELDS} FROM products
        ORDER BY created_at DESC, id DESC
        """
    )


@app.get("/api/marketplace/orders")
def marketplace_orders(customer_name: str = "") -> list[dict[str, Any]]:
    params: list[Any] = []
    where = ""
    if customer_name.strip():
        where = "WHERE lower(o.customer_name) = ?"
        params.append(customer_name.strip().lower())
    rows = fetch_all(
        f"""
        SELECT
          o.id,
          o.code,
          o.order_date,
          o.customer_name,
          o.channel,
          o.status,
          o.total_amount,
          COALESCE(SUM(oi.quantity), 0) AS total_quantity,
          COALESCE(GROUP_CONCAT(p.name || ' x' || oi.quantity, ', '), '') AS items_summary
        FROM orders o
        LEFT JOIN order_items oi ON oi.order_id = o.id
        LEFT JOIN products p ON p.id = oi.product_id
        {where}
        GROUP BY o.id
        ORDER BY o.id DESC
        LIMIT 20
        """,
        tuple(params),
    )
    return rows


@app.post("/api/products", status_code=201)
def create_product(payload: ProductIn) -> dict[str, Any]:
    with get_conn() as conn:
        try:
            cursor = conn.execute(
                """
                INSERT INTO products(sku, name, category, brand, unit, import_price, sale_price, barcode, lot_number, expiry_date, image_url, min_stock, location, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (payload.sku, payload.name, payload.category, payload.brand, payload.unit, payload.import_price, payload.sale_price, payload.barcode or None, payload.lot_number, payload.expiry_date, payload.image_url, payload.min_stock, payload.location, payload.status),
            )
            log(conn, "create", "product", cursor.lastrowid, f"Tao san pham {payload.sku}")
            conn.commit()
        except sqlite3.IntegrityError as exc:
            raise HTTPException(status_code=409, detail="SKU hoac barcode da ton tai") from exc
        return fetch_one(f"SELECT {PRODUCT_FIELDS} FROM products WHERE id = ?", (cursor.lastrowid,))


@app.put("/api/products/{product_id}")
def update_product(product_id: int, payload: ProductIn, background_tasks: BackgroundTasks) -> dict[str, Any]:
    sync_item: Optional[tuple[int, int, int]] = None
    with get_conn() as conn:
        current = conn.execute("SELECT id, stock_qty FROM products WHERE id = ?", (product_id,)).fetchone()
        if not current:
            raise HTTPException(status_code=404, detail="Khong tim thay san pham")
        try:
            conn.execute(
                """
                UPDATE products SET sku=?, name=?, category=?, brand=?, unit=?, import_price=?, sale_price=?, barcode=?, lot_number=?, expiry_date=?, image_url=?, min_stock=?, location=?, status=?
                WHERE id=?
                """,
                (payload.sku, payload.name, payload.category, payload.brand, payload.unit, payload.import_price, payload.sale_price, payload.barcode or None, payload.lot_number, payload.expiry_date, payload.image_url, payload.min_stock, payload.location, payload.status, product_id),
            )
            log(conn, "update", "product", product_id, f"Cap nhat san pham {payload.sku}")
            sync_item = (product_id, current["stock_qty"], current["stock_qty"])
            conn.commit()
        except sqlite3.IntegrityError as exc:
            raise HTTPException(status_code=409, detail="SKU hoac barcode da ton tai") from exc
    if sync_item:
        background_tasks.add_task(sync_stock_to_channels, "product_update", None, [sync_item])
    return fetch_one(f"SELECT {PRODUCT_FIELDS} FROM products WHERE id = ?", (product_id,))


@app.put("/api/products/{product_id}/stock")
def update_product_stock(product_id: int, payload: ProductStockIn, background_tasks: BackgroundTasks) -> dict[str, Any]:
    sync_item: Optional[tuple[int, int, int]] = None
    with get_conn() as conn:
        product = conn.execute("SELECT id, sku, stock_qty FROM products WHERE id = ?", (product_id,)).fetchone()
        if not product:
            raise HTTPException(status_code=404, detail="Khong tim thay san pham")
        conn.execute("UPDATE products SET stock_qty = ? WHERE id = ?", (payload.stock_qty, product_id))
        log(conn, "update", "product", product_id, f"Cap nhat ton kho {product['sku']} tu {product['stock_qty']} thanh {payload.stock_qty}")
        sync_item = (product_id, product["stock_qty"], payload.stock_qty)
        conn.commit()
    background_tasks.add_task(sync_stock_to_channels, "inventory_edit", None, [sync_item])
    return fetch_one(f"SELECT {PRODUCT_FIELDS} FROM products WHERE id = ?", (product_id,))


@app.delete("/api/products/{product_id}")
def deactivate_product(product_id: int, background_tasks: BackgroundTasks) -> dict[str, str]:
    sync_item: Optional[tuple[int, int, int]] = None
    with get_conn() as conn:
        product = conn.execute("SELECT stock_qty FROM products WHERE id = ?", (product_id,)).fetchone()
        conn.execute("UPDATE products SET status = 'Ngung kinh doanh' WHERE id = ?", (product_id,))
        if product:
            sync_item = (product_id, product["stock_qty"], product["stock_qty"])
        log(conn, "deactivate", "product", product_id, "Vo hieu hoa san pham")
        conn.commit()
    if sync_item:
        background_tasks.add_task(sync_stock_to_channels, "product_update", None, [sync_item])
    return {"message": "Da vo hieu hoa san pham"}


@app.get("/api/suppliers")
def list_suppliers(q: str = "") -> list[dict[str, Any]]:
    like = f"%{q.lower()}%"
    return fetch_all(
        "SELECT * FROM suppliers WHERE status != 'Ngung hop tac' AND (lower(name) LIKE ? OR lower(coalesce(email,'')) LIKE ? OR lower(coalesce(phone,'')) LIKE ?) ORDER BY id DESC",
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
        f"""
        SELECT {PRODUCT_FIELDS},
          CASE
            WHEN status IN ('Ngung kinh doanh', 'Tam ngung') THEN status
            WHEN stock_qty <= 0 THEN 'Het hang'
            WHEN stock_qty <= min_stock THEN 'Sap het'
            ELSE 'An toan'
          END AS inventory_status
        FROM products
        WHERE (lower(sku) LIKE ? OR lower(name) LIKE ? OR lower(category) LIKE ? OR lower(coalesce(lot_number, '')) LIKE ?)
        ORDER BY stock_qty ASC, name ASC
        """,
        (like, like, like, like),
    )
    return [row for row in rows if not low_stock or row["stock_qty"] <= row["min_stock"]]


@app.get("/api/receipts")
def list_receipts() -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT
          r.*,
          s.name AS supplier_name,
          COALESCE(SUM(i.quantity), 0) AS total_quantity,
          COALESCE(SUM(i.quantity * i.unit_price), 0) AS total_value,
          COALESCE(GROUP_CONCAT(p.name || ' (' || COALESCE(p.lot_number, '-') || ') x' || i.quantity, ', '), '') AS items_summary
        FROM stock_receipts r
        LEFT JOIN suppliers s ON s.id = r.supplier_id
        LEFT JOIN stock_receipt_items i ON i.receipt_id = r.id
        LEFT JOIN products p ON p.id = i.product_id
        GROUP BY r.id
        ORDER BY r.id DESC
        """
    )


@app.post("/api/receipts", status_code=201)
def create_receipt(payload: ReceiptIn, background_tasks: BackgroundTasks) -> dict[str, Any]:
    if not payload.items:
        raise HTTPException(status_code=400, detail="Phieu nhap can co it nhat mot san pham")
    sync_items: list[tuple[int, int, int]] = []
    with get_conn() as conn:
        code = next_code(conn, "stock_receipts", "RCP")
        cursor = conn.execute(
            "INSERT INTO stock_receipts(code, receipt_date, supplier_id, note) VALUES (?, ?, ?, ?)",
            (code, today_iso(), payload.supplier_id, payload.note),
        )
        receipt_id = cursor.lastrowid
        for item in payload.items:
            product = conn.execute("SELECT id, stock_qty FROM products WHERE id = ?", (item.product_id,)).fetchone()
            if not product:
                raise HTTPException(status_code=404, detail=f"Khong tim thay san pham #{item.product_id}")
            conn.execute(
                "INSERT INTO stock_receipt_items(receipt_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
                (receipt_id, item.product_id, item.quantity, item.unit_price),
            )
            conn.execute("UPDATE products SET stock_qty = stock_qty + ? WHERE id = ?", (item.quantity, item.product_id))
            sync_items.append((item.product_id, product["stock_qty"], product["stock_qty"] + item.quantity))
        log(conn, "confirm", "receipt", receipt_id, f"Xac nhan phieu nhap {code}")
        conn.commit()
    background_tasks.add_task(sync_stock_to_channels, "receipt", None, sync_items)
    return fetch_one("SELECT * FROM stock_receipts WHERE id = ?", (receipt_id,))


@app.get("/api/issues")
def list_issues() -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT
          i.*,
          o.code AS order_code,
          COALESCE(SUM(ii.quantity), 0) AS total_quantity,
          COALESCE(SUM(ii.quantity * ii.unit_price), 0) AS total_value,
          COALESCE(GROUP_CONCAT(p.name || ' x' || ii.quantity, ', '), '') AS items_summary
        FROM stock_issues i
        LEFT JOIN orders o ON o.id = i.order_id
        LEFT JOIN stock_issue_items ii ON ii.issue_id = i.id
        LEFT JOIN products p ON p.id = ii.product_id
        GROUP BY i.id
        ORDER BY id DESC
        """
    )


def create_issue_for_order(conn: sqlite3.Connection, order_id: int) -> tuple[Optional[int], list[tuple[int, int, int]]]:
    existing = conn.execute("SELECT id FROM stock_issues WHERE order_id = ?", (order_id,)).fetchone()
    if existing:
        return existing["id"], []
    order = conn.execute("SELECT code, stock_deducted FROM orders WHERE id = ?", (order_id,)).fetchone()
    if not order:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn hàng")
    items = conn.execute(
        """
        SELECT oi.product_id, oi.quantity, oi.unit_price, p.stock_qty, p.name
        FROM order_items oi
        JOIN products p ON p.id = oi.product_id
        WHERE oi.order_id = ?
        """,
        (order_id,),
    ).fetchall()
    if not items:
        raise HTTPException(status_code=400, detail="Đơn hàng chưa có sản phẩm")
    should_deduct = int(order["stock_deducted"] or 0) == 0
    if should_deduct:
        for item in items:
            if item["stock_qty"] < item["quantity"]:
                raise HTTPException(status_code=409, detail=f"Sản phẩm {item['name']} không đủ tồn kho")
    code = next_code(conn, "stock_issues", "ISS")
    cursor = conn.execute(
        "INSERT INTO stock_issues(code, issue_date, order_id, note, created_by) VALUES (?, ?, ?, ?, ?)",
        (code, today_iso(), order_id, f"Xác nhận xuất kho cho đơn {order['code']}", "order-status"),
    )
    issue_id = cursor.lastrowid
    sync_items: list[tuple[int, int, int]] = []
    for item in items:
        conn.execute(
            "INSERT INTO stock_issue_items(issue_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
            (issue_id, item["product_id"], item["quantity"], item["unit_price"]),
        )
        if should_deduct:
            conn.execute("UPDATE products SET stock_qty = stock_qty - ? WHERE id = ?", (item["quantity"], item["product_id"]))
            sync_items.append((item["product_id"], item["stock_qty"], item["stock_qty"] - item["quantity"]))
    if should_deduct:
        conn.execute("UPDATE orders SET stock_deducted = 1 WHERE id = ?", (order_id,))
    log(conn, "confirm", "issue", issue_id, f"Xác nhận phiếu xuất {code}")
    return issue_id, sync_items


def restore_order_stock(conn: sqlite3.Connection, order_id: int) -> list[tuple[int, int, int]]:
    order = conn.execute("SELECT code, status, stock_deducted FROM orders WHERE id = ?", (order_id,)).fetchone()
    if not order:
        raise HTTPException(status_code=404, detail="Khong tim thay don hang")
    if order["status"] == "Da xuat kho" or int(order["stock_deducted"] or 0) == 0:
        return []
    items = conn.execute(
        """
        SELECT oi.product_id, oi.quantity, p.stock_qty
        FROM order_items oi
        JOIN products p ON p.id = oi.product_id
        WHERE oi.order_id = ?
        """,
        (order_id,),
    ).fetchall()
    sync_items: list[tuple[int, int, int]] = []
    for item in items:
        new_quantity = item["stock_qty"] + item["quantity"]
        conn.execute("UPDATE products SET stock_qty = ? WHERE id = ?", (new_quantity, item["product_id"]))
        sync_items.append((item["product_id"], item["stock_qty"], new_quantity))
    conn.execute("UPDATE orders SET stock_deducted = 0 WHERE id = ?", (order_id,))
    return sync_items


@app.post("/api/issues", status_code=201)
def create_issue(payload: IssueIn, background_tasks: BackgroundTasks) -> dict[str, Any]:
    if payload.order_id:
        with get_conn() as conn:
            current_order = conn.execute("SELECT status FROM orders WHERE id = ?", (payload.order_id,)).fetchone()
            if not current_order:
                raise HTTPException(status_code=404, detail="Không tìm thấy đơn hàng")
            if current_order["status"] == "Da xuat kho":
                raise HTTPException(status_code=409, detail="Đơn hàng này đã xuất kho")
            issue_id, sync_items = create_issue_for_order(conn, payload.order_id)
            conn.execute("UPDATE orders SET status = 'Da xuat kho' WHERE id = ?", (payload.order_id,))
            conn.commit()
        if sync_items:
            background_tasks.add_task(sync_stock_to_channels, "issue", payload.order_id, sync_items)
        background_tasks.add_task(hub.broadcast, {"type": "order_updated", "order_id": payload.order_id, "status": "Da xuat kho"})
        return fetch_one("SELECT * FROM stock_issues WHERE id = ?", (issue_id,))
    items = payload.items
    if not items:
        raise HTTPException(status_code=400, detail="Phieu xuat can co it nhat mot san pham")
    sync_items: list[tuple[int, int, int]] = []
    with get_conn() as conn:
        for item in items:
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
        for item in items:
            product = conn.execute("SELECT stock_qty FROM products WHERE id = ?", (item.product_id,)).fetchone()
            conn.execute(
                "INSERT INTO stock_issue_items(issue_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
                (issue_id, item.product_id, item.quantity, item.unit_price),
            )
            conn.execute("UPDATE products SET stock_qty = stock_qty - ? WHERE id = ?", (item.quantity, item.product_id))
            sync_items.append((item.product_id, product["stock_qty"], product["stock_qty"] - item.quantity))
        log(conn, "confirm", "issue", issue_id, f"Xac nhan phieu xuat {code}")
        conn.commit()
    background_tasks.add_task(sync_stock_to_channels, "issue", payload.order_id, sync_items)
    return fetch_one("SELECT * FROM stock_issues WHERE id = ?", (issue_id,))


@app.get("/api/orders")
def list_orders() -> list[dict[str, Any]]:
    rows = fetch_all(
        """
        SELECT
          o.*,
          COALESCE(SUM(oi.quantity), SUM(ii.quantity), 0) AS total_quantity,
          COALESCE(
            GROUP_CONCAT(COALESCE(op.name, p.name) || ' x' || COALESCE(oi.quantity, ii.quantity), ', '),
            ''
          ) AS items_summary
        FROM orders o
        LEFT JOIN order_items oi ON oi.order_id = o.id
        LEFT JOIN products op ON op.id = oi.product_id
        LEFT JOIN stock_issues si ON si.order_id = o.id
        LEFT JOIN stock_issue_items ii ON ii.issue_id = si.id
        LEFT JOIN products p ON p.id = ii.product_id
        GROUP BY o.id
        HAVING COALESCE(SUM(CASE WHEN COALESCE(op.status, p.status) IN ('Ngung kinh doanh', 'Tam ngung') THEN 1 ELSE 0 END), 0) = 0
        ORDER BY o.id DESC
        """
    )
    if not rows:
        return rows
    order_ids = tuple(row["id"] for row in rows)
    placeholders = ",".join("?" * len(order_ids))
    item_rows = fetch_all(
        f"""
        SELECT oi.order_id, oi.product_id, p.sku, p.name, oi.quantity, oi.unit_price
        FROM order_items oi
        JOIN products p ON p.id = oi.product_id
        WHERE oi.order_id IN ({placeholders})
        ORDER BY oi.id ASC
        """,
        order_ids,
    )
    grouped: dict[int, list[dict[str, Any]]] = {}
    for item in item_rows:
        grouped.setdefault(item["order_id"], []).append(item)
    for row in rows:
        row["items"] = grouped.get(row["id"], [])
    return rows


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
def update_order(order_id: int, payload: OrderIn, background_tasks: BackgroundTasks) -> dict[str, Any]:
    sync_items: list[tuple[int, int, int]] = []
    with get_conn() as conn:
        current = conn.execute("SELECT id, status FROM orders WHERE id = ?", (order_id,)).fetchone()
        if not current:
            raise HTTPException(status_code=404, detail="Khong tim thay don hang")
        if current["status"] in ("Da xuat kho", "Huy don"):
            raise HTTPException(status_code=409, detail="Don hang da dong, khong the chinh sua")
        if payload.status == "Huy don" and current["status"] != "Huy don":
            sync_items = restore_order_stock(conn, order_id)
        conn.execute(
            "UPDATE orders SET customer_name=?, channel=?, status=?, total_amount=?, note=? WHERE id=?",
            (payload.customer_name, payload.channel, payload.status, payload.total_amount, payload.note, order_id),
        )
        if payload.status == "Da xuat kho" and current["status"] != "Da xuat kho":
            _, sync_items = create_issue_for_order(conn, order_id)
        log(conn, "update", "order", order_id, f"Cap nhat don hang #{order_id}")
        conn.commit()
    if sync_items:
        background_tasks.add_task(sync_stock_to_channels, "issue", order_id, sync_items)
    background_tasks.add_task(hub.broadcast, {"type": "order_updated", "order_id": order_id, "status": payload.status})
    return fetch_one("SELECT * FROM orders WHERE id = ?", (order_id,))


@app.delete("/api/orders/{order_id}")
def delete_order(order_id: int, background_tasks: BackgroundTasks) -> dict[str, str]:
    sync_items: list[tuple[int, int, int]] = []
    with get_conn() as conn:
        current = conn.execute("SELECT id, status FROM orders WHERE id = ?", (order_id,)).fetchone()
        if not current:
            raise HTTPException(status_code=404, detail="Khong tim thay don hang")
        if current["status"] in ("Da xuat kho", "Huy don"):
            raise HTTPException(status_code=409, detail="Don hang da dong, khong the huy")
        sync_items = restore_order_stock(conn, order_id)
        conn.execute("UPDATE orders SET status = 'Huy don' WHERE id = ?", (order_id,))
        log(conn, "cancel", "order", order_id, f"Huy don hang #{order_id}")
        conn.commit()
    if sync_items:
        background_tasks.add_task(sync_stock_to_channels, "order_cancel", order_id, sync_items)
    background_tasks.add_task(hub.broadcast, {"type": "order_updated", "order_id": order_id, "status": "Huy don"})
    return {"message": "Da huy don hang"}


@app.get("/api/inventory-checks")
def list_inventory_checks() -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT c.*, COALESCE(SUM(i.difference), 0) AS total_difference
        FROM inventory_checks c
        LEFT JOIN inventory_check_items i ON i.check_id = c.id
        GROUP BY c.id
        ORDER BY c.id DESC
        """
    )


@app.post("/api/inventory-checks", status_code=201)
def create_inventory_check(payload: InventoryCheckIn, background_tasks: BackgroundTasks) -> dict[str, Any]:
    if not payload.items:
        raise HTTPException(status_code=400, detail="Phieu kiem ke can co it nhat mot san pham")
    sync_items: list[tuple[int, int, int]] = []
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
            diff = product["stock_qty"] - item.actual_qty
            conn.execute(
                "INSERT INTO inventory_check_items(check_id, product_id, system_qty, actual_qty, difference) VALUES (?, ?, ?, ?, ?)",
                (check_id, item.product_id, product["stock_qty"], item.actual_qty, diff),
            )
            conn.execute("UPDATE products SET stock_qty = ? WHERE id = ?", (item.actual_qty, item.product_id))
            if diff != 0:
                sync_items.append((item.product_id, product["stock_qty"], item.actual_qty))
        log(conn, "confirm", "inventory_check", check_id, f"Xac nhan phieu kiem ke {code}")
        conn.commit()
    background_tasks.add_task(sync_stock_to_channels, "inventory_check", None, sync_items)
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
        WHERE status NOT IN ('Ngung kinh doanh', 'Tam ngung')
        """
    ) or {}
    order_stats = fetch_one("SELECT COUNT(*) AS today_orders FROM orders WHERE status != 'Huy don'") or {}
    receipt_stats = fetch_one("SELECT COALESCE(SUM(i.quantity), 0) AS month_receipts FROM stock_receipts r JOIN stock_receipt_items i ON i.receipt_id = r.id") or {}
    issue_stats = fetch_one("SELECT COALESCE(SUM(i.quantity), 0) AS month_issues FROM stock_issues s JOIN stock_issue_items i ON i.issue_id = s.id") or {}
    low_stock = inventory(low_stock=True)[:6]
    activities = fetch_all("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 8")
    return {**stats, **order_stats, **receipt_stats, **issue_stats, "low_stock": low_stock, "activities": activities}


@app.get("/api/activities")
def list_activities() -> list[dict[str, Any]]:
    return fetch_all("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 200")


@app.get("/api/activities/unread-count")
def unread_activities() -> dict[str, int]:
    row = fetch_one("SELECT COUNT(*) AS count FROM audit_logs WHERE is_read = 0") or {"count": 0}
    return {"count": int(row["count"])}


@app.put("/api/activities/read-all")
def mark_all_activities_read() -> dict[str, bool]:
    with get_conn() as conn:
        conn.execute("UPDATE audit_logs SET is_read = 1 WHERE is_read = 0")
        conn.commit()
    return {"ok": True}


@app.put("/api/activities/{activity_id}/read")
def mark_activity_read(activity_id: int) -> dict[str, bool]:
    with get_conn() as conn:
        cursor = conn.execute("UPDATE audit_logs SET is_read = 1 WHERE id = ?", (activity_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Khong tim thay hoat dong")
        conn.commit()
    return {"ok": True}


@app.delete("/api/activities")
def clear_activities() -> dict[str, bool]:
    with get_conn() as conn:
        conn.execute("DELETE FROM audit_logs")
        conn.commit()
    return {"ok": True}


@app.delete("/api/activities/{activity_id}")
def delete_activity(activity_id: int) -> dict[str, bool]:
    with get_conn() as conn:
        cursor = conn.execute("DELETE FROM audit_logs WHERE id = ?", (activity_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Khong tim thay hoat dong")
        conn.commit()
    return {"ok": True}


@app.get("/api/reports/summary")
def report_summary() -> dict[str, Any]:
    receipts = fetch_all(
        "SELECT receipt_date AS date, COUNT(*) AS documents, COALESCE(SUM(i.quantity), 0) AS quantity FROM stock_receipts r LEFT JOIN stock_receipt_items i ON i.receipt_id = r.id GROUP BY receipt_date ORDER BY receipt_date DESC"
    )
    issues = fetch_all(
        "SELECT issue_date AS date, COUNT(*) AS documents, COALESCE(SUM(i.quantity), 0) AS quantity FROM stock_issues s LEFT JOIN stock_issue_items i ON i.issue_id = s.id GROUP BY issue_date ORDER BY issue_date DESC"
    )
    checks = fetch_all(
        "SELECT c.check_date AS date, c.code, COALESCE(SUM(i.difference), 0) AS total_difference FROM inventory_checks c LEFT JOIN inventory_check_items i ON i.check_id = c.id GROUP BY c.id ORDER BY c.id DESC LIMIT 12"
    )
    revenue = fetch_all(
        "SELECT order_date AS date, COUNT(*) AS orders, COALESCE(SUM(total_amount), 0) AS revenue FROM orders WHERE status != 'Huy don' GROUP BY order_date ORDER BY order_date DESC"
    )
    return {"receipts": receipts, "issues": issues, "checks": checks, "revenue": revenue}


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
        headers={"Content-Disposition": "attachment; filename=warehouse-report.csv"},
    )


@app.get("/api/scan/{code}")
def scan_product(code: str) -> dict[str, Any]:
    product = fetch_one(f"SELECT {PRODUCT_FIELDS} FROM products WHERE barcode = ? OR sku = ?", (code, code))
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
