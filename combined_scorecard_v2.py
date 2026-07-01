import streamlit as st
import pandas as pd
from snowflake.snowpark.context import get_active_session
from datetime import date, timedelta

st.set_page_config(page_title="Diversified Botanics Scorecards", layout="wide")

# ── Theme ──────────────────────────────────────────────────────────────────────
# Light-only color palette (dark mode removed 2026-05-12).
# Header band is navy, status cells follow heat-map green/red convention.
T = {
    # Page chrome
    "bg":           "#ffffff",
    "bg2":          "#f4f6f9",
    "bg3":          "#ffffff",
    "border":       "#dde2e9",
    "border2":      "#e6eaef",
    "text":         "#1f2937",
    "text2":        "#4b5563",
    "text3":        "#6b7280",
    "text4":        "#9aa1ab",
    "title":        "#1f2937",
    # Navy header band (matches screenshot)
    "hdr_bg":       "#2c5784",
    "hdr_color":    "#ffffff",
    "hdr_border":   "#2c5784",
    # Table chrome
    "th_bg":        "#2c5784",
    "th_color":     "#ffffff",
    "goal_color":   "#6b7280",
    "leg_color":    "#6b7280",
    "hover":        "#f1f4f8",
    "deadline_bg":  "#fff4e5",
    "row_num":      "#9aa1ab",
    "wavg":         "#4b5563",
    "discuss":      "#2c5784",
    "footer_bg":    "#f4f6f9",
    "footer_color": "#6b7280",
    # Status colors — green / yellow / red
    "g_bg":  "#cbe9ce",
    "g_fg":  "#1f6634",
    "y_bg":  "#fff3bf",
    "y_fg":  "#a37500",
    "r_bg":  "#f4cccc",
    "r_fg":  "#9c2828",
    "e_fg":  "#c8ccd1",
    "na_fg": "#9aa1ab",
}

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

*, html, body {{ box-sizing: border-box; }}
.stApp {{ background: {T['bg']}; font-family: 'IBM Plex Sans', sans-serif; }}

/* ── Streamlit native component overrides ── */
/* Main app background */
.stApp, .stApp > div, section.main, .block-container {{
    background-color: {T['bg']} !important;
}}
/* All text */
.stApp p, .stApp li, .stApp span, .stApp label,
.stMarkdown p, .stMarkdown li,
[data-testid="stMarkdownContainer"] p {{
    color: {T['text']} !important;
}}
/* Headers */
.stApp h1, .stApp h2, .stApp h3, .stApp h4 {{
    color: {T['title']} !important;
}}
/* Expander */
[data-testid="stExpander"] {{
    background-color: {T['bg2']} !important;
    border: 1px solid {T['border']} !important;
    border-radius: 6px !important;
}}
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary p,
[data-testid="stExpander"] summary span {{
    color: {T['text']} !important;
    background-color: {T['bg2']} !important;
}}
[data-testid="stExpander"] > div {{
    background-color: {T['bg']} !important;
}}
/* Tables in markdown */
[data-testid="stMarkdownContainer"] table {{
    border-collapse: collapse;
    width: 100%;
    background: {T['bg']} !important;
}}
[data-testid="stMarkdownContainer"] thead tr {{
    background: {T['bg2']} !important;
}}
[data-testid="stMarkdownContainer"] th {{
    background: {T['bg2']} !important;
    color: {T['text']} !important;
    border: 1px solid {T['border']} !important;
    padding: 8px 12px !important;
}}
[data-testid="stMarkdownContainer"] td {{
    color: {T['text']} !important;
    border: 1px solid {T['border']} !important;
    padding: 6px 12px !important;
    background: {T['bg']} !important;
}}
[data-testid="stMarkdownContainer"] tr:nth-child(even) td {{
    background: {T['bg2']} !important;
}}
/* Code blocks in markdown (table cell source names) */
[data-testid="stMarkdownContainer"] code {{
    background: {T['hdr_bg']} !important;
    color: #1971c2 !important;
    padding: 2px 6px !important;
    border-radius: 3px !important;
    font-size: 11px !important;
}}
/* Caption text */
.stApp .stCaption, [data-testid="stCaptionContainer"] p {{
    color: {T['text3']} !important;
}}
/* Tabs */
[data-testid="stTabs"] [role="tab"] {{
    color: {T['text2']} !important;
}}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {{
    color: {T['hdr_border']} !important;
    border-bottom-color: {T['hdr_border']} !important;
}}
/* Buttons */
.stButton > button {{
    background: {T['bg2']} !important;
    color: {T['text']} !important;
    border: 1px solid {T['border']} !important;
}}
.stButton > button:hover {{
    background: {T['hover']} !important;
    border-color: {T['hdr_border']} !important;
}}
</style>
""", unsafe_allow_html=True)

st.markdown(f"""
<style>
.sc-header {{
    display: flex; align-items: baseline; gap: 16px;
    padding: 20px 0 12px;
    border-bottom: 2px solid {T['border']};
    margin-bottom: 8px;
}}
.sc-title {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 20px; font-weight: 600;
    color: {T['title']}; letter-spacing: 0.04em;
    text-transform: uppercase;
}}
.sc-subtitle {{
    font-size: 12px; color: {T['text3']}; letter-spacing: 0.08em;
    font-family: 'IBM Plex Mono', monospace;
}}
.sc-deadline {{
    margin-left: auto;
    font-size: 11px; color: {T['text4']};
    font-family: 'IBM Plex Mono', monospace;
    background: {T['deadline_bg']}; border: 1px solid {T['border']};
    padding: 4px 10px; border-radius: 4px;
}}

.legend-row {{
    display: flex; gap: 20px; padding: 8px 0 16px;
    font-size: 11px; font-family: 'IBM Plex Mono', monospace;
}}
.leg {{ display: flex; align-items: center; gap: 6px; color: {T['leg_color']}; }}
.leg-dot {{ width: 10px; height: 10px; border-radius: 2px; }}

.section-hdr {{
    background: {T['hdr_bg']};
    color: {T['hdr_color']};
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px; font-weight: 600;
    letter-spacing: 0.12em; text-transform: uppercase;
    padding: 6px 12px;
    border-left: 3px solid {T['hdr_border']};
    margin: 8px 0 4px;
    text-align: left;
}}

.sc-table {{
    width: 100%; border-collapse: collapse;
    font-size: 13px;
}}
.sc-table th {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px; letter-spacing: 0.1em; text-transform: uppercase;
    color: {T['th_color']}; font-weight: 600;
    padding: 6px 10px; text-align: right;
    border-bottom: 1px solid {T['border']};
    background: {T['th_bg']};
}}
.sc-table th.left {{ text-align: left !important; }}
.sc-table td {{
    padding: 7px 10px; text-align: right;
    border-bottom: 1px solid {T['border2']};
    color: {T['text']};
    font-family: 'IBM Plex Sans', sans-serif;
}}
.sc-table td.left {{ text-align: left !important; color: {T['text2']}; }}
.sc-table td.num {{ font-family: 'IBM Plex Mono', monospace; font-size: 13px; }}
.sc-table td.goal {{ font-family: 'IBM Plex Mono', monospace; color: {T['goal_color']}; }}
.sc-table td.wavg {{ font-family: 'IBM Plex Mono', monospace; font-weight: 600; color: {T['wavg']}; }}
.sc-table tr:hover td {{ background: {T['hover']}; }}

.row-num {{ color: {T['row_num']}; font-size: 11px; font-family: 'IBM Plex Mono', monospace; }}

