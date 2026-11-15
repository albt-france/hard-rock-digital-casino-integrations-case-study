-- 11 Compliance tracking: approval status per provider and state, and the three alert rules
-- (also implemented in src/compliance_alerts.py, which writes the weekly alert file).

CREATE OR REPLACE TABLE out_compliance_status AS
SELECT provider_id, state,
       SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) AS approved,
       SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) AS pending,
       SUM(CASE WHEN status = 'not_submitted' THEN 1 ELSE 0 END) AS not_submitted,
       SUM(CASE WHEN status = 'not_licensed' THEN 1 ELSE 0 END) AS not_licensed
FROM approvals
GROUP BY ALL
ORDER BY provider_id, state;

CREATE OR REPLACE TABLE out_compliance_alerts AS
-- 1. a game with a live date in a state where it is not approved: disable it there and inform compliance
SELECT 'P1 live without approval' AS alert, game_id AS entity, state, CAST(live_date AS VARCHAR) AS detail
FROM approvals WHERE live_date IS NOT NULL AND status <> 'approved'
UNION ALL
-- 2. supplier licence that expires within 60 days of the as-of date
SELECT 'P2 licence expiring', provider_id, state, CAST(expiry_date AS VARCHAR)
FROM licences WHERE licence_status = 'active' AND CAST(expiry_date AS DATE) <= DATE '2026-11-13' + INTERVAL 60 DAY
UNION ALL
-- 3. submission package incomplete for a game that is not yet approved everywhere it should be
SELECT 'P3 missing documents', game_id, state,
       concat_ws(', ', CASE WHEN NOT par_sheet THEN 'PAR sheet' END, CASE WHEN NOT rules_paytable THEN 'rules/paytable' END,
                 CASE WHEN NOT version_hash THEN 'version hash' END, CASE WHEN NOT rg_messaging_check THEN 'RG messaging check' END)
FROM approvals
WHERE status IN ('pending', 'not_submitted') AND NOT (par_sheet AND rules_paytable AND version_hash AND rg_messaging_check)
  AND provider_id <> 'Q';     -- Provider Q is still collecting its package: tracked in the onboarding plan, not alerted
