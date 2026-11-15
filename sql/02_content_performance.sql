-- 02 Content performance: provider x month, game type demand vs catalogue supply, and game ranking.

-- Provider x month: GGR, margin after content fees, players (sum of daily players: player-days), sessions, live games
CREATE OR REPLACE TABLE out_provider_monthly AS
SELECT date_trunc('month', day)::DATE AS month, provider_id, state,
       SUM(ggr) AS ggr, SUM(margin_after_content_fees) AS margin, SUM(wagers) AS wagers,
       SUM(players) AS player_days, SUM(sessions) AS sessions, COUNT(DISTINCT game_id) AS live_games
FROM game_daily
GROUP BY ALL;

-- Demand vs supply by game type, last 90 days: share of GGR / sessions vs share of the live catalogue.
-- A ratio above 1 means the type earns more than its share of the shelf: an under-supplied type.
CREATE OR REPLACE TABLE out_type_gap AS
WITH last90 AS (
    SELECT * FROM game_daily WHERE day > (SELECT MAX(day) FROM game_daily) - INTERVAL 90 DAY
), demand AS (
    SELECT game_type, SUM(ggr) AS ggr, SUM(sessions) AS sessions, COUNT(DISTINCT game_id) AS live_games
    FROM last90 GROUP BY game_type
)
SELECT game_type, ggr, sessions, live_games,
       ggr / SUM(ggr) OVER () AS ggr_share,
       sessions / SUM(sessions) OVER () AS session_share,
       live_games / SUM(live_games) OVER () AS catalogue_share,
       (ggr / SUM(ggr) OVER ()) / (live_games / SUM(live_games) OVER ()) AS demand_supply_ratio,
       ggr / live_games / 90 AS ggr_per_game_day
FROM demand
ORDER BY demand_supply_ratio DESC;

-- Game ranking inside its type over the last 90 days (window function), with each game's share of its provider's GGR
CREATE OR REPLACE TABLE out_game_rank AS
WITH g90 AS (
    SELECT game_id, provider_id, game_type, title, SUM(ggr) AS ggr, SUM(sessions) AS sessions, SUM(players) AS player_days
    FROM game_daily
    WHERE day > (SELECT MAX(day) FROM game_daily) - INTERVAL 90 DAY
    GROUP BY ALL
)
SELECT *,
       RANK() OVER (PARTITION BY game_type ORDER BY ggr DESC) AS rank_in_type,
       ggr / SUM(ggr) OVER (PARTITION BY provider_id) AS share_of_provider_ggr,
       ggr / SUM(ggr) OVER () AS share_of_total
FROM g90;
