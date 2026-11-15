-- 08 Duplicate catalogue entries: the same game (provider + normalised title) live under more than one game_id,
-- typically after a provider moves from an aggregator to a direct integration and the old entries stay switched on.

CREATE OR REPLACE TABLE out_duplicates AS
WITH norm AS (
    SELECT game_id, provider_id, route, aggregator, status, rtp_theoretical,
           lower(regexp_replace(title, '[^A-Za-z0-9]', '', 'g')) AS title_key
    FROM games
    WHERE status = 'live'
), groups AS (
    SELECT provider_id, title_key, COUNT(*) AS copies, string_agg(game_id || ' (' || route || ')', ', ') AS entries
    FROM norm GROUP BY ALL HAVING COUNT(*) > 1
), perf AS (    -- what the old aggregator copies still earn and cost since the switch
    SELECT n.provider_id, n.title_key, n.route,
           SUM(d.ggr) AS ggr, SUM(d.ggr * g.aggregator_fee) AS aggregator_fees, SUM(d.sessions) AS sessions
    FROM norm n JOIN game_daily d USING (game_id) JOIN games g USING (game_id)
    WHERE d.day >= DATE '2026-04-01'
    GROUP BY ALL
)
SELECT gr.provider_id, gr.title_key, gr.copies, gr.entries,
       SUM(CASE WHEN p.route = 'Aggregator' THEN p.ggr END) AS ggr_old_copy,
       SUM(CASE WHEN p.route = 'Direct' THEN p.ggr END) AS ggr_direct_copy,
       SUM(p.aggregator_fees) AS aggregator_fees_since_switch,
       SUM(CASE WHEN p.route = 'Aggregator' THEN p.sessions END) / SUM(p.sessions) AS session_share_old_copy
FROM groups gr JOIN perf p USING (provider_id, title_key)
GROUP BY ALL
ORDER BY ggr_old_copy DESC;
