from __future__ import annotations

import base64
import json
import os
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes


def _encrypt_payload(report: dict, pin: str) -> dict:
    salt = os.urandom(16)
    iv = os.urandom(12)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100_000,
    )
    key = kdf.derive(pin.encode("utf-8"))
    aesgcm = AESGCM(key)
    plaintext = json.dumps(report, ensure_ascii=False).encode("utf-8")
    ciphertext = aesgcm.encrypt(iv, plaintext, None)
    return {
        "encrypted": True,
        "salt": base64.b64encode(salt).decode("ascii"),
        "iv": base64.b64encode(iv).decode("ascii"),
        "ciphertext": base64.b64encode(ciphertext).decode("ascii"),
    }


def render_web_html(report: dict, dashboard_pin: Optional[str] = None) -> str:
    if dashboard_pin:
        payload = _encrypt_payload(report, dashboard_pin)
    else:
        payload = {"encrypted": False, "data": report}

    payload_json = json.dumps(payload, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover" />
  <meta name="apple-mobile-web-app-capable" content="yes" />
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
  <meta name="apple-mobile-web-app-title" content="Portföyüm" />
  <meta name="theme-color" content="#0D0D0F" />
  <title>Günlük Portföy Raporu</title>
  <link rel="apple-touch-icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 180 180'%3E%3Crect width='180' height='180' rx='40' fill='%2316161A'/%3E%3Cpath d='M36 126h108M48 110l28-32 24 18 32-42' stroke='%2322C55E' stroke-width='12' stroke-linecap='round' stroke-linejoin='round' fill='none'/%3E%3C/svg%3E" />
  <style>
    :root {{
      --bg: #0D0D0F;
      --card: #16161A;
      --card-hover: #1D1D22;
      --border: #26262C;
      --text: #F4F4F6;
      --muted: #9A9AA6;
      --green: #22C55E;
      --red: #EF4444;
      --flat: #9A9AA6;
      --pill-active: #2E2E38;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      padding: max(20px, env(safe-area-inset-top)) 16px max(36px, env(safe-area-inset-bottom));
      display: flex;
      justify-content: center;
    }}
    .container {{ width: 100%; max-width: 460px; }}
    .header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 10px;
      margin-bottom: 16px;
    }}
    .header h1 {{
      font-size: 24px;
      font-weight: 700;
      letter-spacing: -0.4px;
      line-height: 1.15;
    }}
    .header .date {{
      color: var(--muted);
      font-size: 12.5px;
      margin-top: 4px;
    }}
    .add-btn {{
      background: var(--green);
      color: #06210E;
      border: none;
      border-radius: 12px;
      padding: 10px 14px;
      font-size: 13.5px;
      font-weight: 700;
      cursor: pointer;
      white-space: nowrap;
      flex-shrink: 0;
    }}
    .segmented {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 4px;
      background: var(--card);
      border: 1px solid var(--border);
      padding: 4px;
      border-radius: 14px;
      margin-bottom: 16px;
    }}
    .segmented button {{
      border: none;
      background: transparent;
      color: var(--muted);
      font-size: 13px;
      font-weight: 600;
      padding: 9px 4px;
      border-radius: 10px;
      cursor: pointer;
      transition: all 0.16s ease;
    }}
    .segmented button.active {{
      background: var(--pill-active);
      color: var(--text);
      box-shadow: 0 2px 8px rgba(0,0,0,0.35);
    }}
    .hero-card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 20px;
      padding: 20px;
      margin-bottom: 18px;
    }}
    .hero-label {{ color: var(--muted); font-size: 13px; font-weight: 500; }}
    .hero-value {{
      font-size: 35px;
      font-weight: 700;
      letter-spacing: -1px;
      margin-top: 6px;
      font-variant-numeric: tabular-nums;
    }}
    .hero-delta {{
      display: flex;
      align-items: center;
      gap: 6px;
      margin-top: 8px;
      font-size: 15px;
      font-weight: 600;
      flex-wrap: wrap;
    }}
    .hero-delta .period-note {{ color: var(--muted); font-weight: 400; font-size: 13px; }}
    .divider {{ height: 1px; background: var(--border); margin: 16px 0; }}
    .sub-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px 12px; }}
    .sub-item .sub-label {{ color: var(--muted); font-size: 12px; margin-bottom: 4px; }}
    .sub-item .sub-val {{ font-size: 13.5px; font-weight: 600; font-variant-numeric: tabular-nums; }}

    .store-bar {{
      display: flex;
      gap: 8px;
      margin-bottom: 14px;
      overflow-x: auto;
    }}
    .store-chip {{
      border: 1px solid var(--border);
      background: var(--card);
      color: var(--muted);
      border-radius: 999px;
      padding: 7px 14px;
      font-size: 12.5px;
      font-weight: 600;
      cursor: pointer;
      white-space: nowrap;
    }}
    .store-chip.active {{
      background: var(--text);
      color: var(--bg);
      border-color: var(--text);
    }}

    .section-title {{
      font-size: 16px;
      font-weight: 700;
      margin-bottom: 10px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .section-title span.hint {{ font-size: 12px; font-weight: 400; color: var(--muted); }}

    .asset-list {{ display: flex; flex-direction: column; gap: 10px; }}
    .asset-card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 14px 16px;
      transition: background 0.15s ease;
    }}
    .asset-top {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      cursor: pointer;
    }}
    .asset-left {{ display: flex; align-items: center; gap: 12px; min-width: 0; }}
    .asset-icon {{
      width: 42px;
      height: 42px;
      border-radius: 12px;
      background: #1E1E24;
      border: 1px solid #2A2A33;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }}
    .asset-name {{
      font-size: 15px;
      font-weight: 600;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
    .asset-qty {{ font-size: 12.5px; color: var(--muted); margin-top: 2px; }}
    .asset-right {{ text-align: right; flex-shrink: 0; font-variant-numeric: tabular-nums; }}
    .asset-val {{ font-size: 15.5px; font-weight: 700; }}
    .asset-chg {{ font-size: 12.5px; font-weight: 600; margin-top: 2px; }}

    .asset-details {{
      display: none;
      margin-top: 12px;
      padding-top: 12px;
      border-top: 1px solid var(--border);
      font-size: 12.5px;
      color: var(--muted);
    }}
    .asset-card.open .asset-details {{ display: block; }}
    .detail-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px 12px; margin-bottom: 12px; }}
    .detail-row {{ display: flex; flex-direction: column; gap: 2px; }}
    .detail-row strong {{ color: var(--text); font-size: 13px; font-variant-numeric: tabular-nums; }}

    .inline-edit {{
      background: #111114;
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 10px;
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
    }}
    .inline-edit label {{
      display: flex;
      flex-direction: column;
      gap: 4px;
      font-size: 11px;
      color: var(--muted);
    }}
    .inline-edit input {{
      width: 100%;
      padding: 8px 10px;
      border-radius: 8px;
      border: 1px solid var(--border);
      background: var(--card);
      color: var(--text);
      font-size: 14px;
    }}
    .inline-actions {{
      grid-column: 1 / -1;
      display: flex;
      gap: 8px;
      margin-top: 2px;
    }}
    .btn-save {{
      flex: 1;
      background: var(--green);
      color: #06210E;
      border: none;
      border-radius: 8px;
      padding: 9px;
      font-size: 13px;
      font-weight: 700;
      cursor: pointer;
    }}
    .btn-del {{
      background: #2A1619;
      color: var(--red);
      border: 1px solid #4C1D24;
      border-radius: 8px;
      padding: 9px 14px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
    }}

    .empty-state {{
      background: var(--card);
      border: 1px dashed var(--border);
      border-radius: 16px;
      padding: 28px 16px;
      text-align: center;
      color: var(--muted);
      font-size: 13.5px;
    }}
    .empty-state button {{
      margin-top: 12px;
      background: var(--green);
      color: #06210E;
      border: none;
      border-radius: 10px;
      padding: 10px 16px;
      font-weight: 700;
      cursor: pointer;
    }}

    .pos {{ color: var(--green); }}
    .neg {{ color: var(--red); }}
    .flat {{ color: var(--flat); }}

    .footer {{
      text-align: center;
      color: var(--muted);
      font-size: 11.5px;
      margin-top: 22px;
      line-height: 1.6;
    }}
    .footer-actions {{
      display: flex;
      justify-content: center;
      gap: 10px;
      margin-bottom: 10px;
      flex-wrap: wrap;
    }}
    .ghost-btn {{
      background: var(--card);
      color: var(--muted);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 7px 12px;
      font-size: 12px;
      cursor: pointer;
    }}

    /* Modal */
    .modal-backdrop {{
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.72);
      display: none;
      align-items: flex-end;
      justify-content: center;
      z-index: 100;
      padding: 12px;
    }}
    .modal-backdrop.show {{ display: flex; }}
    .modal {{
      width: 100%;
      max-width: 460px;
      background: #16161A;
      border: 1px solid var(--border);
      border-radius: 22px;
      padding: 20px;
      margin-bottom: env(safe-area-inset-bottom);
    }}
    .modal-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
    }}
    .modal-header h3 {{ font-size: 18px; font-weight: 700; }}
    .close-btn {{
      background: #23232A;
      color: var(--text);
      border: none;
      width: 32px;
      height: 32px;
      border-radius: 10px;
      font-size: 18px;
      cursor: pointer;
    }}
    .field {{ margin-bottom: 12px; }}
    .field label {{
      display: block;
      font-size: 12px;
      color: var(--muted);
      margin-bottom: 6px;
    }}
    .store-tabs {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
    }}
    .store-tab {{
      padding: 10px;
      border-radius: 12px;
      border: 1px solid var(--border);
      background: var(--bg);
      color: var(--muted);
      font-weight: 600;
      font-size: 14px;
      cursor: pointer;
    }}
    .store-tab.active {{
      border-color: var(--green);
      color: var(--text);
      background: #132219;
    }}
    .field select, .field input {{
      width: 100%;
      padding: 11px 12px;
      border-radius: 12px;
      border: 1px solid var(--border);
      background: var(--bg);
      color: var(--text);
      font-size: 15px;
    }}
    .field-row {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
    }}
    .modal-submit {{
      width: 100%;
      padding: 13px;
      border-radius: 12px;
      border: none;
      background: var(--green);
      color: #06210E;
      font-weight: 700;
      font-size: 15px;
      cursor: pointer;
      margin-top: 4px;
    }}
    .toast {{
      position: fixed;
      bottom: 24px;
      left: 50%;
      transform: translateX(-50%);
      background: #22C55E;
      color: #06210E;
      font-weight: 700;
      font-size: 13px;
      padding: 10px 18px;
      border-radius: 999px;
      display: none;
      z-index: 200;
    }}
    .toast.show {{ display: block; }}

    .lock-screen {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 20px;
      padding: 28px 20px;
      text-align: center;
      margin-top: 40px;
    }}
    .lock-screen h2 {{ font-size: 20px; margin-bottom: 8px; }}
    .lock-screen p {{ font-size: 13px; color: var(--muted); margin-bottom: 18px; }}
    .lock-screen input {{
      width: 100%;
      padding: 12px 14px;
      border-radius: 12px;
      border: 1px solid var(--border);
      background: var(--bg);
      color: var(--text);
      font-size: 16px;
      text-align: center;
      margin-bottom: 12px;
    }}
    .lock-screen button {{
      width: 100%;
      padding: 12px;
      border-radius: 12px;
      border: none;
      background: var(--green);
      color: #06210E;
      font-weight: 700;
      font-size: 15px;
      cursor: pointer;
    }}
    .lock-error {{ color: var(--red); font-size: 13px; margin-top: 10px; }}
  </style>
