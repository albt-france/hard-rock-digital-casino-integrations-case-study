-- 10 Promotions: overview of the free-spin campaigns, and the PR06 test against its random 10% hold-out.

CREATE OR REPLACE TABLE out_promotions AS
SELECT promo_id, provider_id, game_id, states, start_date, end_date, mechanic, players_targeted, players_reached,
       cost_usd, cost_usd / NULLIF(players_reached, 0) AS cost_per_player_reached, has_holdout
FROM promotions
ORDER BY start_date;

-- Group means for the test (the notebook adds confidence intervals). The naive comparison (players who used their
-- spins vs everyone else) is shown next to the randomised one to make the selection bias visible.
CREATE OR REPLACE TABLE out_promo_test AS
SELECT 'randomised: ' || "group" AS comparison, COUNT(*) AS players,
       AVG(ggr_post_28d) AS ggr_post, AVG(ggr_pre_28d) AS ggr_pre, AVG(active_post_28d) AS active_post,
       AVG(free_spin_cost_usd) AS cost_per_player
FROM promo_players GROUP BY "group"
UNION ALL
SELECT CASE WHEN spins_used > 0 THEN 'naive: used spins' ELSE 'naive: did not use' END, COUNT(*),
       AVG(ggr_post_28d), AVG(ggr_pre_28d), AVG(active_post_28d), AVG(free_spin_cost_usd)
FROM promo_players WHERE "group" = 'treatment' GROUP BY ALL
ORDER BY comparison;