.c-green  {{ background: {T['g_bg']}; color: {T['g_fg']} !important; font-weight: 600; }}
.c-yellow {{ background: {T['y_bg']}; color: {T['y_fg']} !important; font-weight: 600; }}
.c-red    {{ background: {T['r_bg']}; color: {T['r_fg']} !important; font-weight: 600; }}
.c-empty  {{ color: {T['e_fg']} !important; }}
.c-na     {{ color: {T['text']} !important; }}
.label-sub {{ color: #c0c6cc !important; padding-left: 16px !important; }}
.label-sub .row-num {{ color: #c0c6cc !important; }}
/* Extra specificity to beat Streamlit's td overrides */
.sc-table td.c-green  {{ background: {T['g_bg']} !important; color: {T['g_fg']} !important; font-weight: 600; }}
.sc-table td.c-yellow {{ background: {T['y_bg']} !important; color: {T['y_fg']} !important; font-weight: 600; }}
.sc-table td.c-red    {{ background: {T['r_bg']} !important; color: {T['r_fg']} !important; font-weight: 600; }}
.sc-table td.c-empty  {{ color: {T['e_fg']} !important; }}
.sc-table td.c-na     {{ color: {T['text']} !important; }}
.sc-table td.row-num-sub span.row-num {{ color: #c0c6cc !important; }}
.sc-table td.num.c-green  {{ color: {T['g_fg']} !important; }}
.sc-table td.num.c-yellow {{ color: {T['y_fg']} !important; }}
.sc-table td.num.c-red    {{ color: {T['r_fg']} !important; }}
.sc-table td.wavg.c-green  {{ color: {T['g_fg']} !important; }}
.sc-table td.wavg.c-yellow {{ color: {T['y_fg']} !important; }}
.sc-table td.wavg.c-red    {{ color: {T['r_fg']} !important; }}

.discuss-y {{ color: {T['discuss']}; font-size: 11px; font-family: 'IBM Plex Mono', monospace; }}
</style>
""", unsafe_allow_html=True)

# ── v2: shared-password gate + dual session (Snowflake-in-SF OR Community Cloud) ──
# Inside Snowflake: no APP_PASSWORD secret → gate skipped, ambient session used.
# On Community Cloud: APP_PASSWORD gates entry; session built from a key-pair service
# account (REVOPS_DASHBOARD_RO). The Manual Input tab self-disables on Cloud because
# CURRENT_USER() = the service account, which isn't in INPUT_ALLOWED_USERS (read-only).
def _check_password():
    try:
        if "APP_PASSWORD" not in st.secrets:
            return  # no APP_PASSWORD → Streamlit-in-Snowflake (ambient auth)
    except Exception:
        return  # no secrets.toml at all → don't gate (ambient/unconfigured)
    if st.session_state.get("_authed"):
        return
    st.title("Combined Scorecard")
    pw = st.text_input("Password", type="password")   # visible label → not clipped
    if pw == st.secrets["APP_PASSWORD"]:
        st.session_state["_authed"] = True
        st.rerun()
    elif pw:
        st.error("Incorrect password.")
    st.stop()

_check_password()

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
        "schema": st.secrets.get("sf_schema", "PUBLIC"),
    }).create()

session = _get_session()

# Users allowed to access the manual input tab
INPUT_ALLOWED_USERS = {'RICHIE', 'PETE', 'NIKITA'}
try:
    _cu = session.sql("SELECT CURRENT_USER() AS U").to_pandas()
    current_user = _cu.iloc[0]['U'].upper() if not _cu.empty else ''
except:
    current_user = ''
can_input = current_user in INPUT_ALLOWED_USERS

@st.cache_data(ttl=600, show_spinner=False)
def _run_sql(sql):
    """Cached read-only query runner. The cache key is the SQL text itself:
    every query bakes its date range into the f-string, so identical SQL (same
    week) reuses the cached DataFrame instead of re-hitting Snowflake on each
    rerun (tab switch, week nav, input save). `session` is a module global and
    intentionally NOT a parameter, so it is not part of the cache key. Writes
    use session.sql(...).collect() directly and never pass through here."""
    return session.sql(sql).to_pandas()

def q(sql):
    try:
        return _run_sql(sql)
    except Exception:
        # Errors are caught OUTSIDE the cache so a transient Snowflake failure
        # returns an empty frame WITHOUT poisoning the cache for ttl seconds.
        return pd.DataFrame()

def safe_float(v, default=0.0):
    try:
        return float(v) if v is not None and str(v) not in ('', 'nan', 'None') else default
    except:
        return default

# ── Date setup ────────────────────────────────────────────────────────────────
today = date.today()

# Week navigation via session state
if "week_offset" not in st.session_state:
    st.session_state.week_offset = 0

current_mon = today - timedelta(days=today.weekday())
mon = current_mon + timedelta(weeks=st.session_state.week_offset)
days = [mon + timedelta(days=i) for i in range(5)]

# Weekly view range (6 prior weeks + current). Used by daily queries (outlook, aircall)
# so the weekly tab can populate historical weeks for engagement/email rows.
weekly_earliest = (current_mon - timedelta(weeks=6)).strftime('%Y-%m-%d')
weekly_latest   = (current_mon + timedelta(days=6)).strftime('%Y-%m-%d')
day_labels = ["Mon", "Tue", "Wed", "Thu", "Fri"]

# ── Data queries ──────────────────────────────────────────────────────────────

# Ops 1-4: Production
# - Labor Cost, OEE: Liquid lots ONLY (excludes Packing/island lot 2751)
# - Downtime: 100 - AVG(AVAILABILITY_PCT) for Liquid lots ✅ confirmed = 21.9%
#   AVAILABILITY_PCT already removes breaks & planned changeovers from denominator
#   DO NOT use SUM(UNPLANNED_DT_MIN)/SUM(PLANNED_PROD_TIME_MIN) — wrong denominator
# - FPY: Liquid lots only (aligned with Brian's guidance 2026-04-21 — Packing/island excluded)
ops_prod = q(f"""
    SELECT
        PRODUCTION_DATE,
        -- Labor: AVG of per-lot rates for Liquid lots (confirmed method = avg not pooled)
        -- e.g. ($0.2265 + $0.1999 + $0.2788) / 3 = $0.2351 not SUM/SUM
        ROUND(AVG(CASE WHEN PRODUCTION_TYPE='Liquid'
                  THEN DAY_LABOR_COST_AMT / NULLIF(DAY_COMPLETED_QTY, 0) END), 2) AS LABOR_COST_PER_UNIT,
        -- Downtime: 100 - AVG(AVAILABILITY_PCT) for Liquid lots only
        ROUND(100 - AVG(CASE WHEN PRODUCTION_TYPE='Liquid' THEN AVAILABILITY_PCT END), 1) AS UNPLANNED_DT_PCT,
        -- FPY: Liquid lots only (excludes Packing/island)
        ROUND(AVG(CASE WHEN PRODUCTION_TYPE='Liquid' AND FIRST_PASS_PCT > 0 THEN FIRST_PASS_PCT END), 1) AS FPY_PCT,
        -- OEE: Liquid only (Packing OEE is N/A)
        ROUND(AVG(CASE WHEN PRODUCTION_TYPE='Liquid' AND OEE_PCT > 0 THEN OEE_PCT END), 1) AS OEE_PCT
    FROM GOLD_V3_DB.SEMANTIC.SV_DAILY_PRODUCTION
    WHERE PRODUCTION_DATE BETWEEN '{mon}' AND '{days[4]}'
    GROUP BY PRODUCTION_DATE ORDER BY PRODUCTION_DATE
""")

# Ops 5: OTIF DTC — ShipHero on-time % (100 - late rate). Higher = better. Goal 99%
# 2026-04-23: Inverted from late_rate to on-time_pct so the goal column "99%" reads naturally.
ops_otif_dtc = q(f"""
    SELECT
        s.SHIP_DATE,
        ROUND(
            100.0 - COUNT(CASE WHEN s.SHIP_DATE > o.REQUIRED_SHIP_DATE THEN 1 END) * 100.0
            / NULLIF(COUNT(*), 0),
        2) AS ONTIME_PCT
    FROM GOLD_V3_DB.FULFILLMENT.STG_SHIPHERO__SHIPMENTS s
    JOIN GOLD_V3_DB.FULFILLMENT.STG_SHIPHERO__ORDERS o ON o.ORDER_ID = s.ORDER_ID
    WHERE s.SHIP_DATE BETWEEN '{mon}' AND '{days[4]}'
    GROUP BY s.SHIP_DATE ORDER BY s.SHIP_DATE
""")

# Ops 6: OTIF B2B (Acumatica-based) — removed 2026-05-26.
# Replaced by load_b2b_cycle_daily using RAW_V2_DB.SUPABASE_ERP.SALES_ORDERS.
# See b2b_cycle_dict farther down; Target page Fulfillment row 4.


# HR Row 1: Candidates Advanced Through Pipeline
# Best approximation from raw tables: COUNT(*) all stage entries excl Archived, open jobs
# Ashby's exact number (e.g. 68 on Mon Mar 31) uses internal analytics logic we can't replicate
# Our count runs slightly high (~84 vs 68) — gap is Ashby's internal deduplication
# Reverting to include Application Review since excluding it drops count too low (~34)
#
# v2 TODO: LEFT ON RAW (all three Ashby HR loaders below — hr_advanced, hr_interviews,
# hr_qualified). The verified GOLD fact GOLD_V3_DB.SCORECARD.FCT_ASHBY_APPLICATION_EVENTS
# only carries event_type IN (advanced, applied, archived, rejected) + a TO_STAGE label;
# it has NO stage-number (needed for the "qualified" stage>0 rule), NO open-job filter,
# and NO interview-schedule grain (scheduled/completed/cancelled). It cannot reproduce
# any of the app's three HR metric shapes without guessing a stage mapping, so these stay
# on RAW_V2_DB.ASHBY.* until a fuller GOLD Ashby flow/snapshot model exists.
hr_advanced = q(f"""
    SELECT
        h.ENTEREDSTAGEAT::DATE AS DATE,
        COUNT(*) AS ADVANCED
    FROM RAW_V2_DB.ASHBY.APPLICATION_HISTORY h
    JOIN RAW_V2_DB.ASHBY.APPLICATIONS a ON a.ID = h.APPLICATION_ID
    JOIN RAW_V2_DB.ASHBY.JOBS j ON j.ID::STRING = a.JOB:id::STRING
    WHERE h.ENTEREDSTAGEAT::DATE BETWEEN '{mon}' AND '{days[4]}'
      AND j.STATUS = 'Open'
      AND h.TITLE != 'Archived'
    GROUP BY 1 ORDER BY 1
""")

# HR Row 2: Interviews Scheduled vs Completed
# Key: use LATERAL FLATTEN on INTERVIEWEVENTS to get startTime (actual interview date)
# Complete + WaitingOnFeedback = interview happened (feedback pending but interview occurred)
# Cancelled = didn't happen
# Formula: happened / (happened + cancelled)
hr_interviews = q(f"""
    SELECT
        ev.value:startTime::DATE AS DATE,
        COUNT(*) AS SCHEDULED,
        COUNT(CASE WHEN s.STATUS IN ('Complete','WaitingOnFeedback') THEN 1 END) AS COMPLETED,
        COUNT(CASE WHEN s.STATUS = 'Cancelled' THEN 1 END) AS CANCELLED
    FROM RAW_V2_DB.ASHBY.INTERVIEW_SCHEDULES s,
         LATERAL FLATTEN(input => s.INTERVIEWEVENTS) ev
    WHERE ev.value:startTime::DATE BETWEEN '{mon}' AND '{days[4]}'
    GROUP BY 1 ORDER BY 1
""")

# HR Row 3: Net new qualified candidates — CONFIRMED EXACT MATCH vs scorecard (35 for Apr 6)
# stage > 0, open jobs, not Archived or Application Review
hr_qualified = q(f"""
    SELECT h.ENTEREDSTAGEAT::DATE AS DATE, COUNT(*) AS QUALIFIED
    FROM RAW_V2_DB.ASHBY.APPLICATION_HISTORY h
    JOIN RAW_V2_DB.ASHBY.APPLICATIONS a ON a.ID = h.APPLICATION_ID
    JOIN RAW_V2_DB.ASHBY.JOBS j ON j.ID::STRING = a.JOB:id::STRING
    WHERE h.ENTEREDSTAGEAT::DATE BETWEEN '{mon}' AND '{days[4]}'
      AND j.STATUS = 'Open'
      AND h.STAGENUMBER > 0
      AND h.TITLE NOT IN ('Archived', 'Application Review')
    GROUP BY 1 ORDER BY 1
""")

# Marketing: REMOVED 2026-04-29 — current Trailing 90D rows are obsolete; new set arriving next week.
# Original logic preserved verbatim below for reference. Re-enable by uncommenting and
# restoring the lookup dicts, green-count checks, and row definitions further down.
#
# def mkt_90d_weekly(table):
#     return q(f"""
#         WITH all_orders AS (
#             SELECT
#                 BILLING:email::STRING AS EMAIL,
#                 CUSTOMER_ID,
#                 DATE(DATE_CREATED) AS ORDER_DATE,
#                 CAST(TOTAL AS FLOAT) AS ORDER_TOTAL
#             FROM RAW_V2_DB.{table}.ORDERS
#             WHERE STATUS IN ('processing','completed')
#         ),
#         first_order_ever AS (
#             SELECT EMAIL, MIN(ORDER_DATE) AS FIRST_ORDER_DATE
#             FROM all_orders
#             GROUP BY EMAIL
#         ),
#         week_days AS (
#             SELECT DATEADD('day', seq, '{mon}'::DATE) AS REPORT_DATE
#             FROM (SELECT ROW_NUMBER() OVER (ORDER BY SEQ4()) - 1 AS seq
#                   FROM TABLE(GENERATOR(ROWCOUNT => 5)))
#             WHERE DATEADD('day', seq, '{mon}'::DATE) <= CURRENT_DATE()
#         )
#         SELECT
#             w.REPORT_DATE,
#             COUNT(*)                                                          AS ORDERS_90D,
#             ROUND(AVG(o.ORDER_TOTAL), 2)                                     AS AOV_90D,
#             COUNT(DISTINCT CASE
#                 WHEN f.FIRST_ORDER_DATE BETWEEN w.REPORT_DATE - 90 AND w.REPORT_DATE
#                 THEN o.EMAIL END)                                            AS NEW_BUYERS_90D
#         FROM week_days w
#         JOIN all_orders o
#             ON o.ORDER_DATE BETWEEN w.REPORT_DATE - 90 AND w.REPORT_DATE
#         JOIN first_order_ever f ON f.EMAIL = o.EMAIL
#         GROUP BY w.REPORT_DATE
#         ORDER BY w.REPORT_DATE
#     """)
#
# mkt_gm_90_df  = mkt_90d_weekly('WOO_GOLDEN_MONK')
# mkt_mit_90_df = mkt_90d_weekly('WOO_MIT45')
# mkt_up_90_df  = mkt_90d_weekly('WOO_UPRISING')

# Business Ops Row 2: ClickUp tasks past due % — One Brain space (ID 901312029407)
# Reads from TASKS_SNAPSHOT which stores full task state per day
# Key: compare DUE_DATE < SNAPSHOT_DATE (not < today) so each day is self-consistent
# Formula: past due / ALL open tasks (confirmed 3.1% for Apr 7)
clickup_snap = q(f"""
    -- v2: repointed to GOLD_V3_DB.SCORECARD.FCT_CLICKUP_TASKS_PASTDUE_DAILY (verified
    -- fact). One pre-computed row per snapshot date for the One Brain space; the
    -- past-due / open-task / pct math now lives in the GOLD model. Contract preserved:
    -- SNAPSHOT_DATE, TOTAL_OPEN, PAST_DUE, PCT_PAST_DUE (only PCT_PAST_DUE is consumed).
    SELECT
        SNAPSHOT_DATE,
        OPEN_TASKS     AS TOTAL_OPEN,
        PAST_DUE_TASKS AS PAST_DUE,
        PCT_PAST_DUE
    FROM GOLD_V3_DB.SCORECARD.FCT_CLICKUP_TASKS_PASTDUE_DAILY
    WHERE SNAPSHOT_DATE BETWEEN '{mon}' AND '{days[4]}'
    ORDER BY SNAPSHOT_DATE
""")

clickup_dict = {}
if not clickup_snap.empty:
    clickup_snap["SNAPSHOT_DATE"] = pd.to_datetime(clickup_snap["SNAPSHOT_DATE"]).dt.date
    clickup_dict = dict(zip(clickup_snap["SNAPSHOT_DATE"], clickup_snap["PCT_PAST_DUE"]))
# Sales Row 1: Average daily engagements per rep — Aircall calls only
# Excludes Ari Meisel and Corey Helper (non-sales reps)
# "Engagement" = any completed call (inbound or outbound), avg across active reps that day
aircall = q(f"""
    -- v2: repointed to GOLD_V3_DB.SCORECARD.FCT_SALES_REP_CALLS_DAILY (verified fact).
    -- Per-rep daily calls pre-bucketed by MT date with the scorecard-rep roster baked
    -- into IS_SCORECARD_REP, so the day-level aggregate (active reps + total calls +
    -- avg/rep) is rebuilt here to match the prior contract: CALL_DATE, ACTIVE_REPS,
    -- TOTAL_CALLS, AVG_PER_REP. TOTAL_CALLS = all completed/handled calls (= old done).
    SELECT
        ACTIVITY_DATE                                            AS CALL_DATE,
        COUNT(DISTINCT REP_NAME)                                 AS ACTIVE_REPS,
        SUM(TOTAL_CALLS)                                         AS TOTAL_CALLS,
        ROUND(SUM(TOTAL_CALLS) / NULLIF(COUNT(DISTINCT REP_NAME), 0), 1) AS AVG_PER_REP
    FROM GOLD_V3_DB.SCORECARD.FCT_SALES_REP_CALLS_DAILY
    WHERE ACTIVITY_DATE BETWEEN '{weekly_earliest}' AND '{weekly_latest}'
      AND IS_SCORECARD_REP
    GROUP BY 1 ORDER BY 1
""")

# Outlook email activity per day — counts reps active in email (excl Corey Helper)
# Categorization (2026-05-11 update):
#   NEW       = CATEGORY = 'Future Customer' (prospects, not yet in Acumatica)
#   EXISTING  = CATEGORY IN ('Past Customer', 'Current Customer') (anyone in Acumatica list)
#   UNKNOWN   = CATEGORY = 'Unknown' (will be classified over time)
# All three count toward Total Engagements now (was: future + past only).
# Per-recipient counts from SENT_EMAILS_ENRICHED so BCC blasts register each prospect.
outlook = q(f"""
    -- v2: repointed to GOLD_V3_DB.SCORECARD.FCT_SALES_REP_EMAILS_DAILY (verified fact).
    -- Per-rep daily external-email counts pre-bucketed by MT date with the scorecard
    -- roster baked into IS_SCORECARD_REP and internal-domain recipients already
    -- excluded. NEW/EXISTING/UNKNOWN map to the GOLD category breakouts; EMAILS_TOTAL
    -- = EXTERNAL_EMAILS_SENT (= new+existing+unknown). Contract preserved: SENT_DATE,
    -- NEW_TOTAL, EXISTING_TOTAL, UNKNOWN_TOTAL, EMAILS_TOTAL, EMAIL_REPS.
    SELECT
        ACTIVITY_DATE                                            AS SENT_DATE,
        SUM(NEW_CUSTOMER_EMAILS)                                 AS NEW_TOTAL,
        SUM(EXISTING_CUSTOMER_EMAILS)                            AS EXISTING_TOTAL,
        SUM(UNKNOWN_EMAILS)                                      AS UNKNOWN_TOTAL,
        SUM(EXTERNAL_EMAILS_SENT)                                AS EMAILS_TOTAL,
        COUNT(DISTINCT REP_NAME)                                 AS EMAIL_REPS
    FROM GOLD_V3_DB.SCORECARD.FCT_SALES_REP_EMAILS_DAILY
    WHERE ACTIVITY_DATE BETWEEN '{weekly_earliest}' AND '{weekly_latest}'
      AND IS_SCORECARD_REP
    GROUP BY 1 ORDER BY 1
""")
outlook_map = {}
if not outlook.empty:
    outlook["SENT_DATE"] = pd.to_datetime(outlook["SENT_DATE"]).dt.date
    for _, row in outlook.iterrows():
        outlook_map[row["SENT_DATE"]] = {
            "new":      int(row["NEW_TOTAL"]      or 0),
            "existing": int(row["EXISTING_TOTAL"] or 0),
            "unknown":  int(row["UNKNOWN_TOTAL"]  or 0),
            "total":    int(row["EMAILS_TOTAL"]   or 0),
            "reps":     int(row["EMAIL_REPS"]     or 0),
        }

# Snapshot table populated by TASK_SNAPSHOT_AR_PAST_DUE (SYSADMIN task, Mon-Fri 5:30 PM MT)
# Falls back to live Supabase_ERP.INVOICES query for today if snapshot not yet taken
ar_snap = q(f"""
    SELECT SNAPSHOT_DATE, AR_PAST_DUE_AMT
    FROM GOLD_V3_DB.PUBLIC.AR_PAST_DUE_DAILY
    WHERE SNAPSHOT_DATE BETWEEN '{mon}' AND '{days[4]}'
    ORDER BY SNAPSHOT_DATE
""")

# Live fallback for today if today's snapshot hasn't run yet (before 5:30 PM MT)
# Past-due AR from Supabase_ERP invoices (migrated 2026-05-22): sums BALANCE_DUE
# across non-voided invoices > 30 days old. Mirrors SNAPSHOT_AR_PAST_DUE proc.
ar_live = q("""
    SELECT SUM(TRY_CAST(BALANCE_DUE AS NUMBER(18,2))) AS AR_PAST_DUE_AMT
    FROM RAW_V2_DB.SUPABASE_ERP.INVOICES
    WHERE TRY_CAST(BALANCE_DUE AS NUMBER(18,2)) > 0
      AND VOIDED_AT IS NULL
      AND DATEDIFF('day', TRY_TO_DATE(INVOICE_DATE), CURRENT_DATE()) > 30
""")
ar_live_amt = safe_float(ar_live.iloc[0]["AR_PAST_DUE_AMT"]) if not ar_live.empty else 0

# Build AR dict: use snapshot if available, else live value for today only
ar_dict = {}
if not ar_snap.empty:
    ar_snap["SNAPSHOT_DATE"] = pd.to_datetime(ar_snap["SNAPSHOT_DATE"]).dt.date
    ar_dict = dict(zip(ar_snap["SNAPSHOT_DATE"], ar_snap["AR_PAST_DUE_AMT"]))
# Fill in today with live value if no snapshot yet for today
if today not in ar_dict and ar_live_amt > 0:
    ar_dict[today] = ar_live_amt

# ── Manual scorecard inputs ───────────────────────────────────────────────────
# Reads from GOLD_V3_DB.PUBLIC.MANUAL_SCORECARD_INPUTS
# One value per metric per day — latest entry wins via MERGE in save function
manual_inputs_df = q(f"""
    SELECT METRIC_KEY, METRIC_DATE, VALUE
    FROM GOLD_V3_DB.PUBLIC.MANUAL_SCORECARD_INPUTS
    WHERE METRIC_DATE BETWEEN DATE_TRUNC('MONTH', '{mon}'::DATE) AND '{days[4]}'
    ORDER BY METRIC_DATE, METRIC_KEY
""")

# Per-HR-metric date->value dicts (used by Target tab lagging bars + heatmap).
# Spans month-to-date so _weeks_green_so_far can iterate weeks in the current month.
def _hr_metric_dict(metric_key):
    if manual_inputs_df.empty: return {}
    df = manual_inputs_df.copy()
    df = df[df['METRIC_KEY'] == metric_key].copy()
    df['METRIC_DATE'] = pd.to_datetime(df['METRIC_DATE']).dt.date
    return {d: safe_float(v) for d, v in zip(df['METRIC_DATE'], df['VALUE'])}

hr_perf_dict     = _hr_metric_dict('HR_PERFORMANCE_DOC')
hr_training_dict = _hr_metric_dict('HR_TRAINING_COMPLIANCE')
hr_career_dict   = _hr_metric_dict('HR_CAREER_PATH')

# ── Procurement manual inputs (v8 redesign, 2026-05-22) ─────────────────────
# Data is fragmented mid-Acumatica→[new system] migration: receipts in Acumatica,
# new POs in AI-generated PDFs, DTC stock in ShipHero. Procurement enters weekly
# (Monday-dated) and carry-forward fills Mon-Fri cells. Three KPIs:
#   - DSI (DTC, ShipHero-derived) — combined for MTD; brand-split (GM/MIT45/UP) in daily
#   - Supplier OTD % (trailing 90d) — now automated, see load_supplier_otd_combined
#   - % Critical Components Single-Sourced (top-80%-spend Pareto; LOWER is better)
def _carry_forward_dict(metric_key):
    """date -> latest value on-or-before, evaluated for each Mon-Fri in displayed week."""
    if manual_inputs_df.empty: return {}
    df = manual_inputs_df[manual_inputs_df['METRIC_KEY'] == metric_key].copy()
    if df.empty: return {}
    df['METRIC_DATE'] = pd.to_datetime(df['METRIC_DATE']).dt.date
    df = df.sort_values('METRIC_DATE')
    out = {}
    for d in days:
        prior = df[df['METRIC_DATE'] <= d]
        if not prior.empty:
            out[d] = safe_float(prior.iloc[-1]['VALUE'])
    return out

proc_dsi_combined_dict       = _carry_forward_dict('PROC_DSI_COMBINED_DAYS')
proc_dsi_gm_dict             = _carry_forward_dict('PROC_DSI_GM_DAYS')
proc_dsi_mit45_dict          = _carry_forward_dict('PROC_DSI_MIT45_DAYS')
proc_dsi_up_dict             = _carry_forward_dict('PROC_DSI_UP_DAYS')
proc_otd_dict                = _carry_forward_dict('PROC_OTD_PCT_90D')


# Supplier OTD % (trailing 90d) — automated from purchasing data (2026-05-28).
# Combines the legacy Acumatica receipt feed (ACUMATICA_EXPORT.PORECEIPTLINE, which
# stops ~2026-03-12) with the new ERP feed (SUPABASE_ERP.PURCHASE_RECEIPTS). As days
# pass, old receipts roll out of the 90d window and the new ERP data takes over.
# A receipt is on-time if RECEIPT_DATE <= the PO's expected/promised date. When the
# PO has no expected/promised date, we fall back to the receipt date — i.e. count it
# on-time (don't penalize for a missing target). Computed value overrides the manual
# PROC_OTD_PCT_90D carry-forward; manual remains the fallback for days with no receipts.
@st.cache_data(ttl=600)
def load_supplier_otd_combined(win_start, end_date):
    # v2: repointed to GOLD_V3_DB.SCORECARD.FCT_SUPPLIER_OTD_DAILY (verified fact).
    # The GOLD fact is already aggregated per receipt-day (one row/day) with RECEIPTS
    # and ON_TIME_RECEIPTS, so we no longer expand per individual receipt. The trailing
    # 90d rollup downstream now sums ON_TIME_RECEIPTS / RECEIPTS over the window (see
    # _build_supplier_otd_dict and the MBR Supplier-OTD path). Contract: per-day rows
    # with RCV_DATE + ON_TIME (= ON_TIME_RECEIPTS) + RECEIPTS (added denominator).
    return q(f"""
        SELECT RECEIPT_DATE     AS rcv_date,
               ON_TIME_RECEIPTS AS on_time,
               RECEIPTS         AS receipts
        FROM GOLD_V3_DB.SCORECARD.FCT_SUPPLIER_OTD_DAILY
        WHERE RECEIPT_DATE BETWEEN '{win_start}' AND '{end_date}'
    """)

def _build_supplier_otd_dict():
    win_start = (days[0] - timedelta(days=90)).strftime('%Y-%m-%d')
    df = load_supplier_otd_combined(win_start, days[4].strftime('%Y-%m-%d'))
    if df.empty: return {}
    df['RCV_DATE'] = pd.to_datetime(df['RCV_DATE']).dt.date
    out = {}
    for d in days:
        lo = d - timedelta(days=90)
        w = df[(df['RCV_DATE'] > lo) & (df['RCV_DATE'] <= d)]
        # GOLD rows are per-day aggregates: weight on-time by RECEIPTS, not row count.
        denom = w['RECEIPTS'].sum() if not w.empty else 0
        if denom:
            out[d] = round(100.0 * w['ON_TIME'].sum() / denom, 1)
    return out

# Computed OTD overrides manual carry-forward; manual stays as fallback for empty days.
proc_otd_dict.update(_build_supplier_otd_dict())

proc_single_sourced_dict     = _carry_forward_dict('PROC_PCT_SINGLE_SOURCED')

# % Critical Components Single-Sourced — automated hybrid (2026-05-29). LOWER is
# better (target ≤25%). Structural snapshot of how many critical components have
# only one supplier. Hybrid sourcing:
#   - SKU master / identity  → SUPABASE_ERP.ITEMS.SKU (the new ERP item master;
#     resolves all critical 5-digit codes → description/class). Retires the old
#     Acumatica INVENTORYCD↔INVENTORYID crosswalk for identity.
#   - Vendor breadth         → HYBRID (2026-06-17): GREATER of (a) distinct Acumatica
#     POLINE VENDORID per SKU (vendors we've ordered from) and (b) distinct
#     SUPABASE_ERP.VENDOR_ITEMS VENDOR_ID per SKU (vendors qualified to supply it).
#     The catalog grew from 4 rows (too sparse @ 05-29) to a usable item->vendor master,
#     so it now counts. pct keeps falling toward reality as catalog coverage grows.
# A SKU counts single-sourced if that combined vendor count is <= 1 (no PO history AND
# not in the catalog => treated as single — conservative).
# Denominator = critical SKUs that resolve in the Supabase item master.
# 05-29 (PO-history-only): 57 single / 75 = 76.0%.
# 06-17 (hybrid): 53 single / 75 = 70.7% (4 SKUs reclassified multi via the catalog;
# 26/75 critical SKUs in catalog so far). Overrides manual carry-forward; manual stays
# as the fallback.
#
# SOURCE OF TRUTH for the 75-SKU list + hybrid math is the Snowflake view
# GOLD_V3_DB.PUBLIC.V_PROC_SINGLE_SOURCED (DDL: v_proc_single_sourced.sql).
# Every surface (this app, scorecard-tv, pdf digest, Slack proc) does a 1-line
# SELECT from it so the critical-SKU list never drifts. To change the list or
# the single-sourced rule, edit the view DDL and redeploy — not this file.
@st.cache_data(ttl=600)
def load_single_sourced_snapshot():
    return q("SELECT denom, single_cnt, pct FROM GOLD_V3_DB.PUBLIC.V_PROC_SINGLE_SOURCED")

# Daily history of the single-sourced %, written nightly by SNAPSHOT_PROC_SINGLE_SOURCED
# (rides TASK_SNAPSHOT_AR_PAST_DUE, 5:30 PM MT Mon-Fri). Same dated-snapshot + live-today
# pattern as AR Past Due. Gives a real day-over-day trend as the VENDOR_ITEMS catalog grows
# (each new backup vendor lowers that day's pct). Snapshotting began 2026-06-17; days before
# that have no row and render blank — we don't backfill fabricated history.
@st.cache_data(ttl=600)
def load_single_sourced_daily(win_start, end_date):
    return q(f"""
        SELECT SNAPSHOT_DATE, PCT
        FROM GOLD_V3_DB.PUBLIC.PROC_SINGLE_SOURCED_DAILY
        WHERE SNAPSHOT_DATE BETWEEN '{win_start}' AND '{end_date}'
        ORDER BY SNAPSHOT_DATE
    """)

def _build_single_sourced_dict():
    out = {}
    snap = load_single_sourced_daily(days[0].strftime('%Y-%m-%d'), days[4].strftime('%Y-%m-%d'))
    if not snap.empty:
        snap['SNAPSHOT_DATE'] = pd.to_datetime(snap['SNAPSHOT_DATE']).dt.date
        for d, p in zip(snap['SNAPSHOT_DATE'], snap['PCT']):
            v = safe_float(p)
            if v is not None:
                out[d] = v
    # Live fallback for today only, before tonight's snapshot writes today's row.
    if today not in out:
        live = load_single_sourced_snapshot()
        if not live.empty:
            v = safe_float(live.iloc[0]['PCT'])
            if v is not None:
                out[today] = v
    return out

# Snapshot history (locked per day) + live value for today; overrides manual carry-forward.
proc_single_sourced_dict.update(_build_single_sourced_dict())
# Critical stockout SKU counts (≤7 days of cover, active demand only) — daily alert.
# Scoped to Golden Monk only (2026-05-22): MIT45 and Uprising removed since current
# operational focus is GM. Keys PROC_CRITICAL_STOCKOUT_MIT45 / _UP still exist in DB
# but are no longer read or rendered.
proc_critical_stockout_gm    = _carry_forward_dict('PROC_CRITICAL_STOCKOUT_GM')
# Total active SKUs (denominator for DSI lagging composite "X days · Y/Z critical")
proc_total_active_skus_dict  = _carry_forward_dict('PROC_TOTAL_ACTIVE_SKUS')
# Supplier Scorecard % (manual weekly entry, 2026-05-28). Replaces GM Critical
# Stockouts (daily/heatmap) and DSI Combined (lagging). ≥90% = green.
proc_supplier_scorecard_dict = _carry_forward_dict('PROC_SUPPLIER_SCORECARD')

def get_manual(metric_key, date):
    if manual_inputs_df.empty: return None
    df = manual_inputs_df.copy()
    df['METRIC_DATE'] = pd.to_datetime(df['METRIC_DATE']).dt.date
    row = df[(df['METRIC_KEY'] == metric_key) & (df['METRIC_DATE'] == date)]
    if row.empty: return None
    return safe_float(row.iloc[0]['VALUE'])

def save_manual(metric_key, metric_date, value, note=''):
    """MERGE into manual inputs table — one value per metric per day."""
    try:
        session.sql(f"""
            MERGE INTO GOLD_V3_DB.PUBLIC.MANUAL_SCORECARD_INPUTS AS tgt
            USING (SELECT
                '{metric_key}'::VARCHAR       AS METRIC_KEY,
                '{metric_date}'::DATE         AS METRIC_DATE,
                {float(value)}                AS VALUE,
                '{note}'::VARCHAR             AS NOTE,
                CURRENT_TIMESTAMP()           AS ENTERED_AT
            ) AS src
            ON tgt.METRIC_KEY = src.METRIC_KEY AND tgt.METRIC_DATE = src.METRIC_DATE
            WHEN MATCHED THEN UPDATE SET
                VALUE = src.VALUE, NOTE = src.NOTE, ENTERED_AT = src.ENTERED_AT
            WHEN NOT MATCHED THEN INSERT
                (METRIC_KEY, METRIC_DATE, VALUE, NOTE, ENTERED_AT)
            VALUES
                (src.METRIC_KEY, src.METRIC_DATE, src.VALUE, src.NOTE, src.ENTERED_AT)
        """).collect()
        return True
    except Exception as e:
        return str(e)

# ── Support / Intercom metrics ───────────────────────────────────────────────
# CSAT: rolling 7-day window ending each day, scores 4-5 = positive
# Response time: median time_to_admin_reply in minutes per day
# Open backlog: live point-in-time counts (total open + tickets over 48 hours old)
# AI deflection: assumed_resolution + confirmed_resolution / AI-touched conversations

intercom = q(f"""
    SELECT
        TO_TIMESTAMP(CREATED_AT)::DATE AS CONV_DATE,
        -- CSAT rolling 7D ending on each day
        COUNT(CASE WHEN CONVERSATION_RATING:rating::NUMBER >= 4 THEN 1 END) AS CSAT_POS,
        COUNT(CASE WHEN CONVERSATION_RATING:rating::NUMBER IS NOT NULL THEN 1 END) AS CSAT_RATED,
        -- Median first response (minutes) — 24/7, median over mean (Intercom standard)
        ROUND(MEDIAN(STATISTICS:time_to_admin_reply::NUMBER) / 60.0, 1) AS MEDIAN_RESP_MIN,
        -- Fin AI deflection (Intercom-aligned, finalized 2026-05-06)
        --   Numerator   = conversations Fin resolved (assumed_/confirmed_resolution)
        --   Denominator = conversations Fin actually attempted to answer
        --                 (AI_AGENT:last_answer_type = 'ai_answer')
        --   Previously the denominator was `AI_AGENT IS NOT NULL`, which counted any
        --   conversation that hit an AI workflow even when Fin never replied — this
        --   inflated the denom and pushed the % ~30pts too low.
        COUNT(CASE WHEN AI_AGENT:resolution_state::STRING
                        IN ('assumed_resolution','confirmed_resolution') THEN 1 END) AS AI_DEFLECTED,
        COUNT(CASE WHEN AI_AGENT:last_answer_type::STRING = 'ai_answer' THEN 1 END) AS AI_TOUCHED
    FROM RAW_V2_DB.INTERCOM.CONVERSATIONS
    WHERE TO_TIMESTAMP(CREATED_AT)::DATE BETWEEN '{mon}' AND '{days[4]}'
    GROUP BY 1 ORDER BY 1
""")

# Open backlog — snapshot table (frozen at 5:30 PM MT daily) with live fallback
# Same pattern as AR Past Due — snapshot written by TASK_SNAPSHOT_AR_PAST_DUE each evening
# Table stores both TOTAL_OPEN and OPEN_OVER_48H per snapshot date
backlog_snap = q(f"""
    SELECT SNAPSHOT_DATE, TOTAL_OPEN, OPEN_OVER_48H
    FROM GOLD_V3_DB.PUBLIC.INTERCOM_BACKLOG_DAILY
    WHERE SNAPSHOT_DATE BETWEEN '{weekly_earliest}' AND '{weekly_latest}'
    ORDER BY SNAPSHOT_DATE
""")
backlog_live_raw = q("""
    SELECT
        COUNT(*) AS TOTAL_OPEN,
        COUNT(CASE WHEN TO_TIMESTAMP(CREATED_AT)
                        < DATEADD(hour, -48, CURRENT_TIMESTAMP()) THEN 1 END) AS OPEN_OVER_48H
    FROM RAW_V2_DB.INTERCOM.CONVERSATIONS
    WHERE OPEN = TRUE
""")
total_open_live = int(safe_float(backlog_live_raw.iloc[0]['TOTAL_OPEN'])) if not backlog_live_raw.empty else None
over48_live     = int(safe_float(backlog_live_raw.iloc[0]['OPEN_OVER_48H'])) if not backlog_live_raw.empty else None

# Build backlog dicts: snapshot values for past days, live for today if no snapshot yet
total_open_dict, over48_dict = {}, {}
if not backlog_snap.empty:
    backlog_snap['SNAPSHOT_DATE'] = pd.to_datetime(backlog_snap['SNAPSHOT_DATE']).dt.date
    # Drop rows with NULLs before int cast — TOTAL_OPEN is NULL for rows written before the column was added
    total_rows = backlog_snap.dropna(subset=['TOTAL_OPEN'])
    over48_rows = backlog_snap.dropna(subset=['OPEN_OVER_48H'])
    total_open_dict = dict(zip(total_rows['SNAPSHOT_DATE'], total_rows['TOTAL_OPEN'].astype(int)))
    over48_dict     = dict(zip(over48_rows['SNAPSHOT_DATE'], over48_rows['OPEN_OVER_48H'].astype(int)))
if today not in total_open_dict and total_open_live is not None:
    total_open_dict[today] = total_open_live
if today not in over48_dict and over48_live is not None:
    over48_dict[today] = over48_live

# ── Day-keyed lookup helpers ──────────────────────────────────────────────────
def day_lookup(df, date_col, val_col):
    if df.empty: return {}
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col]).dt.date
    return dict(zip(df[date_col], df[val_col]))

def day_lookup_filter(df, date_col, val_col, filter_col, filter_val):
    if df.empty: return {}
    df = df.copy()
    df = df[df[filter_col] == filter_val]
    df[date_col] = pd.to_datetime(df[date_col]).dt.date
    return dict(zip(df[date_col], df[val_col]))

# Marketing lookup dicts — REMOVED 2026-04-29, see top of file
# gm_orders_90  = day_lookup(mkt_gm_90_df.copy(),  "REPORT_DATE", "ORDERS_90D")
# gm_aov_90     = day_lookup(mkt_gm_90_df.copy(),  "REPORT_DATE", "AOV_90D")
# gm_new_90     = day_lookup(mkt_gm_90_df.copy(),  "REPORT_DATE", "NEW_BUYERS_90D")
# mit_orders_90 = day_lookup(mkt_mit_90_df.copy(), "REPORT_DATE", "ORDERS_90D")
# mit_aov_90    = day_lookup(mkt_mit_90_df.copy(), "REPORT_DATE", "AOV_90D")
# mit_new_90    = day_lookup(mkt_mit_90_df.copy(), "REPORT_DATE", "NEW_BUYERS_90D")
# up_orders_90  = day_lookup(mkt_up_90_df.copy(),  "REPORT_DATE", "ORDERS_90D")
# up_aov_90     = day_lookup(mkt_up_90_df.copy(),  "REPORT_DATE", "AOV_90D")
# up_new_90     = day_lookup(mkt_up_90_df.copy(),  "REPORT_DATE", "NEW_BUYERS_90D")

# Aircall lookup dict — store as (avg_per_rep, total_calls) tuple
aircall_dict = {}
if not aircall.empty:
    aircall["CALL_DATE"] = pd.to_datetime(aircall["CALL_DATE"]).dt.date
    for _, row in aircall.iterrows():
        aircall_dict[row["CALL_DATE"]] = (safe_float(row["AVG_PER_REP"]), int(row["TOTAL_CALLS"]))

def get_total_engagements(d):
    """
    Total Engagements/rep = (calls + all emails) / active reps
    Updated 2026-05-11: all email categories (new + existing + unknown) now count.
    Active reps = union of reps who made calls OR sent any email (excl Corey).
    Returns (avg_per_rep, total_engagements, active_reps) tuple or None
    """
    ac  = aircall_dict.get(d)   # (avg_per_rep, total_calls) or None
    em  = outlook_map.get(d)    # dict with new/existing/unknown/total/reps or None

    calls_total  = int(ac[1])    if ac else 0
    calls_reps   = int(round(ac[1] / ac[0])) if ac and ac[0] else 0
    emails_total = em["total"]   if em else 0
    email_reps   = em["reps"]    if em else 0

    total_eng = calls_total + emails_total

    # Union of reps: use max of aircall reps and email reps as proxy
    # (can't perfectly deduplicate without rep-level join, but close enough)
    active_reps = max(calls_reps, email_reps)

    if active_reps == 0:
        return None
    avg = round(total_eng / active_reps, 1)
    return (avg, total_eng, active_reps)


def get_emails_per_rep(d):
    """
    Total emails / email reps for the day. Counts all 3 categories.
    Returns (avg_per_rep, total_emails, active_email_reps) tuple or None
    """
    em = outlook_map.get(d)
    if not em or em["reps"] == 0:
        return None
    return (round(em["total"] / em["reps"], 1), em["total"], em["reps"])


def get_calls_per_rep(d):
    """
    Calls per rep — pulls from aircall_dict, returns same shape as get_emails_per_rep.
    Returns (avg_per_rep, total_calls, active_call_reps) tuple or None.
    """
    ac = aircall_dict.get(d)
    if not ac or not ac[0]:
        return None
    reps = int(round(ac[1] / ac[0]))
    if reps == 0:
        return None
    return (safe_float(ac[0]), int(ac[1]), reps)


# ── TSM Daily Activities — combined calls + emails per rep (target page, 2026-05-13)
# Sales target page narrows to 3 KPIs; calls (50) + emails (40) collapse into one
# combined "Daily Activities" target = 90 total per rep, regardless of mix.
def get_daily_activities(d):
    """Combined calls + emails per rep, plus the breakout components.
    Returns (combined_per_rep, calls_per_rep, emails_per_rep) or None if neither has data.
    """
    calls = get_calls_per_rep(d)
    emails = get_emails_per_rep(d)
    c = calls[0] if isinstance(calls, tuple) else None
    e = emails[0] if isinstance(emails, tuple) else None
    if c is None and e is None:
        return None
    return (round((c or 0) + (e or 0), 1), c or 0, e or 0)


# ── Pipeline Activity Movement — ClickUp Sales CRM stage progressions
# Counts distinct deals that ENTERED a live status on day d, in space 901313268656.
# 2026-05-14 redef: count any change INTO a live state (not lost/abandoned/
# disqualified). That includes revivals (dead→live). Mass cleanups (live→dead)
# excluded as housekeeping rather than pipeline-building activity.
#
# 2026-06-03 rewrite: sourced from RAW.CLICKUP.TASK_STATUS_HISTORY (per-task
# status-change EVENTS with ENTERED_AT) instead of TASKS_SNAPSHOT day-over-day
# diffs. Why:
#   • Exact-day attribution — the old daily snapshot sampled once at ~12:17pm MT,
#     so afternoon moves smeared into the next day. ENTERED_AT is the real moment.
#   • No dependency on the daily snapshot cron + Airbyte timing (which froze
#     05-29→06-01 and silently blanked the metric). History self-backfills gaps.
#   • Validated against the 05-28 snapshot: 96.5% status-match on covered tasks;
#     remaining diffs are mostly the snapshot being stale (it read lagging TASKS).
# ENTERED_AT is UTC (TIMESTAMP_NTZ); we convert to America/Denver (Mountain, DST-
# aware) before bucketing so a move lands on the correct business day. Space
# filter via TASKS.SPACE_ID (the history table carries no space). Note: deals
# that never changed status aren't in history — correct for a *movement* metric
# (they didn't move), but history alone can't reproduce funnel *membership*.
@st.cache_data(ttl=600)
def load_pipeline_movement(start_date, end_date):
    # v2: repointed to GOLD_V3_DB.SCORECARD.FCT_PIPELINE_MOVEMENT_DAILY (verified fact).
    # TASKS_MOVED = distinct deals that entered a live status that day (the app's old
    # COUNT(DISTINCT TASK_ID)); aliased to MOVEMENTS to preserve the contract (D, MOVEMENTS).
    sql = f"""
    SELECT MOVEMENT_DATE AS d,
           TASKS_MOVED   AS movements
    FROM GOLD_V3_DB.SCORECARD.FCT_PIPELINE_MOVEMENT_DAILY
    WHERE MOVEMENT_DATE BETWEEN '{start_date}' AND '{end_date}'
    ORDER BY MOVEMENT_DATE
    """
    return q(sql)

_pipe_df = load_pipeline_movement(days[0], days[4])
pipeline_movement_dict = {}
if not _pipe_df.empty:
    _pipe_df['D'] = pd.to_datetime(_pipe_df['D']).dt.date
    pipeline_movement_dict = dict(zip(_pipe_df['D'], _pipe_df['MOVEMENTS']))


# ── A/R Past Due "31+" naming = same data as the existing ar_dict (2026-05-14
# clarification). The "31+" label is just what Sales calls it — there's no
# separate aging-bucket filter. All Target-page / Daily / Lagging "A/R Past Due
# 31+" rows point at ar_dict, which reads AR_PAST_DUE_AMT from the snapshot.


# ── TARGET-PAGE METRICS (2026-05-13 wave) ─────────────────────────────────────
# Finance + Marketing rows pull from sources outside the original combined-scorecard
# data set. Each loader returns a date→value dict aligned to `days` (Mon–Fri of the
# selected week) so build_target_table_html can fan out into per-day cells.

# ── Finance #1 — Same-Day Cash Reconciliation
# Spec: green if a non-zero cash balance row exists for that BALANCE_DATE, red otherwise.
# Source: GOLD_V3_DB.FINANCE.FACT_DAILY_CASH_BALANCE (currently SharePoint-fed).
@st.cache_data(ttl=600)
def load_cash_balance_dict(start_date, end_date):
    df = q(f"""
        SELECT BALANCE_DATE AS d,
               CASE WHEN ENDING_CASH_BALANCE_AMT IS NOT NULL
                     AND ENDING_CASH_BALANCE_AMT <> 0 THEN 1 ELSE 0 END AS reconciled
        FROM GOLD_V3_DB.FINANCE.FACT_DAILY_CASH_BALANCE
        WHERE BALANCE_DATE BETWEEN '{start_date}' AND '{end_date}'
    """)
    if df.empty: return {}
    df['D'] = pd.to_datetime(df['D']).dt.date
    return dict(zip(df['D'], df['RECONCILED']))

cash_balance_dict = load_cash_balance_dict(days[0], days[4])


# ── Feed freshness guard ──────────────────────────────────────────────────────
# Catches the silent-zero failure mode: when the SharePoint cash feed or the Gold
# daily-revenue build stalls, downstream metrics (Same-Day Cash Rec, Marketing
# Revenue MTD) render as 0/NO and look like real misses. This pulls each feed's
# latest real data point so the render layer can surface the lag — a not-loaded
# day must never be mistaken for a genuine zero.
@st.cache_data(ttl=600)
def load_feed_freshness():
    df = q("""
        SELECT 'cash_balance' AS FEED,
               TO_VARCHAR(MAX(CASE WHEN ENDING_CASH_BALANCE_AMT <> 0 THEN BALANCE_DATE END)) AS LAST_DATA,
               TO_VARCHAR(MAX(_SOURCE_SYNCED_AT)) AS LAST_SYNC
        FROM GOLD_V3_DB.FINANCE.FACT_DAILY_CASH_BALANCE
        UNION ALL
        SELECT 'mktg_dtc_rev',
               TO_VARCHAR(MAX(CASE WHEN CHANNEL='DTC' THEN REVENUE_DATE END)),
               NULL
        FROM GOLD_V3_DB.SALES.FACT_DAILY_REVENUE
    """)
    out = {}
    for _, r in df.iterrows():
        out[r['FEED']] = {'last_data': r['LAST_DATA'], 'last_sync': r['LAST_SYNC']}
    return out

feed_freshness = load_feed_freshness()

# ── Finance #3 — % of Sources Synced in the last 24h
# Spec: 100% green, anything else red.
# Denominator = connectors active in last 7d (filters out long-stale ones).
# Numerator   = connectors whose latest successful COMPLETED_AT on day d
#               was within 24h of EOD on d.
# Per-day historical view so the cell color reflects "data freshness" on that day.
@st.cache_data(ttl=600)
def load_sync_coverage_daily(start_date, end_date):
    df = q(f"""
        WITH active_connectors AS (
            -- Regular-cadence connectors only: 14-day window + ≥2 runs excludes
            -- one-off manual backfills that would inflate the denominator.
            -- Upper bound prevents post-period syncs from leaking back into historical days.
            SELECT CONNECTOR_ID
            FROM ETL_METADATA.PUBLIC.SYNC_HISTORY
            WHERE STARTED_AT BETWEEN DATEADD('day', -14, '{end_date}') AND DATEADD('day', 1, '{end_date}'::DATE)
              AND CONNECTOR_ID NOT IN (
                  '95e56184-c168-4ef7-9d2d-6da7205e3eaa',  -- Acumatica→Supabase: multi-day cadence by design
                  'a404848c-88f1-4ec6-ae99-d360b6c38864'   -- Lunch Money: still in testing
              )
            GROUP BY CONNECTOR_ID
            HAVING COUNT(*) >= 2
        ),
        days AS (
            SELECT d::DATE AS d FROM (
                SELECT DATEADD('day', SEQ4(), '{start_date}'::DATE) AS d
                FROM TABLE(GENERATOR(ROWCOUNT => 5))
            ) WHERE d <= '{end_date}'::DATE
        )
        SELECT d.d AS d,
               COUNT(DISTINCT a.CONNECTOR_ID) AS denom,
               COUNT(DISTINCT CASE
                     WHEN s.COMPLETED_AT BETWEEN
                          TIMESTAMPADD('hour', -24, DATEADD('day', 1, d.d))
                          AND DATEADD('day', 1, d.d)
                      AND s.STATUS = 'completed'
                     THEN s.CONNECTOR_ID END) AS synced
        FROM days d
        CROSS JOIN active_connectors a
        LEFT JOIN ETL_METADATA.PUBLIC.SYNC_HISTORY s ON s.CONNECTOR_ID = a.CONNECTOR_ID
        GROUP BY d.d
    """)
    if df.empty: return {}
    df['D'] = pd.to_datetime(df['D']).dt.date
    # Drop future days: a day that hasn't happened yet has 0 completed syncs, which
    # would read as 0% and drag down the lagging MTD average (which has no future
    # guard, unlike the daily/heatmap getters). No data is correct for a future day.
    df = df[df['D'] <= today]
    df['PCT'] = df.apply(lambda r: round(r['SYNCED'] / r['DENOM'] * 100, 1) if r['DENOM'] else None, axis=1)
    return dict(zip(df['D'], df['PCT']))

sync_coverage_dict = load_sync_coverage_daily(days[0], days[4])


# ── Finance #2 — % of JEs in the New ERP (Supabase_ERP vs Acumatica)
# Updated 2026-05-22: DB_COOL is dead, Supabase_ERP is the new system. Counted
# by unique journal entry (one BATCH_NUMBER in Acumatica = one JOURNAL_ENTRY_ID
# in Supabase_ERP). Numerator = JEs in Supabase. Denominator = Supabase + Acumatica.
# Supabase CREATED_AT is an ISO timestamp string, parsed via TRY_TO_DATE(LEFT(...10)).
@st.cache_data(ttl=600)
def load_je_new_erp_pct(start_date, end_date):
    df = q(f"""
        WITH combined AS (
            SELECT 'ACUMATICA'    AS src,
                   TRANSACTION_DATE AS d,
                   BATCH_NUMBER     AS je_id
            FROM GOLD_V3_DB.ACUMATICA.STG_ACUMATICA__GL_TRANSACTIONS
            WHERE TRANSACTION_DATE BETWEEN '{start_date}' AND '{end_date}'
            UNION ALL
            SELECT 'SUPABASE_ERP' AS src,
                   TRY_TO_DATE(LEFT(CREATED_AT, 10)) AS d,
                   JOURNAL_ENTRY_ID AS je_id
            FROM RAW_V2_DB.SUPABASE_ERP.GL_JOURNAL_ENTRY_LINES
            WHERE TRY_TO_DATE(LEFT(CREATED_AT, 10)) BETWEEN '{start_date}' AND '{end_date}'
        )
        SELECT d,
               COUNT(DISTINCT je_id) AS total_jes,
               COUNT(DISTINCT CASE WHEN src='SUPABASE_ERP' THEN je_id END) AS new_jes,
               ROUND(COUNT(DISTINCT CASE WHEN src='SUPABASE_ERP' THEN je_id END) * 100.0
                     / NULLIF(COUNT(DISTINCT je_id), 0), 1) AS pct_new
        FROM combined
        GROUP BY d
    """)
    if df.empty: return {}
    df['D'] = pd.to_datetime(df['D']).dt.date
    return dict(zip(df['D'], df['PCT_NEW']))

je_new_erp_dict = load_je_new_erp_pct(days[0], days[4])


# ── Marketing — GA4 daily roll-up (all 3 brands) for the week
# Returns dict-by-date with: atc (events), ga4_purchases (events), new_users.
# Cart Abandonment % = (ATC − GA4 purchase) / ATC — matches marketing_scorecard.py
# (Option B picked 2026-05-13: same-client funnel, no Woo/GA4 drift).
# Unique Sessions = newUsers across all brands.
@st.cache_data(ttl=600)
def load_marketing_ga4_daily(start_date, end_date):
    # v2: Cart-abandonment inputs (ATC / purchases) repointed to the verified fact
    # GOLD_V3_DB.SCORECARD.FCT_MARKETING_WEB_FUNNEL_DAILY (per-brand → summed per day).
    # That fact has SESSIONS but no new-users column, so new_users is sourced from
    # GOLD_V3_DB.MARKETING.FACT_WEB_SESSIONS (NEW_USERS, summed across brands per day).
    # Contract preserved: per-date {new_users, atc, purch, cart_abandon_pct}; the
    # Python cart_abandon_pct math below is untouched.
    df = q(f"""
        WITH overview AS (
            SELECT SESSION_DATE AS d, SUM(NEW_USERS) AS new_users
            FROM GOLD_V3_DB.MARKETING.FACT_WEB_SESSIONS
            WHERE SESSION_DATE BETWEEN '{start_date}' AND '{end_date}'
            GROUP BY 1
        ),
        events AS (
            SELECT EVENT_DATE AS d,
                   SUM(ADD_TO_CARTS) AS atc,
                   SUM(PURCHASES)    AS purch
            FROM GOLD_V3_DB.SCORECARD.FCT_MARKETING_WEB_FUNNEL_DAILY
            WHERE EVENT_DATE BETWEEN '{start_date}' AND '{end_date}'
            GROUP BY 1
        )
        SELECT e.d, o.new_users, e.atc, e.purch
        FROM events e LEFT JOIN overview o ON o.d = e.d
        ORDER BY e.d
    """)
    if df.empty: return {}
    df['D'] = pd.to_datetime(df['D']).dt.date
    out = {}
    for _, r in df.iterrows():
        atc = safe_float(r['ATC'])
        purch = safe_float(r['PURCH'])
        abandon_pct = (
            round(max(0, atc - purch) / atc * 100, 1)
            if atc and atc > 0 and purch is not None else None
        )
        out[r['D']] = {
            'new_users':  int(safe_float(r['NEW_USERS'], 0)) if r['NEW_USERS'] is not None else None,
            'atc': atc, 'purch': purch,
            'cart_abandon_pct': abandon_pct,
        }
    return out

marketing_ga4_dict = load_marketing_ga4_daily(days[0], days[4])


# ── Marketing — AOV First (180-day rolling) per day, all 3 brands rolled up.
# Spec (2026-05-13): "First order" = customer with no completed purchase in prior 180 days.
# Cloned from marketing_scorecard.py load_wc_daily_aov_180d.
@st.cache_data(ttl=600)
def load_aov_first_180d_daily(start_date, end_date):
    lookback_start = (pd.to_datetime(start_date) - pd.Timedelta(days=180)).date()
    sources = " UNION ALL ".join(
        f"SELECT BILLING:email::STRING AS email, ID AS order_id, "
        f"DATE(DATE_CREATED) AS d, CAST(TOTAL AS FLOAT) AS total, STATUS "
        f"FROM RAW_V2_DB.{s}.ORDERS"
        for s in ['WOO_GOLDEN_MONK', 'WOO_MIT45', 'WOO_UPRISING']
    )
    df = q(f"""
        WITH all_orders AS ({sources}),
        completed AS (
            SELECT email, order_id, d, total FROM all_orders
            WHERE status IN ('processing','completed')
              AND d BETWEEN '{lookback_start}' AND '{end_date}'
        ),
        classified AS (
            SELECT c.d, c.total,
                   (SELECT COUNT(*) FROM completed p
                    WHERE p.email = c.email
                      AND p.d >= DATEADD('day', -180, c.d)
                      AND p.d < c.d) AS prior_180d
            FROM completed c
            WHERE c.d BETWEEN '{start_date}' AND '{end_date}'
        )
        SELECT d, ROUND(AVG(CASE WHEN prior_180d = 0 THEN total END), 2) AS aov_first
        FROM classified GROUP BY d ORDER BY d
    """)
    if df.empty: return {}
    df['D'] = pd.to_datetime(df['D']).dt.date
    return dict(zip(df['D'], df['AOV_FIRST']))

aov_first_180d_dict = load_aov_first_180d_daily(days[0], days[4])


# ── Fulfillment (added 2026-05-14) — Shiphero shipments + orders join ─────────
# Spec: 3 KPIs on the Target page — On-Time Ship, Same-Day Ship, Median Cycle.
# Source rows: RAW_V2_DB.SHIPHERO.SHIPMENTS joined to RAW_V2_DB.SHIPHERO.ORDERS.
# COMPLETED is a boolean flag (true = shipment is finalized). CREATED_DATE on the
# shipment row is the effective ship date. Cycle time uses ORDER_DATE → CREATED_DATE.
# Same-Day Ship (updated 2026-05-26): warehouse ships Mon–Fri (excluding holidays
# below) with a 1pm MT cutoff. Orders before 1pm MT target same MT day; after 1pm
# MT target the next business day; weekends + holidays push to the next open
# business day. Dict keys stay on UTC ship date so downstream daily/weekly
# lookups (which iterate UTC dates) keep working.
#
# 2026-06-12 — FIRST completed shipment per order only (per Richie: "once an
# order ships, don't count it again"). Return→re-shipments were re-entering the
# metric weeks later as guaranteed misses + giant cycle outliers (e.g. order
# 775323: shipped 5/08, re-shipped 6/09 → counted as a 33-day miss). The rank
# must be computed over ALL of an order's completed shipments (all time) BEFORE
# the date filter, else a re-ship looks like the "first" inside the window.
# Same-day package splits dedupe to the first label (~11 of 8.6k orders/90d).
#
# 2026-06-12 Phase 2 — HOLD-AWARE CLOCK START (ORDER_HISTORY sync landed).
# GOLD_V3_DB.FULFILLMENT.ORDER_FULFILLMENT_CYCLE.CLOCK_START_AT = GREATEST(
# order_date, last blocker-clearing event BEFORE first ship) — clearing = hold
# released or shipping fields updated, classified in FULFILLMENT.ORDER_EVENT_LOG
# from RAW SHIPHERO.ORDER_HISTORY. Both same-day targeting and the cycle clock
# now start at the hold release, so a CS delay (e.g. 778219: address hold
# 6/1→6/9, shipped 6/9 = on-time, ~2 biz-hr cycle) no longer reads as a
# warehouse miss. LEAST(clock, ship_ts) guards against clock > ship; orders
# without history fall back to order_date (COALESCE).
#
# Hit condition is <= (ship ON OR BEFORE target), not =. Required once the
# clock can shift, and it fixes a pre-existing artifact: an after-1pm order
# shipped the same afternoon beat its next-day target and counted as a MISS
# under equality. Early shipping is never a miss.

# US warehouse closure days — covers 2024-2027. Update annually.
# Listed literal dates only; if a fixed-date holiday falls on Sat/Sun, the
# weekend → next-business-day push handles it. Federal "observed Friday" closures
# for Sat holidays are NOT modeled here (revisit if Jul 4 2026 / Christmas 2027
# observance matters).
US_SHIP_HOLIDAYS = [
    '2024-01-01','2024-01-15','2024-02-19','2024-05-27','2024-07-04','2024-09-02',
    '2024-11-28','2024-11-29','2024-12-24','2024-12-25',
    '2025-01-01','2025-01-20','2025-02-17','2025-05-26','2025-07-04','2025-09-01',
    '2025-11-27','2025-11-28','2025-12-24','2025-12-25',
    '2026-01-01','2026-01-19','2026-02-16','2026-05-25','2026-07-04','2026-09-07',
    '2026-11-26','2026-11-27','2026-12-24','2026-12-25',
    '2027-01-01','2027-01-18','2027-02-15','2027-05-31','2027-07-04','2027-09-06',
    '2027-11-25','2027-11-26','2027-12-24','2027-12-25',
]
_HOLIDAY_VALUES_SQL = ",".join(f"('{d}'::DATE)" for d in US_SHIP_HOLIDAYS)
US_SHIP_HOLIDAYS_SET = {pd.to_datetime(d).date() for d in US_SHIP_HOLIDAYS}

# Departments that close on US holidays — daily KPI cells render blank and the
# Target page weekly denominator drops by one per holiday in the week. Other
# depts (Marketing, Customer Support) keep flowing because their metrics come
# from always-on systems (campaigns, Intercom auto-deflection).
HOLIDAY_BLANK_DEPTS = {"Sales", "Manufacturing", "HR", "Fulfillment", "Procurement", "Finance"}

@st.cache_data(ttl=600)
def load_fulfillment_daily(start_date, end_date):
    # v2: repointed to GOLD_V3_DB.SCORECARD.FCT_FULFILLMENT_SCORECARD_DAILY (verified
    # fact). Same-day-ship % and median order-to-ship business-hours cycle are
    # precomputed in the GOLD model (first-completed-shipment, hold-aware clock,
    # 1pm MT cutoff, business-window rules all live there). Aliased back to the prior
    # contract columns (D, SHIPMENTS, SAME_DAY_PCT, MEDIAN_HRS); returns (same_day, cycle).
    df = q(f"""
        SELECT SHIP_DATE                   AS d,
               SHIPPED_ORDERS              AS shipments,
               SAME_DAY_SHIP_PCT           AS same_day_pct,
               MEDIAN_CYCLE_BUSINESS_HOURS AS median_hrs
        FROM GOLD_V3_DB.SCORECARD.FCT_FULFILLMENT_SCORECARD_DAILY
        WHERE SHIP_DATE BETWEEN '{start_date}' AND '{end_date}'
        ORDER BY SHIP_DATE
    """)
    if df.empty: return {}, {}
    df['D'] = pd.to_datetime(df['D']).dt.date
    same_day = dict(zip(df['D'], df['SAME_DAY_PCT']))
    cycle = dict(zip(df['D'], df['MEDIAN_HRS']))
    return same_day, cycle

fulfill_same_day_dict, fulfill_cycle_dict = load_fulfillment_daily(days[0], days[4])


# ── DTC OTIF (added 2026-05-26) ──────────────────────────────────────────────
# Per-order metric: an order passes OTIF when ALL lines were shipped in full
# (qty_shipped >= qty on every line) AND the last shipment date is on/before
# the next-business-day-pushed required ship date. Attributed to the order's
# UTC last_ship_d so it keys consistently with the other Fulfillment dicts.
@st.cache_data(ttl=600)
def load_dtc_otif_daily(start_date, end_date):
    # v2: repointed to GOLD_V3_DB.SCORECARD.FCT_DTC_OTIF_DAILY (verified fact). OTIF_PCT
    # (all lines in-full AND last ship on/before next-business-day required date) is
    # precomputed per ship date in the GOLD model. Contract: {date: otif_pct}.
    df = q(f"""
        SELECT SHIP_DATE AS d, OTIF_PCT AS otif_pct
        FROM GOLD_V3_DB.SCORECARD.FCT_DTC_OTIF_DAILY
        WHERE SHIP_DATE BETWEEN '{start_date}' AND '{end_date}'
        ORDER BY SHIP_DATE
    """)
    if df.empty: return {}
    df['D'] = pd.to_datetime(df['D']).dt.date
    return dict(zip(df['D'], df['OTIF_PCT']))

dtc_otif_dict = load_dtc_otif_daily(days[0], days[4])


# ── B2B OTIF (rev 2026-05-28) ────────────────────────────────────────────────
# Redefined from an on-time/in-full % to AVERAGE BUSINESS HOURS to ship, measured
# APPROVED_AT → COMPLETED_AT.
#
# Business hours = wall-clock elapsed minus any time falling on a Saturday, Sunday
# or US_SHIP_HOLIDAY (those days contribute zero). So Fri 1pm → Mon 1pm = 24 hrs,
# and across a holiday weekend Fri 1pm → Tue 1pm = 24 hrs. Business days count
# their full 24h; only weekends/holidays are stripped.
#
# Attribution: COMPLETED_AT date (MT), so an order finished today posts to today
# regardless of when it was approved.
@st.cache_data(ttl=600)
# v2: repointed to GOLD_V3_DB.SCORECARD.FCT_B2B_OTIF_DAILY. NOTE: no live-today fallback — current-day cell is blank until dbt loads same-day (see SCORECARD-GOLD-DEFINITION-MISMATCHES.md §0).
def load_b2b_ship_hours_daily(start_date, end_date):
    df = q(f"""
        SELECT COMPLETED_DATE AS d, AVG_BUSINESS_HOURS AS ship_hrs
        FROM GOLD_V3_DB.SCORECARD.FCT_B2B_OTIF_DAILY
        WHERE COMPLETED_DATE BETWEEN '{start_date}' AND '{end_date}'
        ORDER BY COMPLETED_DATE
    """)
    if df.empty: return {}
    df['D'] = pd.to_datetime(df['D']).dt.date
    return dict(zip(df['D'], df['SHIP_HRS']))

b2b_ship_hrs_dict = load_b2b_ship_hours_daily(days[0], days[4])


# Intercom lookup dicts
# CSAT: rolling 7D — for each day compute 7-day window ending that day
def get_csat_rolling7(target_date):
    """CSAT % positive over rolling 7 days ending target_date."""
    if target_date > today: return None  # Don't show data for future days
    if intercom.empty: return None
    df = intercom.copy()
    df['CONV_DATE'] = pd.to_datetime(df['CONV_DATE']).dt.date
    window = df[df['CONV_DATE'] <= target_date].tail(7)
    if window.empty: return None
    pos = window['CSAT_POS'].sum()
    rated = window['CSAT_RATED'].sum()
    return round(pos * 100.0 / rated, 1) if rated > 0 else None

def get_deflection(target_date):
    """AI deflection % for that specific day."""
    if target_date > today: return None  # Don't show data for future days
    if intercom.empty: return None
    df = intercom.copy()
    df['CONV_DATE'] = pd.to_datetime(df['CONV_DATE']).dt.date
    row = df[df['CONV_DATE'] == target_date]
    if row.empty: return None
    touched = row.iloc[0]['AI_TOUCHED']
    deflected = row.iloc[0]['AI_DEFLECTED']
    return round(deflected * 100.0 / touched, 1) if touched > 0 else None

intercom_resp_dict = day_lookup(intercom.copy(), 'CONV_DATE', 'MEDIAN_RESP_MIN') if not intercom.empty else {}


prod_labor   = day_lookup(ops_prod.copy(), "PRODUCTION_DATE", "LABOR_COST_PER_UNIT")
prod_dt      = day_lookup(ops_prod.copy(), "PRODUCTION_DATE", "UNPLANNED_DT_PCT")
prod_fpy     = day_lookup(ops_prod.copy(), "PRODUCTION_DATE", "FPY_PCT")
prod_oee     = day_lookup(ops_prod.copy(), "PRODUCTION_DATE", "OEE_PCT")
otif_dtc     = day_lookup(ops_otif_dtc.copy(), "SHIP_DATE", "ONTIME_PCT")
# b2b_cycle removed 2026-05-26 — see b2b_cycle_dict (Supabase ERP source).
hr_adv_dict  = day_lookup(hr_advanced.copy(), "DATE", "ADVANCED")
hr_qual_dict = day_lookup(hr_qualified.copy(), "DATE", "QUALIFIED")

# Interviews: store as "completed/scheduled" string per day, color by pct
hr_int_dict = {}
if not hr_interviews.empty:
    hr_interviews["DATE"] = pd.to_datetime(hr_interviews["DATE"]).dt.date
    for _, row in hr_interviews.iterrows():
        hr_int_dict[row["DATE"]] = (int(row["COMPLETED"]), int(row["SCHEDULED"]))

# Marketing lookups are scalar 90d values (not day-keyed) — handled via _mkt_val above

# ── Color + rendering helpers ─────────────────────────────────────────────────
def raw_color(val, green_fn, yellow_fn, fmt_fn):
    if val is None or str(val) in ('', 'nan', 'None'):
        return "—", "c-empty"
    v = safe_float(val)
    display = fmt_fn(v)
    if green_fn(v):    css = "c-green"
    elif yellow_fn(v): css = "c-yellow"
    else:              css = "c-red"
    return display, css

def td(val_css, extra="num"):
    v, css = val_css
    return f'<td class="{extra} {css}">{v}</td>'

def empty_td():
    return '<td class="num c-empty">—</td>'

# ── Table builder ─────────────────────────────────────────────────────────────
def build_table_html(rows):
    html = ['<table class="sc-table">']
    html.append('<tr>')
    html.append('<th class="left" style="width:32px"></th>')
    html.append('<th class="left" style="min-width:290px">Metric</th>')
    html.append('<th style="width:90px">Goal</th>')
    for lbl in day_labels:
        html.append(f'<th style="width:90px">{lbl}</th>')
    html.append('<th style="width:90px">Weekly Avg.</th>')
    html.append('</tr>')

    current_dept = None
    for row in rows:
        dept, row_num, label, goal_str, get_fn, color_fn, discuss = row
        if dept != current_dept:
            current_dept = dept
            html.append(f'<tr><td colspan="9"><div class="section-hdr">{dept}</div></td></tr>')

        dept_blanks_holidays = dept in HOLIDAY_BLANK_DEPTS
        # Procurement metrics (Critical Stockouts, OTD 90d, % Single-Sourced) are
        # as-of-today snapshots whose getters return the same value for future
        # dates. Blank future cells so the week strip doesn't pre-publish them.
        dept_blanks_future = dept == "Procurement"
        day_vals = []
        for d in days:
            if dept_blanks_holidays and d in US_SHIP_HOLIDAYS_SET:
                day_vals.append(None)
            elif dept_blanks_future and d > today:
                day_vals.append(None)
            else:
                day_vals.append(get_fn(d))
        day_cells = []
        for dv in day_vals:
            day_cells.append(empty_td() if dv is None else td(color_fn(dv)))

        numeric_vals = []
        for v in day_vals:
            if v is None or str(v) in ('','nan','None'):
                continue
            if isinstance(v, tuple):
                continue  # interview row — skip avg
            fv = safe_float(v)
            if fv > 0:
                numeric_vals.append(fv)
        avg_v = sum(numeric_vals) / len(numeric_vals) if numeric_vals else None

        avg_cell = (f'<td class="wavg {color_fn(avg_v)[1]}">{color_fn(avg_v)[0]}</td>'
                    if avg_v is not None else '<td class="wavg c-empty">—</td>')

        is_sub = dept == "Sales" and str(row_num) in ("2","3","4","5","6")
        num_class   = "left row-num-sub" if is_sub else "left"
        label_class = "left label-sub"   if is_sub else "left"
        html.append(f'''<tr>
            <td class="{num_class}"><span class="row-num">{row_num}</span></td>
            <td class="{label_class}">{label}</td>
            <td class="goal">{goal_str}</td>
            {chr(39).join(day_cells)}
            {avg_cell}
        </tr>''')
    html.append('</table>')
    return ''.join(html)


# ── Sales Rep Scorecard (Sales tab) ───────────────────────────────────────────
# Per-rep MTD leaderboard: activity (Aircall outbound + Outlook), live ClickUp
# funnel membership (current TASKS — matches the 2026-06-03 snapshot→TASKS move,
# so it can't go blank when the daily snapshot lags), shipment-based revenue, and
# quota tiers. Styled with the same sc-table design as the Daily scorecard.
@st.cache_data(ttl=600)
def load_sales_reps():
    return q("""
WITH reps AS (
  SELECT * FROM VALUES
    ('Corey Helper',    'Corey Helper',    'Director, National Accounts','National Accounts', NULL),
    ('Kamala Watkins',  'Kamala Watkins',  'Key Account Manager',        'National Accounts', NULL),
    ('Miguel Gonzalez', 'Miguel Gonzales', 'Regional Sales Manager',     'Distributor Channel', NULL),
    ('Santo Perry',     'Santo Perry',     'Regional Sales Manager',     'Distributor Channel', NULL),
    ('Nelson Rosario',  'Nelson Rosario',  'Regional Sales Manager',     'Distributor Channel', NULL),
    ('Melinda Kingston','Melinda Kingston','Inside Sales Rep',           'Inside Sales',        45000),
    ('William Stevens', 'William Stevens', 'Inside Sales Rep',           'Inside Sales',        45000)
  AS r(rep, so_name, role, pod, monthly_target)
),
bounds AS (SELECT DATE_TRUNC('month', CURRENT_DATE())::DATE AS m_start, CURRENT_DATE() AS m_end),
-- v2: calls/emails repointed to the verified per-rep daily facts
-- GOLD_V3_DB.SCORECARD.FCT_SALES_REP_CALLS_DAILY / FCT_SALES_REP_EMAILS_DAILY. REP_NAME
-- matches the roster's display name (`rep`). Weekday (Mon-Fri) totals + distinct active
-- weekdays are summed from the daily grain, preserving the calls/emails CTE columns
-- (outbound_calls, call_days, calls_wd, emails_total, email_days, emails_wd).
calls_base AS (
  SELECT REP_NAME AS rep, ACTIVITY_DATE AS cd, OUTBOUND_COMPLETED_CALLS AS n
  FROM GOLD_V3_DB.SCORECARD.FCT_SALES_REP_CALLS_DAILY, bounds b
  WHERE REP_NAME IN (SELECT rep FROM reps)
    AND ACTIVITY_DATE BETWEEN b.m_start AND b.m_end
),
calls AS (
  SELECT rep, SUM(n) AS outbound_calls,
         COUNT(DISTINCT CASE WHEN DAYOFWEEKISO(cd)<6 AND n>0 THEN cd END) AS call_days,
         SUM(CASE WHEN DAYOFWEEKISO(cd)<6 THEN n ELSE 0 END) AS calls_wd
  FROM calls_base GROUP BY rep
),
emails_base AS (
  SELECT REP_NAME AS rep, ACTIVITY_DATE AS ed, EXTERNAL_EMAILS_SENT AS n
  FROM GOLD_V3_DB.SCORECARD.FCT_SALES_REP_EMAILS_DAILY, bounds b
  WHERE REP_NAME IN (SELECT rep FROM reps)
    AND ACTIVITY_DATE BETWEEN b.m_start AND b.m_end
),
emails AS (
  SELECT rep, SUM(n) AS emails_total,
         COUNT(DISTINCT CASE WHEN DAYOFWEEKISO(ed)<6 AND n>0 THEN ed END) AS email_days,
         SUM(CASE WHEN DAYOFWEEKISO(ed)<6 THEN n ELSE 0 END) AS emails_wd
  FROM emails_base GROUP BY rep
),
act_days AS (
  SELECT rep, COUNT(DISTINCT d) AS days FROM (
    SELECT rep, cd AS d FROM calls_base  WHERE DAYOFWEEKISO(cd)<6 AND n>0
    UNION SELECT rep, ed AS d FROM emails_base WHERE DAYOFWEEKISO(ed)<6 AND n>0
  ) GROUP BY rep
),
-- v2: funnel repointed to the verified snapshot fact FCT_SALES_FUNNEL_CURRENT (keyed
-- on REP_NAME = roster display name). Already per-rep with the 5 stage counts.
funnel AS (
  SELECT REP_NAME AS rep, POOL AS pool, PROSPECT AS prospect,
         PRESENTATION AS presentation, PURCHASE AS purchase, PROFIT AS profit
  FROM GOLD_V3_DB.SCORECARD.FCT_SALES_FUNNEL_CURRENT
  WHERE REP_NAME IN (SELECT rep FROM reps)
),
-- v2: rep revenue/orders repointed to the verified fact FCT_SALES_REP_REVENUE_DAILY
-- (keyed on SALESPERSON = roster so_name). MTD = SUM over the month of ORDER_COUNT
-- (shipments) and TOTAL_REVENUE_AMT (net rev). Preserves the revenue CTE columns
-- (rep, shipments, rev).
revenue AS (
  SELECT r.rep,
         COALESCE(SUM(rd.ORDER_COUNT), 0) AS shipments,
         ROUND(COALESCE(SUM(rd.TOTAL_REVENUE_AMT), 0), 2) AS rev
  FROM reps r
  LEFT JOIN GOLD_V3_DB.SCORECARD.FCT_SALES_REP_REVENUE_DAILY rd
    ON rd.SALESPERSON = r.so_name
   AND rd.REVENUE_DATE BETWEEN (SELECT m_start FROM bounds) AND (SELECT m_end FROM bounds)
  GROUP BY r.rep
),
-- v2: New Auths + Pending repointed RAW -> GOLD (2026-07-01, verified 1:1).
--   New Auths -> FACT_ORDERS B2B leg (shipment-completion grain): first-ever
--     completed shipment per (salesperson, customer_id). Reproduces the app's
--     old ship_to_name-keyed count for every scorecard rep.
--   Pending   -> FACT_SALES_ORDERS open-order headers; same status set (db_cool-only).
--   TODAY-CELL: both lag the current day until the next dbt run; UNION a live
--     RAW_V2_DB.SUPABASE_ERP slice for [today] if penny-accurate current-day is needed.
first_ship AS (
  SELECT salesperson AS so_name, customer_id AS cust, MIN(ship_date) AS first_dt
  FROM GOLD_V3_DB.SALES.FACT_ORDERS
  WHERE channel='B2B'
  GROUP BY 1,2
),
new_auths AS (
  SELECT r.rep, COUNT(*) AS n
  FROM reps r JOIN first_ship fs ON fs.so_name=r.so_name CROSS JOIN bounds b
  WHERE fs.first_dt BETWEEN b.m_start AND b.m_end GROUP BY r.rep
),
pending AS (
  SELECT r.rep, ROUND(SUM(f.ORDER_TOTAL_AMT),2) AS pending_rev
  FROM reps r JOIN GOLD_V3_DB.SALES.FACT_SALES_ORDERS f ON f.SALESPERSON=r.so_name CROSS JOIN bounds b
  WHERE f.STATUS IN ('PENDING_APPROVAL','APPROVED','AWAITING_PAYMENT')
    AND f.ORDER_DATE BETWEEN b.m_start AND b.m_end GROUP BY r.rep
),
tiers AS (
  SELECT r.rep, r.monthly_target AS target_t, ROUND(0.70*r.monthly_target,0) AS base_t,
         ROUND(CASE WHEN r.pod='National Accounts' THEN 1.75 ELSE 1.50 END * r.monthly_target,0) AS ceiling_t
  FROM reps r
)
SELECT
  r.rep AS "Rep", r.role AS "Role", r.pod AS "Pod",
  ROUND(COALESCE(c.calls_wd,0)/NULLIF(c.call_days,0),1)   AS "Calls/Day",
  ROUND(COALESCE(e.emails_wd,0)/NULLIF(e.email_days,0),1) AS "Emails/Day",
  ROUND((COALESCE(c.calls_wd,0)+COALESCE(e.emails_wd,0))/NULLIF(a.days,0),1) AS "Act/Day",
  COALESCE(f.pool,0) AS "Pool", COALESCE(f.prospect,0) AS "Prospect",
  COALESCE(f.presentation,0) AS "Presentation", COALESCE(f.purchase,0) AS "Purchase", COALESCE(f.profit,0) AS "Profit",
  COALESCE(na.n,0) AS "New Auths",
  COALESCE(rv.rev,0) AS "Net Rev",
  COALESCE(p.pending_rev,0) AS "Pending",
  t.target_t AS "Target",
  CASE WHEN t.target_t IS NULL THEN NULL ELSE ROUND(100*COALESCE(rv.rev,0)/t.target_t,0) END AS "Pct",
  CASE
    WHEN t.target_t IS NULL                THEN 'set quota'
    WHEN COALESCE(rv.rev,0) >= t.ceiling_t THEN 'above ceiling'
    WHEN COALESCE(rv.rev,0) >= t.target_t  THEN 'at target'
    WHEN COALESCE(rv.rev,0) >= t.base_t    THEN 'on track'
    ELSE 'below threshold'
  END AS "Tier"
FROM reps r
LEFT JOIN calls c ON c.rep=r.rep LEFT JOIN emails e ON e.rep=r.rep LEFT JOIN act_days a ON a.rep=r.rep
LEFT JOIN funnel f ON f.rep=r.rep LEFT JOIN revenue rv ON rv.rep=r.rep
LEFT JOIN new_auths na ON na.rep=r.rep LEFT JOIN pending p ON p.rep=r.rep LEFT JOIN tiers t ON t.rep=r.rep
ORDER BY "Net Rev" DESC
""")


def build_sales_reps_html(df):
    if df is None or df.empty:
        return ('<div style="padding:18px;color:#888;'
                'font-family:IBM Plex Mono,monospace;">No rep data available.</div>')

    def _iv(v):
        try: return f"{int(v):,}"
        except: return "0"
    def _money(v):
        try:
            return "—" if v is None or pd.isna(v) else f"${float(v):,.0f}"
        except: return "—"
    def _num(v, dec=1):
        try:
            return "—" if v is None or pd.isna(v) else f"{float(v):,.{dec}f}"
        except: return "—"
    def _tier_cls(tier):
        return {'above ceiling': 'c-green', 'at target': 'c-green', 'on track': 'c-yellow',
                'below threshold': 'c-red'}.get(tier, 'c-empty')
    def _act_cls(v):
        try:
            x = float(v)
        except (TypeError, ValueError):
            return 'c-empty'
        if pd.isna(x): return 'c-empty'
        return 'c-green' if x >= 60 else ('c-yellow' if x >= 48 else 'c-red')

    col_heads = ['Calls/Day', 'Emails/Day', 'Act/Day', 'Pool', 'Prospect', 'Presentation',
                 'Purchase', 'Profit', 'New Auths', 'Net Rev', 'Pending', 'Target', '% Target', 'Tier']
    html = ['<table class="sc-table">', '<tr>',
            '<th class="left" style="width:28px"></th>',
            '<th class="left" style="min-width:150px">Rep</th>',
            '<th class="left" style="min-width:115px">Pod</th>']
    for h in col_heads:
        html.append(f'<th style="width:80px">{h}</th>')
    html.append('</tr>')
    html.append(f'<tr><td colspan="{len(col_heads)+3}">'
                f'<div class="section-hdr">SALES — MONTH TO DATE</div></td></tr>')

    for i, (_, r) in enumerate(df.iterrows(), start=1):
        tier = r.get('Tier')
        tcls = _tier_cls(tier)
        pct = r.get('Pct')
        pct_disp = '—' if pct is None or pd.isna(pct) else f"{int(pct)}%"
        tier_label = '⚙︎ set quota' if tier == 'set quota' else (tier or '—')
        html.append(
            '<tr>'
            f'<td class="left"><span class="row-num">{i}</span></td>'
            f'<td class="left">{r["Rep"]}'
            f'<div style="font-size:10px;color:{T["text2"]};">{r["Role"]}</div></td>'
            f'<td class="left">{r["Pod"]}</td>'
            f'<td class="num">{_num(r["Calls/Day"])}</td>'
            f'<td class="num">{_num(r["Emails/Day"])}</td>'
            f'<td class="num {_act_cls(r["Act/Day"])}">{_num(r["Act/Day"])}</td>'
            f'<td class="num">{_iv(r["Pool"])}</td>'
            f'<td class="num">{_iv(r["Prospect"])}</td>'
            f'<td class="num">{_iv(r["Presentation"])}</td>'
            f'<td class="num">{_iv(r["Purchase"])}</td>'
            f'<td class="num">{_iv(r["Profit"])}</td>'
            f'<td class="num">{_iv(r["New Auths"])}</td>'
            f'<td class="num">{_money(r["Net Rev"])}</td>'
            f'<td class="num">{_money(r["Pending"])}</td>'
            f'<td class="num">{_money(r["Target"])}</td>'
            f'<td class="num {tcls}">{pct_disp}</td>'
            f'<td class="{tcls}">{tier_label}</td>'
            '</tr>'
        )
    html.append('</table>')
    return ''.join(html)


# ── Target tab table builder ─────────────────────────────────────────────────
# Heat map: rows are sections, each cell shows `green / section_targets` for that day.
# Yellow or red on a metric both count as "not green" (numerator only).
# ≥80% of section targets hit = GREEN, below = RED (deep-dive candidate).
# Layout matches the EOS-style scorecard target: navy headers, dept name + metric list
# in left column, no Team Total row.
def build_target_table_html(rows, days, day_labels, today):
    """Card-based dark dashboard matching 2026-05-13 redesign spec.
    Renders: Company-Wide Summary card at top, then per-dept cards each containing
    a mini week-strip + score pill + per-metric daily pill cells + week trend %.
    Function signature kept identical so the caller doesn't need to change.
    """
    # Group rows by dept, preserving definition order. Keep TBD rows visible so
    # placeholder departments (Marketing/HR pending) still render with empty cells.
    target_by_dept = {}
    dept_order = []
    for row in rows:
        dept, _, _, goal_str, _, _, _ = row
        if dept not in target_by_dept:
            dept_order.append(dept)
            target_by_dept[dept] = []
        target_by_dept[dept].append(row)

    DEPT_GREEN_THRESHOLD = 0.80   # dept-day strip threshold
    DEPT_YELLOW_THRESHOLD = 0.50

    def _letter_grade(ratio):
        """2026-05-14 grading scale (8-pt bands, F cuts at D-floor):
            A ≥ 92%   ·   B 84-91.9%   ·   C 76-83.9%   ·   D 68-75.9%   ·   F < 68%
        Returns (letter, css_class). A = green; B/C/D/F all red per spec."""
        pct = ratio * 100
        if pct >= 92: return 'A', 'td-c-green'
        if pct >= 84: return 'B', 'td-c-red'
        if pct >= 76: return 'C', 'td-c-red'
        if pct >= 68: return 'D', 'td-c-red'
        return 'F', 'td-c-red'

    def _eval(r, d):
        _, _, _, _, get_fn, color_fn, _ = r
        try:
            val = get_fn(d)
            display, css = color_fn(val)
        except Exception:
            display, css = "—", "c-empty"
        return display, css

    prior_days = [d - timedelta(days=7) for d in days]

    # Pre-compute everything per dept
    summaries = {}
    for dept in dept_order:
        dept_rows = target_by_dept[dept]
        nm = len(dept_rows)
        # per-day dept status for the mini-strip + week total
        strip = []
        week_green = 0
        cells_by_metric = [[] for _ in dept_rows]
        green_count_by_metric = [0] * len(dept_rows)
        data_days_by_metric = [0] * len(dept_rows)
        # Manufacturing runs Mon-Thu only — Friday is non-operating, shown
        # as '—' in the heat map for tabular alignment but excluded from grade.
        # Depts in HOLIDAY_BLANK_DEPTS also skip US holidays (same treatment).
        mfg_skip_friday = (dept == "Manufacturing")
        skip_holidays = (dept in HOLIDAY_BLANK_DEPTS)
        for d in days:
            d_is_holiday = (d in US_SHIP_HOLIDAYS_SET)
            if (d > today
                or (mfg_skip_friday and d.weekday() == 4)
                or (skip_holidays and d_is_holiday)):
                strip.append('e')
                for mi in range(nm):
                    cells_by_metric[mi].append(("—", "c-empty"))
                continue
            day_green = 0
            for mi, r in enumerate(dept_rows):
                display, css = _eval(r, d)
                cells_by_metric[mi].append((display, css))
                if css == "c-green":
                    day_green += 1
                    green_count_by_metric[mi] += 1
                if css != "c-empty":
                    data_days_by_metric[mi] += 1
            week_green += day_green
            if nm == 0:
                strip.append('e')
            elif day_green / nm >= DEPT_GREEN_THRESHOLD:
                strip.append('g')
            elif day_green / nm >= DEPT_YELLOW_THRESHOLD:
                strip.append('y')
            else:
                strip.append('r')

        # Per-metric trend (this-week % vs prior-week %)
        trends = []
        for mi, r in enumerate(dept_rows):
            cur_pct = (green_count_by_metric[mi] / data_days_by_metric[mi] * 100) if data_days_by_metric[mi] > 0 else None
            pg, pd = 0, 0
            for pdate in prior_days:
                _, css = _eval(r, pdate)
                if css != "c-empty":
                    pd += 1
                    if css == "c-green":
                        pg += 1
            prior_pct = (pg / pd * 100) if pd > 0 else None
            trends.append((cur_pct, prior_pct))

        # Score + grade — both based on PACE (week_green / elapsed scored slots).
        # 2026-05-14: switched from "X / nm*5 final-week" to pace-based so mid-week
        # views don't display false-final F's just because Thu/Fri haven't elapsed.
        # On Friday EOD all 5 days are elapsed so pace_ratio = final_ratio naturally.
        # Manufacturing: 4-day workweek (Mon-Thu) → out of 12 not 15.
        # 2026-05-26: depts in HOLIDAY_BLANK_DEPTS lose one slot per holiday in
        # the week (e.g. Memorial Day Mon: 15→12, mfg 12→9).
        if dept == "Manufacturing":
            base_days = 4  # Mon-Thu
            holiday_count = sum(1 for d in days if d.weekday() < 4 and d in US_SHIP_HOLIDAYS_SET)
        elif skip_holidays:
            base_days = 5  # Mon-Fri
            holiday_count = sum(1 for d in days if d.weekday() < 5 and d in US_SHIP_HOLIDAYS_SET)
        else:
            base_days = 5
            holiday_count = 0
        denom = nm * max(base_days - holiday_count, 0)
        elapsed_denom = sum(data_days_by_metric)  # actual scored slots so far
        ratio = (week_green / elapsed_denom) if elapsed_denom > 0 else 0

        if elapsed_denom == 0:
            score_cls = 'td-c-empty'
        elif ratio >= DEPT_GREEN_THRESHOLD:
            score_cls = 'td-c-green'
        elif ratio >= DEPT_YELLOW_THRESHOLD:
            score_cls = 'td-c-yellow'
        else:
            score_cls = 'td-c-red'

        # Grade — stub depts (no real metric data at all) show "—".
        has_data = elapsed_denom > 0
        if not has_data:
            grade_letter, grade_cls = '—', 'td-c-empty'
        else:
            grade_letter, grade_cls = _letter_grade(ratio)

        summaries[dept] = {
            'rows': dept_rows, 'nm': nm, 'denom': denom, 'week_green': week_green,
            'elapsed_denom': elapsed_denom,
            'strip': strip, 'cells_by_metric': cells_by_metric, 'trends': trends,
            'score_cls': score_cls, 'ratio': ratio,
            'grade_letter': grade_letter, 'grade_cls': grade_cls,
            'has_data': has_data,
        }

    # ── HTML output ──
    html = []
    week_lbl = days[0].strftime('%b %d, %Y')

    # Navy banner — restored 2026-05-13 per user feedback (the original style).
    html.append(
        '<div class="td-banner">DAILY LEADING INDICATORS — HEAT MAP &nbsp;'
        f'<span class="td-banner-sub">Week of {week_lbl}</span>'
        '</div>'
        '<div class="td-subtitle">'
        '≥ 80% of section targets = <b class="td-g">GREEN</b>. Below 80% = <b class="td-r">RED</b> '
        '→ automatic deep-dive candidate. Data confirmed by department head daily.'
        '</div>'
    )

    html.append(
        '<div class="td-legend">'
        '<span class="td-legend-item"><span class="td-legend-dot td-c-green"></span>On Target</span>'
        '<span class="td-legend-item"><span class="td-legend-dot td-c-red"></span>Below Target</span>'
        '<span class="td-legend-item"><span class="td-legend-dot td-c-neutral"></span>Neutral</span>'
        '<span class="td-legend-sep">|</span>'
        '<span class="td-legend-note">Green when 80%+ met</span>'
        '<span class="td-legend-right">ⓘ Data confirmed by dept heads daily</span>'
        '</div>'
    )

    # Company-Wide Summary card — title + big grade pill on the same row.
    # Grade based on PACE (week_green / elapsed scored slots) so mid-week views
    # don't read as a false-final F. Caption shows pace + the full-week score.
    # Stub depts (no real metric data yet) excluded from the company calc.
    company_green = sum(summaries[d]['week_green'] for d in dept_order if summaries[d]['has_data'])
    company_denom = sum(summaries[d]['denom']      for d in dept_order if summaries[d]['has_data'])
    company_elapsed_denom = sum(summaries[d]['elapsed_denom'] for d in dept_order if summaries[d]['has_data'])
    if company_elapsed_denom > 0:
        company_pace_ratio = company_green / company_elapsed_denom
        co_grade, co_grade_cls = _letter_grade(company_pace_ratio)
        co_pct_label = f"{company_pace_ratio*100:.0f}% pace · {company_green}/{company_denom}"
    else:
        co_grade, co_grade_cls, co_pct_label = '—', 'td-c-empty', ''

    html.append('<div class="td-card td-summary-card">')
    html.append(
        '<div class="td-summary-header">'
          '<div class="td-summary-title">COMPANY-WIDE SUMMARY</div>'
          f'<div class="td-grade-big {co_grade_cls}">'
            f'<div class="td-grade-big-letter">{co_grade}</div>'
            f'<div class="td-grade-big-pct">{co_pct_label}</div>'
          '</div>'
        '</div>'
    )
    html.append('<div class="td-summary-row">')
    for dept in dept_order:
        s = summaries[dept]
        if s['denom'] == 0:
            bar_w, score_label, cls = 0, '—', 'td-c-empty'
        else:
            bar_w = int(s['ratio'] * 100)
            score_label = f"{s['week_green']}/{s['denom']}"
            cls = s['score_cls']
        html.append(
            f'<div class="td-summary-item">'
              f'<div class="td-summary-dept">{dept}</div>'
              f'<div class="td-summary-bar-wrap">'
                f'<div class="td-summary-bar {cls}" style="width:{bar_w}%"></div>'
              f'</div>'
              f'<div class="td-summary-score {cls}">{score_label}</div>'
            f'</div>'
        )
    html.append('</div></div>')

    # Per-dept cards
    for dept in dept_order:
        s = summaries[dept]
        strip_html = ''
        for status, lbl in zip(s['strip'], day_labels):
            short = lbl[:3].upper()
            strip_html += (
                f'<div class="td-strip-cell">'
                f'<div class="td-strip-lbl">{short}</div>'
                f'<div class="td-strip-bar td-strip-{status}"></div>'
                f'</div>'
            )
        score_label = f"{s['week_green']}/{s['denom']}" if s['denom'] else '—'

        html.append(
            '<div class="td-card">'
              '<div class="td-card-head">'
                '<div class="td-card-head-left">'
                  '<span class="td-chevron">▾</span>'
                  '<div>'
                    f'<div class="td-dept-name">{dept}</div>'
                    f'<div class="td-dept-meta">{s["nm"]} metrics</div>'
                  '</div>'
                '</div>'
                '<div class="td-card-head-right">'
                  f'<div class="td-week-strip">{strip_html}</div>'
                  f'<div class="td-score-pill {s["score_cls"]}">{score_label}</div>'
                  f'<div class="td-grade-pill {s["grade_cls"]}">{s["grade_letter"]}</div>'
                '</div>'
              '</div>'
              '<table class="td-metric-table">'
                '<tr>'
                  '<th class="td-th-left">METRIC</th>'
                  + ''.join(f'<th>{lbl[:3].upper()}</th>' for lbl in day_labels) +
                  '<th>TREND</th>'
                '</tr>'
        )
        for mi, r in enumerate(s['rows']):
            _, _, name, _, _, _, _ = r
            cell_html = ''
            for display, css in s['cells_by_metric'][mi]:
                cell_html += f'<td class="td-cell"><span class="td-cell-pill td-{css}">{display}</span></td>'
            cur_pct, prior_pct = s['trends'][mi]
            if cur_pct is None:
                trend_html = '<td class="td-trend-cell td-c-empty">—</td>'
            else:
                if prior_pct is None or abs(cur_pct - prior_pct) < 5:
                    arrow, tcls = '→', 'td-c-neutral'
                elif cur_pct > prior_pct:
                    arrow, tcls = '↗', 'td-c-green'
                else:
                    arrow, tcls = '↘', 'td-c-red'
                trend_html = f'<td class="td-trend-cell {tcls}">{arrow} {cur_pct:.0f}%</td>'
            html.append(f'<tr><td class="td-metric-name">{name}</td>{cell_html}{trend_html}</tr>')
        html.append('</table></div>')

    return ''.join(html)


# ── Lagging Indicators (Monthly Pace) builder ─────────────────────────────────
# Renders a bar per metric showing month-to-date progress vs target.
#   mode='cumulative' (B2B revenue): bar = MTD$ / month target. Pace tick = days_elapsed.
#                                    Green if MTD$ ≥ pace, Red otherwise.
#   mode='rate' (OEE, downtime, AR, labor): bar = weeks_green / weeks_elapsed.
#                                    80% target line. Green if ratio ≥ 0.80, Red <0.80.
#   mode='pending': stubbed row for departments awaiting target definitions.
# Monthly B2B revenue target — user-specified 2026-05-14 ($3.5M). Overrides the
# elapsed-weeks sum from Q2_WEEKLY_REVENUE_TARGETS (which would give ~$1.87M MTD
# or ~$4.22M full-month for May). Hardcoded here so the lagging bar shows progress
# against the actual goal, not the table's per-week breakdown.
B2B_MONTHLY_TARGET = 3_500_236

def _build_cumulative_b2b():
    """Returns (mtd_actual, monthly_target, pace_pct) for B2B revenue.
    2026-06-05: switched to GROSS shipped-line basis to match the ERP GUI MTD
    and executive_summary.py — revenue = shipment_line.quantity × so_line.unit_price
    on COMPLETED shipments, keyed on shipment.completed_at. Reproduces the GUI's
    MTD to the penny (e.g. June 2026 = $378,100.40 on 13 SOs through 06-03).
    Prior versions used SALES_ORDERS.TOTAL_AMOUNT (net of trade-promo discounts),
    which under-reported by ~$140K/month because of TRADE_PROMO / SLOTTING_FEE /
    DAMAGE_SHORT_CREDIT concessions zeroing out line_amount."""
    today_d = date.today()
    month_start = today_d.replace(day=1)
    # v2 (2026-07-01): repointed to unified GOLD FACT_ORDERS (B2B leg). Its
    # net_revenue_amt IS sum(shipment_line.qty * order_line.unit_price) on COMPLETED
    # shipments dated on completed_at — same basis, FULL PRECISION. The old RAW formula
    # cast unit_price::numeric (NUMBER(38,0)), truncating cents and under-reporting
    # ~$714/mo (June: RAW 1,787,647 vs GOLD 1,788,361.08). GOLD is correct. NOTE:
    # FACT_ORDERS lags the current day until the next dbt run (fine for MTD pacing).
    df = q(f"""
        SELECT COALESCE(SUM(net_revenue_amt), 0) AS mtd
        FROM GOLD_V3_DB.SALES.FACT_ORDERS
        WHERE channel = 'B2B'
          AND order_date BETWEEN '{month_start}' AND '{today_d}'
    """)
    mtd_actual = safe_float(df.iloc[0]['MTD'], 0) if not df.empty else 0.0
    next_month = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
    days_in_month = (next_month - month_start).days
    days_elapsed = (today_d - month_start).days + 1
    pace_pct = days_elapsed / days_in_month
    return mtd_actual, B2B_MONTHLY_TARGET, pace_pct


# Marketing (D2C) monthly revenue target — user-specified 2026-05-14 ($300k).
MARKETING_MONTHLY_TARGET = 300_000

def _build_cumulative_marketing():
    """Returns (mtd_actual, monthly_target, pace_pct) for marketing D2C revenue."""
    today_d = date.today()
    month_start = today_d.replace(day=1)
    df = q(f"""
        SELECT COALESCE(SUM(NET_REVENUE_AMT), 0) AS mtd
        FROM GOLD_V3_DB.SALES.FACT_DAILY_REVENUE
        WHERE CHANNEL = 'DTC'
          AND REVENUE_DATE BETWEEN '{month_start}' AND '{today_d}'
    """)
    mtd_actual = safe_float(df.iloc[0]['MTD'], 0) if not df.empty else 0.0
    next_month = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
    days_in_month = (next_month - month_start).days
    days_elapsed = (today_d - month_start).days + 1
    pace_pct = days_elapsed / days_in_month
    return mtd_actual, MARKETING_MONTHLY_TARGET, pace_pct

def build_lagging_table_html(lagging_rows, T):
    """Dark card-based lagging-indicator view matching 2026-05-13 redesign.
    Each department gets its own card (matches heat map). Rows inside: metric name,
    MTD value, target, vertical progress bar, status pill. Kept return signature
    (html, month_label) so the caller stays unchanged.
    """
    today_d = date.today()
    month_label = today_d.strftime('%B %Y')

    by_dept = {}
    dept_order = []
    for r in lagging_rows:
        d = r[0]
        if d not in by_dept:
            by_dept[d] = []
            dept_order.append(d)
        by_dept[d].append(r)

    html = []
    for dept in dept_order:
        dept_rows = by_dept[dept]
        # Count green metrics for the dept header
        green_n, total_n = 0, 0
        per_row_render = []
        for row in dept_rows:
            _, metric, mode, getter, target_label, threshold_fn = row
            if mode in ('cumulative_b2b', 'cumulative_marketing'):
                if mode == 'cumulative_b2b':
                    mtd, tgt, pace = _build_cumulative_b2b()
                else:
                    mtd, tgt, pace = _build_cumulative_marketing()
                bar_pct = (mtd / tgt) if tgt > 0 else 0
                status_green = bar_pct >= pace and tgt > 0
                mtd_label = f"${mtd:,.0f}"
                tgt_label = f"${tgt:,.0f}"
                progress = _render_bar(min(bar_pct, 1.5), pace, T, status_green)
                status_pill = _render_pill(status_green, f"{bar_pct*100:.0f}% of target")
                total_n += 1
                if status_green: green_n += 1
            elif mode == 'rate':
                # 2026-05-14: bar fill height now = weeks_green / weeks_in_month
                # (was weeks_green / weeks_elapsed which made every "on pace" bar
                # render 100% mid-month regardless of progress). Status pill still
                # uses pace_ratio so the green/red signal is unchanged.
                w_green, w_elapsed = _weeks_green_so_far(getter, threshold_fn) if getter else (0, 0)
                weeks_total = _weeks_in_current_month()
                fill_ratio = (w_green / weeks_total) if weeks_total > 0 else 0
                pace_ratio = (w_green / w_elapsed) if w_elapsed > 0 else 0
                status_green = (w_elapsed > 0) and (pace_ratio >= 0.80)
                mtd_label = f"{w_green}/{w_elapsed} weeks green" if w_elapsed else "—"
                tgt_label = target_label
                progress = _render_bar(fill_ratio, 0.80, T, status_green) if w_elapsed else _render_bar_empty(T)
                status_pill = _render_pill(status_green, f"{pace_ratio*100:.0f}% green pace")
                total_n += 1
                if status_green: green_n += 1
            else:  # pending
                mtd_label = "—"
                tgt_label = "🚧 pending"
                progress = _render_bar_empty(T)
                status_pill = _render_pill(None, "pending")
            per_row_render.append((metric, mtd_label, tgt_label, progress, status_pill))

        # Dept score pill — matches heat-map style
        if total_n == 0:
            score_cls, score_label = 'td-c-empty', '—'
        else:
            ratio = green_n / total_n
            if ratio >= 0.80:   score_cls = 'td-c-green'
            elif ratio >= 0.50: score_cls = 'td-c-yellow'
            else:               score_cls = 'td-c-red'
            score_label = f'{green_n}/{total_n}'

        html.append(
            '<div class="td-card">'
              '<div class="td-card-head">'
                '<div class="td-card-head-left">'
                  '<span class="td-chevron">▾</span>'
                  '<div>'
                    f'<div class="td-dept-name">{dept}</div>'
                    f'<div class="td-dept-meta">{len(dept_rows)} lagging metrics</div>'
                  '</div>'
                '</div>'
                '<div class="td-card-head-right">'
                  f'<div class="td-score-pill {score_cls}">{score_label}</div>'
                '</div>'
              '</div>'
              '<table class="td-lagging-table">'
                '<tr>'
                  '<th class="td-th-left">METRIC</th>'
                  '<th style="width:170px">MTD</th>'
                  '<th style="width:150px">TARGET</th>'
                  '<th style="width:80px">PROGRESS</th>'
                  '<th style="width:130px">STATUS</th>'
                '</tr>'
        )
        for metric, mtd_label, tgt_label, progress, status_pill in per_row_render:
            html.append(
                '<tr>'
                  f'<td class="td-metric-name">{metric}</td>'
                  f'<td class="td-mtd-cell">{mtd_label}</td>'
                  f'<td class="td-target-cell">{tgt_label}</td>'
                  f'<td class="td-progress-cell">{progress}</td>'
                  f'<td class="td-status-cell">{status_pill}</td>'
                '</tr>'
            )
        html.append('</table></div>')

    return ''.join(html), month_label

def _weeks_in_current_month():
    """Returns the count of Mon-anchored weeks that touch the current month
    (4 in most months, 5 in months where a Monday falls late enough)."""
    today_d = date.today()
    month_start = today_d.replace(day=1)
    next_month = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
    cur_mon = month_start - timedelta(days=month_start.weekday())
    weeks = 0
    while cur_mon < next_month:
        # Count this week if any of its Mon-Fri days fall inside the current month
        if any(month_start <= cur_mon + timedelta(days=i) < next_month for i in range(5)):
            weeks += 1
        cur_mon += timedelta(days=7)
    return max(1, weeks)


def _render_bar(filled_ratio, pace_ratio, T, is_green):
    """Vertical bar with banded zones + dotted weekly target lines (2026-05-14).
    Spec: 4 zones bottom-to-top (dark red → light red → yellow → green). Solid
    opaque fill rises from bottom to filled_ratio; its color matches the zone
    its top sits in. Dotted lines mark each weekly target. `pace_ratio` and
    `is_green` retained in the signature for back-compat but not used — the
    zone colors carry the visual signal now.
    """
    fill_pct = min(max(filled_ratio, 0), 1.0) * 100

    # Zone the bar TOP currently occupies — picks the solid fill colour.
    if   fill_pct < 25: fill_bg = '#7f1d1d'  # dark red
    elif fill_pct < 50: fill_bg = '#dc2626'  # light red
    elif fill_pct < 75: fill_bg = '#ca8a04'  # yellow (slightly muted)
    else:               fill_bg = '#16a34a'  # green
    fill_edge = fill_bg

    # Background gradient — faded versions of each zone, always visible.
    # rgba alpha 0.30/0.25/0.25/0.25 reads clearly against the dark card.
    bg = (
        'linear-gradient(to top,'
        ' rgba(127,29,29,0.32) 0%,   rgba(127,29,29,0.32) 25%,'
        ' rgba(220,38,38,0.28) 25%,  rgba(220,38,38,0.28) 50%,'
        ' rgba(234,179,8,0.28) 50%,  rgba(234,179,8,0.28) 75%,'
        ' rgba(34,197,94,0.28) 75%,  rgba(34,197,94,0.28) 100%)'
    )

    # Weekly target dotted lines, evenly spaced (4 or 5 depending on month).
    n_weeks = _weeks_in_current_month()
    line_html = ''
    for i in range(1, n_weeks + 1):
        pos = int(100 * i / n_weeks)
        # Top boundary (100%) is the bar edge itself, skip drawing a line there
        if pos >= 100:
            continue
        line_html += (
            f'<div style="position:absolute;left:-2px;right:-2px;bottom:{pos}%;'
            f'height:0;border-top:1px dashed rgba(255,255,255,0.45);"></div>'
        )

    return (
        f'<div style="display:inline-block;position:relative;width:28px;height:56px;'
        f'background:{bg};border-radius:4px;border:1px solid #2a3a55;'
        f'overflow:hidden;vertical-align:middle;">'
          f'<div style="position:absolute;left:0;right:0;bottom:0;'
          f'height:{fill_pct}%;background:{fill_bg};border-top:2px solid {fill_edge};"></div>'
          f'{line_html}'
        f'</div>'
    )

def _render_bar_empty(T):
    return (
        '<div style="display:inline-block;width:28px;height:56px;background:#1c2740;'
        'border-radius:4px;border:1px dashed #2a3a55;opacity:0.4;'
        'vertical-align:middle;"></div>'
    )

def _render_pill(is_green, label):
    """Tiny coloured pill — green/red/grey, dark-theme palette."""
    if is_green is None:
        bg, fg = 'rgba(148,163,184,0.15)', '#94a3b8'
    elif is_green:
        bg, fg = 'rgba(74,222,128,0.15)',  '#4ade80'
    else:
        bg, fg = 'rgba(248,113,113,0.15)', '#f87171'
    return (
        f'<span style="display:inline-block;padding:4px 10px;border-radius:12px;'
        f'background:{bg};color:{fg};font-size:11px;font-weight:600">{label}</span>'
    )


# ── Green count helper (for Biz Ops row 1) ────────────────────────────────────
# Evaluates each of the 17 scoreable metrics per day and counts how many are green
# Total = 18 metrics; row 1 itself is excluded from its own denominator
def _is_green(val, color_fn):
    """Returns True if the color_fn would produce c-green for this value."""
    if val is None or str(val) in ('', 'nan', 'None'):
        return False
    try:
        _, css = color_fn(val)
        return css == "c-green"
    except:
        return False

def _has_data(val):
    """Returns True if val is not None/empty."""
    if val is None or str(val) in ('', 'nan', 'None'): return False
    try: return True
    except: return False

def _interview_green(val):
    if not isinstance(val, tuple) or val[1] == 0: return False
    return val[0] / val[1] >= 0.90

green_count_dict = {}
for d in days:
    # Skip future days — don't calculate until the day has actually occurred
    if d > today:
        continue
    # Use list accumulator — avoids nonlocal issues with nested def inside for loop
    metrics = []  # list of (is_green,) for each metric that has data

    def cm(val, green_fn):
        """Append to metrics if val has data."""
        has = val is not None and str(val) not in ('', 'nan', 'None')
        if has:
            try: metrics.append(bool(green_fn(float(val))))
            except: metrics.append(False)

    # Sales targets (2026-05-11 update): explicit per-channel quotas replace combined engagement target.
    #   Calls/Rep target = 50/day
    #   Emails/Rep total target = 40/day
    # Total Engagements/Rep is now informational only (not counted toward green %).
    calls_v  = get_calls_per_rep(d)
    if calls_v is not None:
        metrics.append(calls_v[0] >= 50)
    emails_v = get_emails_per_rep(d)
    if emails_v is not None:
        metrics.append(emails_v[0] >= 40)
    # Email category breakout rows (4-6) are informational — not counted in green %
    # Sales AR Past Due
    ar_v = safe_float(ar_dict.get(d)) if ar_dict.get(d) is not None else None
    cm(ar_v, lambda v: v <= 103_000)
    cm(get_manual('OPEN_QUOTES_FOLLOWUP', d),     lambda v: v >= 100)

    # Ops 1-6
    cm(prod_labor.get(d), lambda v: v <= 0.26)
    cm(prod_dt.get(d),    lambda v: v <= 15.5)
    cm(prod_fpy.get(d),   lambda v: v >= 95)
    cm(prod_oee.get(d),   lambda v: v >= 69)
    cm(otif_dtc.get(d),   lambda v: v >= 97)
    # b2b_cycle removed 2026-05-26 — metric moved to Target page Fulfillment.

    # HR 1-3
    cm(get_manual('HR_PERFORMANCE_DOC', d),     lambda v: v >= 75)
    cm(get_manual('HR_TRAINING_COMPLIANCE', d), lambda v: v >= 75)
    cm(get_manual('HR_CAREER_PATH', d),         lambda v: v >= 75)

    # Support 1-5
    cm(get_csat_rolling7(d), lambda v: v >= 80)
    resp_v = safe_float(intercom_resp_dict.get(d)) if intercom_resp_dict.get(d) is not None else None
    cm(resp_v, lambda v: v <= 15)
    cm(total_open_dict.get(d), lambda v: v < 20)
    cm(over48_dict.get(d),     lambda v: v == 0)
    cm(get_deflection(d),   lambda v: v >= 50)

    # Biz Ops 2-3
    cu_v = safe_float(clickup_dict.get(d)) if clickup_dict.get(d) is not None else None
    cm(cu_v, lambda v: v <= 5)
    cm(get_manual('BLOCKERS_24H', d), lambda v: v == 0)

    # Marketing: REMOVED 2026-04-29 — see top of file
    # cm(gm_orders_90.get(d), lambda v: v >= 9800)
    # cm(gm_aov_90.get(d),    lambda v: v >= 84.26)
    # cm(gm_new_90.get(d),    lambda v: v >= 637)
    # cm(mit_orders_90.get(d), lambda v: v >= 588)
    # cm(mit_aov_90.get(d),   lambda v: v >= 205.80)
    # cm(mit_new_90.get(d),   lambda v: v >= 147)
    # cm(up_orders_90.get(d), lambda v: v >= 441)
    # cm(up_aov_90.get(d),    lambda v: v >= 96.04)
    # cm(up_new_90.get(d),    lambda v: v >= 49)

    # Dynamic denominator — only metrics with data count
    if metrics:
        green_count_dict[d] = round(sum(metrics) / len(metrics) * 100, 0)

# ── Row definitions ───────────────────────────────────────────────────────────
rows = [
    # ── SALES ─────────────────────────────────────────────────────────────────
    # Row 1: TSM Daily Activities (Calls + Emails) — combined ≥90/rep.
    # 2026-06-03: consolidated from separate Calls/Rep (50) + Emails/Rep (40) rows
    # to match the Target page's single combined KPI. Same underlying data
    # (get_daily_activities = get_calls_per_rep + get_emails_per_rep). Daily keeps a
    # yellow band (target page is binary green/red).
    ("Sales", "1", "TSM Daily Activities (Calls + Emails)", "90",
     lambda d: get_daily_activities(d),
     lambda v: (
         (f"{v[0]:.0f} ({v[1]:.0f}c + {v[2]:.0f}e)", "c-green")  if isinstance(v, tuple) and v[0] >= 90
         else (f"{v[0]:.0f} ({v[1]:.0f}c + {v[2]:.0f}e)", "c-yellow") if isinstance(v, tuple) and v[0] >= 80
         else (f"{v[0]:.0f} ({v[1]:.0f}c + {v[2]:.0f}e)", "c-red")    if isinstance(v, tuple)
         else ("—", "c-empty")
     ),
     False),
    # Row 2: Emails to New Customers/Rep — informational breakout (prospects, not in Acumatica)
    ("Sales", "2", "Emails — New Customers/Rep", "—",
     lambda d: (round(outlook_map[d]["new"] / max(outlook_map[d]["reps"], 1), 1),
                outlook_map[d]["new"]) if d in outlook_map else None,
     lambda v: (f"{v[0]:.1f} / {v[1]}", "c-na") if isinstance(v, tuple) else ("—", "c-empty"),
     False),
    # Row 3: Emails to Existing Customers/Rep — informational breakout (anyone in Acumatica list)
    ("Sales", "3", "Emails — Existing Customers/Rep", "—",
     lambda d: (round(outlook_map[d]["existing"] / max(outlook_map[d]["reps"], 1), 1),
                outlook_map[d]["existing"]) if d in outlook_map else None,
     lambda v: (f"{v[0]:.1f} / {v[1]}", "c-na") if isinstance(v, tuple) else ("—", "c-empty"),
     False),
    # Row 5: Pipeline Activity Movement — CRM stage progressions in ClickUp Sales space.
    # Replaces former "Emails — Unknown/Rep" informational row (removed 2026-05-13).
    # 2026-05-14: Target dropped 40 → 20 after the revivals-included redef raised
    # the live numbers. Binary green/red on Target page; Daily adds yellow band.
    ("Sales", "4", "Pipeline Activity Movement (CRM stage changes)", "≥20",
     lambda d: pipeline_movement_dict.get(d) if d <= today else None,
     lambda v: raw_color(v,
         lambda x: x >= 20,
         lambda x: x >= 10,
         lambda x: f"{int(x):,}"),
     False),
    ("Sales", "5", "AR Past Due", "$103k",
     lambda d: safe_float(ar_dict.get(d)) if ar_dict.get(d) is not None else None,
     lambda v: raw_color(v,
         lambda x: x <= 103_000,
         lambda x: x <= 109_000,
         lambda x: f"${x:,.0f}"),
     True),

    # ── MANUFACTURING (renamed from "Operations" 2026-05-14) ─────────────────
    ("Manufacturing", "1", "Labor Cost Per Unit  (Liquid)", "$0.25",
     lambda d: prod_labor.get(d),
     lambda v: raw_color(v,
         lambda x: x <= 0.26,
         lambda x: x <= 0.27,
         lambda x: f"${x:.2f}"),
     False),
    ("Manufacturing", "2", "Unplanned Downtime %  (Liquid)", "<=15.5%",
     lambda d: prod_dt.get(d),
     lambda v: raw_color(v,
         lambda x: x <= 15.5,
         lambda x: x <= 16.4,
         lambda x: f"{x:.1f}%"),
     False),
    ("Manufacturing", "3", "First Pass Yield", "97%",
     lambda d: prod_fpy.get(d),
     lambda v: raw_color(v,
         lambda x: x >= 95,
         lambda x: x >= 88,
         lambda x: f"{x:.1f}%"),
     False),
    ("Manufacturing", "4", "OEE", "70%",
     lambda d: prod_oee.get(d),
     lambda v: raw_color(v,
         lambda x: x >= 69,
         lambda x: x >= 64,
         lambda x: f"{x:.1f}%"),
     False),
    # OTIF (D2C) moved to Fulfillment 2026-05-14 — renamed there to "On-Time Ship Rate".
    # OTIF (B2B) removed 2026-05-26 — replaced by B2B Cycle Time on Target page
    # Fulfillment section (uses Supabase ERP instead of legacy Acumatica).

    # ── HR — manual entry pending Ashby sync fix ──────────────────────────────
    ("HR", "1", "Performance Documentation Rate", ">75%",
     lambda d: get_manual('HR_PERFORMANCE_DOC', d),
     lambda v: raw_color(v, lambda x: x >= 75, lambda x: x >= 65, lambda x: f"{v:.1f}%"),
     False),
    ("HR", "2", "Training & Compliance Completion Rate", ">75%",
     lambda d: get_manual('HR_TRAINING_COMPLIANCE', d),
     lambda v: raw_color(v, lambda x: x >= 75, lambda x: x >= 65, lambda x: f"{v:.1f}%"),
     False),
    ("HR", "3", "HR Process Doc Completion Rate", ">75%",
     lambda d: get_manual('HR_CAREER_PATH', d),
     lambda v: raw_color(v, lambda x: x >= 75, lambda x: x >= 65, lambda x: f"{v:.1f}%"),
     False),

    # ── BUSINESS OPERATIONS — REMOVED 2026-05-14 per spec ────────────────────
    # The 3 rows (Total dept metrics green / Click Up past due / Blockers 24h)
    # were removed. green_count_dict + clickup_dict + BLOCKERS_24H still get
    # computed upstream — left in place in case anything else reads them.

    # ── FULFILLMENT (wired 2026-05-14 — Shiphero shipments + orders) ──────────
    # On-Time Ship Rate removed 2026-05-28.
    ("Fulfillment", "1", "Same-Day Ship Rate", "≥80%",
     lambda d: fulfill_same_day_dict.get(d),
     lambda v: raw_color(v,
         lambda x: x >= 80,
         lambda x: x >= 60,
         lambda x: f"{x:.1f}%"),
     False),
    ("Fulfillment", "2", "Median Order-to-Ship Cycle Time", "≤24 hrs",
     lambda d: fulfill_cycle_dict.get(d),
     lambda v: raw_color(v,
         lambda x: x <= 24,
         lambda x: x <= 48,
         lambda x: f"{x:.0f} hrs"),
     False),
    ("Fulfillment", "3", "DTC OTIF", "≥97%",
     lambda d: dtc_otif_dict.get(d),
     lambda v: raw_color(v,
         lambda x: x >= 97,
         lambda x: x >= 90,
         lambda x: f"{x:.1f}%"),
     False),
    # B2B OTIF redefined 2026-05-28 to avg business hours (approve→complete).
    ("Fulfillment", "4", "B2B OTIF", "≤24 hrs",
     lambda d: b2b_ship_hrs_dict.get(d),
     lambda v: raw_color(v,
         lambda x: x <= 24,
         lambda x: x <= 48,
         lambda x: f"{x:.1f} hrs"),
     False),

    # ── PROCUREMENT (v9 stockout-focused, 2026-05-22, GM-only 2026-05-22) ────
    # Supplier Scorecard % (manual weekly entry, 2026-05-28) — replaced GM
    # Critical Stockouts here. ≥90% green, 80-89.9% yellow, <80% red.
    ("Procurement", "1", "Supplier Scorecard", "≥90%",
     lambda d: proc_supplier_scorecard_dict.get(d),
     lambda v: raw_color(v,
         lambda x: x >= 90,
         lambda x: x >= 80,
         lambda x: f"{x:.1f}%"),
     True),
    ("Procurement", "2", "Supplier OTD % (trailing 90d)", "≥90%",
     lambda d: proc_otd_dict.get(d),
     lambda v: raw_color(v,
         lambda x: x >= 90,
         lambda x: False,
         lambda x: f"{x:.1f}%"),
     True),
    ("Procurement", "3", "% Critical Components Single-Sourced", "≤25%",
     lambda d: proc_single_sourced_dict.get(d),
     lambda v: raw_color(v,
         lambda x: x <= 25,
         lambda x: x <= 30,
         lambda x: f"{x:.1f}%"),
     True),


    # ── SUPPORT ───────────────────────────────────────────────────────────────
    ("Support", "1", "CSAT — Rolling 7D % Positive", ">80%",
     lambda d: get_csat_rolling7(d),
     lambda v: raw_color(v, lambda x: x >= 80, lambda x: x >= 60, lambda x: f"{v:.1f}%"),
     False),
    ("Support", "2", "Median First Response Time", "<15 min",
     lambda d: safe_float(intercom_resp_dict.get(d)) if intercom_resp_dict.get(d) is not None else None,
     lambda v: raw_color(v, lambda x: x <= 15, lambda x: x <= 30, lambda x: f"{v:.1f}m"),
     False),
    ("Support", "3", "Total Open Tickets", "<20",
     lambda d: total_open_dict.get(d) if d <= today else None,
     lambda v: raw_color(v, lambda x: x < 20, lambda x: x <= 35, lambda x: f"{int(v)}"),
     False),
    ("Support", "4", "Tickets Over 48 Hours", "0",
     lambda d: over48_dict.get(d) if d <= today else None,
     lambda v: raw_color(v, lambda x: x == 0, lambda x: False, lambda x: f"{int(v)}"),
     False),
    ("Support", "5", "Fin AI Deflection Rate", ">50%",
     lambda d: get_deflection(d),
     lambda v: raw_color(v, lambda x: x >= 50, lambda x: x >= 35, lambda x: f"{v:.1f}%"),
     False),

    # ── MARKETING — REMOVED 2026-04-29 ────────────────────────────────────────
    # Existing rows obsolete; new set arriving next week. Original row defs preserved
    # below for reference. Re-enable by uncommenting and restoring the lookup dicts.
    # ("Marketing", "1", "Goldenmonk - Trailing 90D Orders", "10,000",
    #  lambda d: safe_float(gm_orders_90.get(d)) if gm_orders_90.get(d) is not None else None,
    #  lambda v: raw_color(v, lambda x: x >= 9800, lambda x: x >= 9100, lambda x: f"{int(x):,}"),
    #  False),
    # ("Marketing", "2", "Goldenmonk - Trailing 90D AOV", "$85.98",
    #  lambda d: safe_float(gm_aov_90.get(d)) if gm_aov_90.get(d) is not None else None,
    #  lambda v: raw_color(v, lambda x: x >= 84.26, lambda x: x >= 78.24, lambda x: f"${x:.2f}"),
    #  False),
    # ("Marketing", "3", "Goldenmonk - Trailing 90D First-Time Buyers", "650",
    #  lambda d: safe_float(gm_new_90.get(d)) if gm_new_90.get(d) is not None else None,
    #  lambda v: raw_color(v, lambda x: x >= 637, lambda x: x >= 591.5, lambda x: f"{int(x):,}"),
    #  False),
    # ("Marketing", "4", "MIT45 - Trailing 90D Orders", "600",
    #  lambda d: safe_float(mit_orders_90.get(d)) if mit_orders_90.get(d) is not None else None,
    #  lambda v: raw_color(v, lambda x: x >= 588, lambda x: x >= 546, lambda x: f"{int(x):,}"),
    #  False),
    # ("Marketing", "5", "MIT45 - Trailing 90D AOV", "$210",
    #  lambda d: safe_float(mit_aov_90.get(d)) if mit_aov_90.get(d) is not None else None,
    #  lambda v: raw_color(v, lambda x: x >= 205.80, lambda x: x >= 191.10, lambda x: f"${x:.2f}"),
    #  False),
    # ("Marketing", "6", "MIT45 - Trailing 90D First-Time Buyers", "150",
    #  lambda d: safe_float(mit_new_90.get(d)) if mit_new_90.get(d) is not None else None,
    #  lambda v: raw_color(v, lambda x: x >= 147, lambda x: x >= 136.5, lambda x: f"{int(x):,}"),
    #  False),
    # ("Marketing", "7", "Uprising - Trailing 90D Orders", "450",
    #  lambda d: safe_float(up_orders_90.get(d)) if up_orders_90.get(d) is not None else None,
    #  lambda v: raw_color(v, lambda x: x >= 441, lambda x: x >= 409.5, lambda x: f"{int(x):,}"),
    #  False),
    # ("Marketing", "8", "Uprising - Trailing 90D AOV", "$98",
    #  lambda d: safe_float(up_aov_90.get(d)) if up_aov_90.get(d) is not None else None,
    #  lambda v: raw_color(v, lambda x: x >= 96.04, lambda x: x >= 89.18, lambda x: f"${x:.2f}"),
    #  False),
    # ("Marketing", "9", "Uprising - Trailing 90D First-Time Buyers", "50",
    #  lambda d: safe_float(up_new_90.get(d)) if up_new_90.get(d) is not None else None,
    #  lambda v: raw_color(v, lambda x: x >= 49, lambda x: x >= 45.5, lambda x: f"{int(x):,}"),
    #  False),

    # ── FINANCE (2026-05-13) — mirrors Target tab Finance section ─────────────
    # Daily Scorecard tab uses 3-tier color where it makes sense; binary green/red
    # where the metric is naturally binary (cash rec = yes/no).
    # Future days return None so cells render as "—" (the Target tab gates this
    # in build_target_table_html, but the Daily Scorecard tab's build_table_html
    # does NOT — so we gate at the getter level).
    ("Finance", "1", "Same-Day Cash Reconciliation", "Daily row loaded",
     lambda d: cash_balance_dict.get(d) if d <= today else None,
     lambda v: (
         ("✓ Yes", "c-green") if v == 1
         else ("✗ No", "c-red") if v == 0
         else ("—", "c-empty")
     ),
     False),
    # JE % counted by unique BATCH_NUMBER (one JE = one batch).
    # Daily scorecard band: ≥50% green, 25-50% yellow (progressing), <25% red.
    ("Finance", "2", "% of JEs in New ERP (Supabase)", "≥50%",
     lambda d: je_new_erp_dict.get(d) if d <= today else None,
     lambda v: raw_color(v,
         lambda x: x >= 50,
         lambda x: x >= 25,
         lambda x: f"{x:.1f}%"),
     False),
    ("Finance", "3", "% Sources Synced <24 hrs", "100%",
     lambda d: sync_coverage_dict.get(d) if d <= today else None,
     lambda v: raw_color(v,
         lambda x: x >= 100,
         lambda x: x >= 90,
         lambda x: f"{x:.0f}%"),
     False),

    # ── MARKETING (2026-05-13) — mirrors Target tab Marketing section ─────────
    # Thresholds match marketing_scorecard.py; daily scorecard gets a yellow band
    # for partial-credit days, target tab is strict green/red.
    ("Marketing", "1", "Cart Abandonment % (GA4 ATC vs Purchase)", "≤60%",
     lambda d: (marketing_ga4_dict.get(d) or {}).get('cart_abandon_pct'),
     lambda v: raw_color(v,
         lambda x: x <= 60,
         lambda x: x <= 75,
         lambda x: f"{x:.1f}%"),
     False),
    ("Marketing", "2", "AOV — First (180d rolling)", "≥$85",
     lambda d: aov_first_180d_dict.get(d),
     lambda v: raw_color(v,
         lambda x: x >= 85,
         lambda x: x >= 75,
         lambda x: f"${x:,.2f}"),
     False),
    # Unique Sessions yellow band 400-500 (P25=407 → floor); below P25 = red.
    ("Marketing", "3", "Unique Sessions (1st-time visitors)", "≥500",
     lambda d: (marketing_ga4_dict.get(d) or {}).get('new_users'),
     lambda v: raw_color(v,
         lambda x: x >= 500,
         lambda x: x >= 400,
         lambda x: f"{int(x):,}"),
     False),

]


# ── TARGET TAB ROWS (2026-05-13 rebuild) ─────────────────────────────────────
# Separate from the daily-scorecard `rows` list above. Target tab narrows each
# department to exactly 3 KPIs (per spec). HR / Business Ops / Support / Marketing
# are stubs pending department-head input — they render as grey "🚧 pending" cells
# but the dept still appears in the heat map structure so the layout is final.
#
# Color logic for the target page (per spec 2026-05-13): GREEN at target, RED below.
# No yellow band — keeps the "deep-dive candidate" signal binary.
target_rows = [
    # ── SALES (3 metrics) ─────────────────────────────────────────────────
    # 1. TSM Daily Activities — combined calls + emails ≥ 90/rep
    ("Sales", "1", "TSM Daily Activities (Calls + Emails)", "90",
     lambda d: get_daily_activities(d),
     lambda v: (
         (f"{v[0]:.0f}  ({v[1]:.0f}c + {v[2]:.0f}e)", "c-green")
            if isinstance(v, tuple) and v[0] >= 90
         else (f"{v[0]:.0f}  ({v[1]:.0f}c + {v[2]:.0f}e)", "c-red")
            if isinstance(v, tuple)
         else ("—", "c-empty")
     ),
     False),
    # 2. Pipeline Activity Movement — ≥ 20/day (target dropped 2026-05-14 after
    # the revivals-included redef raised live numbers above the prior 40 floor).
    ("Sales", "2", "Pipeline Activity Movement (CRM stage changes)", "20",
     lambda d: pipeline_movement_dict.get(d),
     lambda v: (
         (f"{int(v)}", "c-green") if v is not None and v >= 20
         else (f"{int(v)}", "c-red") if v is not None
         else ("—", "c-empty")
     ),
     False),
    # 3. A/R Past Due 31+ — green if ≤ $100k; live-today only until snapshot task updated
    ("Sales", "3", "A/R Past Due 31+", "$100k",
     lambda d: ar_dict.get(d),
     lambda v: (
         (f"${v:,.0f}", "c-green") if v is not None and v <= 100_000
         else (f"${v:,.0f}", "c-red") if v is not None
         else ("—", "c-empty")
     ),
     False),

    # ── MANUFACTURING (3 metrics — renamed from "Operations" 2026-05-14) ──
    ("Manufacturing", "1", "Unplanned Downtime %  (Liquid)", "<=15.5%",
     lambda d: prod_dt.get(d),
     lambda v: (
         (f"{v:.1f}%", "c-green") if v is not None and v <= 15.5
         else (f"{v:.1f}%", "c-red") if v is not None
         else ("—", "c-empty")
     ),
     False),
    ("Manufacturing", "2", "OEE", "70%",
     lambda d: prod_oee.get(d),
     lambda v: (
         (f"{v:.1f}%", "c-green") if v is not None and v >= 69
         else (f"{v:.1f}%", "c-red") if v is not None
         else ("—", "c-empty")
     ),
     False),
    ("Manufacturing", "3", "Labor Cost Per Unit  (Liquid)", "$0.25",
     lambda d: prod_labor.get(d),
     lambda v: (
         (f"${v:.2f}", "c-green") if v is not None and v <= 0.26
         else (f"${v:.2f}", "c-red") if v is not None
         else ("—", "c-empty")
     ),
     False),

    # ── CUSTOMER SUPPORT (3 metrics — renamed from Support 2026-05-18) ──────
    ("Customer Support", "1", "CSAT — Rolling 7D % Positive", ">80%",
     lambda d: get_csat_rolling7(d),
     lambda v: (
         (f"{v:.1f}%", "c-green") if v is not None and v >= 80
         else (f"{v:.1f}%", "c-red") if v is not None
         else ("—", "c-empty")
     ),
     False),
    ("Customer Support", "2", "First Response Time (median)", "<15 min",
     lambda d: safe_float(intercom_resp_dict.get(d)) if intercom_resp_dict.get(d) is not None else None,
     lambda v: (
         (f"{v:.1f}m", "c-green") if v is not None and v <= 15
         else (f"{v:.1f}m", "c-red") if v is not None
         else ("—", "c-empty")
     ),
     False),
    ("Customer Support", "3", "Fin AI Deflection Rate", ">50%",
     lambda d: get_deflection(d),
     lambda v: (
         (f"{v:.1f}%", "c-green") if v is not None and v >= 50
         else (f"{v:.1f}%", "c-red") if v is not None
         else ("—", "c-empty")
     ),
     False),

    # ── PEOPLE & CULTURE (renamed from HR 2026-05-18; same Manual Input data) ─
    ("People & Culture", "1", "Performance Documentation Rate", ">75%",
     lambda d: hr_perf_dict.get(d),
     lambda v: (
         (f"{v:.1f}%", "c-green") if v is not None and v >= 75
         else (f"{v:.1f}%", "c-red") if v is not None
         else ("—", "c-empty")
     ),
     False),
    ("People & Culture", "2", "Training & Compliance Completion Rate", ">75%",
     lambda d: hr_training_dict.get(d),
     lambda v: (
         (f"{v:.1f}%", "c-green") if v is not None and v >= 75
         else (f"{v:.1f}%", "c-red") if v is not None
         else ("—", "c-empty")
     ),
     False),
    ("People & Culture", "3", "HR Process Doc Completion Rate", ">75%",
     lambda d: hr_career_dict.get(d),
     lambda v: (
         (f"{v:.1f}%", "c-green") if v is not None and v >= 75
         else (f"{v:.1f}%", "c-red") if v is not None
         else ("—", "c-empty")
     ),
     False),

    # ── FINANCE (3 metrics — 2026-05-13 wave) ────────────────────────────
    # 1. Same-Day Cash Rec: row exists for the day in FACT_DAILY_CASH_BALANCE = green
    ("Finance", "1", "Same-Day Cash Reconciliation", "Daily row loaded",
     lambda d: cash_balance_dict.get(d),
     lambda v: (
         ("✓ Yes", "c-green") if v == 1
         else ("✗ No", "c-red") if v == 0
         else ("—", "c-empty")
     ),
     False),
    # 2. JE % in New ERP — live (2026-05-13). Target tab uses strict binary green/red.
    # Counts unique JEs from Supabase_ERP vs total (Supabase + Acumatica) per day.
    ("Finance", "2", "% of JEs in New ERP (Supabase)", "≥50%",
     lambda d: je_new_erp_dict.get(d),
     lambda v: (
         (f"{v:.1f}%", "c-green") if v is not None and v >= 50
         else (f"{v:.1f}%", "c-red") if v is not None
         else ("—", "c-empty")
     ),
     False),
    # 3. % Sources Synced <24h: ETL_METADATA.SYNC_HISTORY — target 100% green.
    ("Finance", "3", "% Sources Synced <24 hrs", "100%",
     lambda d: sync_coverage_dict.get(d),
     lambda v: (
         (f"{v:.0f}%", "c-green") if v is not None and v >= 100
         else (f"{v:.0f}%", "c-red") if v is not None
         else ("—", "c-empty")
     ),
     False),

    # ── MARKETING (3 metrics — 2026-05-13 wave) ──────────────────────────
    # 1. Cart Abandonment % — GA4 Option B math (mirrors marketing_scorecard.py).
    # Target ≤60% green, anything above red. No yellow per binary target-page spec.
    ("Marketing", "1", "Cart Abandonment % (GA4 ATC vs Purchase)", "≤60%",
     lambda d: (marketing_ga4_dict.get(d) or {}).get('cart_abandon_pct'),
     lambda v: (
         (f"{v:.1f}%", "c-green") if v is not None and v <= 60
         else (f"{v:.1f}%", "c-red") if v is not None
         else ("—", "c-empty")
     ),
     False),
    # 2. AOV — First Purchase (180-day rolling window — same redef as marketing scorecard).
    # Target ≥$85 green (set 2026-05-28; $120 was unreachable — YTD first-order AOV ~$99).
    ("Marketing", "2", "AOV — First (180d rolling)", "≥$85",
     lambda d: aov_first_180d_dict.get(d),
     lambda v: (
         (f"${v:,.2f}", "c-green") if v is not None and v >= 85
         else (f"${v:,.2f}", "c-red") if v is not None
         else ("—", "c-empty")
     ),
     False),
    # 3. Unique Sessions — GA4 newUsers across all 3 brands. Target ≥500/day green.
    # (Threshold set 2026-05-13 from 90-day baseline: mean 484, median 479.)
    ("Marketing", "3", "Unique Sessions (1st-time visitors)", "≥500",
     lambda d: (marketing_ga4_dict.get(d) or {}).get('new_users'),
     lambda v: (
         (f"{int(v):,}", "c-green") if v is not None and v >= 500
         else (f"{int(v):,}", "c-red") if v is not None
         else ("—", "c-empty")
     ),
     False),

    # ── FULFILLMENT (wired 2026-05-14 from Shiphero) ────────────────────────
    # On-Time Ship Rate removed 2026-05-28.
    ("Fulfillment", "1", "Same-Day Ship Rate", "≥80%",
     lambda d: fulfill_same_day_dict.get(d),
     lambda v: (
         (f"{v:.1f}%", "c-green") if v is not None and v >= 80
         else (f"{v:.1f}%", "c-red") if v is not None
         else ("—", "c-empty")
     ),
     False),
    ("Fulfillment", "2", "Median Order-to-Ship Cycle Time", "≤24 hrs",
     lambda d: fulfill_cycle_dict.get(d),
     lambda v: (
         (f"{v:.0f} hrs", "c-green") if v is not None and v <= 24
         else (f"{v:.0f} hrs", "c-red") if v is not None
         else ("—", "c-empty")
     ),
     False),
    # B2B OTIF redefined 2026-05-28 to avg business hours (approve→complete).
    ("Fulfillment", "3", "B2B OTIF", "≤24 hrs",
     lambda d: b2b_ship_hrs_dict.get(d),
     lambda v: (
         (f"{v:.1f} hrs", "c-green") if v is not None and v <= 24
         else (f"{v:.1f} hrs", "c-red") if v is not None
         else ("—", "c-empty")
     ),
     False),

    # ── PROCUREMENT ──────────────────────────────────────────────────────────
    # Supplier Scorecard % (manual weekly entry, 2026-05-28) — replaced GM
    # Critical Stockouts here. ≥90% green, 80-89.9% yellow, <80% red.
    ("Procurement", "1", "Supplier Scorecard", "≥ 90%",
     lambda d: proc_supplier_scorecard_dict.get(d),
     lambda v: (
         (f"{v:.1f}%", "c-green") if v is not None and v >= 90
         else (f"{v:.1f}%", "c-yellow") if v is not None and v >= 80
         else (f"{v:.1f}%", "c-red") if v is not None
         else ("—", "c-empty")
     ),
     True),
    ("Procurement", "2", "Supplier OTD % (trailing 90d)", "≥ 90%",
     lambda d: proc_otd_dict.get(d),
     lambda v: (
         (f"{v:.1f}%", "c-green") if v is not None and v >= 90
         else (f"{v:.1f}%", "c-red") if v is not None
         else ("—", "c-empty")
     ),
     True),
    ("Procurement", "3", "% Critical Components Single-Sourced", "≤ 25%",
     lambda d: proc_single_sourced_dict.get(d),
     lambda v: (
         (f"{v:.1f}%", "c-green") if v is not None and v <= 25
         else (f"{v:.1f}%", "c-yellow") if v is not None and v <= 30
         else (f"{v:.1f}%", "c-red") if v is not None
         else ("—", "c-empty")
     ),
     True),
]


# ── LAGGING INDICATORS (Monthly Pace) — definitions ───────────────────────────
# Each row = one lagging metric per dept, rendered as a progress bar.
# Two visualization modes:
#   'cumulative' — bar = MTD actual / monthly target. Pace tick = days_elapsed/days_in_month.
#                  Used for: revenue, count-based goals.
#   'rate'       — bar = (weeks-elapsed-with-metric-on-target / weeks-elapsed-in-month) / 80%.
#                  Anchor at 80% (same threshold as daily heat map's "green" bar).
#                  Used for: OEE, downtime, labor, AR average.
# Stub rows have mode='pending'. Other departments get 3 stubs each (HR / Business Ops /
# Support / Marketing).
def _mtd_avg(metric_dict, days_in_month_so_far):
    """Mean of metric values across the elapsed weekdays of the current month."""
    today_d = date.today()
    month_start = today_d.replace(day=1)
    vals = [v for d, v in metric_dict.items()
            if month_start <= d <= today_d and v is not None
            and d.weekday() < 5]
    return (sum(safe_float(v, 0) for v in vals) / len(vals)) if vals else None

def _weeks_green_so_far(metric_dict, threshold_fn):
    """Count weeks elapsed in current month where ≥80% of daily values are green.
    Returns (weeks_green, weeks_elapsed)."""
    today_d = date.today()
    month_start = today_d.replace(day=1)
    weeks_green = 0
    weeks_elapsed = 0
    # Mon-anchored weeks that have any day inside current month
    cur_mon = month_start - timedelta(days=month_start.weekday())
    while cur_mon <= today_d:
        week_days = [cur_mon + timedelta(days=i) for i in range(5)
                     if month_start <= cur_mon + timedelta(days=i) <= today_d]
        if not week_days:
            cur_mon += timedelta(days=7); continue
        green_days = sum(1 for d in week_days
                         if metric_dict.get(d) is not None
                         and threshold_fn(safe_float(metric_dict[d], 0)))
        scoreable_days = sum(1 for d in week_days if metric_dict.get(d) is not None)
        if scoreable_days > 0:
            weeks_elapsed += 1
            if green_days / scoreable_days >= 0.80:
                weeks_green += 1
        cur_mon += timedelta(days=7)
    return weeks_green, weeks_elapsed

# Define lagging rows — (dept, metric_name, mode, getter, target_label, target_threshold_fn_or_None)
lagging_rows = [
    # ── SALES ─────────────────────────────────────────────────────────────
    # B2B Revenue MTD (cumulative — has explicit weekly targets to sum)
    ("Sales", "B2B Revenue MTD",       "cumulative_b2b", None, "Q2 Forecast model", None),
    ("Sales", "A/R Past Due 31+",      "rate", ar_dict, "≤ $100k weekly",
     lambda v: v <= 100_000),
    ("Sales", "Pipeline Activity",     "rate", pipeline_movement_dict, "≥ 20/day weekly",
     lambda v: v >= 20),
    # ── MANUFACTURING (renamed from "Operations" 2026-05-14) ─────────────
    ("Manufacturing", "Unplanned Downtime", "rate", prod_dt,    "≤ 15.5% daily",
     lambda v: v <= 15.5),
    ("Manufacturing", "OEE",                "rate", prod_oee,   "≥ 69% daily",
     lambda v: v >= 69),
    ("Manufacturing", "Labor Cost / Unit",  "rate", prod_labor, "≤ $0.26 daily",
     lambda v: v <= 0.26),
    # ── CUSTOMER SUPPORT (renamed from Support 2026-05-18) ───────────────
    ("Customer Support", "CSAT (Rolling 7D)",     "rate",
     {}, "≥ 80% daily",  # getter populated post-define below; see _support_lagging_dicts
     lambda v: v >= 80),
    ("Customer Support", "First Response Time",   "rate",
     {}, "≤ 15 min daily",
     lambda v: v <= 15),
    ("Customer Support", "Fin AI Deflection",     "rate",
     {}, "≥ 50% daily",
     lambda v: v >= 50),
    # ── PEOPLE & CULTURE (renamed from HR 2026-05-18; same Manual Input data) ─
    ("People & Culture", "Performance Documentation",        "rate", hr_perf_dict,     "≥75% daily", lambda v: v >= 75),
    ("People & Culture", "Training & Compliance Completion", "rate", hr_training_dict, "≥75% daily", lambda v: v >= 75),
    ("People & Culture", "HR Process Doc Completion",        "rate", hr_career_dict,   "≥75% daily", lambda v: v >= 75),
    # ── FINANCE (3 metrics — 2026-05-13 wave) ────────────────────────────
    # Bar viz reuses _weeks_green_so_far with the daily-target threshold fns.
    ("Finance", "Same-Day Cash Rec",       "rate", cash_balance_dict, "all days reconciled",
     lambda v: v == 1),
    ("Finance", "% JEs in New ERP",        "rate", je_new_erp_dict, "≥50% daily",
     lambda v: v >= 50),
    ("Finance", "Sync Coverage <24 hrs",   "rate", sync_coverage_dict, "100% daily",
     lambda v: v >= 100),
    # ── MARKETING (3 metrics — 2026-05-13 wave) ──────────────────────────
    # Marketing Revenue MTD — cumulative, target $300k/month (user spec 2026-05-14).
    # Sits at the top of the Marketing lagging block per design ask.
    ("Marketing", "Marketing Revenue MTD", "cumulative_marketing", None, "≥$300k/month", None),
    # Cart Abandonment + AOV pull from per-day dicts. For abandonment we extract the
    # cart_abandon_pct so the rate-mode rollup gets a plain float.
    ("Marketing", "Cart Abandonment %",  "rate",
     {d: (info or {}).get('cart_abandon_pct') for d, info in marketing_ga4_dict.items()},
     "≤60% daily", lambda v: v <= 60),
    ("Marketing", "AOV — First (180d)",  "rate", aov_first_180d_dict, "≥$85 daily",
     lambda v: v >= 85),
    # Unique Sessions removed from lagging 2026-05-14 (stays on Daily target page).
    # ── FULFILLMENT (wired 2026-05-14 from Shiphero) ─────────────────────
    # On-Time Ship Rate replaced by B2B OTIF 2026-05-28 (avg business hrs approve→complete).
    ("Fulfillment", "B2B OTIF (avg hrs)", "rate", b2b_ship_hrs_dict,     "≤ 24 hrs daily",
     lambda v: v <= 24),
    ("Fulfillment", "Same-Day Ship Rate", "rate", fulfill_same_day_dict, "≥ 80% daily",
     lambda v: v >= 80),
    ("Fulfillment", "Median Order-to-Ship Cycle (hrs)", "rate", fulfill_cycle_dict, "≤ 24 hrs daily",
     lambda v: v <= 24),
    # ── PROCUREMENT ───────────────────────────────────────────────────────
    # Supplier Scorecard % (manual weekly entry, 2026-05-28) — replaced DSI
    # Combined as the lead procurement lagging metric. ≥90% = green.
    ("Procurement", "Supplier Scorecard",                   "rate", proc_supplier_scorecard_dict, "≥ 90% daily",
     lambda v: v >= 90),
    ("Procurement", "Supplier OTD % (trailing 90d)",         "rate", proc_otd_dict,            "≥ 90% daily",
     lambda v: v >= 90),
    ("Procurement", "% Critical Components Single-Sourced",  "rate", proc_single_sourced_dict, "≤ 25% daily",
     lambda v: v <= 25),
]

# Populate Support lagging dicts after-the-fact — these are computed per-day on
# the existing intercom data, materialised into a date→value map so the weekly-
# green rollup helper (_weeks_green_so_far) can iterate them like the Ops dicts.
def _build_csat_dict():
    if intercom.empty: return {}
    df = intercom.copy()
    df['CONV_DATE'] = pd.to_datetime(df['CONV_DATE']).dt.date
    cur_mon = today.replace(day=1)
    out = {}
    for d in pd.date_range(cur_mon, today, freq='D'):
        d = d.date()
        out[d] = get_csat_rolling7(d)
    return out

def _build_deflection_dict():
    if intercom.empty: return {}
    cur_mon = today.replace(day=1)
    out = {}
    for d in pd.date_range(cur_mon, today, freq='D'):
        d = d.date()
        out[d] = get_deflection(d)
    return out

def _build_frt_dict():
    return {d: safe_float(intercom_resp_dict.get(d)) for d in intercom_resp_dict.keys()}

# Splice the real dicts into the lagging_rows tuples (positions for Support: -3,-2,-1)
_csat_d  = _build_csat_dict()
_frt_d   = _build_frt_dict()
_deflt_d = _build_deflection_dict()
_support_idx = [i for i, r in enumerate(lagging_rows) if r[0] == 'Customer Support']
if len(_support_idx) == 3:
    _i_csat, _i_frt, _i_def = _support_idx
    lagging_rows[_i_csat] = ('Customer Support', 'CSAT (Rolling 7D)',     'rate', _csat_d,  '≥ 80% daily', lambda v: v >= 80)
    lagging_rows[_i_frt]  = ('Customer Support', 'First Response Time',    'rate', _frt_d,   '≤ 15 min daily', lambda v: v <= 15)
    lagging_rows[_i_def]  = ('Customer Support', 'Fin AI Deflection',      'rate', _deflt_d, '≥ 50% daily', lambda v: v >= 50)


# ── Who can input ──────────────────────────────────────────────────────────────
current_user_df = q("SELECT CURRENT_USER() AS U")
current_user = current_user_df.iloc[0]['U'].upper() if not current_user_df.empty else ''
INPUTTERS = {'RICHIE', 'LATONYA', 'PETE', 'COREY', 'NIKITA'}
can_input = current_user in INPUTTERS

# ══════════════════════════════════════════════════════════════════════════════
# ── WEEKLY DATA ───────────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

# ── Theme (weekly block — kept in sync with top-of-file palette) ──────────────
# Light-only since 2026-05-12.
T = {
    "bg":        "#ffffff",
    "bg2":       "#f4f6f9",
    "bg3":       "#ffffff",
    "border":    "#dde2e9",
    "border2":   "#e6eaef",
    "text":      "#1f2937",
    "text2":     "#4b5563",
    "text3":     "#6b7280",
    "text4":     "#9aa1ab",
    "title":     "#1f2937",
    "hdr_bg":    "#2c5784",
    "hdr_border":"#2c5784",
    "hdr_color": "#ffffff",
    "hover":     "#f1f4f8",
    "th_bg":     "#2c5784",
    "th_color":  "#ffffff",
    "goal_color":"#6b7280",
    "wavg":      "#4b5563",
    "g_bg":  "#cbe9ce",
    "g_fg":  "#1f6634",
    "y_bg":  "#fff3bf",
    "y_fg":  "#a37500",
    "r_bg":  "#f4cccc",
    "r_fg":  "#9c2828",
    "e_fg":  "#c8ccd1",
    "na_fg": "#9aa1ab",
}

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');
*, html, body {{ box-sizing: border-box; }}
.stApp {{ background: {T['bg']}; font-family: 'IBM Plex Sans', sans-serif; }}
.stApp, .stApp > div, section.main, .block-container {{ background-color: {T['bg']} !important; }}
.block-container {{ max-width: 1400px !important; padding-left: 2rem !important; padding-right: 2rem !important; }}
.stApp p, .stApp li, .stApp span, .stApp label {{ color: {T['text']} !important; }}
.stApp h1, .stApp h2, .stApp h3 {{ color: {T['title']} !important; }}
.stButton > button {{ background: {T['bg2']} !important; color: {T['text']} !important; border: 1px solid {T['border']} !important; }}
.stButton > button:hover {{ background: {T['hover']} !important; border-color: {T['hdr_border']} !important; }}

.sc-header {{
    display: flex; align-items: baseline; gap: 16px;
    padding: 16px 0 10px;
    border-bottom: 2px solid {T['border']};
    margin-bottom: 8px;
}}
.sc-title {{
    font-family: 'IBM Plex Mono', monospace; font-size: 20px; font-weight: 600;
    color: {T['title']}; letter-spacing: 0.04em; text-transform: uppercase;
}}
.sc-subtitle {{ font-size: 12px; color: {T['text3']}; font-family: 'IBM Plex Mono', monospace; }}

.section-hdr {{
    background: {T['hdr_bg']}; color: {T['hdr_color']};
    font-family: 'IBM Plex Mono', monospace; font-size: 11px; font-weight: 600;
    letter-spacing: 0.12em; text-transform: uppercase;
    padding: 6px 12px; border-left: 3px solid {T['hdr_border']};
    margin: 8px 0 4px; text-align: left;
}}

.wsc-table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
.wsc-table th {{
    font-family: 'IBM Plex Mono', monospace; font-size: 10px;
    letter-spacing: 0.08em; text-transform: uppercase;
    color: {T['th_color']}; font-weight: 600;
    padding: 6px 8px; text-align: right;
    border-bottom: 1px solid {T['border']}; background: {T['th_bg']};
    white-space: nowrap;
}}
.wsc-table th.left {{ text-align: left !important; }}
.wsc-table th.cur {{ color: #4488ff !important; border-bottom: 2px solid #4488ff !important; }}
.wsc-table td {{
    padding: 6px 8px; text-align: right;
    border-bottom: 1px solid {T['border2']};
    color: {T['text']} !important; font-family: 'IBM Plex Mono', monospace; font-size: 12px;
}}
.wsc-table td.left {{ text-align: left !important; color: {T['text']} !important; font-family: 'IBM Plex Sans', sans-serif; font-size: 13px; }}
.wsc-table td.goal {{ color: {T['goal_color']} !important; }}
.wsc-table td.cur {{ background: #e8f4ff !important; color: {T['text']} !important; }}
/* Current week color cells — keep color but add subtle border highlight */
.wsc-table td.c-green.cur  {{ background: {T['g_bg']} !important; color: {T['g_fg']} !important; font-weight: 600; border-left: 2px solid #4488ff; }}
.wsc-table td.c-yellow.cur {{ background: {T['y_bg']} !important; color: {T['y_fg']} !important; font-weight: 600; border-left: 2px solid #4488ff; }}
.wsc-table td.c-red.cur    {{ background: {T['r_bg']} !important; color: {T['r_fg']} !important; font-weight: 600; border-left: 2px solid #4488ff; }}
.wsc-table td.c-empty.cur  {{ background: #e8f4ff !important; border-left: 2px solid #4488ff; }}
.wsc-table tr:hover td {{ background: {T['hover']}; }}
.row-num {{ color: {T['na_fg']}; font-size: 11px; }}

/* Color cells */
.c-green   {{ background: {T['g_bg']} !important; color: {T['g_fg']} !important; font-weight: 600; }}
.c-yellow  {{ background: {T['y_bg']} !important; color: {T['y_fg']} !important; font-weight: 600; }}
.c-red     {{ background: {T['r_bg']} !important; color: {T['r_fg']} !important; font-weight: 600; }}
.c-empty   {{ color: {T['text3']} !important; }}
.c-na      {{ color: {T['text']} !important; }}
.c-neutral {{ color: {T['text']} !important; }}

/* Trend cell */
.trend-up   {{ color: {T['g_fg']} !important; font-weight: 600; font-family: 'IBM Plex Mono', monospace; }}
.trend-down {{ color: {T['r_fg']} !important; font-weight: 600; font-family: 'IBM Plex Mono', monospace; }}
.trend-flat {{ color: {T['na_fg']} !important; font-family: 'IBM Plex Mono', monospace; }}
</style>
""", unsafe_allow_html=True)

# (duplicate q() removed — now defined once near the top with caching via _run_sql)

def safe_float(v, default=0.0):
    try:
        return float(v) if v is not None and str(v) not in ('', 'nan', 'None') else default
    except:
        return default

def fmt_currency(v):
    if v is None or v == 0: return "—"
    return f"${v:,.0f}"

def fmt_pct(v):
    if v is None: return "—"
    return f"{v:.1f}%"

def fmt_num(v):
    if v is None or v == 0: return "—"
    return f"{v:,.0f}"

def color_pct_of_target(actual, target):
    """Color actual vs target: ≥97% green, ≥85% yellow, else red"""
    if actual is None or target is None or target == 0:
        return "c-empty"
    r = actual / target
    if r >= 0.97: return "c-green"
    if r >= 0.85: return "c-yellow"
    return "c-red"

def trend_cell(cur, prev):
    """Return trend HTML: ↑/↓/→ with % change"""
    if cur is None or prev is None or prev == 0:
        return '<td class="trend-flat">—</td>'
    pct = (cur - prev) / abs(prev) * 100
    if abs(pct) < 1:
        return f'<td class="trend-flat">→ 0%</td>'
    elif pct > 0:
        return f'<td class="trend-up">↑ {pct:.1f}%</td>'
    else:
        return f'<td class="trend-down">↓ {abs(pct):.1f}%</td>'

# ── Date setup ─────────────────────────────────────────────────────────────────
# today already defined above; derive weekly variables from it
cur_week_mon = today - timedelta(days=today.weekday())

# Build list of 7 weeks: 6 prior + current
weeks = [cur_week_mon - timedelta(weeks=6-i) for i in range(7)]
# Week labels
def week_label(d, is_cur=False):
    end = d + timedelta(days=6)
    label = f"{d.strftime('%b %-d')}"
    return label

# ── Pull Revenue Targets ───────────────────────────────────────────────────────
targets_df = q("""
    SELECT WEEK_START, DTC_TARGET, SMOKESHOP_TARGET, CSTORE_TARGET, CUMULATIVE_TARGET
    FROM GOLD_V3_DB.PUBLIC.Q2_WEEKLY_REVENUE_TARGETS
    ORDER BY WEEK_START
""")
def get_target(week_start, col):
    """week_start is Monday — targets table uses Sunday (day before). Convert to match."""
    if targets_df.empty: return None
    # Our weeks are Monday-anchored; targets are Sunday-anchored (day before Monday)
    sunday = week_start - timedelta(days=1)
    row = targets_df[pd.to_datetime(targets_df['WEEK_START']).dt.date == sunday]
    if row.empty: return None
    return safe_float(row.iloc[0][col])

# ── Pull Actuals ───────────────────────────────────────────────────────────────
week_starts = [w.strftime('%Y-%m-%d') for w in weeks]
earliest = weeks[0].strftime('%Y-%m-%d')
latest   = (weeks[-1] + timedelta(days=6)).strftime('%Y-%m-%d')

# B2B Revenue by week (Monday-based — Snowflake DATE_TRUNC uses Sunday, so we fix manually)
b2b_rev = q(f"""
    SELECT
        DATEADD('day', -MOD(DAYOFWEEKISO(ORDER_DATE::DATE)-1, 7), ORDER_DATE::DATE) AS WEEK_START,
        SUM(CASE WHEN CUSTOMER_CLASS = 'Branded Convenience Store'
                 THEN NET_REVENUE_AMT END)                                         AS CSTORE_REV,
        SUM(CASE WHEN CUSTOMER_CLASS = 'Smoke Shop'
                 THEN NET_REVENUE_AMT END)                                         AS SMOKESHOP_REV,
        SUM(NET_REVENUE_AMT)                                                       AS TOTAL_B2B_REV
    FROM GOLD_V3_DB.SALES.FACT_ORDERS
    WHERE CHANNEL = 'B2B'
      AND ORDER_DATE::DATE BETWEEN '{earliest}' AND '{latest}'
    GROUP BY 1 ORDER BY 1
""")

# DTC Revenue by week — REMOVED 2026-04-29, see top of file
# dtc_gm = q(f"""
#     SELECT DATEADD('day', -MOD(DAYOFWEEKISO(DATE(DATE_CREATED))-1, 7), DATE(DATE_CREATED)) AS WEEK_START,
#            SUM(CAST(TOTAL AS FLOAT)) AS REV
#     FROM RAW_V2_DB.WOO_GOLDEN_MONK.ORDERS
#     WHERE STATUS IN ('processing','completed')
#       AND DATE(DATE_CREATED) BETWEEN '{earliest}' AND '{latest}'
#     GROUP BY 1
# """)
# dtc_mit = q(f"""
#     SELECT DATEADD('day', -MOD(DAYOFWEEKISO(DATE(DATE_CREATED))-1, 7), DATE(DATE_CREATED)) AS WEEK_START,
#            SUM(CAST(TOTAL AS FLOAT)) AS REV
#     FROM RAW_V2_DB.WOO_MIT45.ORDERS
#     WHERE STATUS IN ('processing','completed')
#       AND DATE(DATE_CREATED) BETWEEN '{earliest}' AND '{latest}'
#     GROUP BY 1
# """)
# dtc_up = q(f"""
#     SELECT DATEADD('day', -MOD(DAYOFWEEKISO(DATE(DATE_CREATED))-1, 7), DATE(DATE_CREATED)) AS WEEK_START,
#            SUM(CAST(TOTAL AS FLOAT)) AS REV
#     FROM RAW_V2_DB.WOO_UPRISING.ORDERS
#     WHERE STATUS IN ('processing','completed')
#       AND DATE(DATE_CREATED) BETWEEN '{earliest}' AND '{latest}'
#     GROUP BY 1
# """)

# Ops: weekly averages (Monday-based)
ops_weekly = q(f"""
    SELECT
        DATEADD('day', -MOD(DAYOFWEEKISO(PRODUCTION_DATE)-1, 7), PRODUCTION_DATE) AS WEEK_START,
        ROUND(AVG(CASE WHEN PRODUCTION_TYPE='Liquid'
              THEN DAY_LABOR_COST_AMT / NULLIF(DAY_COMPLETED_QTY,0) END), 2)      AS LABOR_COST,
        ROUND(100 - AVG(CASE WHEN PRODUCTION_TYPE='Liquid'
              THEN AVAILABILITY_PCT END), 1)                                       AS DOWNTIME_PCT,
        ROUND(AVG(CASE WHEN PRODUCTION_TYPE='Liquid' AND FIRST_PASS_PCT > 0
              THEN FIRST_PASS_PCT END), 1)                                         AS FPY_PCT,
        ROUND(AVG(CASE WHEN PRODUCTION_TYPE='Liquid' AND OEE_PCT > 0
              THEN OEE_PCT END), 1)                                                AS OEE_PCT
    FROM GOLD_V3_DB.SEMANTIC.SV_DAILY_PRODUCTION
    WHERE PRODUCTION_DATE BETWEEN '{earliest}' AND '{latest}'
    GROUP BY 1 ORDER BY 1
""")

# OTIF DTC: weekly on-time % (avg of daily values, matches the daily view).
otif_dtc_weekly = q(f"""
    SELECT
        WEEK_START,
        ROUND(AVG(DAILY_ONTIME_PCT), 2) AS ONTIME_PCT
    FROM (
        SELECT
            DATEADD('day', -MOD(DAYOFWEEKISO(s.SHIP_DATE)-1, 7), s.SHIP_DATE) AS WEEK_START,
            s.SHIP_DATE,
            100.0 - COUNT(CASE WHEN s.SHIP_DATE > o.REQUIRED_SHIP_DATE THEN 1 END) * 100.0
                  / NULLIF(COUNT(*), 0) AS DAILY_ONTIME_PCT
        FROM GOLD_V3_DB.FULFILLMENT.STG_SHIPHERO__SHIPMENTS s
        JOIN GOLD_V3_DB.FULFILLMENT.STG_SHIPHERO__ORDERS o ON o.ORDER_ID = s.ORDER_ID
        WHERE s.SHIP_DATE BETWEEN '{earliest}' AND '{latest}'
        GROUP BY 1, s.SHIP_DATE
    )
    GROUP BY 1 ORDER BY 1
""")

# OTIF B2B weekly (Acumatica-based) removed 2026-05-26 — replaced by
# load_b2b_cycle_daily (Supabase ERP). Daily lookup is enough for the Target
# Fulfillment row; no separate weekly aggregation needed.


# Aircall: weekly avg calls per rep (Monday-based, MT date)
# 2026-05-12: bucket by Mountain-time so week-boundary edge calls land in the right week.
aircall_weekly = q(f"""
    -- v2: repointed to GOLD_V3_DB.SCORECARD.FCT_SALES_REP_CALLS_DAILY (verified fact).
    -- Weekly avg/rep = SUM(TOTAL_CALLS) / distinct scorecard reps active that week,
    -- Mon-anchored. Contract: WEEK_START, AVG_PER_REP, TOTAL_CALLS.
    SELECT
        DATEADD('day', -MOD(DAYOFWEEKISO(ACTIVITY_DATE)-1, 7), ACTIVITY_DATE) AS WEEK_START,
        ROUND(SUM(TOTAL_CALLS) / NULLIF(COUNT(DISTINCT REP_NAME), 0), 1)      AS AVG_PER_REP,
        SUM(TOTAL_CALLS)                                                      AS TOTAL_CALLS
    FROM GOLD_V3_DB.SCORECARD.FCT_SALES_REP_CALLS_DAILY
    WHERE ACTIVITY_DATE BETWEEN '{earliest}' AND '{latest}'
      AND IS_SCORECARD_REP
    GROUP BY 1 ORDER BY 1
""")

# AR Past Due: from snapshot table (Monday-based)
ar_weekly = q(f"""
    SELECT
        DATEADD('day', -MOD(DAYOFWEEKISO(SNAPSHOT_DATE)-1, 7), SNAPSHOT_DATE)     AS WEEK_START,
        AVG(AR_PAST_DUE_AMT)                                                       AS AR_AMT
    FROM GOLD_V3_DB.PUBLIC.AR_PAST_DUE_DAILY
    WHERE SNAPSHOT_DATE BETWEEN '{earliest}' AND '{latest}'
    GROUP BY 1 ORDER BY 1
""")

# ClickUp tasks past due — weekly avg of daily % (Mon-Fri only).
# Mirrors the daily query's filters (STATUS_TYPE, ARCHIVED) so weekly matches dailies.
clickup_weekly = q(f"""
    -- v2: repointed to GOLD_V3_DB.SCORECARD.FCT_CLICKUP_TASKS_PASTDUE_DAILY (verified
    -- fact). Weekly = AVG of the daily PCT_PAST_DUE over Mon–Fri snapshot days, matching
    -- the daily view. Contract: WEEK_START, AVG_PAST_DUE_PCT.
    SELECT
        DATEADD('day', -MOD(DAYOFWEEKISO(SNAPSHOT_DATE)-1, 7), SNAPSHOT_DATE) AS WEEK_START,
        ROUND(AVG(PCT_PAST_DUE), 1) AS AVG_PAST_DUE_PCT
    FROM GOLD_V3_DB.SCORECARD.FCT_CLICKUP_TASKS_PASTDUE_DAILY
    WHERE SNAPSHOT_DATE BETWEEN '{earliest}' AND '{latest}'
      AND DAYOFWEEKISO(SNAPSHOT_DATE) <= 5
    GROUP BY 1 ORDER BY 1
""")

# Trailing 90D marketing — REMOVED 2026-04-29, see top of file
# def mkt_90d_as_of(table, week_start):
#     week_end = week_start + timedelta(days=6)
#     window_start = week_end - timedelta(days=90)
#     df = q(f"""
#         WITH all_orders AS (
#             SELECT BILLING:email::STRING AS EMAIL,
#                    DATE(DATE_CREATED) AS ORDER_DATE,
#                    CAST(TOTAL AS FLOAT) AS ORDER_TOTAL
#             FROM RAW_V2_DB.{table}.ORDERS
#             WHERE STATUS IN ('processing','completed')
#         ),
#         first_order_ever AS (
#             SELECT EMAIL, MIN(ORDER_DATE) AS FIRST_ORDER_DATE FROM all_orders GROUP BY EMAIL
#         )
#         SELECT
#             COUNT(*)                                                           AS ORDERS_90D,
#             ROUND(AVG(o.ORDER_TOTAL), 2)                                      AS AOV_90D,
#             COUNT(DISTINCT CASE
#                 WHEN f.FIRST_ORDER_DATE BETWEEN '{window_start}' AND '{week_end}'
#                 THEN o.EMAIL END)                                             AS NEW_BUYERS_90D
#         FROM all_orders o
#         JOIN first_order_ever f ON f.EMAIL = o.EMAIL
#         WHERE o.ORDER_DATE BETWEEN '{window_start}' AND '{week_end}'
#     """)
#     if df.empty: return None, None, None
#     return (safe_float(df.iloc[0]['ORDERS_90D']),
#             safe_float(df.iloc[0]['AOV_90D']),
#             safe_float(df.iloc[0]['NEW_BUYERS_90D']))
#
# mkt_cache = {}
# for w in weeks:
#     gm_o, gm_a, gm_n   = mkt_90d_as_of('WOO_GOLDEN_MONK', w)
#     mit_o, mit_a, mit_n = mkt_90d_as_of('WOO_MIT45', w)
#     up_o,  up_a,  up_n  = mkt_90d_as_of('WOO_UPRISING', w)
#     mkt_cache[w] = {
#         'gm_orders': gm_o, 'gm_aov': gm_a, 'gm_new': gm_n,
#         'mit_orders': mit_o, 'mit_aov': mit_a, 'mit_new': mit_n,
#         'up_orders': up_o,  'up_aov': up_a,  'up_new': up_n,
#     }
def week_lookup(df, date_col, val_col):
    if df.empty: return {}
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col]).dt.date
    return dict(zip(df[date_col], df[val_col]))

# def merge_dtc(gm, mit, up):  # REMOVED 2026-04-29
#     """Combine 3 brand DTC dataframes into weekly total"""
#     dfs = []
#     for df in [gm, mit, up]:
#         if not df.empty:
#             df = df.copy()
#             df['WEEK_START'] = pd.to_datetime(df['WEEK_START']).dt.date
#             dfs.append(df.set_index('WEEK_START')['REV'])
#     if not dfs: return {}
#     combined = dfs[0]
#     for d in dfs[1:]:
#         combined = combined.add(d, fill_value=0)
#     return combined.to_dict()

cstore_dict    = week_lookup(b2b_rev, 'WEEK_START', 'CSTORE_REV')
smokeshop_dict = week_lookup(b2b_rev, 'WEEK_START', 'SMOKESHOP_REV')
b2b_total_dict = week_lookup(b2b_rev, 'WEEK_START', 'TOTAL_B2B_REV')
# dtc_dict       = merge_dtc(dtc_gm, dtc_mit, dtc_up)  # REMOVED 2026-04-29
labor_dict     = week_lookup(ops_weekly, 'WEEK_START', 'LABOR_COST')
downtime_dict  = week_lookup(ops_weekly, 'WEEK_START', 'DOWNTIME_PCT')
fpy_dict       = week_lookup(ops_weekly, 'WEEK_START', 'FPY_PCT')
oee_dict       = week_lookup(ops_weekly, 'WEEK_START', 'OEE_PCT')
otif_dtc_dict  = week_lookup(otif_dtc_weekly, 'WEEK_START', 'ONTIME_PCT')
# otif_b2b_dict removed 2026-05-26 — see b2b_cycle_dict (Supabase ERP source).
aircall_weekly_dict = week_lookup(aircall_weekly, 'WEEK_START', 'AVG_PER_REP')
ar_weekly_dict = week_lookup(ar_weekly, 'WEEK_START', 'AR_AMT')
clickup_weekly_dict = week_lookup(clickup_weekly, 'WEEK_START', 'AVG_PAST_DUE_PCT') if not clickup_weekly.empty else {}


# ── Weekly metrics for 2026-05-13 wave (Sales pipeline + Finance + Marketing) ──
# Each loader returns a {week_start_Monday: value} dict.
# Pipeline Movement: daily-average forward/lateral stage changes across the week.
@st.cache_data(ttl=600)
def load_pipeline_movement_weekly(start_date, end_date):
    # 2026-06-03: sourced from TASK_STATUS_HISTORY (status-change events), matching
    # the daily loader. Per-day = distinct deals entering a live status (MT-bucketed),
    # then averaged per week. A date spine LEFT JOINs the events so zero-movement
    # days still count toward the average (same as the old snapshot version, which
    # produced movements=0 for unchanged days); capped at CURRENT_DATE so future
    # days of the in-progress week don't drag the average down.
    # v2: repointed to GOLD_V3_DB.SCORECARD.FCT_PIPELINE_MOVEMENT_DAILY (verified fact).
    # A date spine still LEFT JOINs the daily fact so zero-movement days count toward
    # the weekly average (same semantics as before); capped at CURRENT_DATE. Contract:
    # WEEK_START, AVG_MOVEMENTS.
    span = (end_date - start_date).days + 1   # GENERATOR ROWCOUNT must be a literal
    sql = f"""
    WITH spine AS (
        SELECT DATEADD('day', SEQ4(), '{start_date}'::DATE) AS d
        FROM TABLE(GENERATOR(ROWCOUNT => {span}))
    ),
    daily AS (
        SELECT s.d, COALESCE(f.TASKS_MOVED, 0) AS movements
        FROM spine s
        LEFT JOIN GOLD_V3_DB.SCORECARD.FCT_PIPELINE_MOVEMENT_DAILY f ON f.MOVEMENT_DATE = s.d
        WHERE s.d BETWEEN '{start_date}' AND '{end_date}' AND s.d <= CURRENT_DATE
    )
    SELECT DATEADD('day', -MOD(DAYOFWEEKISO(d)-1, 7), d) AS week_start,
           ROUND(AVG(movements), 1) AS avg_movements
    FROM daily GROUP BY 1 ORDER BY 1
    """
    return q(sql)

pipeline_weekly = load_pipeline_movement_weekly(weeks[0], weeks[-1] + timedelta(days=6))
pipeline_weekly_dict = week_lookup(pipeline_weekly, 'WEEK_START', 'AVG_MOVEMENTS')


# Cash balance: % of weekdays (Mon-Fri) in the week with a non-zero balance row.
@st.cache_data(ttl=600)
def load_cash_balance_weekly(start_date, end_date):
    sql = f"""
    SELECT DATEADD('day', -MOD(DAYOFWEEKISO(BALANCE_DATE)-1, 7), BALANCE_DATE) AS week_start,
           ROUND(COUNT(CASE WHEN ENDING_CASH_BALANCE_AMT IS NOT NULL
                              AND ENDING_CASH_BALANCE_AMT <> 0 THEN 1 END) * 100.0
                 / NULLIF(COUNT(*), 0), 1) AS pct_reconciled
    FROM GOLD_V3_DB.FINANCE.FACT_DAILY_CASH_BALANCE
    WHERE BALANCE_DATE BETWEEN '{start_date}' AND '{end_date}'
      AND EXTRACT(DAYOFWEEK FROM BALANCE_DATE) BETWEEN 1 AND 5
    GROUP BY 1 ORDER BY 1
    """
    return q(sql)

cash_weekly = load_cash_balance_weekly(weeks[0], weeks[-1] + timedelta(days=6))
cash_weekly_dict = week_lookup(cash_weekly, 'WEEK_START', 'PCT_RECONCILED')


# JE %: weekly Supabase_ERP share of unique journal entries (updated 2026-05-22).
@st.cache_data(ttl=600)
def load_je_new_erp_weekly(start_date, end_date):
    sql = f"""
    WITH combined AS (
        SELECT 'ACUMATICA'    AS src,
               TRANSACTION_DATE AS d,
               BATCH_NUMBER     AS je_id
        FROM GOLD_V3_DB.ACUMATICA.STG_ACUMATICA__GL_TRANSACTIONS
        WHERE TRANSACTION_DATE BETWEEN '{start_date}' AND '{end_date}'
        UNION ALL
        SELECT 'SUPABASE_ERP' AS src,
               TRY_TO_DATE(LEFT(CREATED_AT, 10)) AS d,
               JOURNAL_ENTRY_ID AS je_id
        FROM RAW_V2_DB.SUPABASE_ERP.GL_JOURNAL_ENTRY_LINES
        WHERE TRY_TO_DATE(LEFT(CREATED_AT, 10)) BETWEEN '{start_date}' AND '{end_date}'
    )
    SELECT DATEADD('day', -MOD(DAYOFWEEKISO(d)-1, 7), d) AS week_start,
           ROUND(COUNT(DISTINCT CASE WHEN src='SUPABASE_ERP' THEN je_id END) * 100.0
                 / NULLIF(COUNT(DISTINCT je_id), 0), 1) AS pct_new
    FROM combined GROUP BY 1 ORDER BY 1
    """
    return q(sql)

je_weekly = load_je_new_erp_weekly(weeks[0], weeks[-1] + timedelta(days=6))
je_weekly_dict = week_lookup(je_weekly, 'WEEK_START', 'PCT_NEW')


# Sync coverage weekly: daily-average % across the week.
@st.cache_data(ttl=600)
def load_sync_coverage_weekly(start_date, end_date):
    sql = f"""
    WITH active_connectors AS (
        -- Regular-cadence connectors only: 14-day window + ≥2 runs excludes
        -- one-off manual backfills. Upper bound prevents post-period drift.
        SELECT CONNECTOR_ID FROM ETL_METADATA.PUBLIC.SYNC_HISTORY
        WHERE STARTED_AT BETWEEN DATEADD('day', -14, '{end_date}') AND DATEADD('day', 1, '{end_date}'::DATE)
          AND CONNECTOR_ID NOT IN (
              '95e56184-c168-4ef7-9d2d-6da7205e3eaa',  -- Acumatica→Supabase: multi-day cadence by design
              'a404848c-88f1-4ec6-ae99-d360b6c38864'   -- Lunch Money: still in testing
          )
        GROUP BY CONNECTOR_ID
        HAVING COUNT(*) >= 2
    ),
    days AS (
        SELECT DATEADD('day', SEQ4(), '{start_date}'::DATE) AS d
        FROM TABLE(GENERATOR(ROWCOUNT => 50))
        QUALIFY d <= '{end_date}'::DATE
    ),
    daily AS (
        SELECT d.d, COUNT(DISTINCT a.CONNECTOR_ID) AS denom,
               COUNT(DISTINCT CASE WHEN s.COMPLETED_AT BETWEEN TIMESTAMPADD('hour', -24, DATEADD('day', 1, d.d))
                                   AND DATEADD('day', 1, d.d)
                                   AND s.STATUS='completed' THEN s.CONNECTOR_ID END) AS synced
        FROM days d CROSS JOIN active_connectors a
        LEFT JOIN ETL_METADATA.PUBLIC.SYNC_HISTORY s ON s.CONNECTOR_ID = a.CONNECTOR_ID
        GROUP BY d.d
    )
    SELECT DATEADD('day', -MOD(DAYOFWEEKISO(d)-1, 7), d) AS week_start,
           ROUND(AVG(synced * 100.0 / NULLIF(denom, 0)), 1) AS avg_pct
    FROM daily GROUP BY 1 ORDER BY 1
    """
    return q(sql)

sync_weekly = load_sync_coverage_weekly(weeks[0], weeks[-1] + timedelta(days=6))
sync_weekly_dict = week_lookup(sync_weekly, 'WEEK_START', 'AVG_PCT')


# Marketing weekly: cart abandonment + AOV first + unique sessions (3 brands).
@st.cache_data(ttl=600)
def load_marketing_weekly(start_date, end_date):
    # v2: cart-abandon inputs repointed to GOLD_V3_DB.SCORECARD.FCT_MARKETING_WEB_FUNNEL_DAILY
    # (ADD_TO_CARTS / PURCHASES summed across brands); new-users repointed to
    # GOLD_V3_DB.MARKETING.FACT_WEB_SESSIONS (NEW_USERS) since the funnel fact has no
    # new-users column. Contract: WEEK_START, AVG_NEW_USERS, CART_ABANDON_PCT.
    sql = f"""
    WITH overview AS (
        SELECT SESSION_DATE AS d, SUM(NEW_USERS) AS new_users
        FROM GOLD_V3_DB.MARKETING.FACT_WEB_SESSIONS
        WHERE SESSION_DATE BETWEEN '{start_date}' AND '{end_date}'
        GROUP BY 1
    ),
    events AS (
        SELECT EVENT_DATE AS d,
               SUM(ADD_TO_CARTS) AS atc,
               SUM(PURCHASES)    AS purch
        FROM GOLD_V3_DB.SCORECARD.FCT_MARKETING_WEB_FUNNEL_DAILY
        WHERE EVENT_DATE BETWEEN '{start_date}' AND '{end_date}'
        GROUP BY 1
    ),
    merged AS (
        SELECT e.d, o.new_users, e.atc, e.purch
        FROM events e LEFT JOIN overview o ON o.d = e.d
    )
    SELECT DATEADD('day', -MOD(DAYOFWEEKISO(d)-1, 7), d) AS week_start,
           ROUND(AVG(new_users), 0) AS avg_new_users,
           ROUND((SUM(atc) - SUM(purch)) * 100.0 / NULLIF(SUM(atc), 0), 1) AS cart_abandon_pct
    FROM merged GROUP BY 1 ORDER BY 1
    """
    return q(sql)

marketing_weekly = load_marketing_weekly(weeks[0], weeks[-1] + timedelta(days=6))
mkt_new_users_weekly_dict   = week_lookup(marketing_weekly, 'WEEK_START', 'AVG_NEW_USERS')
mkt_cart_abandon_weekly_dict = week_lookup(marketing_weekly, 'WEEK_START', 'CART_ABANDON_PCT')


# AOV First (180d rolling) weekly: average of daily AOV first across the week.
@st.cache_data(ttl=600)
def load_aov_first_180d_weekly(start_date, end_date):
    lookback = (pd.to_datetime(start_date) - pd.Timedelta(days=180)).date()
    sources = " UNION ALL ".join(
        f"SELECT BILLING:email::STRING AS email, DATE(DATE_CREATED) AS d, "
        f"CAST(TOTAL AS FLOAT) AS total, STATUS FROM RAW_V2_DB.{s}.ORDERS"
        for s in ['WOO_GOLDEN_MONK', 'WOO_MIT45', 'WOO_UPRISING']
    )
    sql = f"""
    WITH all_orders AS ({sources}),
    completed AS (
        SELECT email, d, total FROM all_orders
        WHERE status IN ('processing','completed') AND d BETWEEN '{lookback}' AND '{end_date}'
    ),
    classified AS (
        SELECT c.d, c.total,
               (SELECT COUNT(*) FROM completed p WHERE p.email = c.email
                 AND p.d >= DATEADD('day', -180, c.d) AND p.d < c.d) AS prior_180d
        FROM completed c WHERE c.d BETWEEN '{start_date}' AND '{end_date}'
    ),
    daily AS (
        SELECT d, AVG(CASE WHEN prior_180d = 0 THEN total END) AS aov_first
        FROM classified GROUP BY d
    )
    SELECT DATEADD('day', -MOD(DAYOFWEEKISO(d)-1, 7), d) AS week_start,
           ROUND(AVG(aov_first), 2) AS avg_aov_first
    FROM daily WHERE aov_first IS NOT NULL GROUP BY 1 ORDER BY 1
    """
    return q(sql)

aov_first_weekly = load_aov_first_180d_weekly(weeks[0], weeks[-1] + timedelta(days=6))
aov_first_weekly_dict = week_lookup(aov_first_weekly, 'WEEK_START', 'AVG_AOV_FIRST')


# Fulfillment weekly — same Shiphero metrics aggregated by Mon-anchored week.
# On-Time, Same-Day, and median cycle all use the business-window rules
# (see load_fulfillment_daily for the full explanation).
@st.cache_data(ttl=600)
def load_fulfillment_weekly(start_date, end_date):
    # v2 TODO: LEFT ON RAW. The verified GOLD fact FCT_FULFILLMENT_SCORECARD_DAILY can
    # reproduce daily same-day % and median cycle, but the WEEKLY view here needs (a) a
    # true weekly MEDIAN over per-order business-hours — not reconstructable from daily
    # medians — and (b) ON_TIME_PCT, which the GOLD fact does not expose at all. Both
    # would change the metric's shape, so this weekly loader stays on the RAW ShipHero
    # per-order computation. Repoint only once a GOLD weekly fulfillment fact (or per-order
    # cycle grain) exists. (The DAILY fulfillment loader IS repointed to GOLD.)
    df = q(f"""
        WITH holidays(h) AS (
            SELECT * FROM VALUES {_HOLIDAY_VALUES_SQL} AS t(h)
        ),
        cal AS (
            SELECT DATEADD('day', SEQ4(), '2024-01-01'::DATE) AS d
            FROM TABLE(GENERATOR(ROWCOUNT => 1500))
        ),
        cal_biz AS (
            SELECT d, IFF(DAYOFWEEKISO(d) <= 5 AND d NOT IN (SELECT h FROM holidays), 1, 0) AS is_biz
            FROM cal
        ),
        biz_days AS (SELECT d FROM cal_biz WHERE is_biz = 1),
        next_biz AS (
            SELECT c.d AS any_d, MIN(b.d) AS biz_d
            FROM cal c LEFT JOIN biz_days b ON b.d >= c.d
            GROUP BY c.d
        ),
        cal_cum AS (
            SELECT d, is_biz, SUM(is_biz) OVER (ORDER BY d) - is_biz AS cum_biz_before
            FROM cal_biz
        ),
        -- First completed shipment per order, all-time rank (2026-06-12) — see
        -- load_fulfillment_daily for the re-shipment rationale.
        first_ship AS (
            SELECT s.ORDER_ID, s.CREATED_DATE
            FROM RAW_V2_DB.SHIPHERO.SHIPMENTS s
            WHERE s.COMPLETED::BOOLEAN
            QUALIFY ROW_NUMBER() OVER (PARTITION BY s.ORDER_ID ORDER BY s.CREATED_DATE, s.ID) = 1
        ),
        joined AS (
            SELECT DATEADD('day', -MOD(DAYOFWEEKISO(s.CREATED_DATE::DATE)-1, 7), s.CREATED_DATE::DATE) AS week_start,
                   CONVERT_TIMEZONE('UTC','America/Denver', s.CREATED_DATE::TIMESTAMP_NTZ)::DATE       AS ship_d_mt,
                   CONVERT_TIMEZONE('UTC','America/Denver', s.CREATED_DATE::TIMESTAMP_NTZ)            AS ship_mt,
                   -- Hold-aware clock start (2026-06-12) — see load_fulfillment_daily.
                   CONVERT_TIMEZONE('UTC','America/Denver',
                       LEAST(COALESCE(c.CLOCK_START_AT, TO_TIMESTAMP_NTZ(o.ORDER_DATE)),
                             s.CREATED_DATE::TIMESTAMP_NTZ))                                           AS ord_mt,
                   TO_TIMESTAMP_NTZ(o.ORDER_DATE)  AS ord_ts,
                   TO_DATE(o.REQUIRED_SHIP_DATE)   AS req_ship,
                   s.CREATED_DATE::TIMESTAMP_NTZ   AS ship_ts
            FROM first_ship s
            JOIN RAW_V2_DB.SHIPHERO.ORDERS o ON o.ID = s.ORDER_ID
            LEFT JOIN GOLD_V3_DB.FULFILLMENT.ORDER_FULFILLMENT_CYCLE c ON c.ORDER_ID = o.ID
            WHERE s.CREATED_DATE::DATE BETWEEN '{start_date}' AND '{end_date}'
        ),
        targeted AS (
            SELECT j.*,
                   CASE WHEN HOUR(ord_mt) < 13 THEN ord_mt::DATE
                        ELSE DATEADD('day', 1, ord_mt::DATE) END AS naive_target
            FROM joined j
        ),
        final AS (
            SELECT t.*,
                   n.biz_d  AS target_ship_d,
                   nr.biz_d AS effective_req_ship,
                   (t.req_ship <= n.biz_d) AS in_scope,
                   (cb_o.cum_biz_before * 420 + IFF(cb_o.is_biz=1, LEAST(420, GREATEST(0, (HOUR(ord_mt)*60 + MINUTE(ord_mt)) - 480)), 0)) AS ord_biz_min,
                   (cb_s.cum_biz_before * 420 + IFF(cb_s.is_biz=1, LEAST(420, GREATEST(0, (HOUR(ship_mt)*60 + MINUTE(ship_mt)) - 480)), 0)) AS ship_biz_min
            FROM targeted t
            LEFT JOIN next_biz n   ON n.any_d   = t.naive_target
            LEFT JOIN next_biz nr  ON nr.any_d  = t.req_ship
            LEFT JOIN cal_cum  cb_o ON cb_o.d    = t.ord_mt::DATE
            LEFT JOIN cal_cum  cb_s ON cb_s.d    = t.ship_mt::DATE
        )
        SELECT week_start,
               ROUND(100.0 * COUNT(CASE WHEN ship_d_mt <= effective_req_ship THEN 1 END) / NULLIF(COUNT(*),0), 1) AS on_time_pct,
               -- Hit = ship ON OR BEFORE target (<=, 2026-06-12) — early ship never a miss.
               ROUND(100.0 * COUNT(CASE WHEN in_scope AND ship_d_mt <= target_ship_d THEN 1 END) / NULLIF(COUNT_IF(in_scope),0), 1) AS same_day_pct,
               ROUND(MEDIAN((ship_biz_min - ord_biz_min) / 60.0), 1) AS median_hrs
        FROM final GROUP BY week_start ORDER BY week_start
    """)
    return df

fulfill_weekly = load_fulfillment_weekly(weeks[0], weeks[-1] + timedelta(days=6))
fulfill_on_time_weekly_dict  = week_lookup(fulfill_weekly, 'WEEK_START', 'ON_TIME_PCT')
fulfill_same_day_weekly_dict = week_lookup(fulfill_weekly, 'WEEK_START', 'SAME_DAY_PCT')
fulfill_cycle_weekly_dict    = week_lookup(fulfill_weekly, 'WEEK_START', 'MEDIAN_HRS')


# ── DTC OTIF weekly (added 2026-05-26) — same logic as daily, Mon-anchored ───
@st.cache_data(ttl=600)
def load_dtc_otif_weekly(start_date, end_date):
    # v2: repointed to GOLD_V3_DB.SCORECARD.FCT_DTC_OTIF_DAILY (verified fact). Weekly
    # OTIF = SUM(OTIF_ORDERS) / SUM(ORDERS) over the Mon-anchored week — order-weighted,
    # which reproduces the prior per-order weekly OTIF exactly. Contract: WEEK_START, OTIF_PCT.
    df = q(f"""
        SELECT DATEADD('day', -MOD(DAYOFWEEKISO(SHIP_DATE)-1, 7), SHIP_DATE) AS week_start,
               ROUND(100.0 * SUM(OTIF_ORDERS) / NULLIF(SUM(ORDERS), 0), 1) AS otif_pct
        FROM GOLD_V3_DB.SCORECARD.FCT_DTC_OTIF_DAILY
        WHERE SHIP_DATE BETWEEN '{start_date}' AND '{end_date}'
        GROUP BY 1 ORDER BY 1
    """)
    return df

dtc_otif_weekly = load_dtc_otif_weekly(weeks[0], weeks[-1] + timedelta(days=6))
dtc_otif_weekly_dict = week_lookup(dtc_otif_weekly, 'WEEK_START', 'OTIF_PCT')


# ── Weekly Intercom metrics ──────────────────────────────────────────────────
# CSAT rolling 7D as-of end of each week, response time avg, deflection avg
def get_weekly_intercom(week_date):
    """Returns (csat_pct, median_resp, deflection_pct) for a week ending week_date+6."""
    week_end = week_date + timedelta(days=6)
    df = q(f"""
        SELECT
            ROUND(COUNT(CASE WHEN CONVERSATION_RATING:rating::NUMBER >= 4 THEN 1 END) * 100.0
                / NULLIF(COUNT(CASE WHEN CONVERSATION_RATING:rating::NUMBER IS NOT NULL THEN 1 END), 0), 1) AS CSAT_PCT,
            ROUND(MEDIAN(STATISTICS:time_to_admin_reply::NUMBER) / 60.0, 1) AS MEDIAN_RESP_MIN,
            -- Fin AI deflection: Intercom-aligned denominator (finalized 2026-05-06)
            -- Denom = conversations Fin actually attempted (last_answer_type='ai_answer')
            ROUND(COUNT(CASE WHEN AI_AGENT:resolution_state::STRING
                    IN ('assumed_resolution','confirmed_resolution') THEN 1 END) * 100.0
                / NULLIF(COUNT(CASE WHEN AI_AGENT:last_answer_type::STRING = 'ai_answer'
                                    THEN 1 END), 0), 1) AS DEFLECTION_PCT
        FROM RAW_V2_DB.INTERCOM.CONVERSATIONS
        WHERE TO_TIMESTAMP(CREATED_AT)::DATE BETWEEN '{week_date}' AND '{week_end}'
    """)
    if df.empty: return None, None, None
    return (safe_float(df.iloc[0]['CSAT_PCT']) if df.iloc[0]['CSAT_PCT'] is not None else None,
            safe_float(df.iloc[0]['MEDIAN_RESP_MIN']) if df.iloc[0]['MEDIAN_RESP_MIN'] is not None else None,
            safe_float(df.iloc[0]['DEFLECTION_PCT']) if df.iloc[0]['DEFLECTION_PCT'] is not None else None)

weekly_support_cache = {w: get_weekly_intercom(w) for w in weeks}

# ── Manual inputs — aggregate daily entries by week ───────────────────────────
manual_weekly_df = q(f"""
    SELECT
        DATEADD('day', -MOD(DAYOFWEEKISO(METRIC_DATE)-1, 7), METRIC_DATE) AS WEEK_START,
        METRIC_KEY,
        AVG(VALUE) AS VALUE
    FROM GOLD_V3_DB.PUBLIC.MANUAL_SCORECARD_INPUTS
    WHERE METRIC_DATE BETWEEN '{earliest}' AND '{latest}'
    GROUP BY 1, 2
""")

def get_manual_week(metric_key, week_date):
    if manual_weekly_df.empty: return None
    df = manual_weekly_df.copy()
    df['WEEK_START'] = pd.to_datetime(df['WEEK_START']).dt.date
    row = df[(df['METRIC_KEY'] == metric_key) & (df['WEEK_START'] == week_date)]
    if row.empty: return None
    return safe_float(row.iloc[0]['VALUE'])

# ── Table builder ──────────────────────────────────────────────────────────────
def build_weekly_table(sections):
    """
    sections: list of (dept, rows)
    rows: list of (row_num, label, goal_str, get_fn, fmt_fn, color_fn)
      get_fn(week_date) -> value or None
      fmt_fn(v) -> display string
      color_fn(actual, target_or_none) -> css class
    """
    n_weeks = len(weeks)
    cur_idx = n_weeks - 1  # last week = current

    html = ['<table class="wsc-table">']
    # Header
    html.append('<tr>')
    html.append('<th class="left" style="width:28px"></th>')
    html.append('<th class="left" style="min-width:260px">Metric</th>')
    html.append('<th style="width:80px">Target</th>')
    for i, w in enumerate(weeks):
        is_cur = (i == cur_idx)
        cls = 'cur' if is_cur else ''
        label = week_label(w)
        suffix = ' ★' if is_cur else ''
        html.append(f'<th class="{cls}" style="width:85px">{label}{suffix}</th>')
    html.append('<th style="width:70px">Trend</th>')
    html.append('</tr>')

    for dept, rows in sections:
        html.append(f'<tr><td colspan="{n_weeks+4}"><div class="section-hdr">{dept}</div></td></tr>')
        for row_num, label, goal_str, get_fn, fmt_fn, color_fn in rows:
            vals = [get_fn(w) for w in weeks]
            cur_val = vals[cur_idx]
            prev_val = vals[cur_idx - 1] if cur_idx > 0 else None

            cells = []
            for i, v in enumerate(vals):
                is_cur = (i == cur_idx)
                cur_cls = ' cur' if is_cur else ''
                if v is None:
                    cells.append(f'<td class="c-empty{cur_cls}">—</td>')
                else:
                    css = color_fn(v, weeks[i]) if color_fn else 'c-na'
                    display = fmt_fn(v)
                    cells.append(f'<td class="{css}{cur_cls}">{display}</td>')

            # Trend vs prior week
            trend = trend_cell(
                safe_float(cur_val) if cur_val is not None else None,
                safe_float(prev_val) if prev_val is not None else None
            )

            html.append(f'''<tr>
                <td class="left"><span class="row-num">{row_num}</span></td>
                <td class="left">{label}</td>
                <td class="goal">{goal_str}</td>
                {''.join(cells)}
                {trend}
            </tr>''')

    html.append('</table>')
    return ''.join(html)

# ── Define rows ────────────────────────────────────────────────────────────────
def rev_color(actual, week_date, target_key):
    t = get_target(week_date, target_key)
    return color_pct_of_target(actual, t)

def pct_lower_better(v, w, green_thresh, yellow_thresh):
    if v is None: return 'c-empty'
    if v <= green_thresh: return 'c-green'
    if v <= yellow_thresh: return 'c-yellow'
    return 'c-red'

def pct_higher_better(v, w, green_thresh, yellow_thresh):
    if v is None: return 'c-empty'
    if v >= green_thresh: return 'c-green'
    if v >= yellow_thresh: return 'c-yellow'
    return 'c-red'

# Cumulative B2B actual (running total from Q2 start Apr 5)
def get_cumulative_b2b(week_date):
    """MTD cumulative B2B — sums all B2B revenue from start of that week's month
    up through the end of that week (week_date + 6 days), using order_date."""
    week_end = week_date + timedelta(days=6)
    # Anchor the month to the week's Monday (not the end day, to avoid cross-month confusion)
    month_start = week_date.replace(day=1)
    df = q(f"""
        SELECT SUM(NET_REVENUE_AMT) AS CUMULATIVE_B2B
        FROM GOLD_V3_DB.SALES.FACT_ORDERS
        WHERE CHANNEL = 'B2B'
          AND ORDER_DATE::DATE BETWEEN '{month_start}' AND '{week_end}'
    """)
    if df.empty or df.iloc[0]['CUMULATIVE_B2B'] is None: return None
    return safe_float(df.iloc[0]['CUMULATIVE_B2B'])


# ── Weekly email/engagement helpers ──────────────────────────────────────────
def _weekly_email_bucket(week_start, bucket):
    """Returns (avg_per_rep, total) for an email bucket averaged across the week."""
    week_days = [week_start + __import__("datetime").timedelta(days=i) for i in range(5)]
    totals = [outlook_map[d][bucket] for d in week_days if d in outlook_map]
    reps   = [outlook_map[d]["reps"]  for d in week_days if d in outlook_map]
    if not totals: return None
    total = sum(totals)
    avg_reps = round(sum(reps) / len(reps)) if reps else 1
    return (round(total / max(avg_reps, 1), 1), total)

def _weekly_engagements(week_start):
    """Returns (avg_per_rep, total_eng, avg_reps) for Total Engagements for the week.
    Updated 2026-05-11: counts calls + ALL emails (was: calls + future + past only)."""
    week_days = [week_start + __import__("datetime").timedelta(days=i) for i in range(5)]
    ac_data = [aircall_dict[d] for d in week_days if d in aircall_dict]
    em_data = [outlook_map[d] for d in week_days if d in outlook_map]
    calls_total  = sum(int(a[1])    for a in ac_data)
    emails_total = sum(e["total"]   for e in em_data)
    total_eng    = calls_total + emails_total
    # Average active reps across days
    ac_reps  = [round(a[1]/a[0]) for a in ac_data if a[0] > 0]
    em_reps  = [e["reps"] for e in em_data]
    all_reps = [max(ac, em) for ac, em in zip(ac_reps, em_reps)] if ac_reps and em_reps else (ac_reps or em_reps)
    avg_reps = round(sum(all_reps) / len(all_reps)) if all_reps else 1
    days_with_data = len(set([d for d in week_days if d in aircall_dict or d in outlook_map]))
    if days_with_data == 0: return None
    avg_per_rep = round(total_eng / max(avg_reps, 1) / max(days_with_data, 1), 1)
    return (avg_per_rep, total_eng, avg_reps)


def _weekly_emails_per_rep(week_start):
    """Total emails / avg email reps / days-with-data — weekly per-day average for Emails/Rep."""
    week_days = [week_start + __import__("datetime").timedelta(days=i) for i in range(5)]
    em_data = [outlook_map[d] for d in week_days if d in outlook_map]
    if not em_data:
        return None
    total = sum(e["total"] for e in em_data)
    reps_list = [e["reps"] for e in em_data if e["reps"] > 0]
    avg_reps = round(sum(reps_list) / len(reps_list)) if reps_list else 1
    days = len(em_data)
    avg_per_rep = round(total / max(avg_reps, 1) / max(days, 1), 1)
    return (avg_per_rep, total)

# ── Weekly green count — % of weekly metrics that hit their green target ──────
# Computed from weekly aggregates (not avg of daily greens) so historical weeks
# populate from the same data the rest of the weekly view uses.
weekly_green_dict = {}
for w in weeks:
    if w > today:
        continue
    metrics = []

    def cm_w(val, green_fn):
        has = val is not None and str(val) not in ('', 'nan', 'None')
        if has:
            try: metrics.append(bool(green_fn(float(val))))
            except: metrics.append(False)

    # Sales targets (2026-05-11 update): per-channel quotas replace combined target.
    # Calls/Rep weekly avg target = 50/day; Emails/Rep weekly avg target = 40/day.
    calls_w = aircall_weekly_dict.get(w)
    if calls_w is not None:
        metrics.append(safe_float(calls_w) >= 50)
    emails_w = _weekly_emails_per_rep(w)
    if emails_w is not None:
        metrics.append(emails_w[0] >= 40)
    # Sales: AR Past Due, Open Quotes Followup
    cm_w(ar_weekly_dict.get(w),                       lambda v: v <= 103_000)
    cm_w(get_manual_week('OPEN_QUOTES_FOLLOWUP', w),  lambda v: v >= 100)

    # Operations 1-6
    cm_w(labor_dict.get(w),    lambda v: v <= 0.26)
    cm_w(downtime_dict.get(w), lambda v: v <= 15.5)
    cm_w(fpy_dict.get(w),      lambda v: v >= 95)
    cm_w(oee_dict.get(w),      lambda v: v >= 69)
    cm_w(otif_dtc_dict.get(w), lambda v: v >= 97)
    # otif_b2b_dict removed 2026-05-26 — metric moved to Target page Fulfillment.

    # HR 1-3
    cm_w(get_manual_week('HR_PERFORMANCE_DOC', w),     lambda v: v >= 75)
    cm_w(get_manual_week('HR_TRAINING_COMPLIANCE', w), lambda v: v >= 75)
    cm_w(get_manual_week('HR_CAREER_PATH', w),         lambda v: v >= 75)

    # Support 1-5 (CSAT, Median Resp, Total Open, Over48, Deflection)
    csat_w, resp_w, defl_w = weekly_support_cache.get(w, (None, None, None))
    cm_w(csat_w, lambda v: v >= 80)
    cm_w(resp_w, lambda v: v <= 15)
    last_open = next((total_open_dict.get(w + timedelta(days=i)) for i in range(4, -1, -1)
                      if total_open_dict.get(w + timedelta(days=i)) is not None), None)
    last_48   = next((over48_dict.get(w + timedelta(days=i))    for i in range(4, -1, -1)
                      if over48_dict.get(w + timedelta(days=i))    is not None), None)
    cm_w(last_open, lambda v: v < 20)
    cm_w(last_48,   lambda v: v == 0)
    cm_w(defl_w,    lambda v: v >= 50)

    # Business Operations 2-3
    cm_w(clickup_weekly_dict.get(w),               lambda v: v <= 5)
    cm_w(get_manual_week('BLOCKERS_24H', w),       lambda v: v == 0)

    # Marketing — REMOVED 2026-04-29, see top of file
    # mc = mkt_cache.get(w, {})
    # cm_w(mc.get('gm_orders'), lambda v: v >= 9800)
    # cm_w(mc.get('gm_aov'),    lambda v: v >= 84.26)
    # cm_w(mc.get('gm_new'),    lambda v: v >= 637)
    # cm_w(mc.get('mit_orders'), lambda v: v >= 588)
    # cm_w(mc.get('mit_aov'),   lambda v: v >= 205.80)
    # cm_w(mc.get('mit_new'),   lambda v: v >= 147)
    # cm_w(mc.get('up_orders'), lambda v: v >= 441)
    # cm_w(mc.get('up_aov'),    lambda v: v >= 96.04)
    # cm_w(mc.get('up_new'),    lambda v: v >= 49)

    if metrics:
        weekly_green_dict[w] = round(sum(metrics) / len(metrics) * 100, 0)

sections = [
    ("💼 SALES", [
        # Total Engagements row removed 2026-05-11 — explicit per-channel targets are clearer.
        (1, "Calls/Rep (Aircall, day avg)", "50",
         lambda w: aircall_weekly_dict.get(w),
         lambda v: f"{v:.1f}",
         lambda v, w: ('c-green' if v >= 50 else ('c-yellow' if v >= 45 else 'c-red'))),
        (2, "Emails/Rep (Total, day avg)", "40",
         lambda w: _weekly_emails_per_rep(w),
         lambda v: f"{v[0]:.1f} / {v[1]}" if isinstance(v, tuple) else f"{v:.1f}",
         lambda v, w: (
             'c-green'  if (v[0] if isinstance(v, tuple) else v) >= 40
             else ('c-yellow' if (v[0] if isinstance(v, tuple) else v) >= 36
                   else 'c-red')
         )),
        (3, "Emails — New Customers/Rep", "—",
         lambda w: _weekly_email_bucket(w, 'new'),
         lambda v: f"{v[0]:.1f} / {v[1]}" if isinstance(v, tuple) else f"{v:.1f}",
         lambda v, w: 'c-na'),
        (4, "Emails — Existing Customers/Rep", "—",
         lambda w: _weekly_email_bucket(w, 'existing'),
         lambda v: f"{v[0]:.1f} / {v[1]}" if isinstance(v, tuple) else f"{v:.1f}",
         lambda v, w: 'c-na'),
        # Row 5 (2026-05-13): Pipeline Activity Movement — replaces former
        # "Emails — Unknown/Rep" informational row. Daily avg of CRM stage changes.
        (5, "Pipeline Activity Movement (day avg)", "≥20",
         lambda w: pipeline_weekly_dict.get(w),
         lambda v: f"{v:.1f}",
         lambda v, w: 'c-green' if v >= 20 else ('c-yellow' if v >= 10 else 'c-red')),
        (6, "AR Past Due", "$100k",
         lambda w: ar_weekly_dict.get(w),
         fmt_currency,
         lambda v, w: 'c-green' if v <= 103000 else ('c-yellow' if v <= 109000 else 'c-red')),
        (7, "Open Quotes Follow Up (24h)", "100%",
         lambda w: get_manual_week('OPEN_QUOTES_FOLLOWUP', w),
         lambda v: f"{v:.0f}%",
         lambda v, w: 'c-green' if v >= 100 else ('c-yellow' if v >= 80 else 'c-red')),
        (8, "B2B Revenue - C-Store (week)", "Model",
         lambda w: cstore_dict.get(w),
         fmt_currency,
         lambda v, w: rev_color(v, w, 'CSTORE_TARGET')),
        (9, "B2B Revenue - Smoke Shop (week)", "Model",
         lambda w: smokeshop_dict.get(w),
         fmt_currency,
         lambda v, w: rev_color(v, w, 'SMOKESHOP_TARGET')),
        (10, "B2B Revenue - Cumulative (MTD)", "Model",
         get_cumulative_b2b,
         fmt_currency,
         lambda v, w: (
             color_pct_of_target(v, sum(
                 safe_float(r['CSTORE_TARGET']) + safe_float(r['SMOKESHOP_TARGET'])
                 for _, r in targets_df[
                     (pd.to_datetime(targets_df['WEEK_START']).dt.date >= (w - timedelta(days=1)).replace(day=1)) &
                     (pd.to_datetime(targets_df['WEEK_START']).dt.date <= (w - timedelta(days=1)))
                 ].iterrows()
             ) or None)
             if not targets_df.empty and any(
                 pd.to_datetime(targets_df['WEEK_START']).dt.date == (w - timedelta(days=1))
             ) else 'c-neutral'
         )),
    ]),
    # Manufacturing (renamed from "OPERATIONS" 2026-05-14)
    ("🏭 MANUFACTURING", [
        (1, "Labor Cost Per Unit (Liquid)", "$0.25",
         lambda w: labor_dict.get(w),
         lambda v: f"${v:.2f}",
         lambda v, w: 'c-green' if v <= 0.26 else ('c-yellow' if v <= 0.27 else 'c-red')),
        (2, "Unplanned Downtime % (Liquid)", "<=15.5%",
         lambda w: downtime_dict.get(w),
         lambda v: f"{v:.1f}%",
         lambda v, w: 'c-green' if v <= 15.5 else ('c-yellow' if v <= 16.4 else 'c-red')),
        (3, "First Pass Yield", "97%",
         lambda w: fpy_dict.get(w),
         lambda v: f"{v:.1f}%",
         lambda v, w: 'c-green' if v >= 95 else ('c-yellow' if v >= 88 else 'c-red')),
        (4, "OEE", "70%",
         lambda w: oee_dict.get(w),
         lambda v: f"{v:.1f}%",
         lambda v, w: 'c-green' if v >= 69 else ('c-yellow' if v >= 64 else 'c-red')),
        # OTIF D2C moved to Fulfillment 2026-05-14 — renamed "On-Time Ship Rate" there.
        # OTIF B2B (Acumatica-based cycle hours) removed 2026-05-26 — replaced by
        # B2B Cycle Time on the Target page Fulfillment section, using Supabase ERP.
    ]),
    ("👥 HR", [
        (1, "Performance Documentation Rate", ">75%",
         lambda w: get_manual_week('HR_PERFORMANCE_DOC', w),
         lambda v: f"{v:.1f}%",
         lambda v, w: 'c-green' if v >= 75 else ('c-yellow' if v >= 65 else 'c-red')),
        (2, "Training & Compliance Completion Rate", ">75%",
         lambda w: get_manual_week('HR_TRAINING_COMPLIANCE', w),
         lambda v: f"{v:.1f}%",
         lambda v, w: 'c-green' if v >= 75 else ('c-yellow' if v >= 65 else 'c-red')),
        (3, "HR Process Doc Completion Rate", ">75%",
         lambda w: get_manual_week('HR_CAREER_PATH', w),
         lambda v: f"{v:.1f}%",
         lambda v, w: 'c-green' if v >= 75 else ('c-yellow' if v >= 65 else 'c-red')),
    ]),
    ("🎧 SUPPORT", [
        (1, "CSAT — Rolling 7D % Positive", ">80%",
         lambda w: weekly_support_cache.get(w, (None,None,None))[0],
         lambda v: f"{v:.1f}%",
         lambda v, w: 'c-green' if v >= 80 else ('c-yellow' if v >= 73 else 'c-red')),
        (2, "Median First Response Time", "<15 min",
         lambda w: weekly_support_cache.get(w, (None,None,None))[1],
         lambda v: f"{v:.1f}m",
         lambda v, w: 'c-green' if v <= 15 else ('c-yellow' if v <= 30 else 'c-red')),
        (3, "Total Open Tickets", "<20",
         lambda w: next((total_open_dict.get(w + timedelta(days=i)) for i in range(4, -1, -1) if total_open_dict.get(w + timedelta(days=i)) is not None), None),
         lambda v: f"{int(v)}",
         lambda v, w: 'c-green' if v < 20 else ('c-yellow' if v <= 35 else 'c-red')),
        (4, "Tickets Over 48 Hours", "0",
         lambda w: next((over48_dict.get(w + timedelta(days=i)) for i in range(4, -1, -1) if over48_dict.get(w + timedelta(days=i)) is not None), None),
         lambda v: f"{int(v)}",
         lambda v, w: 'c-green' if v == 0 else 'c-red'),
        (5, "Fin AI Deflection Rate", ">50%",
         lambda w: weekly_support_cache.get(w, (None,None,None))[2],
         lambda v: f"{v:.1f}%",
         lambda v, w: 'c-green' if v >= 49 else ('c-yellow' if v >= 45 else 'c-red')),
    ]),
    # Business Operations REMOVED 2026-05-14 per spec.

    # Fulfillment (wired 2026-05-14 from Shiphero — On-Time moved here from Manufacturing)
    ("📦 FULFILLMENT", [
        (1, "On-Time Ship Rate (week)", "≥97%",
         lambda w: fulfill_on_time_weekly_dict.get(w),
         lambda v: f"{v:.1f}%",
         lambda v, w: 'c-green' if v >= 97 else ('c-yellow' if v >= 90 else 'c-red')),
        (2, "Same-Day Ship Rate (week)", "≥80%",
         lambda w: fulfill_same_day_weekly_dict.get(w),
         lambda v: f"{v:.1f}%",
         lambda v, w: 'c-green' if v >= 80 else ('c-yellow' if v >= 60 else 'c-red')),
        (3, "Median Order-to-Ship Cycle (week, hrs)", "≤24h",
         lambda w: fulfill_cycle_weekly_dict.get(w),
         lambda v: f"{v:.0f}h",
         lambda v, w: 'c-green' if v <= 24 else ('c-yellow' if v <= 48 else 'c-red')),
        (4, "DTC OTIF (week)", "≥97%",
         lambda w: dtc_otif_weekly_dict.get(w),
         lambda v: f"{v:.1f}%",
         lambda v, w: 'c-green' if v >= 97 else ('c-yellow' if v >= 90 else 'c-red')),
    ]),

    # Procurement (added 2026-05-14, 3 KPI stubs pending dept-head input)
    ("🛒 PROCUREMENT", [
        (1, "🚧 KPI 1 pending department-head input", "—",
         lambda w: None, lambda v: "—", lambda v, w: 'c-empty'),
        (2, "🚧 KPI 2 pending department-head input", "—",
         lambda w: None, lambda v: "—", lambda v, w: 'c-empty'),
        (3, "🚧 KPI 3 pending department-head input", "—",
         lambda w: None, lambda v: "—", lambda v, w: 'c-empty'),
    ]),
    # ── FINANCE (added 2026-05-13 — mirrors Daily Scorecard Finance section) ──
    ("💰 FINANCE", [
        (1, "Same-Day Cash Reconciliation (% of weekdays)", "100%",
         lambda w: cash_weekly_dict.get(w),
         lambda v: f"{v:.0f}%",
         lambda v, w: 'c-green' if v >= 100 else ('c-yellow' if v >= 80 else 'c-red')),
        (2, "% of JEs in New ERP (Supabase)", "≥50%",
         lambda w: je_weekly_dict.get(w),
         lambda v: f"{v:.1f}%",
         lambda v, w: 'c-green' if v >= 50 else ('c-yellow' if v >= 25 else 'c-red')),
        (3, "% Sources Synced <24 hrs (day avg)", "100%",
         lambda w: sync_weekly_dict.get(w),
         lambda v: f"{v:.0f}%",
         lambda v, w: 'c-green' if v >= 100 else ('c-yellow' if v >= 90 else 'c-red')),
    ]),
    # ── MARKETING (added 2026-05-13 — mirrors Daily Scorecard Marketing section) ──
    ("📈 MARKETING", [
        (1, "Cart Abandonment % (week aggregate)", "≤60%",
         lambda w: mkt_cart_abandon_weekly_dict.get(w),
         lambda v: f"{v:.1f}%",
         lambda v, w: 'c-green' if v <= 60 else ('c-yellow' if v <= 75 else 'c-red')),
        (2, "AOV — First (180d, day avg)", "≥$120",
         lambda w: aov_first_weekly_dict.get(w),
         lambda v: f"${v:,.2f}",
         lambda v, w: 'c-green' if v >= 120 else ('c-yellow' if v >= 75 else 'c-red')),
        (3, "Unique Sessions (day avg)", "≥500",
         lambda w: mkt_new_users_weekly_dict.get(w),
         lambda v: f"{int(v):,}",
         lambda v, w: 'c-green' if v >= 500 else ('c-yellow' if v >= 400 else 'c-red')),
    ]),
    # ("📈 MARKETING — old 90D rollup, REMOVED 2026-04-29", [
    #     (1, "Total DTC Revenue (week)", "Model",
    #      lambda w: dtc_dict.get(w),
    #      fmt_currency,
    #      lambda v, w: rev_color(v, w, 'DTC_TARGET')),
    #     (2, "Goldenmonk - Trailing 90D Orders", "10,000",
    #      lambda w: mkt_cache.get(w, {}).get('gm_orders'),
    #      fmt_num,
    #      lambda v, w: 'c-green' if v >= 9800 else ('c-yellow' if v >= 9100 else 'c-red')),
    #     (3, "Goldenmonk - Trailing 90D AOV", "$85.98",
    #      lambda w: mkt_cache.get(w, {}).get('gm_aov'),
    #      lambda v: f"${v:.2f}",
    #      lambda v, w: 'c-green' if v >= 84.26 else ('c-yellow' if v >= 78.24 else 'c-red')),
    #     (4, "Goldenmonk - Trailing 90D First-Time Buyers", "650",
    #      lambda w: mkt_cache.get(w, {}).get('gm_new'),
    #      fmt_num,
    #      lambda v, w: 'c-green' if v >= 637 else ('c-yellow' if v >= 591.5 else 'c-red')),
    #     (5, "MIT45 - Trailing 90D Orders", "600",
    #      lambda w: mkt_cache.get(w, {}).get('mit_orders'),
    #      fmt_num,
    #      lambda v, w: 'c-green' if v >= 588 else ('c-yellow' if v >= 546 else 'c-red')),
    #     (6, "MIT45 - Trailing 90D AOV", "$210",
    #      lambda w: mkt_cache.get(w, {}).get('mit_aov'),
    #      lambda v: f"${v:.2f}",
    #      lambda v, w: 'c-green' if v >= 205.80 else ('c-yellow' if v >= 191.10 else 'c-red')),
    #     (7, "MIT45 - Trailing 90D First-Time Buyers", "150",
    #      lambda w: mkt_cache.get(w, {}).get('mit_new'),
    #      fmt_num,
    #      lambda v, w: 'c-green' if v >= 147 else ('c-yellow' if v >= 136.5 else 'c-red')),
    #     (8, "Uprising - Trailing 90D Orders", "450",
    #      lambda w: mkt_cache.get(w, {}).get('up_orders'),
    #      fmt_num,
    #      lambda v, w: 'c-green' if v >= 441 else ('c-yellow' if v >= 409.5 else 'c-red')),
    #     (9, "Uprising - Trailing 90D AOV", "$98",
    #      lambda w: mkt_cache.get(w, {}).get('up_aov'),
    #      lambda v: f"${v:.2f}",
    #      lambda v, w: 'c-green' if v >= 96.04 else ('c-yellow' if v >= 89.18 else 'c-red')),
    #     (10,"Uprising - Trailing 90D First-Time Buyers", "50",
    #      lambda w: mkt_cache.get(w, {}).get('up_new'),
    #      fmt_num,
    #      lambda v, w: 'c-green' if v >= 49 else ('c-yellow' if v >= 45.5 else 'c-red')),
    # ]),
]


# ══════════════════════════════════════════════════════════════════════════════
# ── RENDER ────────────────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

# ── Data-freshness banner — warn when a feed has stalled so stale days don't
# silently read as 0/NO (Pipeline Activity Movement, Same-Day Cash Rec). Renders
# above the tab strip so it's visible on every view. ───────────────────────────
def _prev_business_day(d):
    p = d - timedelta(days=1)
    while p.weekday() >= 5:  # Sat=5, Sun=6
        p -= timedelta(days=1)
    return p

_stale_msgs = []

# (ClickUp snapshot check removed 2026-06-03 — Pipeline Activity Movement now
# reads TASK_STATUS_HISTORY, which self-backfills gaps, so snapshot freshness no
# longer affects anything rendered in the combined card.)

# SharePoint cash feed: reconciliation loads ~1 business day late. Warn when the
# latest real balance is older than the previous business day.
_cash_last = feed_freshness.get('cash_balance', {}).get('last_data')
_cash_sync = feed_freshness.get('cash_balance', {}).get('last_sync')
if _cash_last:
    _cash_last_d = pd.to_datetime(_cash_last).date()
    if _cash_last_d < _prev_business_day(today):
        _sync_txt = ''
        if _cash_sync:
            _sync_txt = f" (feed last synced {pd.to_datetime(_cash_sync):%b %d %H:%M})"
        _stale_msgs.append(
            f"**Cash feed** latest reconciled balance is **{_cash_last_d:%a %b %d}**"
            f"{_sync_txt} — newer 'Same-Day Cash Rec = NO' cells are *not-yet-loaded*, "
            f"not genuine misses. Chase the SharePoint sync, not Finance."
        )

# Marketing D2C revenue: Gold FACT_DAILY_REVENUE lags ~1 business day, while raw
# WooCommerce is real-time — so a stalled Gold build reads as $0 MTD even while
# orders are flowing. Warn when the latest DTC day is older than the prev biz day.
_mkt_last = feed_freshness.get('mktg_dtc_rev', {}).get('last_data')
if _mkt_last:
    _mkt_last_d = pd.to_datetime(_mkt_last).date()
    if _mkt_last_d < _prev_business_day(today):
        _stale_msgs.append(
            f"**Marketing revenue feed** (Gold FACT_DAILY_REVENUE, DTC) latest day is "
            f"**{_mkt_last_d:%a %b %d}** — Marketing Revenue MTD reads low/$0 while raw "
            f"WooCommerce orders are still flowing. The Gold daily-revenue build has stalled."
        )

if _stale_msgs:
    st.warning("⚠️ **Stale data feed(s) detected:**\n\n" + "\n\n".join(f"- {m}" for m in _stale_msgs))

tab_daily, tab_weekly, tab_target, tab_mbr, tab_sales, tab_help, tab_input = st.tabs([
    "📊 Daily Scorecard",
    "📅 Weekly Scorecard",
    "🎯 Target",
    "📘 MBR",
    "👥 Sales Reps",
    "❓ Help",
    "✏️ Input"
])

# ── DAILY SCORECARD TAB ───────────────────────────────────────────────────────
with tab_daily:
    # Week navigation
    nav_col1, nav_col2, nav_col3 = st.columns([1, 1, 7])
    with nav_col1:
        if st.button("◀ Prev Week"):
            st.session_state.week_offset -= 1
            st.rerun()
    with nav_col2:
        if st.session_state.week_offset < 0:
            if st.button("Current Week"):
                st.session_state.week_offset = 0
                st.rerun()

    st.markdown(f"""
    <div class="sc-header">
        <span class="sc-title">Daily Metrics Scorecard</span>
        <span class="sc-subtitle">Week of {mon.strftime('%b %d, %Y')}{' &nbsp;·&nbsp; <span style="color:#e8c43a;font-size:11px;">HISTORICAL VIEW</span>' if st.session_state.week_offset < 0 else ''}</span>
        <span class="sc-deadline">⏰ Deadline: 10 p.m. CST</span>
    </div>
    <div class="legend-row">
        <span class="leg"><span class="leg-dot" style="background:{T['g_bg']};border:1px solid {T['g_fg']};"></span>Green — at or above goal</span>
        <span class="leg"><span class="leg-dot" style="background:{T['y_bg']};border:1px solid {T['y_fg']};"></span>Yellow — near goal</span>
        <span class="leg"><span class="leg-dot" style="background:{T['r_bg']};border:1px solid {T['r_fg']};"></span>Red — below goal</span>
        <span class="leg"><span class="leg-dot" style="background:{T['border']};"></span>— No data</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(build_table_html(rows), unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style="margin-top:20px; padding:10px 14px; border:1px solid #2d2d2d; border-radius:6px;
         background:#111; font-size:11px; color:#666; font-family:'IBM Plex Mono',monospace;">
        Data refreshed: {date.today().strftime('%Y-%m-%d')} &nbsp;·&nbsp;
        Production: SV_DAILY_PRODUCTION (Liquid lots only) &nbsp;·&nbsp;
        OTIF DTC: STG_SHIPHERO on-time % (100 − late rate) vs REQUIRED_SHIP_DATE &nbsp;·&nbsp;
        B2B Cycle: SV_SALES_ORDER_ANALYSIS &nbsp;·&nbsp;
        HR: RAW_V2_DB.ASHBY (hourly) &nbsp;·&nbsp;
        Marketing: RAW WOO_GOLDEN_MONK / WOO_MIT45 (processing+completed, real-time) &nbsp;·&nbsp;
        AR: Supabase_ERP.INVOICES &nbsp;·&nbsp;
        Sales / Biz Ops / F&A: manual entry or pending data source
    </div>
    """, unsafe_allow_html=True)
    

# ── WEEKLY SCORECARD TAB ──────────────────────────────────────────────────────
with tab_weekly:
    st.markdown(f"""
    <div class="sc-header">
        <span class="sc-title">Q2 Weekly Metrics Scorecard</span>
        <span class="sc-subtitle">Last 6 weeks + current &nbsp;·&nbsp; ★ = current week &nbsp;·&nbsp; Trend vs prior week</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(build_weekly_table(sections), unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style="margin-top:16px; padding:10px 14px; border:1px solid {T['border']}; border-radius:6px;
         background:{T['bg3']}; font-size:11px; color:{T['text3']}; font-family:'IBM Plex Mono',monospace;">
        Revenue targets from Q2 April Forecast model &nbsp;·&nbsp;
        B2B actuals: FACT_ORDERS (Acumatica) &nbsp;·&nbsp;
        DTC actuals: RAW WooCommerce &nbsp;·&nbsp;
        Ops: SV_DAILY_PRODUCTION (weekly avg) &nbsp;·&nbsp;
        Trailing 90D marketing metrics: coming soon &nbsp;·&nbsp;
        Color: green ≥97% of target, yellow ≥85%, red &lt;85%
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# v7 TARGET PAGE BUILDERS (2026-05-18)
# ══════════════════════════════════════════════════════════════════════════════
# Mirrors scorecard-tv/pdf_friday_digest_v2.py — same 3-bucket layout, letter
# grades at Company/Bucket/Dept, KPI-level heat map with plain X/5 weekly
# tallies (no letter), lagging block with vertical pill bars + no grade pills.
# Binary red/green (≥80% green threshold), Customer Support + People & Culture
# rename, Procurement KPIs render values but stay unscored until targets land.

import re as _v7_re

BUCKETS_V7 = [
    ('Revenue',    ['Sales', 'Marketing']),
    ('Operations', ['Procurement', 'Manufacturing', 'Fulfillment', 'Customer Support']),
    ('G&A',        ['Finance', 'People & Culture']),
]


def _v7_letter(ratio):
    p = ratio * 100
    if p >= 90: return 'A', 'grn'
    if p >= 80: return 'B', 'grn'
    if p >= 70: return 'C', 'red'
    if p >= 60: return 'D', 'red'
    return 'F', 'red'


def _v7_clean_float(v):
    """Coerce to float, returning None for None/NaN/non-numeric. NaN must be
    excluded explicitly — `v is not None` lets NaN through and poisons any
    sum/avg (e.g. a day with a production row but null OEE)."""
    if v is None: return None
    try: f = float(v)
    except (TypeError, ValueError): return None
    if f != f: return None  # NaN
    return f


def _v7_mtd_avg(d):
    if not d: return None
    vals = [f for f in (_v7_clean_float(v) for v in d.values()) if f is not None]
    if not vals: return None
    return sum(vals) / len(vals)


def _v7_latest(d):
    if not d: return None
    for dt in sorted(d.keys(), reverse=True):
        f = _v7_clean_float(d[dt])
        if f is not None: return f
    return None


def _v7_parse_target(label):
    """Parse a target label like '≤ $100k weekly' into (direction, num)."""
    if not label: return (None, None)
    s = label.strip()
    if 'all days reconciled' in s.lower():
        return ('binary', 1)
    direction = None
    if s.startswith('≤') or s.startswith('<='):
        direction = '<='
        rest = s.lstrip('≤<= ').strip()
    elif s.startswith('≥') or s.startswith('>='):
        direction = '>='
        rest = s.lstrip('≥>= ').strip()
    else:
        # Assume "100% daily" style (≥ implied)
        direction = '>='
        rest = s
    m = _v7_re.search(r"\$?([\d,]+(?:\.\d+)?)([kKmM]?)", rest)
    if not m: return (direction, None)
    try:
        num = float(m.group(1).replace(',', ''))
    except ValueError:
        return (direction, None)
    suffix = m.group(2).lower()
    if suffix == 'k': num *= 1_000
    elif suffix == 'm': num *= 1_000_000
    return (direction, num)


def _v7_fmt_current(val, target_label):
    """Format a current value using formatting cues from target_label."""
    s = target_label or ''
    if val is None: return '—'
    if '$' in s and ('k' in s.lower() or 'm' in s.lower()):
        return f"${val:,.0f}"
    if '$' in s:
        return f"${val:.2f}"
    if 'min' in s.lower():
        return f"{val:.1f} min"
    if 'hrs' in s.lower() or 'hr' in s.lower():
        return f"{val:.0f} hrs"
    if '%' in s:
        return f"{val:.1f}%"
    if '/day' in s.lower():
        return f"{val:.0f}"
    return f"{val:.1f}"


def _v7_vbar(value, target, direction, on_pace=None):
    """Vertical pill bar with tick at 100% target mark. Returns (html, color_cls)."""
    if value is None or target is None or target == 0:
        return ('<div class="v7-vbar"></div>', 'neu')
    value = float(value); target = float(target)
    ratio = value / target
    max_visual = 1.4
    fill_pct = min(max(ratio, 0), max_visual) / max_visual * 100
    tick_pct = 100.0 / max_visual
    if direction == 'cumulative':
        cls = 'good' if on_pace else 'bad'
    elif direction == '>=':
        cls = 'good' if ratio >= 1.0 else 'bad'
    elif direction == '<=':
        cls = 'good' if ratio <= 1.0 else 'bad'
    elif direction == 'binary':
        cls = 'good' if value == 1 else 'bad'
    else:
        cls = 'neu'
    return (f'<div class="v7-vbar"><div class="v7-fill v7-{cls}" style="height:{fill_pct:.0f}%"></div>'
            f'<div class="v7-tick" style="bottom:{tick_pct:.0f}%"></div></div>', cls)


def build_target_v7_heatmap_html():
    """Heat map: bucket → dept cards → KPI rows with day cells.
    Uses module-level target_rows (already updated to v7 dept names + procurement)."""
    by_dept = {}
    for r in target_rows:
        by_dept.setdefault(r[0], []).append(r)

    dept_stats = {}
    for _bucket_name, dept_list in BUCKETS_V7:
        for dept in dept_list:
            rows = by_dept.get(dept, [])
            nm = len(rows)
            cells_by_metric = [[] for _ in rows]
            green_count = [0] * nm
            scored_days = [0] * nm
            mfg_skip_friday = (dept == 'Manufacturing')
            skip_holidays = (dept in HOLIDAY_BLANK_DEPTS)
            for d in days:
                d_is_holiday = (d in US_SHIP_HOLIDAYS_SET)
                for mi, r in enumerate(rows):
                    if (d > today
                        or (mfg_skip_friday and d.weekday() == 4)
                        or (skip_holidays and d_is_holiday)):
                        cells_by_metric[mi].append(('—', 'neu'))
                        continue
                    try:
                        val = r[4](d)
                        # Treat NaN/blank as no-data so empty cells render '—'
                        # instead of 'nan%' (e.g. a day with a production row
                        # but null OEE/Labor before the floor logs totals).
                        if val is None or str(val) in ('', 'nan', 'None'):
                            display, css_old = '—', 'c-empty'
                        else:
                            display, css_old = r[5](val)
                    except Exception:
                        display, css_old = '—', 'c-empty'
                    css = ('good' if css_old == 'c-green'
                           else 'warn' if css_old == 'c-yellow'
                           else 'bad' if css_old == 'c-red'
                           else 'neu')
                    cells_by_metric[mi].append((display, css))
                    if css == 'good':
                        green_count[mi] += 1; scored_days[mi] += 1
                    elif css in ('warn', 'bad'):
                        scored_days[mi] += 1
            dept_stats[dept] = {
                'rows': rows, 'nm': nm,
                'cells_by_metric': cells_by_metric,
                'green_count': green_count, 'scored_days': scored_days,
                'dept_green': sum(green_count), 'dept_scored': sum(scored_days),
                'is_procurement': (dept == 'Procurement'),
            }

    bucket_stats = {}
    co_green, co_scored = 0, 0
    for bucket_name, dept_list in BUCKETS_V7:
        bg, bs = 0, 0
        for dept in dept_list:
            s = dept_stats[dept]
            # Procurement now has real thresholds (v9, 2026-05-22) — counts toward totals.
            bg += s['dept_green']; bs += s['dept_scored']
        bucket_stats[bucket_name] = (bg, bs)
        co_green += bg; co_scored += bs

    week_lbl = f"{days[0].strftime('%b %d')}–{days[4].strftime('%b %d, %Y')}"
    parts = [
        f'<div class="v7-banner">DAILY HEAT MAP &nbsp;·&nbsp; WEEK OF {week_lbl.upper()}</div>',
        '<div class="v7-grade-summary">',
    ]
    co_ratio = (co_green / co_scored) if co_scored > 0 else 0
    co_letter, co_cls = _v7_letter(co_ratio) if co_scored else ('—', 'neu')
    parts.append(
        f'<div class="v7-gs-card v7-{co_cls}"><div class="v7-gs-label">Company Grade</div>'
        f'<div class="v7-gs-row"><div class="v7-gs-letter v7-{co_cls}">{co_letter}</div>'
        f'<div><div class="v7-gs-pct">{co_ratio*100:.0f}%</div>'
        f'<div class="v7-gs-frac">{co_green} of {co_scored} cells green</div></div></div></div>'
    )
    for bucket_name, _dl in BUCKETS_V7:
        bg, bs = bucket_stats[bucket_name]
        if bs > 0:
            br = bg / bs
            bl, bcls = _v7_letter(br)
            pct = f"{br*100:.0f}%"; frac = f"{bg} of {bs}"
        else:
            bl, bcls, pct, frac = '—', 'neu', '—', '—'
        parts.append(
            f'<div class="v7-gs-card v7-{bcls}"><div class="v7-gs-label">{bucket_name}</div>'
            f'<div class="v7-gs-row"><div class="v7-gs-letter v7-{bcls}">{bl}</div>'
            f'<div><div class="v7-gs-pct">{pct}</div><div class="v7-gs-frac">{frac}</div></div></div></div>'
        )
    parts.append('</div>')

    for bucket_name, dept_list in BUCKETS_V7:
        bg, bs = bucket_stats[bucket_name]
        if bs > 0:
            br = bg / bs
            bl, bcls = _v7_letter(br)
            bucket_pill = (f'<div class="v7-grade-pill v7-grade-{bcls} v7-grade-big">'
                           f'<span class="v7-ltr">{bl}</span><span class="v7-frc">{bg}/{bs} · {br*100:.0f}%</span></div>')
        else:
            bucket_pill = '<div class="v7-grade-pill v7-grade-neu v7-grade-big"><span class="v7-ltr">—</span><span class="v7-frc">—</span></div>'
        sublabel = ' · '.join(dept_list)
        parts.append(
            f'<div class="v7-bucket"><div class="v7-bucket-head">'
            f'<div><span class="v7-label">{bucket_name.upper()}</span>'
            f'<span class="v7-sublabel">{sublabel}</span></div>{bucket_pill}</div>'
        )
        for dept in dept_list:
            s = dept_stats[dept]
            if s['nm'] == 0: continue
            if s['dept_scored'] > 0:
                dr = s['dept_green'] / s['dept_scored']
                dl, dcls = _v7_letter(dr)
                dept_pill = (f'<div class="v7-grade-pill v7-grade-{dcls}"><span class="v7-ltr">{dl}</span>'
                             f'<span class="v7-frc">{s["dept_green"]}/{s["dept_scored"]} · {dr*100:.0f}%</span></div>')
            else:
                dept_pill = '<div class="v7-grade-pill v7-grade-neu"><span class="v7-ltr">—</span><span class="v7-frc">—</span></div>'
            parts.append(
                f'<div class="v7-heat-card"><div class="v7-heat-dept-head">'
                f'<div class="v7-dept-name">{dept}</div>{dept_pill}</div>'
                '<div class="v7-heat-colhead"><div>Metric</div>'
            )
            for d in days:
                parts.append(
                    f'<div class="v7-day"><div class="v7-dow">{d.strftime("%a").upper()}</div>'
                    f'<div class="v7-dt">{d.strftime("%b %d")}</div></div>'
                )
            parts.append('<div style="text-align:right">Weekly</div></div>')
            for mi, r in enumerate(s['rows']):
                name = r[2]
                cell_html = ''
                for display, css in s['cells_by_metric'][mi]:
                    cell_html += f'<div class="v7-heat-cell v7-{css}">{display}</div>'
                gn, sd = s['green_count'][mi], s['scored_days'][mi]
                if sd == 0:
                    tally = '<span class="v7-pill v7-neu">—/5</span>'
                else:
                    cls = 'good' if (gn / sd) >= 0.80 else 'bad'
                    tally = f'<span class="v7-pill v7-{cls}">{gn}/{sd}</span>'
                parts.append(
                    f'<div class="v7-heat-row"><div class="v7-heat-kpi">{name}</div>'
                    f'{cell_html}<div class="v7-heat-weekly">{tally}</div></div>'
                )
            parts.append('</div>')
        parts.append('</div>')
    return ''.join(parts)


def build_target_v7_lagging_html():
    """Lagging block: bucket → dept cards → metric rows with vertical bars.
    Columns: Metric → Target → Current → % to Goal → Status. No grade pills."""
    by_dept = {}
    for r in lagging_rows:
        by_dept.setdefault(r[0], []).append(r)

    _month_start = today.replace(day=1)
    _next_month_first = (_month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
    days_in_month = (_next_month_first - _month_start).days
    days_elapsed = (today - _month_start).days + 1
    pace = days_elapsed / days_in_month if days_in_month else 0

    parts = [
        f'<div class="v7-banner" style="margin-top:20px;">MONTHLY PACE — LAGGING INDICATORS '
        f'&nbsp;·&nbsp; {today.strftime("%B %Y").upper()} (Day {today.day} of {days_in_month})</div>'
    ]
    for bucket_name, dept_list in BUCKETS_V7:
        sublabel = ' · '.join(dept_list)
        parts.append(
            f'<div class="v7-bucket"><div class="v7-bucket-head">'
            f'<div><span class="v7-label">{bucket_name.upper()}</span>'
            f'<span class="v7-sublabel">{sublabel}</span></div></div>'
        )
        for dept in dept_list:
            rows = by_dept.get(dept, [])
            if not rows: continue
            parts.append(
                f'<div class="v7-card"><div class="v7-card-head">'
                f'<div><div class="v7-dept-name">{dept}</div>'
                f'<div class="v7-dept-meta">{len(rows)} lagging metrics</div></div></div>'
                '<div class="v7-colhead"><div>Metric</div><div>Target</div><div>Current</div>'
                '<div style="text-align:center">% to Goal</div>'
                '<div style="text-align:center">Status</div></div>'
            )
            for r in rows:
                _dept_lbl, name, mode, getter, target_label, _threshold = r
                if mode == 'pending':
                    val = _v7_latest(getter) if getter else None
                    cur_disp = _v7_fmt_current(val, name) if val is not None else '—'
                    if val is not None:
                        if 'DSO' in name: cur_disp = f"{val:.0f} days"
                        elif '%' in name: cur_disp = f"{val:.1f}%"
                    parts.append(
                        f'<div class="v7-row"><div class="v7-metric-name">{name}</div>'
                        f'<div class="v7-metric-target" style="color:#64748b">{target_label}</div>'
                        f'<div class="v7-metric-current">{cur_disp}</div>'
                        '<div class="v7-pace"><div class="v7-num v7-neu">awaiting</div><div class="v7-vbar"></div></div>'
                        '<div style="text-align:center"><span class="v7-status v7-neu">Awaiting target</span></div></div>'
                    )
                    continue
                if mode == 'cumulative_b2b':
                    mtd, tgt_num, _p = _build_cumulative_b2b()
                    bar_pct = (mtd / tgt_num) if tgt_num else 0
                    on_pace = bar_pct >= pace
                    bar_html, cls = _v7_vbar(mtd, tgt_num, 'cumulative', on_pace=on_pace)
                    cur_disp = f"${mtd:,.0f}"
                    tgt_disp = f"≥ ${tgt_num:,.0f} / mo"
                    pct_num = bar_pct * 100
                    status = 'On pace' if on_pace else 'Behind pace'
                elif mode == 'cumulative_marketing':
                    mtd, tgt_num, _p = _build_cumulative_marketing()
                    bar_pct = (mtd / tgt_num) if tgt_num else 0
                    on_pace = bar_pct >= pace
                    bar_html, cls = _v7_vbar(mtd, tgt_num, 'cumulative', on_pace=on_pace)
                    cur_disp = f"${mtd:,.0f}"
                    tgt_disp = f"≥ ${tgt_num:,.0f} / mo"
                    pct_num = bar_pct * 100
                    status = 'On pace' if on_pace else 'Behind pace'
                else:  # 'rate'
                    val = _v7_mtd_avg(getter) if getter else None
                    direction, tgt_num = _v7_parse_target(target_label)
                    tgt_disp = target_label
                    if val is None or tgt_num is None:
                        bar_html, cls = '<div class="v7-vbar"></div>', 'neu'
                        cur_disp = '—'; pct_num = 0; status = 'No data'
                    elif direction == 'binary':
                        # Same-Day Cash Rec: 1 if all reconciled, fraction if not.
                        # _v7_mtd_avg returns the avg of 0/1 values → effectively pass rate.
                        bar_html, cls = _v7_vbar(val, 1.0, '>=')
                        cur_disp = f"{val*100:.0f}%"
                        pct_num = val * 100
                        status = 'All reconciled' if val >= 1.0 else 'Days missed'
                    else:
                        bar_html, cls = _v7_vbar(val, tgt_num, direction)
                        cur_disp = _v7_fmt_current(val, target_label)
                        # DSI composite: surface critical-stockout exposure inside the runway cell
                        # so "165 days · ⚠ 4/190 critical" tells both aggregate-health and outlier
                        # stories. Added 2026-05-22 per user request.
                        # GM-only scope (2026-05-22): MIT45 + Uprising stockout counts dropped.
                        if 'DSI' in name and 'Combined' in name:
                            crit = _v7_latest(proc_critical_stockout_gm) or 0
                            total_skus = _v7_latest(proc_total_active_skus_dict)
                            if crit > 0 and total_skus:
                                cur_disp = f"{val:.0f} days · ⚠ {int(crit)}/{int(total_skus)} critical"
                            elif crit > 0:
                                cur_disp = f"{val:.0f} days · ⚠ {int(crit)} critical"
                            elif total_skus:
                                cur_disp = f"{val:.0f} days · 0/{int(total_skus)} critical"
                            else:
                                cur_disp = f"{val:.0f} days"
                        pct_num = (val / tgt_num) * 100 if tgt_num else 0
                        if direction == '>=':
                            status = 'Above floor' if cls == 'good' else 'Below floor'
                        else:
                            status = 'Under ceiling' if cls == 'good' else 'Over ceiling'
                parts.append(
                    f'<div class="v7-row"><div class="v7-metric-name">{name}</div>'
                    f'<div class="v7-metric-target">{tgt_disp}</div>'
                    f'<div class="v7-metric-current">{cur_disp}</div>'
                    f'<div class="v7-pace"><div class="v7-num v7-{cls}">{pct_num:.0f}%</div>{bar_html}</div>'
                    f'<div style="text-align:center"><span class="v7-status v7-{cls}">{status}</span></div></div>'
                )
            parts.append('</div>')
        parts.append('</div>')
    return ''.join(parts)


# ── TARGET TAB ────────────────────────────────────────────────────────────────
with tab_target:
    # ── v7 redesign (2026-05-18) — mirrors scorecard-tv/pdf_friday_digest_v2.py ─
    # 3 buckets (Revenue / Operations / G&A), KPI-level heat map with letter
    # grades at Company/Bucket/Dept, lagging block with vertical pill bars and
    # no grade pills. Binary red/green (≥80% green threshold). Scoped to .td-v7
    # wrapper so it doesn't bleed into other tabs.
    st.markdown("""
    <style>
        .td-v7 {
            background: #0b1220;
            padding: 18px 14px 28px 14px;
            margin: -8px -10px 0 -10px;
            border-radius: 6px;
            font-family: -apple-system, "SF Pro Text", "IBM Plex Sans", system-ui, sans-serif;
            font-size: 13px; line-height: 1.45; color: #e2e8f0;
        }
        /* High-specificity override to beat Streamlit's global light-theme rule. */
        .td-v7 span, .td-v7 p, .td-v7 label, .td-v7 b, .td-v7 div { color: inherit; }

        .v7-banner {
            background: linear-gradient(90deg, rgba(253,164,175,0.10), transparent 70%);
            border-left: 3px solid #fda4af;
            padding: 10px 14px; margin: 12px 0 12px;
            font-size: 13px; letter-spacing: 0.10em; text-transform: uppercase;
            color: #e2e8f0; font-weight: 600;
        }

        /* Grade summary card row */
        .v7-grade-summary {
            display: grid; grid-template-columns: 1.35fr 1fr 1fr 1fr;
            gap: 10px; margin: 0 0 16px;
        }
        .v7-gs-card {
            border: 1px solid; border-radius: 12px; padding: 10px 14px;
            background: #111a2e; display: flex; flex-direction: column; gap: 6px;
        }
        .v7-gs-card.v7-red { border-color: rgba(239,68,68,0.55); background: rgba(239,68,68,0.10); }
        .v7-gs-card.v7-grn { border-color: rgba(34,197,94,0.55); background: rgba(34,197,94,0.10); }
        .v7-gs-card.v7-neu { border-color: rgba(100,116,139,0.55); background: rgba(100,116,139,0.10); }
        .v7-gs-label { font-size: 10px; letter-spacing: 0.14em; text-transform: uppercase; color: #94a3b8; }
        .v7-gs-row { display: flex; align-items: baseline; gap: 12px; }
        .v7-gs-letter { font-size: 36px; font-weight: 800; line-height: 0.9; letter-spacing: -0.02em; }
        .v7-gs-letter.v7-red { color: #f87171; }
        .v7-gs-letter.v7-grn { color: #4ade80; }
        .v7-gs-letter.v7-neu { color: #94a3b8; font-size: 26px; }
        .v7-gs-pct { color: #e2e8f0; font-size: 15px; font-weight: 700; line-height: 1; }
        .v7-gs-frac { color: #94a3b8; font-size: 11px; font-weight: 500; margin-top: 2px; }

        /* Card chrome */
        .v7-card {
            background: #111a2e; border: 1px solid #1e293b; border-radius: 12px;
            padding: 12px 16px; margin: 6px 0;
        }
        .v7-card-head {
            display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 8px;
        }
        .v7-dept-name { font-size: 14px; font-weight: 600; color: #e2e8f0; }
        .v7-dept-meta { color: #94a3b8; font-size: 11px; margin-top: 1px; }

        .v7-grade-pill {
            font-weight: 700; font-size: 12px; padding: 4px 10px; border-radius: 10px;
            border: 1px solid; white-space: nowrap; display: inline-flex; align-items: center; gap: 6px;
        }
        /* !important needed on all <span> color rules below — Streamlit's global
           ".stApp span { color: <light> !important }" otherwise wipes out the
           letter / fraction / status / tally colors against the dark theme. */
        .v7-grade-pill .v7-ltr { font-size: 15px; font-weight: 800; line-height: 1; }
        .v7-grade-pill .v7-frc { font-size: 11px; color: #94a3b8 !important; font-weight: 600; }
        .v7-grade-red { background: rgba(239,68,68,0.10); border-color: rgba(239,68,68,0.55); color: #f87171; }
        .v7-grade-red .v7-ltr { color: #f87171 !important; }
        .v7-grade-grn { background: rgba(34,197,94,0.10); border-color: rgba(34,197,94,0.55); color: #4ade80; }
        .v7-grade-grn .v7-ltr { color: #4ade80 !important; }
        .v7-grade-neu { background: rgba(100,116,139,0.10); border-color: rgba(100,116,139,0.55); color: #94a3b8; }
        .v7-grade-neu .v7-ltr { color: #94a3b8 !important; }
        .v7-grade-big { padding: 5px 14px; }
        .v7-grade-big .v7-ltr { font-size: 18px; }
        .v7-grade-big .v7-frc { font-size: 11.5px; }

        /* Bucket wrapper */
        .v7-bucket {
            background: #0d1426; border: 1px solid #243049;
            border-radius: 14px; padding: 6px 12px 10px; margin: 0 0 16px;
        }
        .v7-bucket-head {
            display: flex; align-items: center; justify-content: space-between;
            padding: 10px 4px 8px; border-bottom: 1px solid #243049; margin-bottom: 8px;
        }
        .v7-bucket-head .v7-label { font-size: 16px; font-weight: 700; letter-spacing: 0.04em; color: #e2e8f0 !important; }
        .v7-bucket-head .v7-sublabel { color: #94a3b8 !important; font-size: 11px; margin-left: 10px; }
        .v7-bucket .v7-card { margin: 6px 0; }
        .v7-bucket .v7-heat-card { margin: 6px 0; }

        /* Heat map */
        .v7-heat-card {
            background: #111a2e; border: 1px solid #1e293b;
            border-radius: 12px; padding: 10px 14px;
        }
        .v7-heat-dept-head {
            display: flex; justify-content: space-between; align-items: center;
            margin-bottom: 6px; padding-bottom: 4px; border-bottom: 1px solid #1e293b;
        }
        .v7-heat-colhead, .v7-heat-row {
            display: grid; grid-template-columns: 1.7fr repeat(5, 1fr) 70px;
            gap: 6px; align-items: center;
        }
        .v7-heat-colhead { color: #64748b; font-size: 10px; letter-spacing: 0.10em;
                           text-transform: uppercase; padding: 4px 0; }
        .v7-heat-colhead .v7-day { text-align: center; }
        .v7-heat-colhead .v7-day .v7-dow { font-size: 10px; }
        .v7-heat-colhead .v7-day .v7-dt  { font-size: 9px; color: #64748b; display: block; margin-top: 1px; letter-spacing: 0.04em; }
        .v7-heat-row { padding: 4px 0; }
        .v7-heat-kpi { color: #e2e8f0; font-size: 12px; }
        .v7-heat-cell {
            height: 26px; border-radius: 5px; display: flex; align-items: center;
            justify-content: center; font-size: 11.5px; font-weight: 600; border: 1px solid;
        }
        .v7-heat-cell.v7-good { background: rgba(34,197,94,0.22); border-color: rgba(34,197,94,0.55); color: #4ade80; }
        .v7-heat-cell.v7-warn { background: rgba(245,158,11,0.22); border-color: rgba(245,158,11,0.55); color: #fbbf24; }
        .v7-heat-cell.v7-bad  { background: rgba(239,68,68,0.22); border-color: rgba(239,68,68,0.55); color: #f87171; }
        .v7-heat-cell.v7-neu  { background: #1c2538; border-color: #2a3550; color: #64748b; font-weight: 500; }
        .v7-heat-weekly { text-align: right; }
        .v7-heat-weekly .v7-pill {
            display: inline-block; padding: 3px 9px; border-radius: 7px;
            border: 1px solid; font-size: 11px; font-weight: 700;
        }
        .v7-heat-weekly .v7-pill.v7-good { background: rgba(34,197,94,0.10); border-color: rgba(34,197,94,0.55); color: #4ade80 !important; }
        .v7-heat-weekly .v7-pill.v7-warn { background: rgba(245,158,11,0.10); border-color: rgba(245,158,11,0.55); color: #fbbf24 !important; }
        .v7-heat-weekly .v7-pill.v7-bad  { background: rgba(239,68,68,0.10); border-color: rgba(239,68,68,0.55); color: #f87171 !important; }
        .v7-heat-weekly .v7-pill.v7-neu  { background: rgba(100,116,139,0.10); border-color: rgba(100,116,139,0.55); color: #94a3b8 !important; }

        /* Lagging row grid (Metric → Target → Current → % to Goal → Status) */
        .v7-colhead, .v7-row {
            display: grid; grid-template-columns: 1.8fr 1.1fr 1.1fr 110px 0.9fr;
            gap: 14px; align-items: center;
        }
        .v7-colhead { color: #64748b; font-size: 10px; letter-spacing: 0.14em;
                      text-transform: uppercase; padding: 6px 0 4px; border-bottom: 1px solid #1e293b; }
        .v7-row { border-bottom: 1px solid rgba(30,41,59,0.6); padding: 9px 0; }
        .v7-row:last-child { border-bottom: none; }
        .v7-metric-name { color: #e2e8f0; font-size: 12.5px; }
        .v7-metric-current { color: #e2e8f0; font-size: 13px; font-weight: 600; }
        .v7-metric-target { color: #94a3b8; font-size: 12px; }

        .v7-pace { display: flex; flex-direction: column; align-items: center; gap: 4px; }
        .v7-pace .v7-num { font-size: 13px; font-weight: 700; line-height: 1; }
        .v7-pace .v7-num.v7-good { color: #4ade80; }
        .v7-pace .v7-num.v7-bad  { color: #f87171; }
        .v7-pace .v7-num.v7-neu  { color: #94a3b8; font-size: 10px; font-weight: 500; letter-spacing: 0.04em; }

        .v7-vbar {
            width: 24px; height: 48px; background: #1c2538;
            border: 1px solid #2a3550; border-radius: 4px; position: relative; overflow: visible;
        }
        .v7-vbar > .v7-fill { position: absolute; left: 0; right: 0; bottom: 0; border-radius: 0 0 3px 3px; }
        .v7-vbar > .v7-fill.v7-good { background: #22c55e; }
        .v7-vbar > .v7-fill.v7-bad  { background: #ef4444; }
        .v7-vbar > .v7-tick { position: absolute; left: -3px; right: -3px; height: 2px; background: rgba(255,255,255,0.55); }

        .v7-status {
            display: inline-block; padding: 4px 10px; border-radius: 999px;
            font-size: 11px; font-weight: 600; white-space: nowrap;
        }
        .v7-status.v7-good { background: rgba(34,197,94,0.14); color: #4ade80 !important; }
        .v7-status.v7-bad  { background: rgba(239,68,68,0.14); color: #f87171 !important; }
        .v7-status.v7-neu  { background: rgba(100,116,139,0.14); color: #94a3b8 !important; }
    </style>
    """, unsafe_allow_html=True)

    _heat_html_v7    = build_target_v7_heatmap_html()
    _lagging_html_v7 = build_target_v7_lagging_html()
    st.markdown(
        '<div class="td-v7">'
          f'{_heat_html_v7}'
          f'{_lagging_html_v7}'
        '</div>',
        unsafe_allow_html=True
    )


# ══════════════════════════════════════════════════════════════════════════════
# MBR — MONTHLY BUSINESS REVIEW TAB (2026-06-09)
# ══════════════════════════════════════════════════════════════════════════════
# A per-team monthly deep-dive: same bucket→department layout as the Target tab,
# but each department section has a dropdown to pick ONE KPI, and that KPI fills
# the section with a Day×Week cascade (Mon–Fri × week rows) for a chosen month,
# defaulting to the previous month. Green = hit, Red = miss (same thresholds as
# the Target tab — formatters are reused verbatim from target_rows). A browser
# Print → Save-as-PDF button exports the assembled view.
import calendar as _mbr_cal
import streamlit.components.v1 as _mbr_components

# KPI list + reused formatter, sourced straight from target_rows so names/colors
# never drift from the Target tab.
MBR_KPIS_BY_DEPT = {}
MBR_FMT = {}
for _r in target_rows:
    MBR_KPIS_BY_DEPT.setdefault(_r[0], []).append(_r[2])
    MBR_FMT[(_r[0], _r[2])] = _r[5]


@st.cache_data(ttl=600)
def _mbr_ops_prod(ms, me):
    return q(f"""
        SELECT PRODUCTION_DATE,
            ROUND(AVG(CASE WHEN PRODUCTION_TYPE='Liquid'
                      THEN DAY_LABOR_COST_AMT / NULLIF(DAY_COMPLETED_QTY, 0) END), 2) AS LABOR_COST_PER_UNIT,
            ROUND(100 - AVG(CASE WHEN PRODUCTION_TYPE='Liquid' THEN AVAILABILITY_PCT END), 1) AS UNPLANNED_DT_PCT,
            ROUND(AVG(CASE WHEN PRODUCTION_TYPE='Liquid' AND OEE_PCT > 0 THEN OEE_PCT END), 1) AS OEE_PCT
        FROM GOLD_V3_DB.SEMANTIC.SV_DAILY_PRODUCTION
        WHERE PRODUCTION_DATE BETWEEN '{ms}' AND '{me}'
        GROUP BY PRODUCTION_DATE ORDER BY PRODUCTION_DATE
    """)


@st.cache_data(ttl=600)
def _mbr_aircall(ms, me):
    # v2: repointed to GOLD_V3_DB.SCORECARD.FCT_SALES_REP_CALLS_DAILY (verified fact).
    # Contract: CALL_DATE, TOTAL_CALLS, AVG_PER_REP.
    return q(f"""
        SELECT ACTIVITY_DATE AS CALL_DATE,
               SUM(TOTAL_CALLS) AS TOTAL_CALLS,
               ROUND(SUM(TOTAL_CALLS) / NULLIF(COUNT(DISTINCT REP_NAME), 0), 1) AS AVG_PER_REP
        FROM GOLD_V3_DB.SCORECARD.FCT_SALES_REP_CALLS_DAILY
        WHERE ACTIVITY_DATE BETWEEN '{ms}' AND '{me}'
          AND IS_SCORECARD_REP
        GROUP BY 1 ORDER BY 1
    """)


@st.cache_data(ttl=600)
def _mbr_outlook(ms, me):
    # v2: repointed to GOLD_V3_DB.SCORECARD.FCT_SALES_REP_EMAILS_DAILY (verified fact).
    # Contract: SENT_DATE, EMAILS_TOTAL (= EXTERNAL_EMAILS_SENT), EMAIL_REPS.
    return q(f"""
        SELECT ACTIVITY_DATE AS SENT_DATE,
               SUM(EXTERNAL_EMAILS_SENT) AS EMAILS_TOTAL,
               COUNT(DISTINCT REP_NAME) AS EMAIL_REPS
        FROM GOLD_V3_DB.SCORECARD.FCT_SALES_REP_EMAILS_DAILY
        WHERE ACTIVITY_DATE BETWEEN '{ms}' AND '{me}'
          AND IS_SCORECARD_REP
        GROUP BY 1 ORDER BY 1
    """)


@st.cache_data(ttl=600)
def _mbr_ar(ms, me):
    return q(f"""
        SELECT SNAPSHOT_DATE, AR_PAST_DUE_AMT
        FROM GOLD_V3_DB.PUBLIC.AR_PAST_DUE_DAILY
        WHERE SNAPSHOT_DATE BETWEEN '{ms}' AND '{me}' ORDER BY SNAPSHOT_DATE
    """)


@st.cache_data(ttl=600)
def _mbr_intercom(ms, me):
    return q(f"""
        SELECT TO_TIMESTAMP(CREATED_AT)::DATE AS CONV_DATE,
               COUNT(CASE WHEN CONVERSATION_RATING:rating::NUMBER >= 4 THEN 1 END) AS CSAT_POS,
               COUNT(CASE WHEN CONVERSATION_RATING:rating::NUMBER IS NOT NULL THEN 1 END) AS CSAT_RATED,
               ROUND(MEDIAN(STATISTICS:time_to_admin_reply::NUMBER) / 60.0, 1) AS MEDIAN_RESP_MIN,
               COUNT(CASE WHEN AI_AGENT:resolution_state::STRING
                          IN ('assumed_resolution','confirmed_resolution') THEN 1 END) AS AI_DEFLECTED,
               COUNT(CASE WHEN AI_AGENT:last_answer_type::STRING = 'ai_answer' THEN 1 END) AS AI_TOUCHED
        FROM RAW_V2_DB.INTERCOM.CONVERSATIONS
        WHERE TO_TIMESTAMP(CREATED_AT)::DATE BETWEEN '{ms}' AND '{me}'
        GROUP BY 1 ORDER BY 1
    """)


@st.cache_data(ttl=600)
def _mbr_manual(floor_s, me_s):
    return q(f"""
        SELECT METRIC_KEY, METRIC_DATE, VALUE
        FROM GOLD_V3_DB.PUBLIC.MANUAL_SCORECARD_INPUTS
        WHERE METRIC_DATE BETWEEN '{floor_s}' AND '{me_s}' ORDER BY METRIC_DATE
    """)


def _mbr_business_days(month_start, month_end):
    """All Mon–Fri dates in [month_start, month_end], capped at today."""
    out, d = [], month_start
    cap = min(month_end, today)
    while d <= cap:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def _mbr_metric_values(dept, name, ms, me, bdays):
    """date→raw value for one KPI over the selected month. Raw values match the
    target_rows getter semantics so the reused formatter colors identically."""
    ms_s, me_s = ms.strftime('%Y-%m-%d'), me.strftime('%Y-%m-%d')

    # ── SALES ──────────────────────────────────────────────────────────────
    if dept == 'Sales' and name == 'TSM Daily Activities (Calls + Emails)':
        ac_df, om_df = _mbr_aircall(ms_s, me_s), _mbr_outlook(ms_s, me_s)
        ac = {}
        if not ac_df.empty:
            ac_df['CALL_DATE'] = pd.to_datetime(ac_df['CALL_DATE']).dt.date
            ac = {r['CALL_DATE']: safe_float(r['AVG_PER_REP']) for _, r in ac_df.iterrows()}
        om = {}
        if not om_df.empty:
            om_df['SENT_DATE'] = pd.to_datetime(om_df['SENT_DATE']).dt.date
            om = {r['SENT_DATE']: (int(r['EMAILS_TOTAL'] or 0), int(r['EMAIL_REPS'] or 0))
                  for _, r in om_df.iterrows()}
        out = {}
        for d in bdays:
            c = ac.get(d)
            et = om.get(d)
            e = round(et[0] / et[1], 1) if et and et[1] else None
            if c is None and e is None:
                continue
            out[d] = (round((c or 0) + (e or 0), 1), c or 0, e or 0)
        return out
    if dept == 'Sales' and name.startswith('Pipeline Activity'):
        df = load_pipeline_movement(ms_s, me_s)
        if df.empty: return {}
        df['D'] = pd.to_datetime(df['D']).dt.date
        return dict(zip(df['D'], df['MOVEMENTS']))
    if dept == 'Sales' and name.startswith('A/R Past Due'):
        df = _mbr_ar(ms_s, me_s)
        if df.empty: return {}
        df['SNAPSHOT_DATE'] = pd.to_datetime(df['SNAPSHOT_DATE']).dt.date
        return dict(zip(df['SNAPSHOT_DATE'], df['AR_PAST_DUE_AMT']))

    # ── MANUFACTURING ───────────────────────────────────────────────────────
    if dept == 'Manufacturing':
        df = _mbr_ops_prod(ms_s, me_s)
        if df.empty: return {}
        df['PRODUCTION_DATE'] = pd.to_datetime(df['PRODUCTION_DATE']).dt.date
        col = ('UNPLANNED_DT_PCT' if 'Downtime' in name
               else 'OEE_PCT' if name == 'OEE' else 'LABOR_COST_PER_UNIT')
        return {d: v for d, v in zip(df['PRODUCTION_DATE'], df[col]) if pd.notna(v)}

    # ── CUSTOMER SUPPORT ─────────────────────────────────────────────────────
    if dept == 'Customer Support':
        # CSAT needs 6 extra trailing days for the rolling-7 window.
        ic = _mbr_intercom((ms - timedelta(days=6)).strftime('%Y-%m-%d'), me_s)
        if ic.empty: return {}
        ic = ic.copy()
        ic['CONV_DATE'] = pd.to_datetime(ic['CONV_DATE']).dt.date
        ic = ic.sort_values('CONV_DATE')
        if name.startswith('CSAT'):
            out = {}
            for d in bdays:
                w = ic[ic['CONV_DATE'] <= d].tail(7)
                rated = w['CSAT_RATED'].sum()
                if rated > 0:
                    out[d] = round(w['CSAT_POS'].sum() * 100.0 / rated, 1)
            return out
        if name.startswith('First Response'):
            return {r['CONV_DATE']: r['MEDIAN_RESP_MIN'] for _, r in ic.iterrows()
                    if r['CONV_DATE'] in bdays and pd.notna(r['MEDIAN_RESP_MIN'])}
        if name.startswith('Fin AI'):
            out = {}
            for _, r in ic.iterrows():
                if r['CONV_DATE'] in bdays and r['AI_TOUCHED']:
                    out[r['CONV_DATE']] = round(r['AI_DEFLECTED'] * 100.0 / r['AI_TOUCHED'], 1)
            return out

    # ── PEOPLE & CULTURE (exact-date manual) ─────────────────────────────────
    if dept == 'People & Culture':
        key = ('HR_PERFORMANCE_DOC' if name.startswith('Performance')
               else 'HR_TRAINING_COMPLIANCE' if name.startswith('Training')
               else 'HR_CAREER_PATH')
        mdf = _mbr_manual(ms_s, me_s)
        if mdf.empty: return {}
        sub = mdf[mdf['METRIC_KEY'] == key].copy()
        sub['METRIC_DATE'] = pd.to_datetime(sub['METRIC_DATE']).dt.date
        m = {d: safe_float(v) for d, v in zip(sub['METRIC_DATE'], sub['VALUE'])}
        return {d: m[d] for d in bdays if d in m}

    # ── FINANCE ──────────────────────────────────────────────────────────────
    if dept == 'Finance' and name.startswith('Same-Day Cash'):
        return load_cash_balance_dict(ms_s, me_s)
    if dept == 'Finance' and name.startswith('% of JEs'):
        return load_je_new_erp_pct(ms_s, me_s)
    if dept == 'Finance' and name.startswith('% Sources Synced'):
        return load_sync_coverage_daily(ms_s, me_s)

    # ── MARKETING ─────────────────────────────────────────────────────────────
    if dept == 'Marketing' and name.startswith('Cart Abandonment'):
        ga = load_marketing_ga4_daily(ms_s, me_s)
        return {d: (ga.get(d) or {}).get('cart_abandon_pct')
                for d in bdays if (ga.get(d) or {}).get('cart_abandon_pct') is not None}
    if dept == 'Marketing' and name.startswith('AOV'):
        return load_aov_first_180d_daily(ms_s, me_s)
    if dept == 'Marketing' and name.startswith('Unique Sessions'):
        ga = load_marketing_ga4_daily(ms_s, me_s)
        return {d: (ga.get(d) or {}).get('new_users')
                for d in bdays if (ga.get(d) or {}).get('new_users') is not None}

    # ── FULFILLMENT ────────────────────────────────────────────────────────────
    if dept == 'Fulfillment' and name.startswith('Same-Day Ship'):
        return load_fulfillment_daily(ms_s, me_s)[0]
    if dept == 'Fulfillment' and name.startswith('Median Order-to-Ship'):
        return load_fulfillment_daily(ms_s, me_s)[1]
    if dept == 'Fulfillment' and name == 'B2B OTIF':
        return load_b2b_ship_hours_daily(ms_s, me_s)

    # ── PROCUREMENT ─────────────────────────────────────────────────────────────
    if dept == 'Procurement':
        mdf = _mbr_manual((ms - timedelta(days=400)).strftime('%Y-%m-%d'), me_s)

        def _cf(key):
            if mdf.empty: return {}
            sub = mdf[mdf['METRIC_KEY'] == key].copy()
            if sub.empty: return {}
            sub['METRIC_DATE'] = pd.to_datetime(sub['METRIC_DATE']).dt.date
            sub = sub.sort_values('METRIC_DATE')
            out = {}
            for d in bdays:
                prior = sub[sub['METRIC_DATE'] <= d]
                if not prior.empty:
                    out[d] = safe_float(prior.iloc[-1]['VALUE'])
            return out

        if name == 'Supplier Scorecard':
            return _cf('PROC_SUPPLIER_SCORECARD')
        if name.startswith('Supplier OTD'):
            otd = _cf('PROC_OTD_PCT_90D')  # manual fallback
            odf = load_supplier_otd_combined(
                (ms - timedelta(days=90)).strftime('%Y-%m-%d'), me_s)
            if not odf.empty:
                odf = odf.copy()
                odf['RCV_DATE'] = pd.to_datetime(odf['RCV_DATE']).dt.date
                for d in bdays:
                    w = odf[(odf['RCV_DATE'] > d - timedelta(days=90)) & (odf['RCV_DATE'] <= d)]
                    # GOLD rows are per-day aggregates: weight on-time by RECEIPTS.
                    denom = w['RECEIPTS'].sum() if not w.empty else 0
                    if denom:
                        otd[d] = round(100.0 * w['ON_TIME'].sum() / denom, 1)
            return otd
        if name.startswith('% Critical Components'):
            cf = _cf('PROC_PCT_SINGLE_SOURCED')
            if cf:
                return cf
            snap = load_single_sourced_snapshot()
            if not snap.empty:
                v = safe_float(snap.iloc[0]['PCT'])
                if v is not None:
                    return {d: v for d in bdays}
            return {}

    return {}


def build_mbr_cascade_html(dept, name, ms, me):
    """Day×Week cascade for one KPI over the chosen month.
    Rows = Mon-anchored weeks; columns = Mon–Fri; right cols = Weekly #/total + %Hit;
    bottom MONTH row = month totals. Reuses Target-tab green/red thresholds."""
    fmt = MBR_FMT.get((dept, name))
    if fmt is None:
        return '<div class="mbr-empty">No KPI selected.</div>'
    bdays = _mbr_business_days(ms, me)
    values = _mbr_metric_values(dept, name, ms, me, bdays)

    mfg_skip_friday = (dept == 'Manufacturing')
    skip_holidays = (dept in HOLIDAY_BLANK_DEPTS)

    def classify(d):
        """→ (display, kind) where kind ∈ good/warn/bad/neu. neu = no-data/skip."""
        if d > today or d.month != ms.month \
           or (mfg_skip_friday and d.weekday() == 4) \
           or (skip_holidays and d in US_SHIP_HOLIDAYS_SET):
            return ('—', 'neu')
        val = values.get(d)
        if val is None or str(val) in ('', 'nan', 'None'):
            return ('—', 'neu')
        try:
            disp, css_old = fmt(val)
        except Exception:
            return ('—', 'neu')
        kind = ('good' if css_old == 'c-green' else 'warn' if css_old == 'c-yellow'
                else 'bad' if css_old == 'c-red' else 'neu')
        return (disp, kind)

    # Monday-anchored weeks overlapping the month.
    first_mon = ms - timedelta(days=ms.weekday())
    weeks, cur = [], first_mon
    while cur <= me:
        weeks.append([cur + timedelta(days=i) for i in range(5)])
        cur += timedelta(days=7)

    rows_html = []
    mo_green = mo_scored = 0
    wk_num = 0
    for wk in weeks:
        if all(d.month != ms.month for d in wk):
            continue
        wk_num += 1
        cells, wk_green, wk_scored = [], 0, 0
        for d in wk:
            disp, kind = classify(d)
            cells.append(f'<div class="mbr-chip mbr-{kind}">{disp}</div>')
            if kind == 'good':
                wk_green += 1; wk_scored += 1
            elif kind in ('warn', 'bad'):
                wk_scored += 1
        mo_green += wk_green; mo_scored += wk_scored
        if wk_scored:
            pct = wk_green / wk_scored * 100
            tcls = 'good' if pct >= 80 else 'bad'
            tot = f'<div class="mbr-pcell"><span class="mbr-pill mbr-{tcls}">{wk_green}/{wk_scored}</span></div>'
            hit = f'<div class="mbr-pcell"><span class="mbr-pill mbr-{tcls}">{pct:.0f}%</span></div>'
        else:
            tot = '<div class="mbr-pcell"><span class="mbr-pill mbr-neu">—</span></div>'
            hit = '<div class="mbr-pcell"><span class="mbr-pill mbr-neu">—</span></div>'
        rows_html.append(
            f'<div class="mbr-row"><div class="mbr-rh">Week {wk_num}<span>{wk[0]:%m/%d}</span></div>'
            + ''.join(cells) + tot + hit + '</div>')

    if mo_scored:
        mpct = mo_green / mo_scored * 100
        mcls = 'good' if mpct >= 80 else 'bad'
        mo_tot = f'<div class="mbr-pcell"><span class="mbr-pill mbr-{mcls}">{mo_green}/{mo_scored}</span></div>'
        mo_hit = f'<div class="mbr-pcell"><span class="mbr-pill mbr-{mcls}">{mpct:.0f}%</span></div>'
    else:
        mo_tot = '<div class="mbr-pcell"><span class="mbr-pill mbr-neu">—</span></div>'
        mo_hit = '<div class="mbr-pcell"><span class="mbr-pill mbr-neu">—</span></div>'

    tgt = next((r[3] for r in target_rows if r[0] == dept and r[2] == name), '')
    head = ''.join(f'<div>Day {i+1}</div>' for i in range(5))
    return (
        '<div class="mbr-card">'
        f'<div class="mbr-kpi-title">{name} <span class="mbr-kpi-target">target {tgt}</span></div>'
        f'<div class="mbr-head"><div></div>{head}'
        '<div>Month Hit</div><div>% Hit</div></div>'
        + ''.join(rows_html)
        + '<div class="mbr-row mbr-month-row"><div class="mbr-rh">MONTH</div>'
          f'<div class="mbr-month-note">{mo_green} of {mo_scored} business days hit</div>'
          f'{mo_tot}{mo_hit}</div>'
        '</div>'
    )


with tab_mbr:
    st.markdown("""
    <style>
        /* Built with divs + CSS grid (NOT <table>) — same approach as the Target
           page's .td-v7 block — so Streamlit's markdown-<table> theme can't paint
           light backgrounds. Cards are dark; only the chips/pills carry color. */
        .mbr-wrap { background:#0b1220; padding:6px 12px 14px; margin:-2px -10px 14px; border-radius:6px;
            font-family:-apple-system,"SF Pro Text","IBM Plex Sans",system-ui,sans-serif; color:#e2e8f0; }
        .mbr-wrap, .mbr-wrap * { -webkit-print-color-adjust:exact !important; print-color-adjust:exact !important; }
        .mbr-banner, .mbr-bucket-lbl { background:linear-gradient(90deg, rgba(96,165,250,0.14), transparent 70%);
            border-left:3px solid #60a5fa; padding:10px 14px; margin:14px 0 8px;
            font-size:13px; letter-spacing:0.10em; text-transform:uppercase; font-weight:600; color:#e2e8f0 !important; }
        .mbr-banner .mbr-sub, .mbr-bucket-lbl .mbr-sub { color:#94a3b8 !important; font-size:11px; margin-left:10px; letter-spacing:0; text-transform:none; }
        .mbr-dept-name { font-size:14px; font-weight:600; color:#e2e8f0 !important; margin:4px 0 4px; }
        .mbr-empty { color:#64748b; font-size:12px; padding:8px 0; }

        /* Dark card (mirror .v7-heat-card) */
        .mbr-card { background:#111a2e; border:1px solid #1e293b; border-radius:12px; padding:10px 14px; }
        .mbr-kpi-title { font-size:13px; font-weight:600; color:#e2e8f0 !important; margin:0 0 8px; }
        .mbr-kpi-target { color:#94a3b8 !important; font-size:11px; font-weight:500; margin-left:8px; }

        .mbr-head, .mbr-row {
            display:grid; grid-template-columns:1.4fr repeat(5,1fr) 84px 84px; gap:6px; align-items:center; }
        .mbr-head { color:#64748b !important; font-size:10px; letter-spacing:0.08em;
            text-transform:uppercase; padding:2px 0 4px; }
        .mbr-head > div { text-align:center; }
        .mbr-row { padding:3px 0; }
        .mbr-rh { text-align:left; color:#cbd5e1 !important; font-size:11px; font-weight:600; }
        .mbr-rh span { display:block; color:#64748b !important; font-size:9px; font-weight:500; }

        /* Day chips (mirror .v7-heat-cell) — colored fill on the dark card */
        .mbr-wrap .mbr-chip {
            height:26px; display:flex; align-items:center; justify-content:center;
            border-radius:5px; border:1px solid; font-size:11.5px; font-weight:600; }
        .mbr-wrap .mbr-chip.mbr-good { background:rgba(34,197,94,0.22); border-color:rgba(34,197,94,0.55); color:#4ade80 !important; }
        .mbr-wrap .mbr-chip.mbr-warn { background:rgba(245,158,11,0.22); border-color:rgba(245,158,11,0.55); color:#fbbf24 !important; }
        .mbr-wrap .mbr-chip.mbr-bad  { background:rgba(239,68,68,0.22); border-color:rgba(239,68,68,0.55); color:#f87171 !important; }
        .mbr-wrap .mbr-chip.mbr-neu  { background:#1c2538; border-color:#2a3550; color:#64748b !important; font-weight:500; }
        /* Total pills (mirror .v7-pill) */
        .mbr-pcell { display:flex; justify-content:center; }
        .mbr-wrap .mbr-pill {
            display:inline-block; padding:3px 9px; border-radius:7px; border:1px solid;
            font-size:11px; font-weight:700; }
        .mbr-wrap .mbr-pill.mbr-good { background:rgba(34,197,94,0.10); border-color:rgba(34,197,94,0.55); color:#4ade80 !important; }
        .mbr-wrap .mbr-pill.mbr-warn { background:rgba(245,158,11,0.10); border-color:rgba(245,158,11,0.55); color:#fbbf24 !important; }
        .mbr-wrap .mbr-pill.mbr-bad  { background:rgba(239,68,68,0.10); border-color:rgba(239,68,68,0.55); color:#f87171 !important; }
        .mbr-wrap .mbr-pill.mbr-neu  { background:rgba(100,116,139,0.10); border-color:rgba(100,116,139,0.55); color:#94a3b8 !important; }
        .mbr-month-row { border-top:1px solid #1e293b; margin-top:4px; padding-top:6px; }
        .mbr-month-row .mbr-rh { color:#e2e8f0 !important; }
        .mbr-month-note { grid-column:span 5; height:26px; display:flex; align-items:center; justify-content:center;
            background:#0d1426; border-radius:5px; color:#94a3b8 !important; font-size:11.5px; font-weight:600; }

        /* Print → Save as PDF: drop Streamlit chrome + controls, force colors,
           landscape. Content flows top→down (page 1 = titles + first team); the
           section header is inside .mbr-wrap so it never separates from its table,
           and each unit stays whole so no card is cut across a page. */
        @media print {
            [data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stSidebar"],
            .stTabs [data-baseweb="tab-list"], .stButton, .stSelectbox, .stDateInput,
            iframe, .mbr-noprint { display:none !important; }
            .stApp, .main, .block-container { background:#0b1220 !important; }
            .mbr-wrap { page-break-inside: avoid; break-inside: avoid; }
            @page { size: A4 landscape; margin: 8mm; }
        }
    </style>
    """, unsafe_allow_html=True)

    # ── Month picker (defaults to previous month) ───────────────────────────
    _first_this = today.replace(day=1)
    _month_opts, _cur = [], _first_this
    for _ in range(14):
        _label = _cur.strftime('%B %Y')
        _m_last = _cur.replace(day=_mbr_cal.monthrange(_cur.year, _cur.month)[1])
        _month_opts.append((_label, _cur, _m_last))
        _cur = (_cur - timedelta(days=1)).replace(day=1)

    ctl1, ctl2 = st.columns([2, 1])
    with ctl1:
        _sel_label = st.selectbox(
            "MBR month", [o[0] for o in _month_opts],
            index=1,  # previous month
            help="Each department section below dives into one KPI for this month.")
    with ctl2:
        _mbr_components.html(
            """<button onclick="window.parent.print()" style="margin-top:26px;width:100%;
                 padding:8px 12px;background:#1e293b;color:#e2e8f0;border:1px solid #334155;
                 border-radius:8px;font-size:13px;font-weight:600;cursor:pointer;
                 font-family:-apple-system,system-ui,sans-serif;">🖨 Export to PDF</button>
               <div style="color:#64748b;font-size:10px;margin-top:4px;font-family:system-ui;">
                 Opens print dialog · choose “Save as PDF”. (Cmd/Ctrl-P also works.)</div>""",
            height=70)

    _ms, _me = next((o[1], o[2]) for o in _month_opts if o[0] == _sel_label)

    parts = [f'<div class="mbr-banner">MONTHLY BUSINESS REVIEW '
             f'<span class="mbr-sub">{_sel_label} · one KPI per team · green = hit, red = miss</span></div>']
    st.markdown(''.join(parts), unsafe_allow_html=True)

    # ── Bucket → department sections, each with its own KPI dropdown ─────────
    # Content flows top→down so page 1 fills with the titles + first team(s); each
    # department's table is kept whole (break-inside: avoid) so none get cut across
    # a page boundary, and section headers stick to their table (break-after: avoid).
    for _bucket_name, _dept_list in BUCKETS_V7:
        _bucket_labeled = False
        for _dept in _dept_list:
            _kpis = MBR_KPIS_BY_DEPT.get(_dept, [])
            if not _kpis:
                continue
            # KPI picker first (hidden in print); the dark card below carries the
            # bucket label + dept name + table as ONE atomic block so the heading
            # never separates from its table across a page boundary.
            _chosen = st.selectbox(
                f"{_dept} — choose KPI", _kpis, key=f"mbr_kpi_{_dept}")
            _hdr = ''
            if not _bucket_labeled:
                _hdr += (f'<div class="mbr-bucket-lbl">{_bucket_name.upper()} '
                         f'<span class="mbr-sub">{" · ".join(_dept_list)}</span></div>')
                _bucket_labeled = True
            _hdr += f'<div class="mbr-dept-name">{_dept}</div>'
            st.markdown(
                f'<div class="mbr-wrap">{_hdr}{build_mbr_cascade_html(_dept, _chosen, _ms, _me)}</div>',
                unsafe_allow_html=True)


# ── SALES REPS TAB ────────────────────────────────────────────────────────────
with tab_sales:
    st.markdown(f"""
    <div class="sc-header">
        <span class="sc-title">Sales Rep Scorecard</span>
        <span class="sc-subtitle">Month-to-date &nbsp;·&nbsp; {date.today().strftime('%B %Y')}</span>
    </div>
    <div class="legend-row">
        <span class="leg"><span class="leg-dot" style="background:{T['g_bg']};border:1px solid {T['g_fg']};"></span>At/above target · Act/Day ≥ 60</span>
        <span class="leg"><span class="leg-dot" style="background:{T['y_bg']};border:1px solid {T['y_fg']};"></span>On track · Act/Day ≥ 48</span>
        <span class="leg"><span class="leg-dot" style="background:{T['r_bg']};border:1px solid {T['r_fg']};"></span>Below threshold</span>
        <span class="leg"><span class="leg-dot" style="background:{T['border']};"></span>No quota set</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(build_sales_reps_html(load_sales_reps()), unsafe_allow_html=True)

    st.markdown(f"""
    <div style="margin-top:20px; padding:10px 14px; border:1px solid #2d2d2d; border-radius:6px;
         background:#111; font-size:11px; color:#666; font-family:'IBM Plex Mono',monospace;">
        Data refreshed: {date.today().strftime('%Y-%m-%d')} &nbsp;·&nbsp;
        Activity: Aircall (outbound) + Outlook, MTD weekday averages &nbsp;·&nbsp;
        Funnel: live RAW_V2_DB.CLICKUP.TASKS current stage (space 901313268656) &nbsp;·&nbsp;
        Revenue: SUPABASE_ERP shipments (COMPLETED, MTD) &nbsp;·&nbsp;
        Targets: Inside Sales $45k/mo; others pending quota
    </div>
    """, unsafe_allow_html=True)


with tab_help:
    st.markdown("## 📖 Metric Definitions & Data Sources")
    st.caption("How each metric is calculated, where the data comes from, and known limitations.")

    # ── SALES ─────────────────────────────────────────────────────────────────
    with st.expander("💼 SALES", expanded=True):
        st.markdown("""
| # | Metric | Calculation | Source | Notes |
|---|---|---|---|---|
| 1 | **Average daily engagements per rep** | Total completed calls ÷ active reps that day | `RAW_V2_DB.AIRCALL.CALLS` | Calls only (inbound + outbound, status=done). Excludes Ari Meisel & Corey Helper. SMS/email not available in Aircall tables. |
| 2 | **Orders as a % of Presentations** | Manual entry | — | No automated data source yet. Requires Pipedrive integration. |
| 3 | **New Opportunities** | Manual entry | — | No automated data source yet. Requires Pipedrive integration. |
| 4 | **AR Past Due** | SUM(BALANCE_DUE) across non-voided invoices > 30 days old | `RAW_V2_DB.SUPABASE_ERP.INVOICES` | Source migrated 2026-05-22 from Acumatica to Supabase_ERP. Past-due rule = `INVOICE_DATE + 30 days < today` (uniform, ignores per-customer payment terms). Excludes voided invoices. Snapshot frozen at 5:30 PM MT daily; live value shown before 5:30 PM. Historical values pre-2026-05-22 are Acumatica-era and use different math. |
        """)

    # ── OPERATIONS ────────────────────────────────────────────────────────────
    with st.expander("⚙️ OPERATIONS", expanded=True):
        st.markdown("""
| # | Metric | Calculation | Source | Notes |
|---|---|---|---|---|
| 1 | **Labor Cost Per Unit (Liquid)** | AVG(DAY_LABOR_COST_AMT ÷ DAY_COMPLETED_QTY) across Liquid lots | `GOLD_V3_DB.SEMANTIC.SV_DAILY_PRODUCTION` | Averages per-lot rates equally (not pooled). Liquid lots only — excludes Packing/island lots. Data comes from Brian's SharePoint Trends tab via Airbyte sync. T-1 lag (overnight). |
| 2 | **Unplanned Downtime % (Liquid)** | 100 - AVG(AVAILABILITY_PCT) across Liquid lots | `GOLD_V3_DB.SEMANTIC.SV_DAILY_PRODUCTION` | AVAILABILITY_PCT already removes breaks & planned changeovers from denominator. Liquid only. |
| 3 | **First Pass Yield (Liquid)** | AVG(FIRST_PASS_PCT) across Liquid lots only | `GOLD_V3_DB.SEMANTIC.SV_DAILY_PRODUCTION` | Liquid lots only — Packing/island lots excluded (aligned 2026-04-21 with the Liquid-only filter used on Labor, Downtime, and OEE). |
| 4 | **OEE** | AVG(OEE_PCT) across Liquid lots where OEE > 0 | `GOLD_V3_DB.SEMANTIC.SV_DAILY_PRODUCTION` | Packing/island lots excluded (OEE = N/A for manual processes). |
| 5 | **OTIF (D2C) — On-Time %** | 100 − (COUNT(ship_date > required_ship_date) ÷ COUNT(total shipped)) × 100 | `GOLD_V3_DB.FULFILLMENT.STG_SHIPHERO__SHIPMENTS` joined to `STG_SHIPHERO__ORDERS` | Higher = better. Display inverted 2026-04-23 from late-rate to on-time % so the 99% goal reads naturally. ShipHero syncs ~11 AM daily so prior-day numbers may shift as late shipments are backdated. |
| 6 | **OTIF (B2B) — Avg Cycle Time** | AVG(CYCLE_TIME_HOURS) for completed orders | `GOLD_V3_DB.SEMANTIC.SV_SALES_ORDER_ANALYSIS` | Hours from order CREATED_AT to Completed status (LAST_MODIFIED_AT). Old SOs completed in bulk can spike this number (e.g. Mar 18 orders completed Apr 7 = 480 hrs). |
        """)

    # ── HR ────────────────────────────────────────────────────────────────────
    with st.expander("👥 HR", expanded=True):
        st.markdown("""
| # | Metric | Calculation | Source | Notes |
|---|---|---|---|---|
| 1 | **Performance Documentation Rate** | Manual entry — % of employees with current performance docs | `GOLD_V3_DB.PUBLIC.MANUAL_SCORECARD_INPUTS` | Key: `HR_PERFORMANCE_DOC`. Green ≥75%, Yellow 65-74.9%, Red <65%. |
| 2 | **Training & Compliance Completion Rate** | Manual entry — % of employees with training completed | `GOLD_V3_DB.PUBLIC.MANUAL_SCORECARD_INPUTS` | Key: `HR_TRAINING_COMPLIANCE`. Green ≥75%, Yellow 65-74.9%, Red <65%. |
| 3 | **HR Process Doc Completion Rate** | Manual entry — % of HR process documentation completed | `GOLD_V3_DB.PUBLIC.MANUAL_SCORECARD_INPUTS` | Key: `HR_CAREER_PATH`. Green ≥75%, Yellow 65-74.9%, Red <65%. |
        """)

    # ── BUSINESS OPERATIONS ───────────────────────────────────────────────────
    with st.expander("🏢 BUSINESS OPERATIONS", expanded=True):
        st.markdown("""
| # | Metric | Calculation | Source | Notes |
|---|---|---|---|---|
| 1 | **Total department metrics green** | COUNT(green metrics) ÷ 27 total metrics × 100 | Computed from all other scorecard rows | Counts 27 metrics across Sales, Ops, HR, Support, Biz Ops, Marketing. Rows with no data count as not-green. |
| 2 | **ClickUp tasks past due** | COUNT(tasks with due_date < today) ÷ COUNT(all open tasks) | `RAW_V2_DB.CLICKUP.TASKS_SNAPSHOT` | One Brain space only (ID: 901312029407). Historical via daily snapshot table — compares DUE_DATE < SNAPSHOT_DATE for each day. |
| 3 | **Cross-functional blockers** | Manual entry via ✏️ Input tab | `GOLD_V3_DB.PUBLIC.MANUAL_SCORECARD_INPUTS` | Key: `BLOCKERS_24H` |
        """)

    # ── SUPPORT ───────────────────────────────────────────────────────────────
    with st.expander("🎧 SUPPORT", expanded=True):
        st.markdown("""
All support metrics source from `RAW_V2_DB.INTERCOM.CONVERSATIONS`. Intercom syncs hourly via Airbyte (full refresh).

| # | Metric | Calculation | Source | Notes |
|---|---|---|---|---|
| 1 | **CSAT — Rolling 7D % Positive** | COUNT(rating >= 4) ÷ COUNT(rated) over rolling 7-day window | `CONVERSATIONS.CONVERSATION_RATING:rating` | Scores 1-5; 4-5 = positive. Rolling 7-day window ending that day. Low response volume (~3-5% of conversations get rated) — results can be volatile on low-traffic days. |
| 2 | **Median First Response Time** | MEDIAN(time_to_admin_reply) ÷ 60 (minutes) | `CONVERSATIONS.STATISTICS:time_to_admin_reply` | Seconds converted to minutes. Includes all days (24/7 support). Null values excluded from median (conversations with no admin reply). |
| 3 | **Total Open Tickets** | COUNT(OPEN=TRUE) at 5:30 PM MT | `GOLD_V3_DB.PUBLIC.INTERCOM_BACKLOG_DAILY.TOTAL_OPEN` + live fallback | Point-in-time total of all open Intercom conversations. Snapshot frozen daily at 5:30 PM MT via Snowflake Task; live count used before snapshot runs. |
| 4 | **Tickets Over 48 Hours** | COUNT(OPEN=TRUE AND created > 48 hours ago) at 5:30 PM MT | `GOLD_V3_DB.PUBLIC.INTERCOM_BACKLOG_DAILY.OPEN_OVER_48H` + live fallback | Same snapshot as Total Open. Green only if zero — any ticket older than 48h turns the cell red. |
| 5 | **Fin AI Deflection Rate** | COUNT(assumed_resolution + confirmed_resolution) ÷ COUNT(Fin-attempted) | `CONVERSATIONS.AI_AGENT:resolution_state` + `CONVERSATIONS.AI_AGENT:last_answer_type` | Intercom-aligned (finalized 2026-05-06). Denominator = `last_answer_type='ai_answer'` (only conversations Fin actually attempted to resolve). Deflected = assumed_resolution or confirmed_resolution. Not deflected = routed_to_team. |
        """)

    # ── MARKETING — REMOVED 2026-04-29 (new set arriving) ─────────────────────
    # with st.expander("📈 MARKETING", expanded=True):
    #     st.markdown("""...trailing 90D docs...""")

    # ── DATA REFRESH SCHEDULE ─────────────────────────────────────────────────
    with st.expander("🔄 Data Refresh Schedule", expanded=False):
        st.markdown("""
| Source | Refresh Frequency | Notes |
|---|---|---|
| **SharePoint Production** (Ops 1-4) | Overnight ~1 AM | Always T-1 (yesterday's data) |
| **ShipHero** (OTIF D2C) | ~11 AM daily | Prior-day numbers may shift as late shipments backfill |
| **Acumatica Sales Orders** (OTIF B2B) | ~9:30 AM daily | |
| **Ashby** (HR) | Hourly | Mid-day values lag Ashby's live UI — final by EOD |
| **Aircall** (Sales engagements) | Hourly | |
| **Intercom** (Support) | Hourly full refresh | CSAT/response time/deflection update each sync |
| **WooCommerce** (Marketing) | Real-time via Airbyte | Marketing trailing 90D capped at yesterday |
| **ClickUp** (Tasks snapshot) | Daily Airbyte sync | |
| **AR Past Due snapshot** | 5:30 PM MT daily | Snowflake Task — live value shown before 5:30 PM |
| **Manual inputs** (Sales 1b, 2, 3, 5 / HR / Biz Ops 3) | On-demand via ✏️ Input tab | Richie, Pete, Latonya have write access |
        """)

    # ── KNOWN LIMITATIONS ─────────────────────────────────────────────────────
    with st.expander("⚠️ Known Limitations & Gaps", expanded=False):
        st.markdown("""
- **Sales Rows 2, 3, 5** (Orders as % of Presentations, New Opportunities, Open Quotes) — manual entry via Input tab. No automated source yet — requires Pipedrive integration (currently has a pagination bug capping at 100 rows).
- **Sales Row 1b** (Engagements per rep — manual) — manual entry fallback alongside Aircall automated row.
- **HR all rows** — temporarily on manual entry pending Ashby connector fix. Ashby's APPLICATION_HISTORY table only pulls 14,277 rows all with the same sync date, missing many stage history events.
- **OTIF D2C** — ShipHero sync timing means prior-day numbers can shift when late shipments are backdated overnight.
- **OTIF B2B** — Large wholesale orders completed in bulk can spike the average cycle time.
- **AR Past Due** — Definition changed 2026-04-17 to customer-level positive past-due: SUM(PASTDUE) aggregated per CUSTID, keeping only customers whose net past-due is positive. Historical snapshot values before 2026-04-17 used the Acumatica-email net calculation (all doc types where AGEDAYS > 0) and can read much lower (credits netted against invoices — sometimes negative). Before that (pre-Apr 10, 2026) an even older invoices-only filter was used.
- **Aircall** — Calls only. SMS and email engagements from other tools not included.
- **CSAT** — Only ~3-5% of conversations receive a rating. Daily CSAT scores are based on small samples (8-17 responses/day) and can be volatile. Rolling 7D smooths this out.
- **Total Open Tickets / Tickets Over 48 Hours** — Snapshot table (`INTERCOM_BACKLOG_DAILY`) frozen daily at 5:30 PM MT stores both counts; live query used for today before the snapshot runs. Weekly view shows the most recent snapshot in that week.
- **Fin AI Deflection** — Denominator is conversations Fin actually attempted (`AI_AGENT:last_answer_type = 'ai_answer'`). `assumed_resolution` + `confirmed_resolution` = deflected; `routed_to_team` = not deflected. Aligned with Intercom's native reporting (finalized 2026-05-06).
        """)



with tab_input:
    if not can_input:
        st.warning(f"⛔ Input access is restricted. You're logged in as **{current_user}**. Contact Richie to request access.")
    else:
            st.markdown("## ✏️ Manual Metric Entry")
            st.caption("Fill in any metrics below and hit Save All — one write per date, last entry wins.")
        
            input_date = st.date_input("Date", value=today, key="input_date")
            st.markdown("---")
        
            with st.form("manual_entry_form"):
                # Each field uses text_input so it can be blank (= skip on save)
                # Pre-fills with existing value if one exists for the selected date
                def prefill(key):
                    v = get_manual(key, input_date)
                    return str(int(v)) if v is not None and v == int(v) else (str(round(v, 1)) if v is not None else "")
        
                st.markdown("**💼 Sales**")
                sc1, sc2 = st.columns(2)
                with sc1:
                    open_quotes_s = st.text_input("Open Quotes Follow Up (%)", value=prefill("OPEN_QUOTES_FOLLOWUP"), placeholder="e.g. 100")
                with sc2:
                    st.caption("Engagements & email activity are now automated from Aircall + Outlook")
        
                st.markdown("**👥 HR**")
                hc1, hc2, hc3 = st.columns(3)
                with hc1:
                    hr_perf_s  = st.text_input("Performance Documentation Rate (%)", value=prefill("HR_PERFORMANCE_DOC"),     placeholder="e.g. 80")
                with hc2:
                    hr_train_s = st.text_input("Training & Compliance Rate (%)",      value=prefill("HR_TRAINING_COMPLIANCE"), placeholder="e.g. 90")
                with hc3:
                    hr_career_s = st.text_input("HR Process Doc Completion Rate (%)", value=prefill("HR_CAREER_PATH"),         placeholder="e.g. 75")
        
                st.markdown("**🏢 Business Operations**")
                bc1, _, _ = st.columns(3)
                with bc1:
                    blockers_s = st.text_input("Cross-functional Blockers (24h)", value=prefill("BLOCKERS_24H"), placeholder="e.g. 0")

                st.markdown("**🛒 Procurement**")
                st.caption("Weekly entry dated Monday-of-week (carry-forward fills Mon-Fri). GM Critical Stockouts (≤7d cover) drive the daily heatmap; DSI Combined drives the MTD runway view. Brand-level DSI values are reference-only. MIT45 + Uprising stockouts removed 2026-05-22 (operational focus = GM).")
                pc1, _pc2, _pc3, _pc4 = st.columns(4)
                with pc1:
                    proc_stockout_gm_s = st.text_input("Critical Stockouts — Golden Monk", value=prefill("PROC_CRITICAL_STOCKOUT_GM"), placeholder="e.g. 4")
                pc5, pc6, pc7, _pc8 = st.columns(4)
                with pc5:
                    proc_otd_s = st.text_input("Supplier OTD % (trailing 90d)", value=prefill("PROC_OTD_PCT_90D"), placeholder="e.g. 66.7")
                with pc6:
                    proc_single_s = st.text_input("% Critical Components Single-Sourced", value=prefill("PROC_PCT_SINGLE_SOURCED"), placeholder="e.g. 42.9")
                with pc7:
                    proc_supplier_sc_s = st.text_input("Supplier Scorecard (%)", value=prefill("PROC_SUPPLIER_SCORECARD"), placeholder="e.g. 92.5",
                                                       help="Weekly supplier scorecard score. ≥90% = green. Drives the Procurement daily/heatmap and lagging views (2026-05-28).")
                pc9, pc10, pc11, pc12 = st.columns(4)
                with pc9:
                    proc_dsi_comb_s = st.text_input("DSI — DTC Combined (days)", value=prefill("PROC_DSI_COMBINED_DAYS"), placeholder="e.g. 165")
                with pc10:
                    proc_dsi_gm_s = st.text_input("DSI — Golden Monk (ref)", value=prefill("PROC_DSI_GM_DAYS"), placeholder="e.g. 173")
                with pc11:
                    proc_dsi_mit45_s = st.text_input("DSI — MIT45 (ref)", value=prefill("PROC_DSI_MIT45_DAYS"), placeholder="e.g. 92")
                with pc12:
                    proc_dsi_up_s = st.text_input("DSI — Uprising (ref)", value=prefill("PROC_DSI_UP_DAYS"), placeholder="e.g. 194")
                pc13, _pc14, _pc15, _pc16 = st.columns(4)
                with pc13:
                    proc_total_skus_s = st.text_input("Total Active SKUs (denominator)", value=prefill("PROC_TOTAL_ACTIVE_SKUS"), placeholder="e.g. 190",
                                                       help="Denominator for the DSI lagging cell's '⚠ N/X critical' display. Count of active SKUs across GM/MIT45/UP after apparel + hex-variant filter.")

                st.markdown("**📈 Sales**")
                st.caption("Manual B2B revenue MTD override — data is scattered mid-Acumatica/Supabase migration. Latest in-month entry wins; falls back to FACT_DAILY_REVENUE if no current-month entry.")
                sc1, _sc2, _sc3, _sc4 = st.columns(4)
                with sc1:
                    b2b_mtd_s = st.text_input("B2B Revenue MTD ($)", value=prefill("MANUAL_B2B_REV_MTD"), placeholder="e.g. 1381217.50")

                st.markdown("")
                submitted = st.form_submit_button("💾 Save All", use_container_width=False)
                if submitted:
                    all_inputs = [
                        ("OPEN_QUOTES_FOLLOWUP",     open_quotes_s),
                        ("HR_PERFORMANCE_DOC",      hr_perf_s),
                        ("HR_TRAINING_COMPLIANCE",   hr_train_s),
                        ("HR_CAREER_PATH",            hr_career_s),
                        ("BLOCKERS_24H",             blockers_s),
                        ("PROC_CRITICAL_STOCKOUT_GM",                proc_stockout_gm_s),
                        ("PROC_DSI_COMBINED_DAYS",                   proc_dsi_comb_s),
                        ("PROC_DSI_GM_DAYS",                         proc_dsi_gm_s),
                        ("PROC_DSI_MIT45_DAYS",                      proc_dsi_mit45_s),
                        ("PROC_DSI_UP_DAYS",                         proc_dsi_up_s),
                        ("PROC_TOTAL_ACTIVE_SKUS",                   proc_total_skus_s),
                        ("PROC_OTD_PCT_90D",                         proc_otd_s),
                        ("PROC_PCT_SINGLE_SOURCED",                  proc_single_s),
                        ("PROC_SUPPLIER_SCORECARD",                  proc_supplier_sc_s),
                        ("MANUAL_B2B_REV_MTD",                       b2b_mtd_s),
                    ]
                    errors, saved = [], []
                    for key, raw in all_inputs:
                        if raw.strip() == "":
                            continue  # blank = skip, don't write
                        try:
                            val = float(raw.strip())
                        except ValueError:
                            errors.append(f"{key}: '{raw}' is not a number")
                            continue
                        result = save_manual(key, input_date, val)
                        if result is True:
                            saved.append(key)
                        else:
                            errors.append(f"{key}: {result}")
                    if errors:
                        st.error(f"❌ {'; '.join(errors)}")
                    elif not saved:
                        st.warning("Nothing to save — all fields were blank.")
                    else:
                        st.success(f"✅ Saved {len(saved)} metric(s) for {input_date}: {', '.join(saved)}")
                    st.rerun()
        
            st.markdown("---")
            st.markdown("**📋 Recent entries**")
            recent = q("""
                SELECT METRIC_DATE, METRIC_KEY, VALUE, ENTERED_AT
                FROM GOLD_V3_DB.PUBLIC.MANUAL_SCORECARD_INPUTS
                ORDER BY METRIC_DATE DESC, ENTERED_AT DESC
                LIMIT 20
            """)
            if not recent.empty:
                st.dataframe(recent, use_container_width=True, hide_index=True)
            else:
                st.caption("No entries yet.")