"""
RevOps Signal Architecture — Daily Dashboard
Streamlit app. Internal sell-in operations: daily/weekly heat maps, at-risk
radar, fulfillment, AR, NRR, pipeline, margin and trade spend.

Design mirrors combined_scorecard.py (daily tab): navy header band, IBM Plex
type, green/yellow/red heat-map cells. Reads the REVOPS_* views in
GOLD_V3_DB.SALES (see revops_signal_views.sql).

Split out 2026-06-29: Market Analysis (Nielsen + SPINS) now lives in its own
Streamlit app, market_analysis.py.
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
