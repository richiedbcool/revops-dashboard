"""
DB Accounts — key-account YTD purchases + last order
Standalone Streamlit app (Community Cloud or Streamlit-in-Snowflake). Mirrors the
revops_signal_dashboard.py design (IBM Plex, navy header band, mono table cells) and
its shared-password + key-pair service-account connection. Reads only
GOLD_V3_DB.SALES.REVOPS_SALES_UNIFIED (REVOPS_DASHBOARD_RO already has SELECT).
"""
import streamlit as st
import pandas as pd
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="DB Accounts", layout="wide")

# Watched key accounts (singular J&M variant kept just in case)
ACCOUNTS = [
    'Red Dawn', 'Annbiz FL', 'Annbiz GA', 'Phresh Picks Distribution, Inc.',
    'NJ Imports', 'Mountain Service Distributors', 'Full House Wholesale',
    'J&M Distributors', 'J&M Distributor',
]

# ── Theme (from revops_signal_dashboard.py) ─────────────────────────────────
T = {"bg": "#ffffff", "border": "#dde2e9", "text": "#1f2937", "text3": "#6b7280",
     "hdr_bg": "#2c5784", "th_bg": "#2c5784", "row_alt": "#f4f6f9"}
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap');
.stApp {{ background:{T['bg']}; font-family:'IBM Plex Sans',sans-serif; }}
.block-container {{ padding-top:1.5rem; }}
.da-header {{ display:flex; align-items:baseline; gap:16px; padding:16px 0 10px;
    border-bottom:2px solid {T['border']}; margin-bottom:16px; }}
.da-title {{ font-family:'IBM Plex Mono',monospace; font-size:20px; font-weight:600;
    color:{T['text']}; letter-spacing:.04em; text-transform:uppercase; }}
.da-sub {{ font-size:12px; color:{T['text3']}; letter-spacing:.08em;
    font-family:'IBM Plex Mono',monospace; }}
table.da-table {{ border-collapse:collapse; width:100%; font-size:13px; }}
table.da-table th {{ background:{T['th_bg']}; color:#fff; padding:8px 12px; text-align:right;
    font-weight:500; font-size:11px; letter-spacing:.03em; border:1px solid {T['hdr_bg']};
    text-transform:uppercase; }}
table.da-table th.acct {{ text-align:left; min-width:240px; }}
table.da-table td {{ border:1px solid {T['border']}; padding:7px 12px; text-align:right;
    font-family:'IBM Plex Mono',monospace; color:{T['text']}; }}
table.da-table td.acct {{ text-align:left; font-family:'IBM Plex Sans',sans-serif; }}
table.da-table tr:nth-child(even) td {{ background:{T['row_alt']}; }}
</style>
""", unsafe_allow_html=True)

# ── Shared-password gate ────────────────────────────────────────────────────
def _check_password():
    if "APP_PASSWORD" not in st.secrets:
        return
    if st.session_state.get("_authed"):
        return
    st.markdown('<div class="da-header"><span class="da-title">DB Accounts</span>'
                '<span class="da-sub">ENTER PASSWORD TO CONTINUE</span></div>',
                unsafe_allow_html=True)
    pw = st.text_input("Password", type="password")   # visible label → not clipped
    if pw == st.secrets["APP_PASSWORD"]:
        st.session_state["_authed"] = True
        st.rerun()
    elif pw:
        st.error("Incorrect password.")
    st.stop()

_check_password()

# ── Snowflake session (ambient in SF; key-pair service acct on Cloud) ───────
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
        "account": st.secrets["sf_account"], "user": st.secrets["sf_user"], "private_key": pk,
        "role": st.secrets.get("sf_role", "REVOPS_DASHBOARD_RO"),
        "warehouse": st.secrets["sf_warehouse"],
        "database": st.secrets.get("sf_database", "GOLD_V3_DB"),
        "schema": st.secrets.get("sf_schema", "SALES"),
    }).create()

session = _get_session()

@st.cache_data(ttl=600, show_spinner=False)
def load_accounts():
    names = ", ".join("'" + a.replace("'", "''") + "'" for a in ACCOUNTS)
    return session.sql(f"""
        WITH u AS (
            SELECT CUSTOMER_NAME, SALE_DATE, REVENUE
            FROM GOLD_V3_DB.SALES.REVOPS_SALES_UNIFIED
            WHERE SALE_DATE >= DATE_TRUNC('year', CURRENT_DATE)
              AND CUSTOMER_NAME IN ({names})
        ),
        ytd AS (SELECT CUSTOMER_NAME, SUM(REVENUE) AS YTD_PURCHASES FROM u GROUP BY 1),
        last_day AS (
            SELECT CUSTOMER_NAME, SALE_DATE AS LAST_PURCHASE_DATE, SUM(REVENUE) AS LAST_PURCHASE_AMT
            FROM u GROUP BY 1, 2
            QUALIFY ROW_NUMBER() OVER (PARTITION BY CUSTOMER_NAME ORDER BY SALE_DATE DESC) = 1
        )
        SELECT y.CUSTOMER_NAME, y.YTD_PURCHASES, d.LAST_PURCHASE_DATE, d.LAST_PURCHASE_AMT
        FROM ytd y JOIN last_day d USING (CUSTOMER_NAME)
        ORDER BY y.YTD_PURCHASES DESC
    """).to_pandas()

# ── Render ──────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="da-header"><span class="da-title">DB Accounts</span>'
    '<span class="da-sub">KEY ACCOUNTS · CALENDAR YTD PURCHASES + LAST ORDER</span></div>',
    unsafe_allow_html=True)

df = load_accounts()
if df.empty:
    st.info("No purchases found for the watched accounts this year.")
    st.stop()

def _money(v):
    return f"${v:,.0f}" if pd.notna(v) else "—"
def _date(v):
    return pd.to_datetime(v).strftime("%b %-d, %Y") if pd.notna(v) else "—"

rows = "".join(
    f"<tr><td class='acct'>{r.CUSTOMER_NAME}</td>"
    f"<td>{_money(r.YTD_PURCHASES)}</td>"
    f"<td>{_date(r.LAST_PURCHASE_DATE)}</td>"
    f"<td>{_money(r.LAST_PURCHASE_AMT)}</td></tr>"
    for r in df.itertuples()
)
total_ytd = _money(df["YTD_PURCHASES"].sum())
st.markdown(
    "<table class='da-table'><thead><tr>"
    "<th class='acct'>Account</th><th>YTD Purchases</th>"
    "<th>Last Purchase</th><th>Last Purchase Amt</th></tr></thead>"
    f"<tbody>{rows}</tbody>"
    f"<tfoot><tr><td class='acct'><b>Total ({len(df)})</b></td>"
    f"<td><b>{total_ytd}</b></td><td></td><td></td></tr></tfoot>"
    "</table>",
    unsafe_allow_html=True)

st.caption("Source: GOLD_V3_DB.SALES.REVOPS_SALES_UNIFIED · calendar YTD · 10-min cache")
