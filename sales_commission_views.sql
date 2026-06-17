-- ============================================================
-- Secure views for the MTD sales commission app (sales_commission_mtd.py)
-- Run as a role that can read RAW_V2_DB (e.g. CLAUDE_MCP_ROLE / SYSADMIN).
--
-- Why secure views: the app's service account REVOPS_DASHBOARD_RO has NO
-- access to RAW_V2_DB (only GOLD_V3_DB.SALES.REVOPS_* + its warehouse). These
-- views live in GOLD_V3_DB.SALES (role already has schema USAGE), are owned by a
-- role that CAN read raw, and are SECURE so the consumer can't see the definition
-- or reach underlying PII. V_SALES_REP_ROLES deliberately exposes only name +
-- title — never ADP pay columns (PAY_RATE, PAY_FREQUENCY).
--
-- Validated revenue math (2026-06-17, reproduces the sales-by-salesperson export
-- to the dollar): revenue = shipment-line QUANTITY x order-line UNIT_PRICE,
-- period = shipment COMPLETED_AT in the current month, #orders = distinct
-- SO_NUMBER, Sales Admin excluded. Price is on the ORDER line (shipment line
-- ENTERED_UNIT_PRICE is empty).
-- ============================================================

CREATE OR REPLACE SECURE VIEW GOLD_V3_DB.SALES.V_SALES_COMMISSION_MTD AS
WITH ln AS (
  SELECT so.SALESPERSON, so.SO_NUMBER,
         TRY_TO_DATE(LEFT(s.COMPLETED_AT,10)) AS comp_date,
         TRY_CAST(sl.QUANTITY AS NUMBER(18,4)) * TRY_CAST(sol.UNIT_PRICE AS NUMBER(18,4)) AS rev
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
GROUP BY SALESPERSON;

CREATE OR REPLACE SECURE VIEW GOLD_V3_DB.SALES.V_SALES_REP_ROLES AS
SELECT FORMATTED_NAME, POSITION_TITLE, WORKER_STATUS, DEPARTMENT_NAME
FROM RAW_V2_DB.ADP.WORKERS
WHERE WORKER_STATUS = 'Active';

GRANT SELECT ON VIEW GOLD_V3_DB.SALES.V_SALES_COMMISSION_MTD TO ROLE REVOPS_DASHBOARD_RO;
GRANT SELECT ON VIEW GOLD_V3_DB.SALES.V_SALES_REP_ROLES      TO ROLE REVOPS_DASHBOARD_RO;
