-- 03 Game life curve (novelty effect): average daily sessions per game by age (days since first release),
-- for games released inside the simulated year with at least 60 days of history. Indexed to days 45-60 (steady state).

CREATE OR REPLACE TABLE out_lifecycle AS
WITH first_live AS (
    SELECT game_id, MIN(day) AS first_day
    FROM game_daily
    WHERE game_id NOT LIKE 'HD-%'                       -- direct copies of existing games are not new content
    GROUP BY game_id
), aged AS (
    SELECT d.game_id, DATEDIFF('day', f.first_day, d.day) AS age, SUM(d.sessions) AS sessions, SUM(d.ggr) AS ggr
    FROM game_daily d JOIN first_live f USING (game_id)
    WHERE f.first_day > (SELECT MIN(day) FROM game_daily)
      AND f.first_day <= (SELECT MAX(day) FROM game_daily) - INTERVAL 60 DAY
    GROUP BY ALL
), steady AS (
    SELECT game_id, AVG(sessions) AS steady_sessions FROM aged WHERE age BETWEEN 45 AND 60 GROUP BY game_id
)
SELECT a.age, COUNT(*) AS games, AVG(a.sessions) AS avg_sessions,
       AVG(a.sessions / NULLIF(s.steady_sessions, 0)) AS index_vs_steady
FROM aged a JOIN steady s USING (game_id)
WHERE a.age <= 60
GROUP BY a.age
ORDER BY a.age;
