-- 05 Wallet API health: error rates and latency by provider route and day; rollback failures.

-- Daily health per provider and route. Business declines (insufficient funds) and idempotent replays are not errors.
CREATE OR REPLACE TABLE out_wallet_daily AS
SELECT day, provider_id, route,
       SUM(n_calls) AS calls,
       SUM(CASE WHEN status IN ('ERR_TIMEOUT', 'ERR_ROLLBACK_FAILED') THEN n_calls ELSE 0 END) AS tech_errors,
       SUM(CASE WHEN status IN ('ERR_TIMEOUT', 'ERR_ROLLBACK_FAILED') THEN n_calls ELSE 0 END) / SUM(n_calls) AS tech_error_rate,
       SUM(CASE WHEN call_type = 'rollback' THEN n_calls ELSE 0 END) AS rollbacks,
       SUM(CASE WHEN status = 'ERR_ROLLBACK_FAILED' THEN n_calls ELSE 0 END) AS rollback_failed,
       SUM(CASE WHEN status = 'OK_IDEMPOTENT_REPLAY' THEN n_calls ELSE 0 END) AS idempotent_replays,
       -- call-weighted p95 of successful debits: a simple, explainable approximation of the daily p95
       SUM(CASE WHEN call_type = 'debit' AND status = 'OK' THEN latency_p95_ms * n_calls END)
         / SUM(CASE WHEN call_type = 'debit' AND status = 'OK' THEN n_calls END) AS debit_p95_ms
FROM wallet
GROUP BY ALL;

-- Rollback failures: a failed rollback means a debit that was never reversed, so a player balance may be wrong.
-- Flag any provider-day above 2% with at least 5 failures (normal level ~0.05%) and estimate the money at risk with the provider's average bet.
CREATE OR REPLACE TABLE out_rollback_alerts AS
WITH bet AS (
    SELECT provider_id, SUM(wagers) / SUM(rounds) AS avg_bet FROM game_daily GROUP BY provider_id
)
SELECT w.day, w.provider_id, w.route, w.rollbacks, w.rollback_failed,
       w.rollback_failed / NULLIF(w.rollbacks, 0) AS rollback_fail_rate,
       w.rollback_failed * b.avg_bet AS balance_at_risk_usd
FROM out_wallet_daily w JOIN bet b USING (provider_id)
WHERE w.rollback_failed / NULLIF(w.rollbacks, 0) > 0.02 AND w.rollback_failed >= 5
ORDER BY w.day;
