-- 07 Realised RTP vs theoretical RTP, last 90 days, with statistical bounds.
-- Over n rounds, realised RTP ~ theoretical RTP +/- z * sd_per_round / sqrt(n) (central limit theorem).
-- With wagers in dollars the variance of total player wins is (sd_per_round * bet)^2 * rounds, summed over days.
-- Two rules: naive = "more than 3 points below theory"; statistical = |z| > 3 (watch) and |z| > 4 (escalate).

CREATE OR REPLACE TABLE out_rtp_check AS
WITH w AS (
    SELECT game_id, provider_id, game_type, volatility, rtp_theoretical,
           SUM(rounds) AS rounds, SUM(wagers) AS wagers, SUM(player_wins) AS wins,
           SUM(POWER(sd_per_round * avg_bet, 2) * rounds) AS var_wins
    FROM game_daily
    WHERE day > (SELECT MAX(day) FROM game_daily) - INTERVAL 90 DAY
    GROUP BY ALL
)
SELECT *, wins / wagers AS rtp_realised,
       wins / wagers - rtp_theoretical AS gap,
       (wins - rtp_theoretical * wagers) / SQRT(var_wins) AS z,
       3 * SQRT(var_wins) / wagers AS band_3sd,                     -- half-width of the 3-sigma band, in RTP points
       (wins / wagers - rtp_theoretical) < -0.03 AS naive_flag,
       CASE WHEN ABS((wins - rtp_theoretical * wagers) / SQRT(var_wins)) > 4 THEN 'escalate'
            WHEN ABS((wins - rtp_theoretical * wagers) / SQRT(var_wins)) > 3 THEN 'watch'
            ELSE 'ok' END AS stat_flag
FROM w
WHERE rounds > 0;
