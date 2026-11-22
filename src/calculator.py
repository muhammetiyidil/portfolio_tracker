from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Dict

from fetcher import PricePoints

TR_MONTHS = [
    "", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
    "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"
]


def build_catalog_payload(catalog: dict, prices: Dict[str, PricePoints]) -> dict:
    """Attach live price points to every store item in catalog.json for the web UI."""
    tr_tz = timezone(timedelta(hours=3))
    now_tr = datetime.now(tr_tz)
    date_label = f"{now_tr.day} {TR_MONTHS[now_tr.month]} {now_tr.year}"
    updated_at = now_tr.strftime("%d.%m.%Y %H:%M")

    stores_payload = []
    for store in catalog.get("stores", []):
        store_items = []
        for item in store.get("items", []):
            p = prices.get(item["id"])
            if p is None:
                continue
            store_items.append({
                "id": item["id"],
                "name": item["name"],
                "short_name": item.get("short_name", item["name"]),
                "type": item["type"],
                "symbol": item["symbol"],
                "unit": item["unit"],
                "icon": item.get("icon", "stock"),
                "store_id": store["id"],
                "store_name": store["name"],
                "prices": p.to_dict(),
            })
        stores_payload.append({
            "id": store["id"],
            "name": store["name"],
            "items": store_items,
        })

    return {
        "title": "Portföyüm",
        "date_label": date_label,
        "updated_at": updated_at,
        "stores": stores_payload,
    }
