-- 01 Staging: typed views over the SIMULATED files. {SIM} is replaced by data/simulated at run time (src/run_sql.py).
-- One view per source table; later files only read these views.

CREATE OR REPLACE VIEW providers AS
SELECT * FROM read_csv_auto('{SIM}/providers.csv', header = true);

CREATE OR REPLACE VIEW games AS
SELECT game_id, provider_id, title, game_type, volatility, rtp_theoretical, sd_per_round, avg_bet,
       CAST(release_date AS DATE) AS release_date, CAST(retired_date AS DATE) AS retired_date,
       route, aggregator, provider_fee, aggregator_fee, status, states_approved
FROM read_csv_auto('{SIM}/games.csv', header = true);

-- game x state x day; joined once to the game attributes the later queries need
CREATE OR REPLACE VIEW game_daily AS
SELECT d.*, CAST(d."date" AS DATE) AS day, g.game_type, g.volatility, g.rtp_theoretical, g.sd_per_round, g.avg_bet,
       g.route, g.aggregator, g.title, g.release_date,
       d.ggr * (1 - g.provider_fee - g.aggregator_fee) AS margin_after_content_fees
FROM read_parquet('{SIM}/game_daily.parquet') d
JOIN games g USING (game_id);

CREATE OR REPLACE VIEW approvals AS
SELECT * FROM read_csv_auto('{SIM}/game_approvals.csv', header = true);

CREATE OR REPLACE VIEW pipeline AS
SELECT * FROM read_csv_auto('{SIM}/integration_pipeline.csv', header = true);

CREATE OR REPLACE VIEW licences AS
SELECT * FROM read_csv_auto('{SIM}/provider_licences.csv', header = true);

CREATE OR REPLACE VIEW wallet AS
SELECT *, CAST("date" AS DATE) AS day FROM read_csv_auto('{SIM}/wallet_api_logs.csv', header = true);

CREATE OR REPLACE VIEW promotions AS
SELECT * FROM read_csv_auto('{SIM}/promotions.csv', header = true);

CREATE OR REPLACE VIEW promo_players AS
SELECT * FROM read_csv_auto('{SIM}/promo_players.csv', header = true);

-- quick data-quality checks: these must all return 0 (the runner prints them)
CREATE OR REPLACE TABLE out_dq_checks AS
SELECT 'negative wagers' AS check_name, COUNT(*) AS n FROM game_daily WHERE wagers < 0
UNION ALL SELECT 'sessions > launch attempts', COUNT(*) FROM game_daily WHERE sessions > launch_attempts
UNION ALL SELECT 'ggr <> wagers - wins', COUNT(*) FROM game_daily WHERE ABS(ggr - (wagers - player_wins)) > 0.02
UNION ALL SELECT 'daily rows for unknown games', COUNT(*) FROM read_parquet('{SIM}/game_daily.parquet') d
          WHERE NOT EXISTS (SELECT 1 FROM games g WHERE g.game_id = d.game_id);
