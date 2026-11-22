from __future__ import annotations

from typing import Optional


def _fmt_try(val: float, decimals: int = 2) -> str:
    s = f"{val:,.{decimals}f}"
    # Convert US thousands/decimal to Turkish format (1,234.56 -> 1.234,56)
    s = s.replace(",", "_").replace(".", ",").replace("_", ".")
    return f"₺{s}"


def _fmt_signed_try(val: float, decimals: int = 0) -> str:
    formatted = _fmt_try(abs(val), decimals)
    if val > 0.005:
        return f"+{formatted}"
    if val < -0.005:
        return f"−{formatted}"
    return formatted


def _fmt_signed_pct(pct: float) -> str:
    s = f"{abs(pct):.2f}".replace(".", ",")
    if pct > 0.005:
        return f"+%{s}"
    if pct < -0.005:
        return f"−%{s}"
    return "%0,00"


def _color(val: float) -> str:
    if val > 0.005:
        return "#22C55E"
    if val < -0.005:
        return "#EF4444"
    return "#9A9AA6"


def _fmt_qty(qty: float, unit: str) -> str:
    if qty == int(qty):
        s = f"{int(qty):,}".replace(",", ".")
    else:
        s = f"{qty:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
    return f"{s} {unit}"


def _icon_badge(kind: str) -> str:
    icons = {
        "gold": ("#F59E0B", "Au"),
        "silver": ("#9CA3AF", "Ag"),
        "fund": ("#3B82F6", "F"),
        "stock": ("#38BDF8", "H"),
    }
    bg, label = icons.get(kind, ("#38BDF8", "•"))
    return (
        f'<div style="width:36px;height:36px;border-radius:10px;background:#1E1E24;'
        f'border:1px solid #2A2A33;text-align:center;line-height:36px;'
        f'font-weight:700;font-size:13px;color:{bg};">{label}</div>'
    )


def render_email_html(report: dict, dashboard_url: Optional[str] = None) -> str:
    tot = report["total"]
    c1d = tot["changes"]["1d"]
    c1w = tot["changes"]["1w"]
    c1m = tot["changes"]["1m"]
    call = tot["changes"]["all"]

    arrow = "↗" if c1d["diff"] > 0.005 else ("↘" if c1d["diff"] < -0.005 else "→")

    asset_rows = []
    for a in report["assets"]:
        a1d = a["changes"]["1d"]
        a1w = a["changes"]["1w"]
        a1m = a["changes"]["1m"]
        aall = a["changes"]["all"]

        source_tag = f" · {a['source']}" if a.get("source") else ""
        asset_rows.append(f"""
        <tr>
          <td style="padding-bottom:10px;">
            <table width="100%" cellpadding="0" cellspacing="0" border="0"
                   style="background:#16161A;border:1px solid #26262C;border-radius:14px;">
              <tr>
                <td style="padding:14px 16px;">
                  <table width="100%" cellpadding="0" cellspacing="0" border="0">
                    <tr>
                      <td width="46" valign="middle">{_icon_badge(a.get("icon", "stock"))}</td>
                      <td valign="middle">
                        <div style="font-size:15px;font-weight:700;color:#F4F4F6;">{a["name"]}</div>
                        <div style="font-size:12px;color:#9A9AA6;margin-top:2px;">{_fmt_qty(a["quantity"], a["unit"])}{source_tag}</div>
                      </td>
                      <td align="right" valign="middle">
                        <div style="font-size:15px;font-weight:700;color:#F4F4F6;">{_fmt_try(a["current_value"], 0)}</div>
                        <div style="font-size:12.5px;font-weight:600;color:{_color(a1d["diff"])};margin-top:2px;">{_fmt_signed_pct(a1d["pct"])} (1G)</div>
                      </td>
                    </tr>
                  </table>
                  <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:10px;border-top:1px solid #26262C;padding-top:8px;">
                    <tr>
                      <td style="font-size:11.5px;color:#9A9AA6;padding-top:8px;">
                        Maliyet: <strong style="color:#E4E4E7;">{_fmt_try(a["cost_basis_total"], 0)}</strong>
                        (<span style="color:{_color(aall["diff"])};font-weight:600;">{_fmt_signed_pct(aall["pct"])}</span>)
                      </td>
                      <td align="right" style="font-size:11.5px;color:#9A9AA6;padding-top:8px;">
                        1H: <span style="color:{_color(a1w["diff"])};font-weight:600;">{_fmt_signed_pct(a1w["pct"])}</span>
                        &nbsp;|&nbsp;
                        1A: <span style="color:{_color(a1m["diff"])};font-weight:600;">{_fmt_signed_pct(a1m["pct"])}</span>
                      </td>
                    </tr>
                  </table>
                </td>
              </tr>
            </table>
          </td>
        </tr>
        """)

    cta_html = ""
    if dashboard_url:
        cta_html = f"""
        <tr>
          <td align="center" style="padding-top:16px;">
            <a href="{dashboard_url}"
               style="display:inline-block;background:#22C55E;color:#06210E;text-decoration:none;
                      font-weight:700;font-size:14px;padding:12px 24px;border-radius:12px;">
              İnteraktif Paneli Aç (1G / 1H / 1A)
            </a>
          </td>
        </tr>
        """

    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{report["title"]}</title>