</head>
<body>
  <div class="container" id="app"></div>
  <div class="modal-backdrop" id="modal-backdrop" onclick="if(event.target===this) closeModal()">
    <div class="modal" id="modal-content"></div>
  </div>
  <div class="toast" id="toast"></div>

  <script>
    const PAYLOAD = {payload_json};
    const STORAGE_KEY = "portfolio_holdings_v2";

    const PERIOD_META = {{
      "1d":  {{ tab: "Günlük",   label: "Düne göre" }},
      "1w":  {{ tab: "Haftalık", label: "Geçen haftaya göre" }},
      "1m":  {{ tab: "Aylık",    label: "Geçen aya göre" }},
      "all": {{ tab: "Maliyet",  label: "İlk maliyete göre" }}
    }};

    let currentPeriod = "1d";
    let currentStoreFilter = "all";
    let modalStoreId = "kuveytturk";
    let openAssetIds = new Set();
    let reportData = null;
    let catalogMap = {{}};
    let holdings = [];

    function showToast(msg) {{
      const t = document.getElementById("toast");
      t.textContent = msg;
      t.classList.add("show");
      setTimeout(() => t.classList.remove("show"), 2200);
    }}

    function fmtTRY(val, decimals = 2) {{
      return "₺" + Number(val).toLocaleString("tr-TR", {{
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
      }});
    }}

    function fmtSignedTRY(val, decimals = 0) {{
      const abs = Math.abs(val);
      const formatted = fmtTRY(abs, decimals);
      if (val > 0.005) return "+" + formatted;
      if (val < -0.005) return "−" + formatted;
      return formatted;
    }}

    function fmtSignedPct(pct) {{
      const abs = Math.abs(pct).toLocaleString("tr-TR", {{
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }});
      if (pct > 0.005) return "+%" + abs;
      if (pct < -0.005) return "−%" + abs;
      return "%0,00";
    }}

    function clsFor(val) {{
      if (val > 0.005) return "pos";
      if (val < -0.005) return "neg";
      return "flat";
    }}

    function fmtQty(qty, unit) {{
      const s = Number(qty).toLocaleString("tr-TR", {{ maximumFractionDigits: 4 }});
      return `${{s}} ${{unit}}`;
    }}

    function deltaObj(cur, prev) {{
      const diff = cur - prev;
      const pct = prev ? (diff / prev * 100) : 0;
      return {{ diff, pct, previous: prev }};
    }}

    function iconSvg(kind) {{
      if (kind === "gold") {{
        return `<svg width="22" height="22" viewBox="0 0 24 24"><defs><linearGradient id="g1" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#FDE047"/><stop offset="100%" stop-color="#F59E0B"/></linearGradient></defs><rect x="3" y="3" width="18" height="18" rx="5" fill="url(#g1)"/></svg>`;
      }}
      if (kind === "silver") {{
        return `<svg width="22" height="22" viewBox="0 0 24 24"><defs><radialGradient id="s1" cx="35%" cy="35%" r="70%"><stop offset="0%" stop-color="#FFFFFF"/><stop offset="100%" stop-color="#9CA3AF"/></radialGradient></defs><circle cx="12" cy="12" r="9" fill="url(#s1)"/></svg>`;
      }}
      if (kind === "fund") {{
        return `<svg width="22" height="22" viewBox="0 0 24 24" fill="none"><rect x="3" y="12" width="4" height="9" rx="1.5" fill="#22C55E"/><rect x="10" y="7" width="4" height="14" rx="1.5" fill="#3B82F6"/><rect x="17" y="3" width="4" height="18" rx="1.5" fill="#A855F7"/></svg>`;
      }}
      return `<svg width="22" height="22" viewBox="0 0 24 24" fill="none"><rect x="2" y="3" width="20" height="18" rx="4" fill="#1E293B" stroke="#38BDF8" stroke-width="1.5"/><path d="M6 15l4-4 3 2.5 5-5.5" stroke="#38BDF8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
    }}

    function loadHoldings() {{
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {{
        try {{
          const parsed = JSON.parse(saved);
          if (Array.isArray(parsed)) return parsed;
        }} catch (e) {{}}
      }}
      return (reportData.default_holdings || []).map(h => ({{ ...h }}));
    }}

    function saveHoldings() {{
      localStorage.setItem(STORAGE_KEY, JSON.stringify(holdings));
    }}

    function computeState() {{
      let totCur = 0, tot1d = 0, tot1w = 0, tot1m = 0, totCost = 0;
      const computed = [];

      for (const h of holdings) {{
        const item = catalogMap[h.catalog_id];
        if (!item) continue;
        if (currentStoreFilter !== "all" && item.store_id !== currentStoreFilter) continue;

        const qty = Number(h.quantity) || 0;
        const cost = Number(h.cost_basis_total) || 0;
        const p = item.prices;

        const cur = qty * p.current;
        const v1d = qty * p.prev_day;
        const v1w = qty * p.prev_week;
        const v1m = qty * p.prev_month;

        totCur += cur;
        tot1d += v1d;
        tot1w += v1w;
        tot1m += v1m;
        totCost += cost;

        computed.push({{
          ...item,
          quantity: qty,
          cost_basis_total: cost,
          current_value: cur,
          changes: {{
            "1d": deltaObj(cur, v1d),
            "1w": deltaObj(cur, v1w),
            "1m": deltaObj(cur, v1m),
            "all": deltaObj(cur, cost)
          }}
        }});
      }}

      for (const a of computed) {{
        a.weight_pct = totCur ? Number((a.current_value / totCur * 100).toFixed(1)) : 0;
      }}

      return {{
        total: {{
          current_value: totCur,
          cost_basis_total: totCost,
          changes: {{
            "1d": deltaObj(totCur, tot1d),
            "1w": deltaObj(totCur, tot1w),
            "1m": deltaObj(totCur, tot1m),
            "all": deltaObj(totCur, totCost)
          }}
        }},
        assets: computed
      }};
    }}

    function renderApp() {{
      const d = reportData;
      const state = computeState();
      const tot = state.total;
      const activeChg = tot.changes[currentPeriod];
      const activeCls = clsFor(activeChg.diff);
      const arrow = activeChg.diff > 0.005 ? "↗" : (activeChg.diff < -0.005 ? "↘" : "→");

      const tabsHtml = Object.entries(PERIOD_META).map(([key, meta]) => `
        <button class="${{key === currentPeriod ? "active" : ""}}" onclick="setPeriod('${{key}}')">${{meta.tab}}</button>
      `).join("");

      const subPeriods = [
        {{ label: "Düne göre", chg: tot.changes["1d"] }},
        {{ label: "Geçen haftaya göre", chg: tot.changes["1w"] }},
        {{ label: "Geçen aya göre", chg: tot.changes["1m"] }},
        {{ label: "İlk maliyet (" + fmtTRY(tot.cost_basis_total, 0) + ")", chg: tot.changes["all"] }}
      ];

      const subHtml = subPeriods.map(s => `
        <div class="sub-item">
          <div class="sub-label">${{s.label}}</div>
          <div class="sub-val ${{clsFor(s.chg.diff)}}">${{fmtSignedTRY(s.chg.diff, 0)}} (${{fmtSignedPct(s.chg.pct)}})</div>
        </div>
      `).join("");

      const storeChips = [
        {{ id: "all", name: "Tümü" }},
        ...d.stores.map(s => ({{ id: s.id, name: s.name }}))
      ].map(s => `
        <button class="store-chip ${{currentStoreFilter === s.id ? "active" : ""}}" onclick="setStoreFilter('${{s.id}}')">${{s.name}}</button>
      `).join("");

      let assetsHtml = "";
      if (state.assets.length === 0) {{
        assetsHtml = `
          <div class="empty-state">
            Bu görünümde henüz varlık yok.<br/>
            Kuveyt Türk veya Midas'tan varlık ekleyerek başlayabilirsin.
            <div><button onclick="openAddModal()">+ İlk Varlığını Ekle</button></div>
          </div>
        `;
      }} else {{
        assetsHtml = state.assets.map(a => {{
          const c = a.changes[currentPeriod];
          const cCls = clsFor(c.diff);
          const statusText = Math.abs(c.pct) < 0.01 ? "Sabit %0,00" : `${{fmtSignedPct(c.pct)}} · ${{fmtSignedTRY(c.diff, 0)}}`;
          const isOpen = openAssetIds.has(a.id);
          return `
            <div class="asset-card ${{isOpen ? "open" : ""}}" id="card-${{a.id}}">
              <div class="asset-top" onclick="toggleAsset('${{a.id}}')">
                <div class="asset-left">
                  <div class="asset-icon">${{iconSvg(a.icon)}}</div>
                  <div style="min-width:0">
                    <div class="asset-name">${{a.short_name}}</div>
                    <div class="asset-qty">${{fmtQty(a.quantity, a.unit)}} · ${{a.store_name}}</div>
                  </div>
                </div>
                <div class="asset-right">
                  <div class="asset-val">${{fmtTRY(a.current_value, 0)}}</div>
                  <div class="asset-chg ${{cCls}}">${{statusText}}</div>
                </div>
              </div>
              <div class="asset-details">
                <div class="detail-grid">
                  <div class="detail-row">
                    <span>İlk Alış Maliyeti</span>
                    <strong>${{fmtTRY(a.cost_basis_total, 2)}}</strong>
                  </div>
                  <div class="detail-row">
                    <span>Toplam Kâr / Zarar</span>
                    <strong class="${{clsFor(a.changes.all.diff)}}">${{fmtSignedTRY(a.changes.all.diff, 0)}} (${{fmtSignedPct(a.changes.all.pct)}})</strong>
                  </div>
                  <div class="detail-row">
                    <span>Birim Fiyat</span>
                    <strong>${{fmtTRY(a.prices.current, 2)}}</strong>
                  </div>
                  <div class="detail-row">
                    <span>Portföy Ağırlığı</span>
                    <strong>%${{a.weight_pct.toLocaleString("tr-TR")}}</strong>
                  </div>
                  <div class="detail-row">
                    <span>1G / 1H Değişim</span>
                    <strong>
                      <span class="${{clsFor(a.changes['1d'].pct)}}">${{fmtSignedPct(a.changes['1d'].pct)}}</span> /
                      <span class="${{clsFor(a.changes['1w'].pct)}}">${{fmtSignedPct(a.changes['1w'].pct)}}</span>
                    </strong>
                  </div>
                  <div class="detail-row">
                    <span>1A Değişim</span>
                    <strong class="${{clsFor(a.changes['1m'].pct)}}">${{fmtSignedPct(a.changes['1m'].pct)}} (${{fmtSignedTRY(a.changes['1m'].diff, 0)}})</strong>
                  </div>
                </div>

                <div class="inline-edit">
                  <label>
                    Miktar (${{a.unit}})
                    <input type="number" step="any" id="qty-${{a.id}}" value="${{a.quantity}}" />
                  </label>
                  <label>
                    İlk Maliyet (₺)
                    <input type="number" step="any" id="cost-${{a.id}}" value="${{a.cost_basis_total}}" />
                  </label>
                  <div class="inline-actions">
                    <button class="btn-save" onclick="updateHolding('${{a.id}}')">Miktarı Güncelle</button>
                    <button class="btn-del" onclick="deleteHolding('${{a.id}}')">Sil</button>
                  </div>
                </div>
              </div>
            </div>
          `;
        }}).join("");
      }}

      const storeLabel = currentStoreFilter === "all"
        ? "Toplam portföy değeri"
        : (d.stores.find(s => s.id === currentStoreFilter)?.name + " toplamı");

      document.getElementById("app").innerHTML = `
        <div class="header">
          <div>
            <h1>${{d.title}}</h1>
            <div class="date">${{d.date_label}} · ${{d.updated_at}}</div>
          </div>
          <button class="add-btn" onclick="openAddModal()">+ Ekle</button>
        </div>

        <div class="segmented">${{tabsHtml}}</div>

        <div class="hero-card">
          <div class="hero-label">${{storeLabel}}</div>
          <div class="hero-value">${{fmtTRY(tot.current_value, 2)}}</div>
          <div class="hero-delta">
            <span class="${{activeCls}}">${{arrow}} ${{fmtSignedTRY(activeChg.diff, 0)}} (${{fmtSignedPct(activeChg.pct)}})</span>
            <span class="period-note">${{PERIOD_META[currentPeriod].label}}</span>
          </div>
          <div class="divider"></div>
          <div class="sub-grid">${{subHtml}}</div>
        </div>

        <div class="store-bar">${{storeChips}}</div>

        <div class="section-title">
          <span>Varlıklarım</span>
          <span class="hint">Miktar değiştirmek için dokun</span>
        </div>
        <div class="asset-list">${{assetsHtml}}</div>

        <div class="footer">
          <div class="footer-actions">
            <button class="ghost-btn" onclick="copySecretJson()">📋 PORTFOLIO_JSON Kopyala</button>
            <button class="ghost-btn" onclick="resetDefaults()">↺ Varsayılana Dön</button>
          </div>
          Değişiklikler telefonuna kaydedilir ve tüm sayfa anlık hesaplanır.<br/>
          E-posta raporunun da aynı miktarları kullanması için JSON'u kopyalayıp GitHub Secret'a yapıştırabilirsin.
        </div>
      `;
    }}

    window.setPeriod = function(period) {{
      currentPeriod = period;
      renderApp();
    }};

    window.setStoreFilter = function(storeId) {{
      currentStoreFilter = storeId;
      renderApp();
    }};

    window.toggleAsset = function(id) {{
      if (openAssetIds.has(id)) openAssetIds.delete(id);
      else openAssetIds.add(id);
      renderApp();
    }};

    window.updateHolding = function(id) {{
      const qty = parseFloat(document.getElementById("qty-" + id).value);
      const cost = parseFloat(document.getElementById("cost-" + id).value);
      if (isNaN(qty) || qty < 0) return showToast("Geçerli bir miktar gir");
      const idx = holdings.findIndex(h => h.catalog_id === id);
      if (idx >= 0) {{
        holdings[idx].quantity = qty;
        holdings[idx].cost_basis_total = isNaN(cost) ? 0 : cost;
        saveHoldings();
        renderApp();
        showToast("Güncellendi");
      }}
    }};

    window.deleteHolding = function(id) {{
      holdings = holdings.filter(h => h.catalog_id !== id);
      openAssetIds.delete(id);
      saveHoldings();
      renderApp();
      showToast("Varlık kaldırıldı");
    }};

    window.openAddModal = function() {{
      if (currentStoreFilter !== "all") modalStoreId = currentStoreFilter;
      renderModal();
      document.getElementById("modal-backdrop").classList.add("show");
    }};

    window.closeModal = function() {{
      document.getElementById("modal-backdrop").classList.remove("show");
    }};

    window.selectModalStore = function(storeId) {{
      modalStoreId = storeId;
      renderModal();
    }};

    function renderModal() {{
      const store = reportData.stores.find(s => s.id === modalStoreId) || reportData.stores[0];
      const storeTabs = reportData.stores.map(s => `
        <button class="store-tab ${{s.id === store.id ? "active" : ""}}" onclick="selectModalStore('${{s.id}}')">${{s.name}}</button>
      `).join("");

      const options = store.items.map(it => `
        <option value="${{it.id}}">${{it.name}} (${{fmtTRY(it.prices.current, 2)}})</option>
      `).join("");

      document.getElementById("modal-content").innerHTML = `
        <div class="modal-header">
          <h3>Varlık Ekle / Güncelle</h3>
          <button class="close-btn" onclick="closeModal()">×</button>
        </div>
        <div class="field">
          <label>1. Kurum Seç (Data Store)</label>
          <div class="store-tabs">${{storeTabs}}</div>
        </div>
        <div class="field">
          <label>2. Varlık Seç</label>
          <select id="modal-asset" onchange="prefillExisting()">${{options}}</select>
        </div>
        <div class="field-row">
          <div class="field">
            <label>3. Miktar</label>
            <input type="number" step="any" id="modal-qty" placeholder="Örn: 12.5" />
          </div>
          <div class="field">
            <label>İlk Alış Maliyeti (₺)</label>
            <input type="number" step="any" id="modal-cost" placeholder="Boşsa güncel değer" />
          </div>
        </div>
        <button class="modal-submit" onclick="submitModal()">Portföye Kaydet</button>
      `;
      prefillExisting();
    }}

    window.prefillExisting = function() {{
      const cid = document.getElementById("modal-asset")?.value;
      const existing = holdings.find(h => h.catalog_id === cid);
      const qEl = document.getElementById("modal-qty");
      const cEl = document.getElementById("modal-cost");
      if (existing) {{
        qEl.value = existing.quantity;
        cEl.value = existing.cost_basis_total;
      }} else {{
        qEl.value = "";
        cEl.value = "";
      }}
    }};

    window.submitModal = function() {{
      const cid = document.getElementById("modal-asset").value;
      const qty = parseFloat(document.getElementById("modal-qty").value);
      let cost = parseFloat(document.getElementById("modal-cost").value);
      if (isNaN(qty) || qty <= 0) return showToast("Geçerli bir miktar gir");

      const item = catalogMap[cid];
      if (isNaN(cost) || cost < 0) {{
        cost = Number((qty * item.prices.current).toFixed(2));
      }}

      const idx = holdings.findIndex(h => h.catalog_id === cid);
      if (idx >= 0) {{
        holdings[idx] = {{ catalog_id: cid, quantity: qty, cost_basis_total: cost }};
      }} else {{
        holdings.push({{ catalog_id: cid, quantity: qty, cost_basis_total: cost }});
      }}
      saveHoldings();
      closeModal();
      renderApp();
      showToast(item.short_name + " kaydedildi");
    }};

    window.copySecretJson = async function() {{
      const obj = {{ currency: "TRY", holdings }};
      const text = JSON.stringify(obj, null, 2);
      try {{
        await navigator.clipboard.writeText(text);
        showToast("PORTFOLIO_JSON kopyalandı!");
      }} catch (e) {{
        prompt("Kopyala:", text);
      }}
    }};

    window.resetDefaults = function() {{
      localStorage.removeItem(STORAGE_KEY);
      holdings = loadHoldings();
      renderApp();
      showToast("Varsayılan portföye dönüldü");
    }};

    function bootstrapData(data) {{
      reportData = data;
      catalogMap = {{}};
      for (const s of data.stores || []) {{
        for (const it of s.items || []) {{
          catalogMap[it.id] = it;
        }}
      }}
      holdings = loadHoldings();
      renderApp();
    }}

    async function decryptWithPin(pin) {{
      const b64ToBuf = (b) => Uint8Array.from(atob(b), c => c.charCodeAt(0));
      const enc = new TextEncoder();
      const keyMaterial = await crypto.subtle.importKey(
        "raw", enc.encode(pin), "PBKDF2", false, ["deriveKey"]
      );
      const key = await crypto.subtle.deriveKey(
        {{ name: "PBKDF2", salt: b64ToBuf(PAYLOAD.salt), iterations: 100000, hash: "SHA-256" }},
        keyMaterial,
        {{ name: "AES-GCM", length: 256 }},
        false,
        ["decrypt"]
      );
      const decrypted = await crypto.subtle.decrypt(
        {{ name: "AES-GCM", iv: b64ToBuf(PAYLOAD.iv) }},
        key,
        b64ToBuf(PAYLOAD.ciphertext)
      );
      return JSON.parse(new TextDecoder().decode(decrypted));
    }}

    function renderLockScreen(errMsg = "") {{
      document.getElementById("app").innerHTML = `
        <div class="lock-screen">
          <h2>🔒 Portföy Raporu Kilitli</h2>
          <p>Verilerin şifrelenmiştir. Devam etmek için PIN kodunu gir.</p>
          <input type="password" id="pin-input" placeholder="PIN / Şifre" autofocus />
          <button onclick="unlock()">Aç</button>
          ${{errMsg ? `<div class="lock-error">${{errMsg}}</div>` : ""}}
        </div>
      `;
      const input = document.getElementById("pin-input");
      input.addEventListener("keydown", (e) => {{ if (e.key === "Enter") unlock(); }});
    }}

    window.unlock = async function() {{
      const pin = document.getElementById("pin-input").value;
      try {{
        const data = await decryptWithPin(pin);
        localStorage.setItem("portfolio_pin", pin);
        bootstrapData(data);
      }} catch (e) {{
        renderLockScreen("Hatalı PIN. Tekrar dene.");
      }}
    }};

    (async function init() {{
      if (!PAYLOAD.encrypted) {{
        bootstrapData(PAYLOAD.data);
        return;
      }}
      const savedPin = localStorage.getItem("portfolio_pin");
      if (savedPin) {{
        try {{
          const data = await decryptWithPin(savedPin);
          bootstrapData(data);
          return;
        }} catch (e) {{
          localStorage.removeItem("portfolio_pin");
        }}
      }}
      renderLockScreen();
    }})();
  </script>
</body>
</html>
"""
