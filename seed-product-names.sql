-- Friendly MIT45 product names for the Market Analysis tables.
-- The Nielsen/SPINS feeds only give raw strings like "MIT 45 MTRG SPCS EXTR LQD BTL 0.5 OZ".
-- This lookup maps each UPC to a clean family name; the dashboard LEFT JOINs it
-- (on LPAD(REPLACE(upc,'-',''),12,'0')) and rolls a family's UPCs into one row.
--
-- TO ADD A NEW SKU: insert one row here (UPC = 12 digits, no dashes). Every dashboard
-- table picks it up automatically — no app code change needed.
--
-- Run as a role that can write GOLD_V3_DB.SALES (e.g. CLAUDE_MCP_ROLE / sysadmin).

CREATE OR REPLACE TABLE GOLD_V3_DB.SALES.REVOPS_PRODUCT_NAMES (
  upc_core      STRING,   -- 12-digit UPC, no dashes
  product_clean STRING,   -- friendly family name shown in the dashboard
  brand_family  STRING    -- parent brand (MIT45)
) AS
SELECT * FROM VALUES
  ('068039289333','Liquid Gold','MIT45'),     -- KRTM EXTR LQD BTL 2 OZ
  ('068058539638','Liquid Gold','MIT45'),     -- KRTM EXTR LQD BTL 2 OZ (2nd UPC)
  ('081014970003','Liquid Gold','MIT45'),     -- KRTM LQD BOX 0.5 FL OZ
  ('068020185718','SKES','MIT45'),            -- MTRG SPCS EXTR LQD BTL 0.5 OZ
  ('068609197464','SKES','MIT45'),            -- MTRG SPCS EXTR LQD BAG 0.5 OZ
  ('068020185721','SKES','MIT45'),            -- MTRG SPCS EXTR CPSL IN BOX 2 CT
  ('070874470586','Super K','MIT45'),         -- SPR K MTRG SPCS LQD BTL 1 OZ
  ('070874470587','Super K','MIT45'),         -- SPR K MTRG SPCS LQD BTL 1 OZ (2nd UPC)
  ('081014970007','Super K','MIT45'),         -- Super K Purple
  ('081014970001','MITGO','MIT45'),           -- Mitgo 12/dsp
  ('068435799955','Mit45 Capsules','MIT45')   -- ENHN KRTM MTRG SPCS PC CRDD 10 CT
AS t(upc_core, product_clean, brand_family);

GRANT SELECT ON TABLE GOLD_V3_DB.SALES.REVOPS_PRODUCT_NAMES TO ROLE REVOPS_DASHBOARD_RO;