</head>
<body style="margin:0;padding:0;background:#0D0D0F;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;color:#F4F4F6;">
  <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#0D0D0F;padding:24px 12px;">
    <tr>
      <td align="center">
        <table width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:460px;">
          <!-- Header -->
          <tr>
            <td style="padding-bottom:16px;">
              <div style="font-size:24px;font-weight:700;color:#F4F4F6;letter-spacing:-0.4px;">{report["title"]}</div>
              <div style="font-size:13px;color:#9A9AA6;margin-top:4px;">{report["date_label"]} · {report["updated_at"]}</div>
            </td>
          </tr>

          <!-- Hero Card -->
          <tr>
            <td style="padding-bottom:20px;">
              <table width="100%" cellpadding="0" cellspacing="0" border="0"
                     style="background:#16161A;border:1px solid #26262C;border-radius:18px;">
                <tr>
                  <td style="padding:20px;">
                    <div style="font-size:13px;color:#9A9AA6;">Toplam portföy değeri</div>
                    <div style="font-size:34px;font-weight:700;color:#F4F4F6;margin-top:6px;letter-spacing:-0.8px;">
                      {_fmt_try(tot["current_value"], 2)}
                    </div>
                    <div style="font-size:14px;font-weight:600;margin-top:8px;">
                      <span style="color:{_color(c1d["diff"])};">{arrow} {_fmt_signed_try(c1d["diff"], 0)} ({_fmt_signed_pct(c1d["pct"])})</span>
                      <span style="color:#9A9AA6;font-weight:400;"> Düne göre</span>
                    </div>

                    <table width="100%" cellpadding="0" cellspacing="0" border="0"
                           style="margin-top:16px;border-top:1px solid #26262C;">
                      <tr>
                        <td width="50%" style="padding-top:14px;">
                          <div style="font-size:12px;color:#9A9AA6;">Geçen haftaya göre</div>
                          <div style="font-size:13px;font-weight:600;color:{_color(c1w["diff"])};margin-top:3px;">
                            {_fmt_signed_try(c1w["diff"], 0)} ({_fmt_signed_pct(c1w["pct"])})
                          </div>
                        </td>
                        <td width="50%" style="padding-top:14px;">
                          <div style="font-size:12px;color:#9A9AA6;">Geçen aya göre</div>
                          <div style="font-size:13px;font-weight:600;color:{_color(c1m["diff"])};margin-top:3px;">
                            {_fmt_signed_try(c1m["diff"], 0)} ({_fmt_signed_pct(c1m["pct"])})
                          </div>
                        </td>
                      </tr>
                      <tr>
                        <td colspan="2" style="padding-top:12px;">
                          <div style="font-size:12px;color:#9A9AA6;">
                            İlk alış maliyeti: <strong style="color:#F4F4F6;">{_fmt_try(tot["cost_basis_total"], 0)}</strong>
                            &nbsp;·&nbsp;
                            Toplam K/Z: <strong style="color:{_color(call["diff"])};">{_fmt_signed_try(call["diff"], 0)} ({_fmt_signed_pct(call["pct"])})</strong>
                          </div>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Assets Title -->
          <tr>
            <td style="font-size:16px;font-weight:700;color:#F4F4F6;padding-bottom:10px;">Varlıklarım</td>
          </tr>

          <!-- Asset Cards -->
          {"".join(asset_rows)}

          <!-- CTA -->
          {cta_html}

          <!-- Footer -->
          <tr>
            <td align="center" style="padding-top:20px;font-size:11px;color:#71717A;">
              GitHub Actions tarafından otomatik oluşturuldu.
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""
