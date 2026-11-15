-- 09 Aggregator vs direct: Provider H, 90 days before vs after its move to a direct integration (2026-04-01).
-- Compares wallet latency, launch errors, load time and margin after content fees, per route actually used.

CREATE OR REPLACE TABLE out_route_switch AS
WITH perf AS (
    SELECT CASE WHEN day < DATE '2026-04-01' THEN '1 before (Aggregator X)'
                WHEN route = 'Direct' THEN '2 after: direct entries'
                ELSE '3 after: old aggregator entries' END AS period,
           SUM(launch_errors) / SUM(launch_attempts) AS launch_error_rate,
           AVG(avg_load_ms) AS avg_load_ms,
           SUM(margin_after_content_fees) / SUM(ggr) AS margin_rate,
           SUM(ggr) AS ggr
    FROM game_daily
    WHERE provider_id = 'H' AND day BETWEEN DATE '2026-01-01' AND DATE '2026-06-29'
    GROUP BY ALL
), lat AS (
    SELECT CASE WHEN day < DATE '2026-04-01' THEN '1 before (Aggregator X)'
                WHEN route = 'Direct' THEN '2 after: direct entries'
                ELSE '3 after: old aggregator entries' END AS period,
           SUM(CASE WHEN call_type = 'debit' AND status = 'OK' THEN latency_p95_ms * n_calls END)
             / SUM(CASE WHEN call_type = 'debit' AND status = 'OK' THEN n_calls END) AS debit_p95_ms,
           SUM(CASE WHEN status = 'ERR_TIMEOUT' THEN n_calls END) / SUM(n_calls) AS timeout_rate
    FROM wallet
    WHERE provider_id = 'H' AND day BETWEEN DATE '2026-01-01' AND DATE '2026-06-29'
    GROUP BY ALL
)
SELECT * FROM perf JOIN lat USING (period) ORDER BY period;
