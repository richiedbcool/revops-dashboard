"""
RevOps Signal Architecture — Daily Dashboard
Streamlit-in-Snowflake app. Design mirrors combined_scorecard.py (daily tab):
navy header band, IBM Plex type, green/yellow/red heat-map cells.

Reads the REVOPS_* views in GOLD_V3_DB.SALES (see revops_signal_views.sql).
Daily heat map colors each day vs the trailing-28-day daily average ("pace"),
matching the spec's "track direction, not absolute value" principle.

Two top-level tabs (2026-06-10):
  📊 RevOps Signal   — internal operations (sell-in, at-risk, fulfillment, AR…)
  🌐 Market Analysis — Nielsen + SPINS competitive intel (nested sub-tabs)
"""
import html as _html
import streamlit as st
import pandas as pd
import streamlit.components.v1 as _components
from snowflake.snowpark.context import get_active_session
from datetime import date, timedelta

st.set_page_config(page_title="RevOps Signal — Daily", layout="wide")

# ── Theme (from combined_scorecard.py) ──────────────────────────────────────
T = {
    "bg": "#ffffff", "bg2": "#f4f6f9", "border": "#dde2e9", "text": "#1f2937",
    "text2": "#4b5563", "text3": "#6b7280", "hdr_bg": "#2c5784", "th_bg": "#2c5784",
    "g_bg": "#cbe9ce", "g_fg": "#1f6634", "y_bg": "#fff3bf", "y_fg": "#a37500",
    "r_bg": "#f4cccc", "r_fg": "#9c2828", "e_bg": "#f4f6f9", "e_fg": "#c8ccd1",
}

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');
.stApp {{ background:{T['bg']}; font-family:'IBM Plex Sans',sans-serif; }}
.block-container {{ padding-top:1.5rem; }}
.rv-header {{ display:flex; align-items:baseline; gap:16px; padding:16px 0 10px;
    border-bottom:2px solid {T['border']}; margin-bottom:14px; }}
.rv-title {{ font-family:'IBM Plex Mono',monospace; font-size:20px; font-weight:600;
    color:{T['text']}; letter-spacing:.04em; text-transform:uppercase; }}
.rv-sub {{ font-size:12px; color:{T['text3']}; letter-spacing:.08em;
    font-family:'IBM Plex Mono',monospace; }}
.rv-band {{ background:{T['hdr_bg']}; color:#fff; font-family:'IBM Plex Mono',monospace;
    font-size:13px; font-weight:600; letter-spacing:.06em; padding:8px 14px;
    border-radius:5px 5px 0 0; text-transform:uppercase; margin-top:18px; }}
.rv-band-sub {{ font-weight:400; opacity:.8; font-size:11px; }}
/* heat-map table */
table.rv-table {{ border-collapse:collapse; width:100%; font-size:13px; }}
table.rv-table th {{ background:{T['th_bg']}; color:#fff; padding:7px 9px; text-align:center;
    font-weight:500; font-size:11px; letter-spacing:.03em; border:1px solid {T['hdr_bg']}; }}
table.rv-table th.metric {{ text-align:left; min-width:230px; }}
table.rv-table td {{ border:1px solid {T['border']}; padding:6px 9px; text-align:center;
    font-family:'IBM Plex Mono',monospace; }}
table.rv-table td.metric {{ text-align:left; font-family:'IBM Plex Sans',sans-serif; color:{T['text']}; }}
table.rv-table td.goal {{ color:{T['text3']}; font-size:11px; }}
.c-g {{ background:{T['g_bg']}; color:{T['g_fg']}; font-weight:600; }}
.c-y {{ background:{T['y_bg']}; color:{T['y_fg']}; font-weight:600; }}
.c-r {{ background:{T['r_bg']}; color:{T['r_fg']}; font-weight:600; }}
.c-e {{ background:{T['e_bg']}; color:{T['e_fg']}; }}
.rv-wtd {{ background:{T['bg2']}; font-weight:600; color:{T['text']}; }}
/* KPI tiles */
.rv-tiles {{ display:flex; gap:12px; flex-wrap:wrap; margin:6px 0 4px; }}
.rv-tile {{ flex:1; min-width:150px; background:{T['bg2']}; border:1px solid {T['border']};
    border-radius:6px; padding:12px 14px; }}
.rv-tile .lbl {{ font-size:11px; color:{T['text3']}; letter-spacing:.05em; text-transform:uppercase;
    font-family:'IBM Plex Mono',monospace; }}
