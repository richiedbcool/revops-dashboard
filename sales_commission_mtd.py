"""
Sales Commission — MTD (per salesperson)
Standalone Streamlit app (Community Cloud, like revops_signal_dashboard.py):
shared-password gate + key-pair Snowflake service account.

Purpose: month-end commission worksheet. Shows each rep's MTD revenue + order
count (validated against the "sales-by-salesperson" export to the dollar), their
MTD target, and a $1,500 prepayment column for Inside Sales. Comm % and Payout
are left blank in-app — HR fills Comm % at month-end. The "Export to Excel"
download ships a workbook with LIVE FORMULAS so typing a % into Comm %
auto-computes Payout (= Revenue × Comm%) and Net Payout (= Payout − Prepayment).

Revenue math (reverse-engineered + validated 2026-06-17):
  grain   = SALES_ORDER_SHIPMENT_LINES
  revenue = Σ(shipment-line QUANTITY × order-line UNIT_PRICE)
  period  = shipment COMPLETED_AT in the current calendar month
  #orders = distinct SO_NUMBER
  Sales Admin bucket excluded (moving in-house sales to the group soon).
"""
import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import date
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="Sales Commission — MTD", layout="wide")

# ── Roster crosswalk ────────────────────────────────────────────────────────
# Names differ across systems: ADP stores "Family, Given"; SALES_ORDERS stores a
# free-text "Given Family" (note Miguel is "Gonzales" with an s in orders vs
# "Gonzalez" everywhere else). Role is pulled live from ADP.WORKERS by adp_name.
# mtd_target: derived from the Dec-2027 monthly EXIT targets discounted back at
# each rep's CMGR to the June-2026 month-0 anchor (~$500K). PENDING RICHIE'S
# CONFIRMATION — edit here once locked. William (Inside Sales) + Corey (VP) have
# no exit target in the plan, so left as None (blank).
ROSTER = [
    # display,            order_name (SALES_ORDERS.SALESPERSON), adp_name (ADP.FORMATTED_NAME), inside_sales, mtd_target
    ("Miguel Gonzalez",   "Miguel Gonzales",  "Gonzalez, Miguel",         False, 502_000),
    ("Melinda Kingston",  "Melinda Kingston", "Kingston, Melinda Orlean", False, 502_000),
    ("Santo Perry",       "Santo Perry",      "Perry, Santo A",           False, 497_000),
    ("Nelson Rosario",    "Nelson Rosario",   "Rosario, Nelson",          False, 500_000),
    ("Kamala Watkins",    "Kamala Watkins",   "Lambert-Watkins, Kamala",  False, 496_000),
    ("Quinn McHenry",     "Quinn McHenry",    "McHenry, Quinn Louis",     False, 496_000),
    ("William Stevens",   "William Stevens",  "Stevens, William",         True,  None),
    ("Corey Helper",      "Corey Helper",     "Helper, Corey Leigh",      False, None),
]
INSIDE_SALES_PREPAYMENT = 1_500.0

# ── Shared-password gate (mirrors revops_signal_dashboard.py) ───────────────
def _check_password():
    if "APP_PASSWORD" not in st.secrets:
        return True  # Streamlit-in-Snowflake → already authed
    if st.session_state.get("_authed"):
        return True
    st.title("Sales Commission — MTD")
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

# ── Snowflake session (ambient inside SF; key-pair service acct on Cloud) ───
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
        "schema": st.secrets.get("sf_schema", "PUBLIC"),
    }).create()

session = _get_session()

@st.cache_data(ttl=600, show_spinner=False)
def q(sql):
    return session.sql(sql).to_pandas()

# ── Data: MTD revenue + orders per salesperson, + ADP roles ─────────────────
@st.cache_data(ttl=600, show_spinner=False)
def load_mtd():
    return q("""
        WITH ln AS (
          SELECT so.SALESPERSON,
                 so.SO_NUMBER,
                 TRY_TO_DATE(LEFT(s.COMPLETED_AT,10)) AS comp_date,
                 TRY_CAST(sl.QUANTITY AS NUMBER(18,4))
                   * TRY_CAST(sol.UNIT_PRICE AS NUMBER(18,4)) AS rev
          FROM RAW_V2_DB.SUPABASE_ERP.SALES_ORDER_SHIPMENTS s
          JOIN RAW_V2_DB.SUPABASE_ERP.SALES_ORDERS so ON so.ID = s.SALES_ORDER_ID
          JOIN RAW_V2_DB.SUPABASE_ERP.SALES_ORDER_SHIPMENT_LINES sl ON sl.SHIPMENT_ID = s.ID
          LEFT JOIN RAW_V2_DB.SUPABASE_ERP.SALES_ORDER_LINES sol ON sol.ID = sl.SALES_ORDER_LINE_ID
          WHERE TRY_TO_DATE(LEFT(s.COMPLETED_AT,10)) >= DATE_TRUNC('month', CURRENT_DATE())
        )
        SELECT SALESPERSON,
               ROUND(SUM(rev),2)         AS MTD_REVENUE,
               COUNT(DISTINCT SO_NUMBER) AS NUM_ORDERS
        FROM ln
        WHERE SALESPERSON <> 'Sales Admin'
        GROUP BY SALESPERSON
    """)

