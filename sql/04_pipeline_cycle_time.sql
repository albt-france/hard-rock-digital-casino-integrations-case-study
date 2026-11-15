-- 04 Integration pipeline: cycle time by stage, open items, and state approval time per game.

-- Cycle time of finished stages, by stage, route and state (state only for approval and launch)
CREATE OR REPLACE TABLE out_stage_cycle_time AS
SELECT stage, route, COALESCE(state, 'All') AS state, COUNT(*) AS n,
       MEDIAN(DATEDIFF('day', start_date, end_date)) AS median_days,
       QUANTILE_CONT(DATEDIFF('day', start_date, end_date), 0.8) AS p80_days,
       AVG(blocked_days) AS avg_blocked_days,
       AVG(CASE WHEN end_date > planned_end_date THEN 1 ELSE 0 END) AS late_share
FROM pipeline
WHERE status = 'done'
GROUP BY ALL
ORDER BY stage, route, state;

-- Open pipeline items (in progress, blocked or not started) with days open at the as-of date
CREATE OR REPLACE TABLE out_pipeline_open AS
SELECT project_id, provider_id, route, stage, state, status, start_date, planned_end_date, blocker,
       DATEDIFF('day', start_date, DATE '2026-11-13') AS days_open
FROM pipeline
WHERE status <> 'done'
ORDER BY project_id, start_date;

-- Game-level state approval time (submission -> approval), by state and quarter of submission.
-- This is where the State C bottleneck shows: same games, same documents, twice the wait.
CREATE OR REPLACE TABLE out_approval_time AS
SELECT state, date_trunc('quarter', CAST(submitted AS DATE))::DATE AS quarter, COUNT(*) AS approvals,
       MEDIAN(DATEDIFF('day', CAST(submitted AS DATE), CAST(approved AS DATE))) AS median_days,
       QUANTILE_CONT(DATEDIFF('day', CAST(submitted AS DATE), CAST(approved AS DATE)), 0.9) AS p90_days
FROM approvals
WHERE status = 'approved'
GROUP BY ALL
ORDER BY state, quarter;
