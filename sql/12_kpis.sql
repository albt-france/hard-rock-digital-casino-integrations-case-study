-- 12 Headline KPIs for the overview and the dashboard (last full quarter: Jul-Sep 2026, vs Apr-Jun 2026).

CREATE OR REPLACE TABLE out_kpis AS
WITH q AS (
    SELECT CASE WHEN day >= DATE '2026-07-01' THEN 'Q3' WHEN day >= DATE '2026-04-01' THEN 'Q2' END AS qtr, *
    FROM game_daily WHERE day >= DATE '2026-04-01'
)
SELECT qtr, SUM(ggr) AS ggr, SUM(margin_after_content_fees) AS margin, SUM(sessions) AS sessions,
       SUM(players) AS player_days, COUNT(DISTINCT game_id) AS live_games, COUNT(DISTINCT provider_id) AS live_providers,
       SUM(launch_errors) / SUM(launch_attempts) AS launch_error_rate
FROM q GROUP BY qtr ORDER BY qtr;

-- New games released per month (first day live anywhere), excluding direct copies of existing games
CREATE OR REPLACE TABLE out_new_games AS
SELECT date_trunc('month', first_day)::DATE AS month, game_type, COUNT(*) AS new_games
FROM (SELECT game_id, game_type, MIN(day) AS first_day FROM game_daily WHERE game_id NOT LIKE 'HD-%' GROUP BY ALL)
WHERE first_day > (SELECT MIN(day) FROM game_daily)
GROUP BY ALL ORDER BY month;
