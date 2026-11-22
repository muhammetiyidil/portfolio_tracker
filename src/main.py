from __future__ import annotations

import argparse
import json
from pathlib import Path

from calculator import build_catalog_payload
from fetcher import fetch_catalog_prices
from render_web import render_web_html


def main() -> None:
    parser = argparse.ArgumentParser(description="Portföy Web Paneli Üreticisi")
    parser.add_argument("--catalog", default="catalog.json", help="Kurum ve varlık kataloğu JSON dosyası")
    parser.add_argument("--out", default="dist", help="Çıktı klasörü (index.html)")
    args = parser.parse_args()

    catalog = json.loads(Path(args.catalog).read_text(encoding="utf-8"))
    prices = fetch_catalog_prices(catalog)
    payload = build_catalog_payload(catalog, prices)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(render_web_html(payload), encoding="utf-8")

    print(f"[OK] {len(prices)} varlığın güncel fiyatı çekildi -> {out_dir / 'index.html'}")


if __name__ == "__main__":
    main()
