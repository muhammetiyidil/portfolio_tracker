from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Dict

from fetcher import PricePoints

TR_MONTHS = [
    "", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
    "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"
]


def _delta(current: float, previous: float) -> dict:
    diff = current - previous
    pct = (diff / previous * 100.0) if previous else 0.0
    return {
        "diff": round(diff, 2),
        "pct": round(pct, 2),
        "previous": round(previous, 2),
    }


def _index_catalog(catalog: dict) -> Dict[str, dict]:
    indexed: Dict[str, dict] = {}
    for store in catalog.get("stores", []):
        for item in store.get("items", []):
            indexed[item["id"]] = {
                **item,
                "store_id": store["id"],
                "store_name": store["name"],
            }
    return indexed


def calculate_report(portfolio: dict, catalog: dict, prices: Dict[str, PricePoints]) -> dict:
    """Compute email report & embed live catalog prices for the interactive web dashboard."""
    tr_tz = timezone(timedelta(hours=3))
    now_tr = datetime.now(tr_tz)
    date_label = f"{now_tr.day} {TR_MONTHS[now_tr.month]} {now_tr.year}"
    updated_at = now_tr.strftime("%d.%m.%Y %H:%M")

    catalog_index = _index_catalog(catalog)

    # Enrich stores with live price points for the web UI's dynamic store selector
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

    # Compute summary for default holdings (used by email & initial web state)
    holdings = portfolio.get("holdings", [])
    asset_reports = []
    tot_current = 0.0
    tot_prev_day = 0.0
    tot_prev_week = 0.0
    tot_prev_month = 0.0
    tot_cost = 0.0

    for h in holdings:
        cid = h["catalog_id"]
        meta = catalog_index.get(cid)
        p = prices.get(cid)
        if not meta or not p:
            continue

        qty = float(h["quantity"])
        cost = float(h["cost_basis_total"])

        val_cur = qty * p.current
        val_1d = qty * p.prev_day
        val_1w = qty * p.prev_week
        val_1m = qty * p.prev_month

        tot_current += val_cur
        tot_prev_day += val_1d
        tot_prev_week += val_1w
        tot_prev_month += val_1m
        tot_cost += cost

        asset_reports.append({
            "id": cid,
            "name": meta.get("short_name", meta["name"]),
            "source": meta["store_name"],
            "unit": meta["unit"],
            "icon": meta.get("icon", "stock"),
            "quantity": qty,
            "unit_price": round(p.current, 4),
            "cost_basis_total": round(cost, 2),
            "current_value": round(val_cur, 2),
            "as_of_date": p.as_of_date,
            "changes": {
                "1d": _delta(val_cur, val_1d),
                "1w": _delta(val_cur, val_1w),
                "1m": _delta(val_cur, val_1m),
                "all": _delta(val_cur, cost),
            },
        })

    for item in asset_reports:
        item["weight_pct"] = round(
            (item["current_value"] / tot_current * 100.0) if tot_current else 0.0, 1
        )

    return {
        "title": "Günlük Portföy Raporu",
        "date_label": date_label,
        "updated_at": updated_at,
        "currency": portfolio.get("currency", "TRY"),
        "stores": stores_payload,
        "default_holdings": holdings,
        "total": {
            "current_value": round(tot_current, 2),
            "cost_basis_total": round(tot_cost, 2),
            "changes": {
                "1d": _delta(tot_current, tot_prev_day),
                "1w": _delta(tot_current, tot_prev_week),
                "1m": _delta(tot_current, tot_prev_month),
                "all": _delta(tot_current, tot_cost),
            },
        },
        "assets": asset_reports,
    }
