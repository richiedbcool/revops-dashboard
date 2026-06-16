-- Read-only service account for the hosted RevOps Signal dashboard.
-- Run as ACCOUNTADMIN (or a role with CREATE ROLE / CREATE USER / CREATE WAREHOUSE).
-- Auth is key-pair only (no password, no MFA) — see DEPLOY-revops-dashboard.md.

-- 1. Dedicated read-only role
CREATE ROLE IF NOT EXISTS REVOPS_DASHBOARD_RO;

-- 2. Small dedicated warehouse (auto-suspends fast to keep cost near zero)
CREATE WAREHOUSE IF NOT EXISTS REVOPS_DASHBOARD_WH
  WAREHOUSE_SIZE = 'XSMALL'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE
  INITIALLY_SUSPENDED = TRUE;
GRANT USAGE ON WAREHOUSE REVOPS_DASHBOARD_WH TO ROLE REVOPS_DASHBOARD_RO;

-- 3. Scope the role to ONLY the REVOPS_* views the dashboard reads
GRANT USAGE ON DATABASE GOLD_V3_DB TO ROLE REVOPS_DASHBOARD_RO;
GRANT USAGE ON SCHEMA GOLD_V3_DB.SALES TO ROLE REVOPS_DASHBOARD_RO;

-- Existing REVOPS_* views (run after views exist):
GRANT SELECT ON ALL VIEWS IN SCHEMA GOLD_V3_DB.SALES TO ROLE REVOPS_DASHBOARD_RO;
-- Auto-grant to views created later:
GRANT SELECT ON FUTURE VIEWS IN SCHEMA GOLD_V3_DB.SALES TO ROLE REVOPS_DASHBOARD_RO;
-- (Tighten further if you want: replace the two grants above with explicit
--  GRANT SELECT ON VIEW GOLD_V3_DB.SALES.REVOPS_xxx TO ROLE REVOPS_DASHBOARD_RO;
--  per view, so the role can read ONLY the dashboard's views.)

-- IMPORTANT: the dashboard also queries one TABLE directly (the US-state map
-- geometry). Granting views alone is NOT enough — the table needs its own grant,
-- otherwise the app crashes on the choropleth query with "object does not exist
-- or not authorized".
GRANT SELECT ON TABLE GOLD_V3_DB.SALES.REVOPS_US_STATE_PATHS TO ROLE REVOPS_DASHBOARD_RO;

-- 4. Service-account user — no password, key-pair auth only
CREATE USER IF NOT EXISTS REVOPS_DASHBOARD_SVC
  DEFAULT_ROLE = REVOPS_DASHBOARD_RO
  DEFAULT_WAREHOUSE = REVOPS_DASHBOARD_WH
  DEFAULT_NAMESPACE = 'GOLD_V3_DB.SALES'
  MUST_CHANGE_PASSWORD = FALSE
  COMMENT = 'Service account for hosted RevOps Signal Streamlit dashboard (read-only)';
GRANT ROLE REVOPS_DASHBOARD_RO TO USER REVOPS_DASHBOARD_SVC;

-- 5. Attach the public key (paste the body of rsa_key.pub — no BEGIN/END lines,
--    no newlines). Generate the pair per DEPLOY-revops-dashboard.md.
ALTER USER REVOPS_DASHBOARD_SVC SET RSA_PUBLIC_KEY = 'PASTE_PUBLIC_KEY_BODY_HERE';

-- Verify:
-- DESC USER REVOPS_DASHBOARD_SVC;        -- check RSA_PUBLIC_KEY_FP is set
-- SHOW GRANTS TO ROLE REVOPS_DASHBOARD_RO;