.rv-tile .val {{ font-size:24px; font-weight:600; color:{T['text']}; font-family:'IBM Plex Mono',monospace; }}
.rv-tile .sub {{ font-size:11px; color:{T['text3']}; }}
.rv-badge {{ font-size:10px; padding:1px 6px; border-radius:3px; font-family:'IBM Plex Mono',monospace; }}
.rv-real {{ background:{T['g_bg']}; color:{T['g_fg']}; }}
.rv-proxy {{ background:{T['y_bg']}; color:{T['y_fg']}; }}
/* ── density: tighter than default, but with safe clearance (no overlaps) ── */
.block-container {{ padding-top:1.2rem; padding-bottom:1.2rem; max-width:1500px; }}
[data-testid="stVerticalBlock"] {{ gap:0.8rem; }}
[data-testid="stHorizontalBlock"] {{ gap:1rem; }}
[data-testid="stDataFrame"] {{ font-size:12px; }}
[data-testid="stCaptionContainer"] {{ margin-top:4px; font-size:11px; line-height:1.45; }}
.rv-band {{ margin-top:16px; margin-bottom:6px; }}
.rv-tiles {{ margin:6px 0 12px; overflow:hidden; }}
.rv-tile {{ overflow:hidden; }}
/* compact help expander */
details[data-testid="stExpander"] {{ border:1px dashed {T['border']}; border-radius:6px;
    margin:2px 0 4px; background:#fbfcfe; }}
details[data-testid="stExpander"] summary {{ font-size:12px; color:{T['text2']};
    font-family:'IBM Plex Mono',monospace; padding:5px 10px; }}
details[data-testid="stExpander"] summary:hover {{ color:{T['hdr_bg']}; }}
.rv-help h4 {{ font-size:12px; margin:8px 0 3px; color:{T['hdr_bg']};
    font-family:'IBM Plex Mono',monospace; text-transform:uppercase; letter-spacing:.04em; }}
.rv-help p, .rv-help li {{ font-size:12.5px; line-height:1.5; color:{T['text']}; margin:2px 0; }}
.rv-help b {{ color:{T['text']}; }}
/* ── card-style data table (Market Analysis) ── */
.rv-card-wrap {{ margin:6px 0 8px; border:1px solid #e6e9ef; border-radius:8px;
    overflow:auto; box-shadow:0 2px 10px rgba(0,0,0,0.07); }}
table.rv-card {{ width:100%; border-collapse:collapse; background:#fff; font-size:13px; }}
table.rv-card th {{ background:{T['hdr_bg']}; color:#fff; font-weight:600; text-align:right;
    padding:10px 14px; white-space:nowrap; position:sticky; top:0; z-index:1;
    font-family:'IBM Plex Mono',monospace; font-size:11px; letter-spacing:.03em; text-transform:uppercase; }}
table.rv-card th:first-child {{ text-align:left; }}
table.rv-card td {{ padding:9px 14px; text-align:right; border-bottom:1px solid #eceef2;
    font-family:'IBM Plex Mono',monospace; color:{T['text']}; white-space:nowrap; }}
table.rv-card td:first-child {{ text-align:left; font-weight:600; background:#f8fafc;
    font-family:'IBM Plex Sans',sans-serif; }}
table.rv-card tbody tr:hover td {{ background:#eef4fb; }}
table.rv-card tbody tr:last-child td {{ border-bottom:none; }}
table.rv-card tr.rv-lead td {{ font-weight:700; color:#1e40af; }}
</style>
""", unsafe_allow_html=True)

# ── Shared-password gate ────────────────────────────────────────────────────
# One password for everyone (set in Streamlit secrets as APP_PASSWORD).
# Skipped automatically when running inside Snowflake (no APP_PASSWORD secret).
def _check_password():
    if "APP_PASSWORD" not in st.secrets:
        return True  # running in Streamlit-in-Snowflake → Snowflake already authed
    if st.session_state.get("_authed"):
        return True
    st.markdown('<div class="rv-header"><span class="rv-title">RevOps Signal Architecture</span>'
                '<span class="rv-sub">ENTER PASSWORD TO CONTINUE</span></div>', unsafe_allow_html=True)
    pw = st.text_input("Password", type="password", label_visibility="collapsed",
                       placeholder="Password")
    if pw and pw == st.secrets["APP_PASSWORD"]:
        st.session_state["_authed"] = True
        st.rerun()
    elif pw:
        st.error("Incorrect password.")
    return False

if not _check_password():
    st.stop()

# ── Snowflake session ───────────────────────────────────────────────────────
# Inside Snowflake: use the ambient session. Hosted (Community Cloud): build a
# session from a key-pair service account in secrets — programmatic auth, no MFA.
@st.cache_resource(show_spinner=False)
def _get_session():
    try:
        return get_active_session()
    except Exception:
        pass
    from snowflake.snowpark import Session
    from cryptography.hazmat.primitives import serialization
    pk = serialization.load_pem_private_key(
        st.secrets["sf_private_key"].encode(),
        password=(st.secrets["sf_private_key_passphrase"].encode()
                  if st.secrets.get("sf_private_key_passphrase") else None),
    ).private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return Session.builder.configs({
        "account": st.secrets["sf_account"],
        "user": st.secrets["sf_user"],
        "private_key": pk,
        "role": st.secrets.get("sf_role", "REVOPS_DASHBOARD_RO"),
        "warehouse": st.secrets["sf_warehouse"],
        "database": st.secrets.get("sf_database", "GOLD_V3_DB"),
        "schema": st.secrets.get("sf_schema", "SALES"),
        # Heartbeat keeps the session/token alive across idle periods (e.g. overnight)
        # so the cached session doesn't go stale and fail on the next morning's query.
        "client_session_keep_alive": True,
    }).create()

session = _get_session()

@st.cache_data(ttl=1800, show_spinner=False)
def q(sql):
    try:
        return _get_session().sql(sql).to_pandas()
    except Exception:
        # Session likely expired/stale — drop the cached one, rebuild, and retry once.
        _get_session.clear()
        return _get_session().sql(sql).to_pandas()

def money(df, cols):
    """Format money columns as $0,000.00 strings for readability."""
    for c in cols:
        if c in df.columns:
            df[c] = df[c].apply(lambda v: f"${v:,.2f}" if pd.notna(v) else "")
    return df

def band(title, sub=""):
    st.markdown(f'<div class="rv-band">{title} <span class="rv-band-sub">{sub}</span></div>',
                unsafe_allow_html=True)

def tile(lbl, val, sub="", badge=""):
    b = f'<span class="rv-badge {badge}">{ "REAL" if badge=="rv-real" else "PROXY" }</span>' if badge else ""
    return (f'<div class="rv-tile"><div class="lbl">{lbl} {b}</div>'
            f'<div class="val">{val}</div><div class="sub">{sub}</div></div>')

def help_box(md, label="ℹ️  What am I looking at? (plain English)"):
    """Collapsible, plain-English explanation under a table. Collapsed by default so
    it adds no whitespace until a rep opens it."""
    with st.expander(label):
        st.markdown(f'<div class="rv-help">{md}</div>', unsafe_allow_html=True)

def _fmt_cell(col, v, money_cols):
    """Format one cell for the card table: $ for money cols, % for %-headed cols,
    thousands separators otherwise. Already-formatted strings pass through."""
    if v is None or (not isinstance(v, str) and pd.isna(v)):
        return ""
    if isinstance(v, str):
        return _html.escape(v)
    try:
        fv = float(v)
    except (TypeError, ValueError):
        return _html.escape(str(v))
    if col in money_cols:
        s = f"${fv:,.2f}"
        return s[:-3] if s.endswith(".00") else s          # drop trailing cents
    if "%" in str(col):
        return f"{fv:,.1f}%"
    if fv == int(fv):
        return f"{int(fv):,}"
    return f"{fv:,.2f}".rstrip("0").rstrip(".")

def show_table(df, money_cols=None, bold_top=False, scroll_h=None):
    """Render a DataFrame as a clean card-style HTML table (Market Analysis look)."""
    money_cols = set(money_cols or [])
    cols = list(df.columns)
    head = "".join(f"<th>{_html.escape(str(c))}</th>" for c in cols)
    rows = []
    for i, (_, r) in enumerate(df.iterrows()):
        cls = ' class="rv-lead"' if (bold_top and i == 0) else ""
        tds = "".join(f"<td>{_fmt_cell(c, r[c], money_cols)}</td>" for c in cols)
        rows.append(f"<tr{cls}>{tds}</tr>")
    style = f' style="max-height:{scroll_h}px"' if scroll_h else ""
    st.markdown(
        f'<div class="rv-card-wrap"{style}><table class="rv-card">'
        f"<thead><tr>{head}</tr></thead><tbody>{''.join(rows)}</tbody></table></div>",
        unsafe_allow_html=True)

# ── Header + week picker ────────────────────────────────────────────────────
st.markdown(
    '<div class="rv-header"><span class="rv-title">RevOps Signal Architecture</span>'
    '<span class="rv-sub">B2B WHOLESALE · DAILY · SELL-IN + SHELF</span></div>',
    unsafe_allow_html=True)

c1, c2, c3 = st.columns([1, 2, 1])
with c1:
    anchor = st.date_input("Week of", value=date.today())
with c3:
    st.markdown("<div style='height:26px'></div>", unsafe_allow_html=True)
    if st.button("🔄  Refresh data", use_container_width=True,
                 help="Pull the latest numbers now. Data is otherwise cached for 30 min for speed."):
        st.cache_data.clear()
        st.rerun()
week_start = anchor - timedelta(days=anchor.weekday())          # Monday
days = [week_start + timedelta(days=i) for i in range(7)]
today = date.today()

# ── Load daily metrics for week + 28-day trailing baseline ──────────────────
base_start = week_start - timedelta(days=28)
daily = q(f"""
    SELECT d, revenue, units, orders, active_accounts, new_accounts,
           gross_profit, gross_margin_pct, avg_order_value
    FROM GOLD_V3_DB.SALES.REVOPS_DAILY
    WHERE d BETWEEN '{base_start}' AND '{days[-1]}'
""")
daily.columns = [c.lower() for c in daily.columns]   # Snowflake returns UPPERCASE
daily['d'] = pd.to_datetime(daily['d']).dt.date
daily = daily.set_index('d')

METRICS = [
    ("revenue",         "B2B Revenue (shipped, completed)","${:,.0f}",  "$"),
    ("units",           "Units Shipped",                  "{:,.0f}",   "#"),
    ("orders",          "Orders",                         "{:,.0f}",   "#"),
    ("active_accounts", "Active Accounts",                "{:,.0f}",   "#"),
    ("new_accounts",    "New Accounts",                   "{:,.0f}",   "#"),
    ("gross_margin_pct","Gross Margin %",                 "{:.1f}%",   "%"),
    ("avg_order_value", "Avg Order Value",                "${:,.0f}",  "$"),
]

def baseline(col):
    """Trailing-28-day average of business days with data (>0 revenue/orders)."""
    hist = daily[daily.index < week_start]
    s = hist[col]
    s = s[s.notna()]
    if col not in ("gross_margin_pct",):
        s = s[s > 0]
    return s.mean() if len(s) else None

def cell_class(col, val, base):
    if val is None or pd.isna(val):
        return "c-e", "—"
    fmt = dict(METRICS_FMT)[col]
    disp = fmt.format(val) if not (col != "gross_margin_pct" and val == 0) else "—"
    if base is None or base == 0:
        return "c-e", disp
    ratio = val / base
    cls = "c-g" if ratio >= 1.0 else ("c-y" if ratio >= 0.6 else "c-r")
    if col != "gross_margin_pct" and (val == 0 or pd.isna(val)):
        cls = "c-e"
    return cls, disp

METRICS_FMT = [(k, f) for k, lbl, f, kind in METRICS]

# ── CORE STRIP — month-to-date ──────────────────────────────────────────────
# Anchor the MTD window to the month of the selected date, capped at today.
month_start = anchor.replace(day=1)
mtd_end = min(today, anchor)
mtd = q(f"""
    SELECT SUM(revenue) revenue, SUM(units) units, SUM(orders) orders,
           SUM(gross_profit) gross_profit, AVG(gross_margin_pct) gross_margin_pct
    FROM GOLD_V3_DB.SALES.REVOPS_DAILY
    WHERE d BETWEEN '{month_start}' AND '{mtd_end}'
""")
mtd.columns = [c.lower() for c in mtd.columns]
mtd_rev = float(mtd['revenue'][0] or 0)
mtd_units = float(mtd['units'][0] or 0)
mtd_orders = float(mtd['orders'][0] or 0)
mtd_gp = mtd['gross_profit'][0]
mtd_gm = (float(mtd_gp) / mtd_rev * 100) if mtd_gp is not None and mtd_rev else (
    float(mtd['gross_margin_pct'][0] or 0))

# supporting one-number pulls
rk = q("""SELECT COUNT(*) N, SUM(IFF(needs_outreach,1,0)) NEED,
                 SUM(IFF(needs_outreach,last_order_value,0)) UNTOUCHED
          FROM GOLD_V3_DB.SALES.REVOPS_AT_RISK_RADAR""")
risk = int(rk['N'][0] or 0); need = int(rk['NEED'][0] or 0)
untouched = float(rk['UNTOUCHED'][0] or 0)
ar = q("""SELECT ROUND(SUM(balance_due)) OPEN_AR FROM GOLD_V3_DB.SALES.REVOPS_DSO_AGING
          WHERE aging_bucket NOT IN ('paid')""")
open_ar = ar['OPEN_AR'][0] if len(ar) and ar['OPEN_AR'][0] is not None else 0
nielsen = q("""SELECT ROUND(AVG(usw_real),2) USW, ROUND(AVG(dollar_per_tdp),0) SPPD
               FROM GOLD_V3_DB.SALES.REVOPS_NIELSEN_LIVE
               WHERE is_mit45 AND NOT is_market_total AND period_type='Latest 4 Weeks'
                 AND is_latest_rolling AND usw_real IS NOT NULL""")
usw_real = nielsen['USW'][0] if len(nielsen) else None
sppd_real = nielsen['SPPD'][0] if len(nielsen) else None
# MIT45 competitive position — share of tracked kratom-shot set in Total Convenience (Latest 52 wks)
share_df = q("""SELECT ROUND(dollar_share_pct,1) SH, ROUND(fsi,2) FSI, dollar_rank RK
                FROM GOLD_V3_DB.SALES.REVOPS_NIELSEN_COMPETITIVE
                WHERE is_mit45 AND channel='Convenience Stores' AND is_market_total
                  AND period_type='Latest 52 Weeks' AND is_latest_rolling""")
mit_share = share_df['SH'][0] if len(share_df) else None
mit_fsi   = share_df['FSI'][0] if len(share_df) else None
mit_rank  = int(share_df['RK'][0]) if len(share_df) and share_df['RK'][0] is not None else None
dso = q("SELECT ROUND(dso_days,1) D FROM GOLD_V3_DB.SALES.REVOPS_DSO")['D'][0]
pr = q("""SELECT ROUND(SUM(net_amount)/NULLIF(SUM(gross_amount),0)*100,1) P
          FROM GOLD_V3_DB.SALES.REVOPS_TRADE_CONCESSIONS""")['P'][0]

# ── HEAT-MAP RENDERER (reused for Daily + Weekly) ───────────────────────────
def render_heatmap(metrics, period_keys, period_labels, value_fn, baseline_fn, total_label, is_future_fn=None):
    html = ['<table class="rv-table"><tr><th class="metric">Metric</th>']
    for lbl in period_labels:
        html.append(f'<th>{lbl}</th>')
    html.append(f'<th>{total_label}</th></tr>')
    for col, lbl, fmt, kind in metrics:
        base = baseline_fn(col)
        html.append(f'<tr><td class="metric">{lbl}</td>')
        vals = []
        for pk in period_keys:
            if is_future_fn and is_future_fn(pk):
                html.append('<td class="c-e">—</td>'); continue
            val = value_fn(col, pk)
            cls, disp = cell_class(col, val, base)
            html.append(f'<td class="{cls}">{disp}</td>')
            if val is not None and not pd.isna(val):
                vals.append(val)
        tot = (sum(vals)/len(vals) if vals else None) if kind == "%" else (sum(vals) if vals else None)
        html.append(f'<td class="rv-wtd">{fmt.format(tot) if tot is not None else "—"}</td></tr>')
    html.append('</table>')
    return ''.join(html)

# Weekly aggregate (trailing 4 weeks) straight from the unified view — correct distinct accounts
weekly = q("""SELECT DATE_TRUNC('week', sale_date) wk,
                     SUM(revenue) revenue, SUM(qty_sold) units,
                     COUNT(DISTINCT order_ref) orders,
                     COUNT(DISTINCT customer_key) active_accounts,
                     SUM(gross_profit)/NULLIF(SUM(revenue),0)*100 gross_margin_pct,
                     SUM(revenue)/NULLIF(COUNT(DISTINCT order_ref),0) avg_order_value
              FROM GOLD_V3_DB.SALES.REVOPS_SALES_UNIFIED
              WHERE sale_date >= DATEADD('week',-4, DATE_TRUNC('week',CURRENT_DATE))
              GROUP BY 1 ORDER BY 1""")
weekly.columns = [c.lower() for c in weekly.columns]
weekly['wk'] = pd.to_datetime(weekly['wk']).dt.date
weekly = weekly.set_index('wk')
WEEKLY_METRICS = [m for m in METRICS if m[0] != 'new_accounts']
wk_keys = list(weekly.index)
def wk_base(col):
    s = weekly[col]; s = s[s.notna()]
    return s.mean() if len(s) else None

# ── Shared US-state choropleth machinery (geometry + renderer) ───────────────
_geo = q("SELECT state, path_d FROM GOLD_V3_DB.SALES.REVOPS_US_STATE_PATHS")
_GREENS = ['#123524', '#18512f', '#1f7342', '#2a9759', '#4cc07b', '#7fe6a3']

def _swatch(color, label):
    return (f'<span style="display:flex;align-items:center;gap:5px;"><span style="width:12px;height:12px;'
            f'border-radius:2px;background:{color};display:inline-block;"></span>{label}</span>')

def _choropleth(vals, tips, color_fn, legend_html, height=560):
    _pp = []
    for _, gr in _geo.iterrows():
        nm, d = gr['STATE'], gr['PATH_D']
        if nm in vals and vals[nm] is not None:
            fill = color_fn(vals[nm]); ttl = tips.get(nm, nm)
        else:
            fill = '#222a38'; ttl = tips.get(nm, f"{nm} — no data")
        _pp.append(f'<path d="{d}" fill="{fill}" stroke="#0b1220" stroke-width="0.8"><title>{ttl}</title></path>')
    _h = ("<style>body{margin:0;background:#0b1220;font-family:-apple-system,system-ui,sans-serif;}</style>"
          '<svg viewBox="0 0 880 540" style="width:100%;max-width:840px;height:auto;display:block;margin:0 auto;">'
          + ''.join(_pp) + '</svg>'
          '<div style="display:flex;gap:14px;flex-wrap:wrap;justify-content:center;font-size:11px;'
          'color:#94a3b8;margin-top:6px;">' + legend_html + '</div>')
    _components.html(_h, height=height)

# ════════════════════════════════════════════════════════════════════════════
# TOP-LEVEL TABS
# ════════════════════════════════════════════════════════════════════════════
tab_signal, tab_market = st.tabs(["📊 RevOps Signal", "🌐 Market Analysis"])

# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — REVOPS SIGNAL (internal operations)
# ════════════════════════════════════════════════════════════════════════════
with tab_signal:
    st.markdown('<div class="rv-tiles">'
        + tile("Revenue MTD", f"${mtd_rev:,.0f}", "shipped/completed", "rv-proxy")
        + tile("Units MTD", f"{mtd_units:,.0f}")
        + tile("Orders MTD", f"{mtd_orders:,.0f}")
        + tile("Gross Margin MTD", f"{mtd_gm:,.1f}%")
        + tile("At-Risk · No Touch", f"{need}/{risk}", f"${untouched:,.0f} last-order value")
        + tile("Open AR / DSO", f"${open_ar:,.0f}", f"{dso} day DSO")
        + tile("Price Realization", f"{pr}%", "net ÷ gross")
        + '</div>', unsafe_allow_html=True)

    tab_d, tab_w = st.tabs(["📅  Daily", "🗓  Weekly (trailing 4 wks)"])
    with tab_d:
        st.markdown(f'<div class="rv-band">DAILY SELL-IN HEAT MAP '
                    f'<span class="rv-band-sub">Week of {week_start:%b %d, %Y} · green = at/above trailing-28d pace</span></div>',
                    unsafe_allow_html=True)
        st.markdown(render_heatmap(
            METRICS, days, [f"{d:%a}<br>{d:%m/%d}" for d in days],
            lambda col, d: daily[col].get(d), baseline, "WTD",
            is_future_fn=lambda d: d > today), unsafe_allow_html=True)
        st.caption("Sell-in = what we ship to accounts (not retail shelf). Current period revenue = COMPLETED "
                   "shipments keyed on completed_at (ties to ERP GUI MTD); Acumatica history = invoiced actuals.")
    with tab_w:
        st.markdown('<div class="rv-band">WEEKLY SELL-IN HEAT MAP '
                    '<span class="rv-band-sub">trailing 4 weeks · green = at/above 4-wk average</span></div>',
                    unsafe_allow_html=True)
        st.markdown(render_heatmap(
            WEEKLY_METRICS, wk_keys, [f"wk of<br>{w:%m/%d}" for w in wk_keys],
            lambda col, w: weekly[col].get(w), wk_base, "4wk"), unsafe_allow_html=True)

    opsL, opsR = st.columns(2)
    with opsL:
        band("At-Risk Radar", "31–90d no order × last rep touch (Aircall + Outlook) · ⚠ = no touch in 14d")
        rr = q("""SELECT IFF(needs_outreach,'⚠','') "!", customer_name "Account", segment "Segment",
                         days_since_last_order "No Order(d)", last_order_value "Last Order $",
                         days_since_call "Last Call(d)", days_since_email "Last Email(d)"
                  FROM GOLD_V3_DB.SALES.REVOPS_AT_RISK_RADAR
                  ORDER BY needs_outreach DESC, last_order_value DESC NULLS LAST LIMIT 25""")
        st.dataframe(money(rr, ['Last Order $']), use_container_width=True, hide_index=True)

        band("Inventory Weeks on Hand", "live FG · weeks of supply at current pace · lowest first")
        iw = q("""SELECT sku "SKU", product_name "Product", ROUND(qty_on_hand) "On Hand",
                         ROUND(avg_weekly_units,1) "Wk Units", ROUND(inventory_weeks_on_hand,1) "IWoH",
                         iwoh_signal "Signal"
                  FROM GOLD_V3_DB.SALES.REVOPS_IWOH
                  WHERE iwoh_signal <> 'no_recent_sales'
                  ORDER BY inventory_weeks_on_hand LIMIT 15""")
        st.dataframe(iw, use_container_width=True, hide_index=True)

        band("Order Fulfillment", "MTD completed orders · fill / on-time / perfect order / cycle")
        ff = q("""SELECT
                    ROUND(AVG(fill_rate)*100,1) "Fill %",
                    ROUND(SUM(IFF(on_time,1,0))/NULLIF(COUNT(*),0)*100,1) "On-Time %",
                    ROUND(SUM(IFF(perfect_order,1,0))/NULLIF(COUNT(*),0)*100,1) "Perfect Order %",
                    ROUND(AVG(cycle_days_approved_to_complete),1) "Cycle (d)",
                    COUNT(*) "Completed"
                  FROM GOLD_V3_DB.SALES.REVOPS_FULFILLMENT
                  WHERE completed_date >= DATE_TRUNC('month',CURRENT_DATE)""")
        st.dataframe(ff, use_container_width=True, hide_index=True)
        cx = q("""SELECT ROUND(SUM(IFF(is_cancelled,1,0))/NULLIF(COUNT(*),0)*100,1) C,
                         SUM(IFF(has_backorder,1,0)) B
                  FROM GOLD_V3_DB.SALES.REVOPS_FULFILLMENT""")
        st.caption(f"Cancellation rate: **{cx['C'][0]}%** (committed orders) · backordered orders: **{int(cx['B'][0] or 0)}** · "
                   "POR = on-time × in-full (2 of 4 factors; damage-free & doc-accuracy not tracked).")

    with opsR:
        band("Net Revenue Retention", "monthly · same-account revenue vs 12 mo prior")
        nrr = q("""SELECT TO_CHAR(sale_month,'YYYY-MM') "Month", ROUND(nrr_pct,1) "NRR %",
                          retained_plus_expansion "Retained+Exp", base_revenue_prior_year "Base PY"
                   FROM GOLD_V3_DB.SALES.REVOPS_NRR_MONTHLY
                   WHERE nrr_pct IS NOT NULL AND sale_month >= DATEADD('month',-12,CURRENT_DATE)
                   ORDER BY sale_month DESC""")
        st.dataframe(money(nrr, ['Retained+Exp','Base PY']), use_container_width=True, hide_index=True)

        band("Pipeline", "WON confirmed from ERP · open/lost from ClickUp CRM")
        won_erp = q("""SELECT COUNT(DISTINCT order_ref) N, SUM(revenue) REV
                       FROM GOLD_V3_DB.SALES.REVOPS_SALES_UNIFIED
                       WHERE source='supabase' AND sale_month = DATE_TRUNC('month',CURRENT_DATE)""")
        won_n = int(won_erp['N'][0] or 0); won_rev = float(won_erp['REV'][0] or 0)
        pf = q("""SELECT pipeline_outcome "Stage", COUNT(*) "Deals",
                         AVG(avg_order_value) "Avg AOV", ROUND(AVG(cycle_days)) "Avg Cycle(d)"
                  FROM GOLD_V3_DB.SALES.REVOPS_PIPELINE
                  WHERE pipeline_outcome IN ('open','lost') GROUP BY 1 ORDER BY 2 DESC""")
        st.dataframe(money(pf, ['Avg AOV']), use_container_width=True, hide_index=True)
        st.caption(f"**WON (ERP, MTD): {won_n} sales orders · ${won_rev:,.2f}** — authoritative. "
                   "CRM 'won' is excluded here because sales-team stage ≠ ERP-confirmed sale.")

        band("Margin by Channel", "MTD · gross margin (no trade/broker/deductions) · Acumatica+supabase")
        mc = q("""SELECT channel "Channel", COALESCE(class_name,'(unmapped)') "Segment",
                         revenue "Revenue", ROUND(gross_margin_pct,1) "GM %"
                  FROM GOLD_V3_DB.SALES.REVOPS_MARGIN_CHANNEL
                  WHERE sale_month = DATE_TRUNC('month',CURRENT_DATE)
                  ORDER BY revenue DESC LIMIT 12""")
        st.dataframe(money(mc, ['Revenue']), use_container_width=True, hide_index=True)

        band("AR Aging", "open invoices (supabase ERP)")
        ag = q("""SELECT aging_bucket "Bucket", COUNT(*) "Invoices", SUM(balance_due) "Open AR"
                  FROM GOLD_V3_DB.SALES.REVOPS_DSO_AGING
                  WHERE aging_bucket <> 'paid' GROUP BY 1
                  ORDER BY CASE aging_bucket WHEN 'current' THEN 0 WHEN '1-30' THEN 1
                           WHEN '31-60' THEN 2 WHEN '61-90' THEN 3 ELSE 4 END""")
        st.dataframe(money(ag, ['Open AR']), use_container_width=True, hide_index=True)

        band("Trade Spend & Concessions", "by reason code · concession = gross − net")
        tc = q("""SELECT reason_code "Reason", COUNT(*) "Lines",
                         SUM(concession_amount) "Concession $", ROUND(AVG(discount_percent),1) "Avg Disc %"
                  FROM GOLD_V3_DB.SALES.REVOPS_TRADE_CONCESSIONS
                  WHERE is_concession GROUP BY 1 ORDER BY 3 DESC""")
        st.dataframe(money(tc, ['Concession $']), use_container_width=True, hide_index=True)
        st.caption("TRADE_PROMO + SLOTTING_FEE = trade spend · DAMAGE_SHORT_CREDIT = deduction credit · "
                   "PRICE_ADJUSTMENT = concessions. Partial unlock of trade-spend/deduction visibility.")

    band("Instrument Next — Not Yet Available", "data needed to light these up")
    st.markdown("""
| Metric | Blocked on |
|---|---|
| Sell-Through Rate (distributor) | downstream POS / EDI 852 (Nielsen covers shelf velocity only) |
| Deduction **Recovery** Rate | dispute ledger + recovered $ (spend side now visible via reason codes) |
| Trade Spend **ROI** | ✅ lift side now built (Circle K base vs incremental + % lift); pair with internal spend $ for full ROI |
| Forecast Accuracy | a stored forecast (auto-baseline buildable from history) |
| FSI (Fair Share Index) | ✅ built — see Market Analysis › Shelf & Share |
| GMROI / GMROF | inventory-investment $ (Nielsen supplies the share side only) |
| Field execution (OOS, planogram) · Broker performance | no source data |
""")
    st.caption("Source: GOLD_V3_DB.SALES.REVOPS_* views · 🟢 REAL (Nielsen/SPINS) · 🟡 PROXY/sell-in · "
               "current period = supabase completed shipments; history = Acumatica invoiced.")

# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — MARKET ANALYSIS (Nielsen + SPINS competitive intel)
# ════════════════════════════════════════════════════════════════════════════
with tab_market:
    mt_over, mt_shelf, mt_maps, mt_expl, mt_acct, mt_chan, mt_promo = st.tabs(
        ["Overview", "Shelf & Share", "Maps", "Explorer", "Key Accounts",
         "Channels & SPINS", "Promo & Price"])

    # ── OVERVIEW ─────────────────────────────────────────────────────────────
    with mt_over:
        # SPINS conventional share for MIT45 family + 7-OH segment size
        spx = q("""SELECT brand_family, ROUND(dollar_share_pct,1) sh, ROUND(dollars) dol
                   FROM GOLD_V3_DB.SALES.REVOPS_SPINS_COMPETITIVE
                   WHERE geography_raw='TOTAL US - MULO + CONVENIENCE'""")
        sp_mit = spx[spx['BRAND_FAMILY'] == 'MIT45']['SH'].sum() if len(spx) else None
        sp_7oh = spx[spx['BRAND_FAMILY'] == '7-OH SEGMENT']['DOL'].sum() if len(spx) else 0
        st.markdown('<div class="rv-tiles">'
            + tile("Shelf $ Share (Nielsen)", f"{mit_share if mit_share is not None else '—'}%",
                   f"FSI {mit_fsi if mit_fsi is not None else '—'} · #{mit_rank}/6 · C-store L52W", "rv-real")
            + tile("Shelf USW (Nielsen)", f"{usw_real if usw_real is not None else '—'}", "units/store/wk · L4W", "rv-real")
            + tile("SPINS Conv Share", f"{sp_mit:.1f}%" if sp_mit is not None else "—",
                   "MIT45 family · Total US MULO+Conv", "rv-real")
            + tile("7-OH Threat", f"${sp_7oh/1e6:.0f}M", "emerging segment · SPINS 52wk", "rv-real")
            + '</div>', unsafe_allow_html=True)
        st.caption("MIT45 is a small, premium-priced player on the shelf (FSI 0.70 = sells below its distribution "
                   "footprint), thin in both Nielsen c-store (~6%) and SPINS conventional (~3%). Watch the emerging "
                   "7-OH segment (7TABZ et al.) — already a top-3 brand in SPINS conventional. Tabs above drill in.")

        with st.expander("📖  New to these terms? Read this first — every Market Analysis metric in plain English",
                         expanded=False):
            st.markdown("""<div class="rv-help">

<h4>The big idea: shelf data ≠ our sales</h4>
<p>The <b>RevOps Signal</b> tab is <b>sell-in</b> — what <b>we ship</b> to our wholesale accounts (our revenue).
This <b>Market Analysis</b> tab is <b>sell-through</b> — what shoppers <b>actually buy off the store shelf</b>,
measured by outside firms (Nielsen &amp; SPINS). It tells us how MIT45 is really doing at retail vs competitors,
which is different from how much we ship.</p>

<h4>Nielsen vs SPINS — why there are two</h4>
<p>They're two different store-measurement panels. <b>Nielsen</b> (here) ≈ <b>convenience stores</b>.
<b>SPINS</b> ≈ <b>conventional + natural/specialty</b> stores and specific chains. They count <b>different stores</b>,
so <b>compare within one panel — never add Nielsen + SPINS together.</b></p>

<h4>Distribution vs velocity — the two ways to grow</h4>
<p>Every brand grows two ways: <b>get into more stores</b> (distribution) or <b>sell faster in the stores it's
already in</b> (velocity). Most of these metrics are measuring one or the other.</p>

<h4>$ Share (Dollar Share)</h4>
<p>Of every $100 shoppers spend in the tracked kratom-shot category in that area, how many dollars go to this brand.
Higher = a bigger slice of the category. This is the headline "how big are we on shelf" number.</p>

<h4>%ACV &amp; ACV Share — "how widely is it stocked?"</h4>
<p><b>ACV</b> = All-Commodity Volume. Think of it as <b>"% of stores that carry it, weighted by how big those stores
are."</b> 100% ACV = available basically everywhere that matters; 30% = only in stores doing 30% of category volume.
It's a <b>distribution / availability</b> measure, not a sales measure.</p>

<h4>FSI (Fair Share Index) — the most important one</h4>
<p><b>FSI = $ share ÷ distribution (ACV) share.</b> It answers: <b>"is the brand punching above or below its shelf
presence?"</b><br>
• <b>FSI &gt; 1.0</b> = sells <b>more</b> than its store footprint predicts → strong shopper pull. Fix = get into more stores.<br>
• <b>FSI &lt; 1.0</b> = it's <b>on the shelf but not moving</b> → a <b>velocity problem</b>, not a distribution problem.<br>
MIT45 ≈ <b>0.70</b>: we're stocked but under-selling our footprint. Adding doors won't fix that — moving product faster will.</p>

<h4>USW (Units per Store per Week)</h4>
<p>In the stores that <b>do</b> carry it, how many units sell per store each week. Pure <b>velocity</b> — how fast it
moves where it's stocked. Higher is better.</p>

<h4>$/Store/Wk &amp; $/TDP</h4>
<p><b>$/Store/Wk</b> = weekly dollar sales per carrying store (velocity in dollars). <b>$/TDP</b> = dollars per
"Total Distribution Point" — velocity adjusted for how widely distributed a brand is, so you can fairly compare a
big brand to a small one.</p>

<h4>$/EQ Unit (Equivalized Unit)</h4>
<p>Pack sizes differ (singles, 2-packs, big bottles). EQ "equivalizes" them to one common size so prices are
apples-to-apples. Use <b>$/EQ Unit</b> when comparing price across brands with different pack sizes.</p>

<h4>% Incremental / Promo Lift</h4>
<p>Of a brand's sales, how much came from <b>promotion</b> (deals, displays) <b>above its normal "base" rate.</b>
High % = sales are <b>promo-driven</b>; low or zero = selling at full price with no deals. MIT45 runs <b>low</b> —
it's the premium brand that doesn't discount. "Base vs incremental" splits normal sales from the promo-driven extra.</p>

<h4>Whitespace / Untapped $ / Distribution gap</h4>
<p>Category demand in a state that MIT45 <b>isn't capturing yet</b> — competitor-held dollars up for grabs.
"Distribution gap" = states where the category sells but our %ACV is low (we're barely stocked there).</p>

<h4>7-OH segment</h4>
<p>A fast-growing competing product class (7-hydroxymitragynine — 7TABZ, 7 OHMZ, etc.). It's the emerging threat to
watch; 7TABZ alone is already bigger in SPINS conventional than MIT45's whole family.</p>

</div>""", unsafe_allow_html=True)

    # ── SHELF & SHARE (Nielsen) ──────────────────────────────────────────────
    with mt_shelf:
        cshareL, cshareR = st.columns([3, 2])
        with cshareL:
            band("Competitive Shelf Share & FSI (Nielsen)",
                 "REAL · share of tracked kratom-shot set · Total Convenience · Latest 52 Wks")
            comp = q("""SELECT brand_name "Brand", dollar_rank "#",
                               dollars "$ (52wk)",
                               ROUND(dollar_share_pct,1) "$ Share %",
                               ROUND(acv_share_pct,1) "ACV Share %",
                               ROUND(fsi,2) "FSI", ROUND(usw,1) "USW"
                        FROM GOLD_V3_DB.SALES.REVOPS_NIELSEN_COMPETITIVE
                        WHERE channel='Convenience Stores' AND is_market_total
                          AND period_type='Latest 52 Weeks' AND is_latest_rolling
                        ORDER BY dollar_rank""")
            show_table(comp, money_cols=['$ (52wk)'], bold_top=True)
            st.caption("FSI = $ share ÷ distribution (ACV) share. >1 over-indexes (sells above shelf footprint), "
                       "<1 under-indexes. MIT45 FSI ≈ 0.70 → selling below its distribution — a velocity, not a "
                       "shelf-presence, problem.")
            help_box("""
<p><b>What this table ranks:</b> every kratom-shot brand in convenience stores by how big a slice of category
dollars it holds over the last 52 weeks.</p>
<p><b>How to read a row:</b> <b>$ Share %</b> = size on shelf. <b>ACV Share %</b> = how widely it's stocked.
<b>FSI</b> = is it punching above (&gt;1) or below (&lt;1) its shelf presence. <b>USW</b> = units sold per carrying
store per week (raw speed).</p>
<p><b>What to do with it:</b> a brand with high share but FSI &lt; 1 is coasting on distribution — beatable on
velocity. A small brand with FSI &gt; 1 is a rising threat (shoppers seek it out). MIT45's low FSI says our job is
to <b>sell faster where we already are</b>, not just chase more doors.</p>""")
        with cshareR:
            band("MIT45 Shelf-Share Trend", "share of tracked set · Total Convenience · monthly")
            trend = q("""SELECT period_month, ROUND(dollar_share_pct,1) share_pct
                         FROM GOLD_V3_DB.SALES.REVOPS_NIELSEN_SHARE_TREND
                         WHERE is_mit45
                           AND week_ending_date >= DATEADD('month',-18,
                                (SELECT MAX(week_ending_date) FROM GOLD_V3_DB.SALES.REVOPS_NIELSEN_SHARE_TREND))
                         ORDER BY week_ending_date""")
            if not trend.empty:
                st.line_chart(trend.set_index('PERIOD_MONTH')['SHARE_PCT'], height=240)
                st.caption(f"MIT45 C-store $ share slid from {trend['SHARE_PCT'].iloc[0]:.1f}% to "
                           f"{trend['SHARE_PCT'].iloc[-1]:.1f}% over the trailing year (monthly Nielsen, "
                           "ends Dec-2025; 2026 only in rolling aggregates).")

        band("Shelf Velocity (Nielsen)", "REAL · MIT45 brand · per product×state · Latest 4 Wks · W/E 05-30-2026")
        nv = q("""SELECT n.state "State",
                         COALESCE(p.product_clean, n.product_description) "Product",
                         ROUND(AVG(n.usw_real),2) "USW", ROUND(AVG(n.pct_acv),2) "%ACV",
                         ROUND(AVG(n.dollar_per_tdp),2) "$/TDP",
                         ROUND(AVG(n.dollar_per_store_week),2) "$/Store/Wk"
                  FROM GOLD_V3_DB.SALES.REVOPS_NIELSEN_LIVE n
                  LEFT JOIN GOLD_V3_DB.SALES.REVOPS_PRODUCT_NAMES p
                    ON p.upc_core = LPAD(REPLACE(n.upc,'-',''),12,'0')
                  WHERE n.is_mit45 AND NOT n.is_market_total AND n.period_type='Latest 4 Weeks'
                    AND n.is_latest_rolling AND n.usw_real IS NOT NULL
                  GROUP BY 1, 2
                  ORDER BY AVG(n.usw_real) DESC LIMIT 15""")
        show_table(nv, money_cols=['$/TDP','$/Store/Wk'])
        help_box("""
<p><b>What this is:</b> our real shelf <b>speed</b> per MIT45 product, per state — how fast each item sells in the
stores that carry it (not how much we shipped).</p>
<p><b>Columns:</b> <b>USW</b> = units per store per week · <b>%ACV</b> = how widely it's stocked · <b>$/Store/Wk</b>
= weekly dollars per carrying store · <b>$/TDP</b> = velocity adjusted for distribution.</p>
<p><b>Use it for:</b> high USW but low %ACV = a proven winner that just needs more doors (a clean expansion pitch).
Low USW = it's stocked but sitting — a velocity/merchandising problem to fix before adding stores.</p>""")

        band("Distribution-Void / OOS Watch (Nielsen)",
             "MIT45 · % stores selling — recent 4wk vs 12wk baseline · biggest drops first")
        oos = q("""WITH d AS (
                     SELECT n.state "State",
                       COALESCE(p.product_clean, n.product_description) "Product",
                       AVG(IFF(n.period_type='Latest 12 Weeks',     n.pct_stores_selling, NULL)) sps_12w,
                       AVG(IFF(n.period_type='Latest 4 Weeks',      n.pct_stores_selling, NULL)) sps_4w,
                       AVG(IFF(n.period_type='Latest 52 Weeks',     n.pct_stores_selling, NULL)) sps_52w,
                       AVG(IFF(n.period_type='Latest 52 Weeks YoY', n.pct_stores_selling, NULL)) sps_52w_ya
                     FROM GOLD_V3_DB.SALES.REVOPS_NIELSEN_LIVE n
                     LEFT JOIN GOLD_V3_DB.SALES.REVOPS_PRODUCT_NAMES p
                       ON p.upc_core = LPAD(REPLACE(n.upc,'-',''),12,'0')
                     WHERE n.is_mit45 AND NOT n.is_market_total AND n.is_latest_rolling
                       AND n.period_type IN ('Latest 4 Weeks','Latest 12 Weeks',
                                           'Latest 52 Weeks','Latest 52 Weeks YoY')
                     GROUP BY 1,2)
                   SELECT "State", "Product",
                          ROUND(sps_12w,1) "Stores% 12w", ROUND(sps_4w,1) "Stores% 4w",
                          ROUND(sps_4w - sps_12w,1) "Δ 4v12", ROUND(sps_52w - sps_52w_ya,1) "Δ YoY"
                   FROM d
                   WHERE sps_12w IS NOT NULL AND sps_4w IS NOT NULL AND sps_4w < sps_12w
                   ORDER BY (sps_4w - sps_12w) ASC LIMIT 15""")
        if oos.empty:
            st.caption("No distribution erosion vs the trailing-quarter baseline this period. ✅")
        else:
            show_table(oos)
        st.caption("Negative Δ = MIT45 losing shelf presence (stores carrying it) recently vs its 12-week "
                   "baseline — a void / out-of-stock / delist signal to chase per state. Proxy (Nielsen has no "
                   "weekly series here); pairs with the FSI read above.")
        help_box("""
<p><b>What this catches:</b> states where the <b>% of stores carrying MIT45 is dropping</b> — an early warning that
we're getting dropped, going out of stock, or being delisted.</p>
<p><b>Columns:</b> <b>Stores% 12w</b> = baseline distribution · <b>Stores% 4w</b> = recent · <b>Δ 4v12</b> = the
recent change (negative = shrinking) · <b>Δ YoY</b> = vs a year ago.</p>
<p><b>Use it for:</b> the most-negative rows are your call list — phone the distributor/buyer in that state to
find out why we're losing shelf and win the space back before a competitor takes it.</p>""")

    # ── MAPS (Nielsen) ───────────────────────────────────────────────────────
    with mt_maps:
        band("Shelf Position by State (Nielsen)",
             "REAL · Convenience · Latest 52 Wks · pick a brand — map recolors; hover a state for full detail")
        _map_brands = q("""SELECT DISTINCT brand_name FROM GOLD_V3_DB.SALES.REVOPS_NIELSEN_STATE_BRAND
                           ORDER BY brand_name""")['BRAND_NAME'].tolist()
        _mbc1, _mbc2 = st.columns([1, 2])
        with _mbc1:
            _map_brand = st.selectbox("Brand", _map_brands,
                index=(_map_brands.index('MIT 45') if 'MIT 45' in _map_brands else 0), key="nlsn_map_brand")
        with _mbc2:
            _map_metric = st.radio("Color states by", ["$ Share %", "$ Sales", "$/Unit", "%ACV"],
                                   horizontal=True, key="nlsn_map_metric")
        _mb = _map_brand.replace("'", "''")
        msdf = q(f"""SELECT state "State", ROUND(dollar_share_pct,1) "Share", ROUND(dollars) "Sales",
                            ROUND(dollars_last4wk) "Last4wk", ROUND(price_per_unit,2) "PPU", ROUND(pct_acv,1) "ACV"
                     FROM GOLD_V3_DB.SALES.REVOPS_NIELSEN_STATE_BRAND
                     WHERE brand_name='{_mb}' AND dollars > 0
                     ORDER BY dollars DESC""")
        _mkey = {"$ Share %": "Share", "$ Sales": "Sales", "$/Unit": "PPU", "%ACV": "ACV"}[_map_metric]
        _vals = {r['State']: float(r[_mkey]) for _, r in msdf.iterrows()}
        _tip = {r['State']: (float(r['Share']), float(r['Last4wk']), float(r['PPU']), float(r['ACV']))
                for _, r in msdf.iterrows()}
        _mx = max(_vals.values()) if _vals else 1.0

        def _mfmt(v):
            if _map_metric == '$ Sales':
                return f"${v/1e6:.1f}M" if v >= 1e6 else f"${v/1e3:.0f}K"
            if _map_metric == '$/Unit':
                return f"${v:.0f}"
            return f"{v:.0f}%"

        def _shade(v):
            if v is None or v <= 0:
                return '#222a38'
            return _GREENS[min(5, int((v / _mx) ** 0.5 * 6))]

        _mtips = {}
        for nm, t in _tip.items():
            sh, l4, ppu, acv = t
            _mtips[nm] = f"{nm} — {sh:.1f}% share · last-4wk ${l4:,.0f} · ${ppu:.2f}/unit · {acv:.1f}% ACV"
        _map_legend = ''.join(_swatch(_GREENS[i], _mfmt((i/6)**2*_mx) + '+') for i in range(6))
        _choropleth(_vals, _mtips, _shade, _map_legend)
        with st.expander(f"State detail (table) — {_map_brand}"):
            show_table(msdf.rename(columns={'Share':'$ Share %','Sales':'$ Sales (52wk)',
                       'Last4wk':'$ Last 4wk','PPU':'$/Unit','ACV':'%ACV'}),
                       money_cols=['$ Sales (52wk)','$ Last 4wk','$/Unit'])
        st.caption(f"Coloring {_map_brand} by {_map_metric}. Hover any state for share · last-4wk $ · $/unit · %ACV. "
                   "Share = % of the tracked kratom-shot set in that state. Grey = no measured sales for this brand.")
        help_box("""
<p><b>How to drive these maps:</b> pick a <b>brand</b>, then pick what to <b>color states by</b> ($ share, total $,
price, or %ACV). Darker green = stronger on that metric. <b>Hover any state</b> for the full read. Grey = no measured
sales there.</p>
<p><b>Three maps, three jobs:</b><br>
• <b>This map</b> — where any one brand is strong or weak.<br>
• <b>Head-to-Head</b> — MIT45 vs one competitor; green = we lead that state, red = they lead.<br>
• <b>Whitespace</b> — brightest states = biggest untapped category dollars MIT45 isn't getting yet (target list).</p>
<p><b>Use it for:</b> building a geographic game plan — defend the green, attack the red, and prioritize the
brightest whitespace states for new distribution.</p>""")

        # Head-to-head map
        band("Head-to-Head Map — MIT45 vs competitor by state",
             "REAL · Convenience · Latest 52 Wks · green = MIT45 leads · red = competitor leads (Δ share points)")
        _hh_comp = st.selectbox("Compare MIT45 against",
            [b for b in _map_brands if b != 'MIT 45'],
            index=([b for b in _map_brands if b != 'MIT 45'].index('BOTANIC TONICS')
                   if 'BOTANIC TONICS' in _map_brands else 0), key="hh_map_comp")
        _hc = _hh_comp.replace("'", "''")
        _hh = q(f"""SELECT state "State",
                           MAX(IFF(brand_name='MIT 45',dollar_share_pct,NULL)) mit_sh,
                           MAX(IFF(brand_name='{_hc}',dollar_share_pct,NULL)) comp_sh
                    FROM GOLD_V3_DB.SALES.REVOPS_NIELSEN_STATE_BRAND
                    WHERE brand_name IN ('MIT 45','{_hc}') GROUP BY 1""")
        _hh_vals, _hh_tips = {}, {}
        for _, r in _hh.iterrows():
            _sname = r['State']
            _ms = float(r['MIT_SH'] or 0); _cs = float(r['COMP_SH'] or 0)
            if r['MIT_SH'] is None and r['COMP_SH'] is None:
                continue
            _hh_vals[_sname] = _ms - _cs
            _hh_tips[_sname] = f"{_sname} — MIT45 {_ms:.1f}% vs {_hh_comp.title()} {_cs:.1f}% · Δ {(_ms-_cs):+.1f} pts"
        _hh_maxabs = max((abs(v) for v in _hh_vals.values()), default=1.0) or 1.0
        _REDS = ['#5a2230', '#a32d2d', '#e24b4a']
        _GRNS = ['#1f5a38', '#2a9759', '#4cc07b']

        def _div_color(v):
            mag = min(2, int(min(1.0, abs(v)/_hh_maxabs) * 3))
            return (_GRNS[mag] if v >= 0 else _REDS[mag])

        _hh_legend = (_swatch('#e24b4a', f'{_hh_comp.title()} leads big') + _swatch('#a32d2d', 'leads')
                      + _swatch('#2a9759', 'MIT45 leads') + _swatch('#4cc07b', 'MIT45 leads big')
                      + _swatch('#222a38', 'no data'))
        _choropleth(_hh_vals, _hh_tips, _div_color, _hh_legend)
        st.caption(f"Δ = MIT45 share − {_hh_comp.title()} share, in points. Red = {_hh_comp.title()} out-shares MIT45 "
                   "(the norm vs the leaders); green = MIT45 leads. Flip to a smaller competitor to find where MIT45 wins.")

        # Whitespace map
        band("Whitespace Map — biggest MIT45 opportunities",
             "REAL · Convenience · Latest 52 Wks · category demand MIT45 doesn't yet hold")
        _ws_metric = st.radio("Opportunity metric",
            ["Untapped $ (competitor-held)", "Share gap", "Distribution gap (low %ACV)"],
            horizontal=True, key="ws_map_metric")
        _ws = q("""SELECT state "State", ROUND(cat_dollars) cat, ROUND(mit_dollars) mit,
                          ROUND(mit_share_pct,1) sh, ROUND(mit_pct_acv,1) acv,
                          ROUND(untapped_dollars) untapped, ROUND(share_gap,1) sgap, ROUND(distribution_gap,1) dgap
                   FROM GOLD_V3_DB.SALES.REVOPS_NIELSEN_STATE_OPPORTUNITY""")
        _wskey = {"Untapped $ (competitor-held)": 'UNTAPPED', "Share gap": 'SGAP',
                  "Distribution gap (low %ACV)": 'DGAP'}[_ws_metric]
        _ws_vals = {r['State']: float(r[_wskey]) for _, r in _ws.iterrows()}
        _ws_tips = {r['State']: (f"{r['State']} — untapped ${r['UNTAPPED']:,.0f} · MIT45 {r['SH']}% sh · "
                                 f"{r['ACV']}% ACV · category ${r['CAT']:,.0f}") for _, r in _ws.iterrows()}
        _ws_mx = max(_ws_vals.values()) if _ws_vals else 1.0
        _OPP = ['#3a2a12', '#6b4a12', '#9a6a10', '#c98a0f', '#e9b949', '#ffd97a']

        def _ws_color(v):
            if v is None or v <= 0:
                return '#222a38'
            return _OPP[min(5, int((v/_ws_mx) ** 0.5 * 6))]

        def _wsfmt(v):
            if _ws_metric.startswith('Untapped'):
                return f"${v/1e6:.0f}M" if v >= 1e6 else f"${v/1e3:.0f}K"
            return f"{v:.0f}%"

        _ws_legend = ''.join(_swatch(_OPP[i], _wsfmt((i/6) ** 2 * _ws_mx) + '+') for i in range(6))
        _choropleth(_ws_vals, _ws_tips, _ws_color, _ws_legend)
        st.caption("Brighter = bigger opportunity. Untapped $ = category dollars not going to MIT45 (≈ competitor "
                   "volume up for grabs). Biggest: TX (~$31M), GA (~$31M), FL (~$28M), then OR/KY/PA. Hover for detail.")

    # ── EXPLORER (Nielsen) ───────────────────────────────────────────────────
    with mt_expl:
        band("Competitive Explorer (Nielsen)",
             "REAL · Convenience · Latest 52 Wks · pick a brand to dig into its products & markets")
        _brands = q("""SELECT DISTINCT brand_name FROM GOLD_V3_DB.SALES.REVOPS_NIELSEN_LIVE
                       WHERE channel='Convenience Stores' AND period_type='Latest 52 Weeks'
                         AND is_latest_rolling ORDER BY brand_name""")['BRAND_NAME'].tolist()
        _exc1, _exc2 = st.columns(2)
        with _exc1:
            _ex_brand = st.selectbox("Brand to investigate", _brands,
                index=(_brands.index('MIT 45') if 'MIT 45' in _brands else 0), key="ce_brand")
        with _exc2:
            _vs_opts = [b for b in _brands if b != _ex_brand]
            _vs_brand = st.selectbox("Head-to-head vs", _vs_opts,
                index=(_vs_opts.index('BOTANIC TONICS') if 'BOTANIC TONICS' in _vs_opts else 0), key="ce_vs")
        _exb = _ex_brand.replace("'", "''")

        st.markdown(f"**Top products — {_ex_brand}**")
        _ce_prod = q(f"""SELECT COALESCE(p.product_clean, n.product_description) "Product",
                                SUM(n.total_dollar_sales) "$ (52wk)", ROUND(SUM(n.total_unit_sales)) "Units",
                                ROUND(AVG(n.pct_acv),1) "%ACV"
                         FROM GOLD_V3_DB.SALES.REVOPS_NIELSEN_LIVE n
                         LEFT JOIN GOLD_V3_DB.SALES.REVOPS_PRODUCT_NAMES p
                           ON p.upc_core = LPAD(REPLACE(n.upc,'-',''),12,'0')
                         WHERE n.is_market_total AND n.period_type='Latest 52 Weeks' AND n.is_latest_rolling
                           AND n.brand_name='{_exb}'
                         GROUP BY 1 ORDER BY 2 DESC LIMIT 8""")
        show_table(_ce_prod, money_cols=['$ (52wk)'], bold_top=True)

        st.markdown(f"**Top states — {_ex_brand}**  ·  $/Store/Wk = what each carrying store sells weekly")
        _ce_state = q(f"""SELECT state "State", SUM(total_dollar_sales) "$ (52wk)",
                                 ROUND(AVG(dollar_per_store_week)) "$/Store/Wk",
                                 ROUND(AVG(usw_real),1) "Units/Store/Wk", ROUND(AVG(pct_acv),1) "%ACV"
                          FROM GOLD_V3_DB.SALES.REVOPS_NIELSEN_LIVE
                          WHERE NOT is_market_total AND state<>'' AND period_type='Latest 52 Weeks'
                            AND is_latest_rolling AND brand_name='{_exb}'
                          GROUP BY 1 ORDER BY 2 DESC LIMIT 10""")
        show_table(_ce_state, money_cols=['$ (52wk)'], bold_top=True)

        st.markdown(f"**Head-to-head by state — {_ex_brand} vs {_vs_brand}**")
        _vsb = _vs_brand.replace("'", "''")
        _hhx = q(f"""SELECT state "State",
                           SUM(IFF(brand_name='{_exb}',total_dollar_sales,0)) "{_ex_brand} $",
                           ROUND(AVG(IFF(brand_name='{_exb}',dollar_per_store_week,NULL))) "{_ex_brand} $/St/Wk",
                           SUM(IFF(brand_name='{_vsb}',total_dollar_sales,0)) "{_vs_brand} $",
                           ROUND(AVG(IFF(brand_name='{_vsb}',dollar_per_store_week,NULL))) "{_vs_brand} $/St/Wk"
                    FROM GOLD_V3_DB.SALES.REVOPS_NIELSEN_LIVE
                    WHERE NOT is_market_total AND state<>'' AND period_type='Latest 52 Weeks'
                      AND is_latest_rolling AND brand_name IN ('{_exb}','{_vsb}')
                    GROUP BY 1
                    ORDER BY (SUM(total_dollar_sales)) DESC LIMIT 15""")
        if not _hhx.empty:
            _a, _b = f"{_ex_brand} $/St/Wk", f"{_vs_brand} $/St/Wk"
            _hhx["Velocity lead"] = _hhx.apply(
                lambda r: _ex_brand if (r[_a] or 0) > (r[_b] or 0) else (_vs_brand if (r[_b] or 0) > 0 else "—"),
                axis=1)
            show_table(_hhx, money_cols=[f"{_ex_brand} $", f"{_vs_brand} $"])
        st.caption("Nielsen is aggregated to state × channel — no individual store names. $/Store/Wk is the "
                   "per-store velocity proxy. Head-to-head sorted by combined retail $; 'Velocity lead' flags "
                   "who sells more per carrying store in each state.")
        help_box("""
<p><b>What this tab is for:</b> picking <b>any</b> brand (yours or a competitor's) and seeing its best products,
its strongest states, and a head-to-head vs one rival — your pre-call research on a competitor.</p>
<p><b>Top products</b> = its biggest sellers. <b>Top states</b> = where it's strongest, with $/Store/Wk showing how
fast it moves per carrying store. <b>Head-to-head</b> = side-by-side $ and per-store velocity; <b>Velocity lead</b>
names who sells more per store in each state.</p>
<p><b>Use it for:</b> before you walk into a buyer, know which brand owns that state and whether MIT45 out-sells it
per store — that's your talking point.</p>""")

    # ── KEY ACCOUNTS (Nielsen Circle K + SPINS chains) ───────────────────────
    with mt_acct:
        st.markdown("##### 🏪 Circle K (Nielsen — 16 regions · promo · price)")
        _ckp = q("""SELECT brand_name, dollars, dollar_share_pct, price_per_unit, price_per_eq_unit, pct_incremental
                    FROM GOLD_V3_DB.SALES.REVOPS_NIELSEN_CK_PRICE ORDER BY dollars DESC""")
        _ckp.columns = [c.lower() for c in _ckp.columns]
        _ck_brands = list(_ckp['brand_name'])
        if 'MIT 45' in _ck_brands and len(_ckp):
            _mr = _ckp[_ckp['brand_name'] == 'MIT 45'].iloc[0]
            _lead = _ckp.iloc[0]
            _rank = _ck_brands.index('MIT 45') + 1
            st.markdown('<div class="rv-tiles">'
                + tile("MIT45 @ Circle K", f"{_mr['dollar_share_pct']:.1f}%", f"#{_rank} of {len(_ckp)} · $ share", "rv-real")
                + tile("MIT45 $/unit", f"${_mr['price_per_unit']:.2f}",
                       f"vs {_lead['brand_name'].title()} ${_lead['price_per_unit']:.2f}", "rv-real")
                + tile("Promo lift", f"{_mr['pct_incremental']:.0f}%", "incremental vs base", "rv-real")
                + tile("CK Total / yr", f"${_mr['dollars']:,.0f}", "trailing 52 wks", "rv-real")
                + '</div>', unsafe_allow_html=True)
        _ckcol1, _ckcol2 = st.columns([3, 2])
        with _ckcol1:
            _ckreg_brand = st.selectbox("Brand — by Circle K region", _ck_brands,
                index=(_ck_brands.index('MIT 45') if 'MIT 45' in _ck_brands else 0), key="ck_region_brand")
            _crb = _ckreg_brand.replace("'", "''")
            band(f"{_ckreg_brand} by Circle K Region", "share · $ · price · distribution per CK division")
            _ckr = q(f"""SELECT region "CK Region", ROUND(dollar_share_pct,1) "Share %", dollars "$ (52wk)",
                                ROUND(price_per_unit,2) "$/Unit", ROUND(pct_acv,1) "%ACV"
                         FROM GOLD_V3_DB.SALES.REVOPS_NIELSEN_CK_REGION
                         WHERE brand_name='{_crb}' ORDER BY dollar_share_pct DESC""")
            show_table(_ckr, money_cols=['$ (52wk)', '$/Unit'], bold_top=True)
        with _ckcol2:
            band(f"{_ckreg_brand} Weekly Sell-Through", "Circle K Total · true week-over-week (52 wks)")
            _ckw = q(f"""SELECT week_ending_date, ROUND(dollars) wk_dollars
                         FROM GOLD_V3_DB.SALES.REVOPS_NIELSEN_CK_WEEKLY
                         WHERE brand_name='{_crb}' ORDER BY week_ending_date""")
            if not _ckw.empty:
                _ckw['WEEK_ENDING_DATE'] = pd.to_datetime(_ckw['WEEK_ENDING_DATE'])
                st.line_chart(_ckw.set_index('WEEK_ENDING_DATE')['WK_DOLLARS'], height=260)
        st.caption("Circle K: MIT45 underweight at 3.4% share vs 6.2% across total convenience. Botanic Tonics "
                   "owns ~69%. Tri-State is MIT45's strongest CK division, Las Vegas weakest.")
        help_box("""
<p><b>What this is:</b> a single chain (Circle K) broken into its sales regions, so you can see exactly where MIT45
is strong or weak <b>inside one account</b>, plus the weekly sell-through trend.</p>
<p><b>Read it:</b> <b>Share %</b> = MIT45's slice of the category in that CK region · <b>$/Unit</b> = our price vs
the field · <b>%ACV</b> = how many CK stores carry us · the <b>line chart</b> = real week-over-week sales off CK
shelves.</p>
<p><b>Use it for:</b> a Circle K account review — point to the regions where we under-index and the weeks where
sell-through dipped, and tie asks (more facings, a promo) to those specific gaps.</p>""")

        st.markdown("---")
        st.markdown("##### 🛒 SPINS C-store accounts (Maverik · Love's · Murphy · GetGo · Hy-Vee · Pilot · Wawa · Circle K)")
        _sp_accts = q("""SELECT DISTINCT account_name FROM GOLD_V3_DB.SALES.REVOPS_SPINS_ACCOUNT
                         ORDER BY account_name""")['ACCOUNT_NAME'].tolist()
        _sp_acct = st.selectbox("Account (SPINS own-store / CRMA)", _sp_accts,
            index=(_sp_accts.index('MURPHY') if 'MURPHY' in _sp_accts else 0), key="spins_acct")
        _spa = _sp_acct.replace("'", "''")

        # MIT45 scorecard tiles for the selected account
        _spacct = q(f"""SELECT brand_family, dollar_rank, dollars, dollar_share_pct,
                               price_per_unit, pct_incremental
                        FROM GOLD_V3_DB.SALES.REVOPS_SPINS_ACCOUNT
                        WHERE account_name='{_spa}' ORDER BY dollar_rank""")
        _spacct.columns = [c.lower() for c in _spacct.columns]
        _acct_brands = list(_spacct['brand_family'])
        if 'MIT45' in _acct_brands:
            _m = _spacct[_spacct['brand_family'] == 'MIT45'].iloc[0]
            _ld = _spacct.iloc[0]
            _rk = _acct_brands.index('MIT45') + 1
            st.markdown('<div class="rv-tiles">'
                + tile(f"MIT45 @ {_sp_acct.title()}", f"{_m['dollar_share_pct']:.1f}%",
                       f"#{_rk} of {len(_spacct)} · $ share", "rv-real")
                + tile("MIT45 $/unit (wtd)", f"${_m['price_per_unit']:.2f}",
                       f"vs {_ld['brand_family'].title()} ${_ld['price_per_unit']:.2f}", "rv-real")
                + tile("Promo lift", f"{_m['pct_incremental']:.0f}%", "incremental vs base", "rv-real")
                + tile("MIT45 $ / yr", f"${_m['dollars']:,.0f}", "trailing 52 wks", "rv-real")
                + '</div>', unsafe_allow_html=True)
        else:
            st.info(f"MIT45 has no measured sales at {_sp_acct.title()} in SPINS (not carried / below reporting).")

        band(f"{_sp_acct.title()} — brand share & price (SPINS · 52wk)", "all brand families in this chain")
        _spdf = q(f"""SELECT brand_family "Brand", dollar_rank "#", dollars "$ (52wk)",
                             ROUND(dollar_share_pct,1) "$ Share %", ROUND(price_per_unit,2) "$/Unit (wtd)",
                             ROUND(pct_incremental,1) "% Promo"
                      FROM GOLD_V3_DB.SALES.REVOPS_SPINS_ACCOUNT
                      WHERE account_name='{_spa}' ORDER BY dollar_rank""")
        show_table(_spdf, money_cols=['$ (52wk)', '$/Unit (wtd)'], bold_top=True)

        band(f"Weekly sell-through @ {_sp_acct.title()}", "true week-over-week (52 wks) · pick a brand")
        _sw1, _sw2 = st.columns([2, 3])
        with _sw1:
            _sw_brand = st.selectbox("Brand", _acct_brands,
                index=(_acct_brands.index('MIT45') if 'MIT45' in _acct_brands else 0), key="spins_wk_brand")
        _swb = _sw_brand.replace("'", "''")
        _spw = q(f"""SELECT week_ending_date, ROUND(SUM(dollars)) wk_dollars
                     FROM GOLD_V3_DB.SALES.REVOPS_SPINS_WEEKLY
                     WHERE account_name='{_spa}' AND brand_family='{_swb}'
                     GROUP BY 1 ORDER BY 1""")
        if not _spw.empty and _spw['WK_DOLLARS'].sum() > 0:
            _spw['WEEK_ENDING_DATE'] = pd.to_datetime(_spw['WEEK_ENDING_DATE'])
            st.line_chart(_spw.set_index('WEEK_ENDING_DATE')['WK_DOLLARS'], height=240)
        else:
            st.caption(f"No weekly {_sw_brand.title()} sales at {_sp_acct.title()}.")
        st.caption("SPINS own-store (CRMA) read per chain. MIT45 by $: Murphy ~$21.6M, Circle K ~$16.1M, "
                   "Wawa ~$11.8M; Wawa is MIT45's strongest by SHARE (~11%). Maverik doesn't carry MIT45 in SPINS. "
                   "Separate panel from Nielsen — compare, don't sum.")
        help_box("""
<p><b>What this is:</b> the same kind of account read as Circle K above, but from the <b>SPINS</b> panel, for the
big c-store chains it tracks (Murphy, Love's, Wawa, GetGo, etc.). Pick a chain to see MIT45's rank, share, price,
and weekly trend inside it.</p>
<p><b>Heads-up:</b> SPINS and Nielsen measure <b>different stores</b> — use this to understand a chain, but
<b>don't add</b> SPINS dollars to Nielsen dollars. "No measured sales" means MIT45 isn't carried there (or is below
reporting), which is itself a prospecting signal.</p>
<p><b>Use it for:</b> chain-specific prep — Wawa is our strongest by share, Maverik doesn't carry us at all (a clear
target). Walk in knowing where we stand in <b>their</b> stores.</p>""")

    # ── CHANNELS & SPINS ─────────────────────────────────────────────────────
    with mt_chan:
        band("SPINS Conventional — brand share (Total US MULO + Convenience · 52 wks)",
             "REAL · the natural/specialty + conventional panel Nielsen's c-store cut misses")
        _spc = q("""SELECT brand_family "Brand", dollar_rank "#", dollars "$ (52wk)",
                           ROUND(dollar_share_pct,1) "$ Share %", ROUND(price_per_unit,2) "$/Unit (wtd)",
                           ROUND(pct_incremental,1) "% Promo"
                    FROM GOLD_V3_DB.SALES.REVOPS_SPINS_COMPETITIVE
                    WHERE geography_raw='TOTAL US - MULO + CONVENIENCE'
                    ORDER BY dollar_rank""")
        show_table(_spc, money_cols=['$ (52wk)', '$/Unit (wtd)'], bold_top=True)

        band("⚠ 7-OH Emerging Segment Watch (SPINS)", "7TABZ · 7 OHMZ · 7ZEN · 7OHS — the new entrant Nielsen missed")
        _7oh = q("""SELECT brand_raw "7-OH Brand", ROUND(SUM(dollars)) "$ (52wk)",
                          ROUND(100*SUM(incr_dollars)/NULLIF(SUM(dollars),0),1) "% Incremental"
                   FROM GOLD_V3_DB.SALES.REVOPS_SPINS_7OH
                   WHERE geo_type='TOTAL' GROUP BY 1 ORDER BY 2 DESC""")
        show_table(_7oh, money_cols=['$ (52wk)'], bold_top=True)
        st.caption("The 7-hydroxymitragynine segment is now a top-3 force in SPINS conventional — 7TABZ alone "
                   "(~$151M) is larger than MIT45's entire family (~$32M). High % incremental = promo-fueled "
                   "growth. SPINS is a different panel from Nielsen; treat as a complementary channel lens.")

        band("SPINS Region — Share Matrix (8 Standard Regions · MULO+Conv · 52wk)",
             "$ share within each SPINS region · all brand families — read across to see MIT45 vs competitors")
        _spregmat = q("""SELECT region_name, brand_family, ROUND(dollar_share_pct,1) share
                         FROM GOLD_V3_DB.SALES.REVOPS_SPINS_COMPETITIVE WHERE geo_type='REGION'""")
        if not _spregmat.empty:
            _rpiv = _spregmat.pivot_table(index='REGION_NAME', columns='BRAND_FAMILY', values='SHARE',
                                          aggfunc='first').reset_index().rename(columns={'REGION_NAME': 'SPINS Region'})
            _rb = [c for c in _rpiv.columns if c != 'SPINS Region']
            _rord = (['MIT45'] if 'MIT45' in _rb else []) + sorted([c for c in _rb if c != 'MIT45'])
            _rpiv = _rpiv[['SPINS Region'] + _rord]
            if 'MIT45' in _rpiv.columns:
                _rpiv = _rpiv.sort_values('MIT45', ascending=False)
            show_table(_rpiv)
        st.caption("MIT45 is heavily Northeast-skewed (~13% share there vs ~3% nationally) and near-absent in "
                   "California / West (BT 70%+). The 7-OH segment concentrates in the Southeast (~33%) and "
                   "Mid-South (~26%) — watch those regions. Regions are SPINS' MULO+Conv standard regions "
                   "(not account-specific).")
        help_box("""
<p><b>What this tab adds:</b> the SPINS view of the whole category — including conventional + natural/specialty
stores that Nielsen's c-store cut misses — plus a watch on the fast-rising 7-OH segment and a region-by-region
share grid.</p>
<p><b>Share matrix:</b> read <b>across a row</b> to see MIT45 vs every competitor <b>within one region</b>. It
exposes where we're concentrated (Northeast) and where we're nearly absent (West).</p>
<p><b>Why 7-OH matters:</b> it's a new product class growing on promotion — 7TABZ alone is already bigger than
MIT45's entire family in this panel. High "% incremental" = that growth is deal-driven.</p>
<p><b>Use it for:</b> spotting regional whitespace and emerging competitive threats before they show up in the
c-store numbers.</p>""")

    # ── PROMO & PRICE ────────────────────────────────────────────────────────
    with mt_promo:
        band("Circle K — Price & Promo Ladder (Nielsen)", "Circle K Total · 52wk · $/EQ = pack-size-normalized")
        _ladder = q("""SELECT brand_name "Brand", dollars "$ (52wk)", ROUND(dollar_share_pct,1) "Share %",
                              ROUND(price_per_unit,2) "$/Unit", ROUND(price_per_eq_unit,2) "$/EQ Unit",
                              ROUND(pct_incremental,1) "% Promo"
                       FROM GOLD_V3_DB.SALES.REVOPS_NIELSEN_CK_PRICE ORDER BY dollars DESC""")
        show_table(_ladder, money_cols=['$ (52wk)', '$/Unit', '$/EQ Unit'], bold_top=True)

        band("SPINS Conventional — Price & Promo Ladder", "Total US MULO+Conv · 52wk · volume-weighted $/unit + promo lift")
        _sppp = q("""SELECT brand_family "Brand", dollars "$ (52wk)", ROUND(dollar_share_pct,1) "Share %",
                            ROUND(price_per_unit,2) "$/Unit (wtd)",
                            ROUND(pct_incremental,1) "% Incremental"
                     FROM GOLD_V3_DB.SALES.REVOPS_SPINS_COMPETITIVE
                     WHERE geography_raw='TOTAL US - MULO + CONVENIENCE' ORDER BY dollars DESC""")
        show_table(_sppp, money_cols=['$ (52wk)', '$/Unit (wtd)'], bold_top=True)
        st.caption("Volume-weighted $/unit (Σ$ ÷ Σunits) — the comparable price. MIT45 ≈ $19/unit vs Botanic Tonics "
                   "≈ $10 and the field ≈ $9–10: MIT45 is the premium-priced one in BOTH panels (Nielsen $17). "
                   "MIT45's low/negative % incremental = it isn't promoting. Use base-vs-incremental to test "
                   "price elasticity before any move. (Raw per-SKU ARP only meaningful at UPC grain — a simple "
                   "average across UPCs over-weights tiny premium SKUs, which is why an earlier '$25' showed.)")
        help_box("""
<p><b>What these ladders show:</b> where every brand sits on <b>price</b> and how much it leans on <b>promotion</b>,
in both the Circle K (Nielsen) and conventional (SPINS) panels.</p>
<p><b>Columns:</b> <b>$/Unit</b> = comparable shelf price · <b>$/EQ Unit</b> = price after normalizing pack sizes
(the fairest comparison) · <b>% Promo / % Incremental</b> = how much of sales comes from deals.</p>
<p><b>The MIT45 story:</b> we're the <b>premium</b> price (~$17–19 vs ~$9–10 for the field) and we <b>barely
promote</b> (low % incremental). That's a deliberate position — but it means we win on brand, not price.</p>
<p><b>Use it for:</b> any pricing or promo conversation — see the gap to competitors, and use base-vs-incremental
to gauge whether a promo would actually lift volume before committing spend.</p>""")