@st.cache_data(ttl=600, show_spinner=False)
def load_adp_roles():
    names = ", ".join("'" + r[2].replace("'", "''") + "'" for r in ROSTER)
    df = q(f"""
        SELECT FORMATTED_NAME, POSITION_TITLE
        FROM RAW_V2_DB.ADP.WORKERS
        WHERE FORMATTED_NAME IN ({names})
    """)
    return dict(zip(df["FORMATTED_NAME"], df["POSITION_TITLE"]))

mtd = load_mtd()
rev_by_name = dict(zip(mtd["SALESPERSON"], mtd["MTD_REVENUE"]))
ord_by_name = dict(zip(mtd["SALESPERSON"], mtd["NUM_ORDERS"]))
roles = load_adp_roles()

rows = []
for display, order_name, adp_name, inside, target in ROSTER:
    rows.append({
        "Rep": display,
        "Role": roles.get(adp_name, ""),
        "MTD Revenue": float(rev_by_name.get(order_name, 0) or 0),
        "# Orders": int(ord_by_name.get(order_name, 0) or 0),
        "MTD Target": target,                                   # may be None
        "Comm %": None,                                         # HR fills at month-end
        "Payout": None,                                         # = Revenue × Comm%
        "Prepayment": INSIDE_SALES_PREPAYMENT if inside else 0.0,
    })
df = pd.DataFrame(rows).sort_values("MTD Revenue", ascending=False).reset_index(drop=True)

# ── Display ─────────────────────────────────────────────────────────────────
st.title("Sales Commission — MTD")
st.caption(f"Month-to-date through {date.today():%b %-d, %Y} · revenue recognized on shipment "
           f"completion · Sales Admin excluded · Comm % / Payout filled by HR at month-end")

show = df.copy()
show["MTD Revenue"] = show["MTD Revenue"].map(lambda v: f"${v:,.0f}")
show["MTD Target"]  = show["MTD Target"].map(lambda v: f"${v:,.0f}" if pd.notna(v) else "—")
show["Comm %"]      = "—"
show["Payout"]      = "—"
show["Prepayment"]  = show["Prepayment"].map(lambda v: f"${v:,.0f}" if v else "—")
st.dataframe(show, use_container_width=True, hide_index=True)

# ── Excel export with LIVE formulas ─────────────────────────────────────────
def build_excel(df):
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    wb = Workbook(); ws = wb.active; ws.title = "MTD Commission"
    headers = ["Rep", "Role", "MTD Revenue", "# Orders", "MTD Target",
               "Comm %", "Payout", "Prepayment", "Net Payout"]
    ws.append(headers)
    hdr_fill = PatternFill("solid", fgColor="2C5784")
    hdr_font = Font(color="FFFFFF", bold=True)
    thin = Side(style="thin", color="DDE2E9")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    for c in range(1, len(headers) + 1):
        cell = ws.cell(1, c); cell.fill = hdr_fill; cell.font = hdr_font
        cell.alignment = Alignment(horizontal="center"); cell.border = border

    for i, rec in enumerate(df.to_dict("records"), start=2):
        ws.cell(i, 1, rec["Rep"])
        ws.cell(i, 2, rec["Role"])
        ws.cell(i, 3, round(float(rec["MTD Revenue"]), 2))           # MTD Revenue
        ws.cell(i, 4, int(rec["# Orders"]))                          # # Orders
        if pd.notna(rec["MTD Target"]):
            ws.cell(i, 5, float(rec["MTD Target"]))                  # MTD Target
        ws.cell(i, 6, None)                                          # Comm % — HR input
        ws.cell(i, 7, f"=C{i}*F{i}")                                 # Payout = Revenue × Comm%
        ws.cell(i, 8, float(rec["Prepayment"]))                      # Prepayment
        ws.cell(i, 9, f"=G{i}-H{i}")                                 # Net Payout = Payout − Prepayment
        for col in ["C", "E", "G", "H", "I"]:
            ws[f"{col}{i}"].number_format = '$#,##0.00'
        ws[f"F{i}"].number_format = '0.0%'                           # type 5% (or 0.05)
        for c in range(1, len(headers) + 1):
            ws.cell(i, c).border = border

    widths = {"A": 20, "B": 30, "C": 15, "D": 9, "E": 14, "F": 9, "G": 15, "H": 13, "I": 15}
    for col, w in widths.items():
        ws.column_dimensions[col].width = w
    ws.freeze_panes = "A2"

    # note row explaining the formula behavior
    note = ws.cell(len(df) + 3, 1,
                   "Type a commission rate into Comm % (e.g. 5%). Payout = Revenue × Comm%. "
                   "Net Payout = Payout − Prepayment (Inside Sales $1,500 advance; negative = owed back).")
    note.font = Font(italic=True, color="6B7280")

    bio = BytesIO(); wb.save(bio); return bio.getvalue()

st.download_button(
    "⬇ Export to Excel (with live commission formulas)",
    data=build_excel(df),
    file_name=f"mtd_commission_{date.today():%Y-%m}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
