-- 06 Game launch errors: provider daily error rate vs its own trailing 28-day baseline (window function),
-- an alert when the rate is both 3x the baseline and above 3%, and the GGR lost on alert days.

CREATE OR REPLACE TABLE out_launch_errors AS
WITH daily AS (
    SELECT day, provider_id, SUM(launch_attempts) AS attempts, SUM(launch_errors) AS errors,
           SUM(sessions) AS sessions, SUM(ggr) AS ggr, AVG(avg_load_ms) AS avg_load_ms
    FROM game_daily GROUP BY ALL
), base AS (
    SELECT *, errors / attempts AS error_rate,
           SUM(errors) OVER w / SUM(attempts) OVER w AS baseline_rate,
           SUM(ggr) OVER w / SUM(sessions) OVER w AS ggr_per_session_baseline
    FROM daily
    WINDOW w AS (PARTITION BY provider_id ORDER BY day ROWS BETWEEN 28 PRECEDING AND 1 PRECEDING)
)
SELECT *,
       (error_rate > 3 * baseline_rate AND error_rate > 0.03) AS alert,
       -- sessions that failed beyond the normal rate, valued at the provider's usual GGR per session
       GREATEST(errors - baseline_rate * attempts, 0) * ggr_per_session_baseline AS ggr_lost_est
FROM base
ORDER BY provider_id, day;
