from __future__ import annotations

import asyncio
import os
import random
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent
WAREHOUSE_BASE_URL = os.getenv("WAREHOUSE_BASE_URL", "http://localhost:8000")

app = FastAPI(title="TikTok Shop Demo Storefront", version="1.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FALLBACK_LISTINGS: dict[str, dict[str, Any]] = {
    "SK001": {"sku": "SK001", "name": "Son môi Velvet Tint", "category": "Makeup", "price": 159000, "stock": 500, "status": "Dang ban", "image_url": ""},
    "SK002": {"sku": "SK002", "name": "Kem chống nắng Aqua", "category": "Skincare", "price": 249000, "stock": 350, "status": "Dang ban", "image_url": ""},
}

listings: dict[str, dict[str, Any]] = {}


class BuyRequest(BaseModel):
    quantity: int = Field(gt=0)
    customer_name: str = "Khach TikTok Shop"
    channel_code: str = "tiktok"


class StockUpdate(BaseModel):
    quantity: int = Field(ge=0)
    status: str = "Dang ban"


async def seed_listings_from_warehouse() -> None:
    """Pulls the real, current stock from the warehouse system on boot so the storefront
    starts in sync with it, instead of drifting from hardcoded demo numbers."""
    async with httpx.AsyncClient(base_url=WAREHOUSE_BASE_URL, timeout=5) as client:
        for attempt in range(10):
            try:
                response = await client.get("/api/marketplace/listings")
                if response.status_code == 200:
                    for product in response.json():
                        listings[product["sku"]] = {
                            "sku": product["sku"],
                            "name": product["name"],
                            "category": product["category"],
                            "price": product["sale_price"],
                            "stock": product["stock_qty"],
                            "status": product["status"],
                            "image_url": product["image_url"],
                        }
                    return
            except httpx.HTTPError:
                pass
            await asyncio.sleep(1.5)
    listings.update(FALLBACK_LISTINGS)


@app.on_event("startup")
async def on_startup() -> None:
    await seed_listings_from_warehouse()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/listings")
def list_listings() -> list[dict[str, Any]]:
    return list(listings.values())


@app.get("/api/orders")
async def list_orders(customer_name: str = "") -> list[dict[str, Any]]:
    async with httpx.AsyncClient(base_url=WAREHOUSE_BASE_URL, timeout=5) as client:
        try:
            response = await client.get("/api/marketplace/orders", params={"customer_name": customer_name})
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"Khong the lay trang thai don hang tu he thong kho: {exc}") from exc


@app.delete("/api/orders/{order_id}")
async def cancel_order(order_id: int) -> dict[str, Any]:
    async with httpx.AsyncClient(base_url=WAREHOUSE_BASE_URL, timeout=5) as client:
        try:
            response = await client.delete(f"/api/orders/{order_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.json().get("detail", "Khong the huy don hang")
            raise HTTPException(status_code=exc.response.status_code, detail=detail) from exc
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"Khong the ket noi toi he thong kho de huy don: {exc}") from exc


@app.post("/api/listings/{sku}/buy")
async def buy_listing(sku: str, payload: BuyRequest) -> dict[str, Any]:
    listing = listings.get(sku)
    if not listing:
        raise HTTPException(status_code=404, detail="San pham khong ton tai tren san")
    if listing.get("status") != "Dang ban":
        raise HTTPException(status_code=409, detail="San pham da ngung kinh doanh")
    if listing["stock"] < payload.quantity:
        raise HTTPException(status_code=409, detail=f"Chi con {listing['stock']} san pham tren san")
    async with httpx.AsyncClient(base_url=WAREHOUSE_BASE_URL, timeout=5) as client:
        try:
            response = await client.post(
                "/api/webhooks/orders",
                json={
                    "channel_code": payload.channel_code,
                    "sku": sku,
                    "quantity": payload.quantity,
                    "customer_name": payload.customer_name,
                },
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"Khong the ket noi toi he thong kho, don hang chua duoc ghi nhan: {exc}") from exc
    return {"success": True, "order": response.json(), "remaining_stock": listing["stock"]}


@app.put("/api/mock/{channel_code}/products/{sku}/stock")
async def update_stock(channel_code: str, sku: str, payload: StockUpdate) -> dict[str, Any]:
    """Called by the warehouse system after every stock out/in/count so the storefront
    always reflects the seller's authoritative stock level (prevents overselling)."""
    await asyncio.sleep(random.uniform(0.05, 0.18))
    listing = listings.setdefault(sku, {"sku": sku, "name": sku, "price": 0, "stock": 0})
    listing["stock"] = payload.quantity
    listing["status"] = payload.status
    return {"success": True, "channel": channel_code, "sku": sku, "quantity": payload.quantity, "message": "Da cap nhat ton TikTok Shop"}


@app.get("/", include_in_schema=False)
def storefront() -> FileResponse:
    return FileResponse(BASE_DIR / "storefront.html")
