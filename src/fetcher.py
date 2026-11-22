from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Dict, Optional

import pandas as pd
import yfinance as yf
from pytefas import Crawler

TROY_OUNCE_IN_GRAMS = 31.1034768


@dataclass
class PricePoints:
    current: float
    prev_day: float
    prev_week: float
    prev_month: float
    as_of_date: str

    def to_dict(self) -> dict:
        return asdict(self)


def _extract_price_points(series: pd.Series) -> PricePoints:
    clean = series.dropna().sort_index()
    if clean.empty:
        raise ValueError("Fiyat verisi boş döndü.")

    if getattr(clean.index, "tz", None) is not None:
        clean.index = clean.index.tz_localize(None)

    latest_dt = clean.index[-1]
    current = float(clean.iloc[-1])
    prev_day = float(clean.iloc[-2]) if len(clean) >= 2 else current

    def price_on_or_before(days_ago: int) -> float:
        target = latest_dt - timedelta(days=days_ago)
        subset = clean[clean.index <= target]
        if not subset.empty:
            return float(subset.iloc[-1])
        return float(clean.iloc[0])

    return PricePoints(
        current=round(current, 6),
        prev_day=round(prev_day, 6),
        prev_week=round(price_on_or_before(7), 6),
        prev_month=round(price_on_or_before(30), 6),
        as_of_date=latest_dt.strftime("%Y-%m-%d"),
    )


def _fetch_yf_batch(tickers: list[str], period: str = "3mo") -> Dict[str, pd.Series]:
    if not tickers:
        return {}
    unique = sorted(set(tickers))
    df = yf.download(
        unique,
        period=period,
        interval="1d",
        auto_adjust=False,
        progress=False,
        group_by="ticker",
        threads=True,
    )
    out: Dict[str, pd.Series] = {}
    if len(unique) == 1:
        t = unique[0]
        if "Close" in df:
            out[t] = df["Close"].dropna()
        elif t in df and "Close" in df[t]:
            out[t] = df[t]["Close"].dropna()
    else:
        for t in unique:
            try:
                s = df[t]["Close"].dropna()
                if not s.empty:
                    out[t] = s
            except Exception:
                continue
    return out


def _compute_metal_gram_try(metal_series: pd.Series, fx_series: pd.Series) -> PricePoints:
    m = metal_series.copy()
    f = fx_series.copy()
    if getattr(m.index, "tz", None) is not None:
        m.index = m.index.tz_localize(None)
    if getattr(f.index, "tz", None) is not None:
        f.index = f.index.tz_localize(None)

    m.index = m.index.normalize()
    f.index = f.index.normalize()

    df = pd.DataFrame({"metal": m, "fx": f}).sort_index().ffill().dropna()
    gram_try = (df["metal"] * df["fx"]) / TROY_OUNCE_IN_GRAMS
    return _extract_price_points(gram_try)


def _fetch_tefas_batch(fund_codes: list[str]) -> Dict[str, PricePoints]:
    if not fund_codes:
        return {}
    end_dt = datetime.now()
    start_dt = end_dt - timedelta(days=45)
    crawler = Crawler()
    df = crawler.fetch(
        start=start_dt.strftime("%Y-%m-%d"),
        end=end_dt.strftime("%Y-%m-%d"),
        kind="YAT",
        columns="info",
    )
    if df.empty:
        return {}

    df["date"] = pd.to_datetime(df["date"])
    wanted = {c.upper() for c in fund_codes}
    df = df[df["fund_code"].isin(wanted)]

    results: Dict[str, PricePoints] = {}
    for code, grp in df.groupby("fund_code"):
        s = grp.set_index("date")["price"].astype(float)
        s = s[s > 0]
        if not s.empty:
            results[str(code)] = _extract_price_points(s)
    return results


def fetch_catalog_prices(catalog: dict) -> Dict[str, PricePoints]:
    """Fetch price points for every item across all stores in catalog.json."""
    all_items = [
        item
        for store in catalog.get("stores", [])
        for item in store.get("items", [])
    ]

    yf_tickers: list[str] = []
    tefas_codes: list[str] = []
    needs_fx = False

    for item in all_items:
        t = item["type"]
        if t == "bist":
            yf_tickers.append(item["symbol"])
        elif t == "gold_gram":
            yf_tickers.append("GC=F")
            needs_fx = True
        elif t == "silver_gram":
            yf_tickers.append("SI=F")
            needs_fx = True
        elif t == "tefas":
            tefas_codes.append(item["symbol"])

    if needs_fx:
        yf_tickers.append("TRY=X")

    yf_data = _fetch_yf_batch(yf_tickers)

    tefas_data: Dict[str, PricePoints] = {}
    if tefas_codes:
        try:
            tefas_data = _fetch_tefas_batch(tefas_codes)
        except Exception as exc:
            print(f"[WARN] TEFAS verisi çekilirken hata oluştu: {exc}")

    results: Dict[str, PricePoints] = {}
    fx_series: Optional[pd.Series] = yf_data.get("TRY=X")

    for item in all_items:
        item_id = item["id"]
        t = item["type"]
        sym = item["symbol"]
        try:
            if t == "gold_gram" and "GC=F" in yf_data and fx_series is not None:
                results[item_id] = _compute_metal_gram_try(yf_data["GC=F"], fx_series)
            elif t == "silver_gram" and "SI=F" in yf_data and fx_series is not None:
                results[item_id] = _compute_metal_gram_try(yf_data["SI=F"], fx_series)
            elif t == "bist" and sym in yf_data:
                results[item_id] = _extract_price_points(yf_data[sym])
            elif t == "tefas" and sym.upper() in tefas_data:
                results[item_id] = tefas_data[sym.upper()]
            else:
                print(f"[WARN] Fiyat bulunamadı, atlanıyor: {item_id} ({sym})")
        except Exception as exc:
            print(f"[WARN] {item_id} işlenemedi: {exc}")

    return results
