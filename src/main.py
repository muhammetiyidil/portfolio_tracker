from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from calculator import calculate_report
from fetcher import fetch_catalog_prices
from render_email import render_email_html, _fmt_try, _fmt_signed_pct
from render_web import render_web_html
from send_email import send_report_email


def load_json_or_secret(path: Path, env_key: str) -> dict:
    env_val = os.getenv(env_key, "").strip()
    if env_val:
        return json.loads(env_val)
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Günlük Portföy Raporu Üreticisi")
    parser.add_argument("--config", default="portfolio.json", help="Portföy JSON dosyası")
    parser.add_argument("--catalog", default="catalog.json", help="Kurum ve varlık kataloğu JSON dosyası")
    parser.add_argument("--out", default="dist", help="Çıktı klasörü (index.html, email.html, report.json)")
    parser.add_argument("--send-email", action="store_true", help="SMTP ile e-posta gönder")
    args = parser.parse_args()

    catalog = json.loads(Path(args.catalog).read_text(encoding="utf-8"))
    portfolio = load_json_or_secret(Path(args.config), "PORTFOLIO_JSON")

    prices = fetch_catalog_prices(catalog)
    report = calculate_report(portfolio, catalog, prices)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    dashboard_pin = os.getenv("DASHBOARD_PIN", "").strip() or None
    dashboard_url = os.getenv("DASHBOARD_URL", "").strip() or None

    web_html = render_web_html(report, dashboard_pin=dashboard_pin)
    email_html = render_email_html(report, dashboard_url=dashboard_url)

    (out_dir / "index.html").write_text(web_html, encoding="utf-8")
    (out_dir / "email.html").write_text(email_html, encoding="utf-8")
    if not dashboard_pin:
        (out_dir / "report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    tot_val = _fmt_try(report["total"]["current_value"], 0)
    tot_1d = _fmt_signed_pct(report["total"]["changes"]["1d"]["pct"])
    print(f"[OK] Katalogdan {len(prices)} varlık çekildi -> {out_dir / 'index.html'}")
    print(f"     Toplam: {tot_val} | 1G: {tot_1d}")

    if args.send_email:
        subject = f"Portföy Raporu ({report['date_label']}): {tot_val} ({tot_1d})"
        send_report_email(subject, email_html)
        print("[OK] E-posta başarıyla gönderildi.")


if __name__ == "__main__":
    main()
