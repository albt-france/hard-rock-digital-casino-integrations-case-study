# Simulation assumptions (SIMULATED data)

Everything in `data/simulated/` is invented by `src/simulate.py` (seed 42). Providers ("Provider A" ... "Provider T"),
aggregators ("Aggregator X", "Aggregator Y"), game titles, players and states ("State A, B, C") are **fictional**. Nothing
here describes Hard Rock Digital's catalogue, partners or results.

## Scope
- 12 months: 2025-10-01 to 2026-09-30 (aligned with the latest regulator month). Pipeline and compliance status "as of"
  2026-11-13.
- 20 providers: 13 live (A-M), 2 in onboarding (N via Aggregator Y, Q direct), 5 candidates (O, P, R, S, T).
- 605 catalogue entries (530 live, including 30 duplicates; 65 in certification), 3 states.

## Calibration on public data
| Item | Value used | Public anchor |
|---|---|---|
| Slot theoretical RTP | uniform 93.5% - 96.2% | PA online slots paid back 94.7% of wagers (Oct 2025 - Sep 2026; operators 93.5% - 95.3%) |
| Table / live RTP | 97.3% - 99.5% | PA online tables hold 1.8% of wagers |
| Jackpot slots RTP | 92% - 95% | lower base RTP, jackpot variance |
| Operator size | ~$13-18M GGR per month over 3 states | a mid-size operator: NJ online casino win is ~$260M a month; the "Hard Rock Bet" skin ~$17M |
| Growth | +1.2% per month trend + new content | NJ online casino win +15% YoY |

## Demand model (game x state x day)
- Expected launches = base x game popularity (log-normal) x game-type weight x state size (A 1.0, B 0.72, C 0.48)
  x day of week (weekend +12-18%) x trend x **novelty** (1 + 1.4 exp(-age / 10 days)) x **cannibalisation**
  ((live games in the state / 300)^-0.55).
- Game-type weights make live dealer and jackpot slots earn more per game than plain slots (the "shelf gap").
- Rounds per session: slots 110, jackpot 100, tables 45, live 32. Average bet: $1.25, $1.40, $9, $16 (x log-normal).
- Player wins = wagers x RTP + Normal(0, sd per round x bet x sqrt(rounds)). sd per round by volatility: low 3, medium 6,
  high 12, very high 22 (x1.15 for jackpot slots); tables 1.1, live 1.4.

## Integration and compliance
- Stage durations (log-normal medians): agreement 14 days (aggregator) / 28 (direct); technical integration 16 / 56;
  QA 10 / 21; lab certification 24; state approval 14 (A), 17 (B), **31 (C)**; launch 4. 20-45% of stages hit a blocker
  of 3-18 days.
- Content fees (share of GGR): provider 10-14%; aggregator 3.0% (X) or 2.5% (Y) on top.
- Wallet: one debit per round, a credit per winning round; timeouts 0.04% (direct) / 0.09% (aggregator) trigger
  rollbacks; failed rollbacks 0.05%. p50 / p95 latency: direct 70 / 160 ms, Aggregator X 185 / 430, Aggregator Y 205 / 480.

## Planted events (answer key: `simulated/_hidden_truth.csv`, read only at the end of the notebook)
1. Provider F update: launch error rate ~14% for 6 days (2026-05-12 to 05-17), load time x2.6.
2. RTP: C-007 (very high volatility) forced to 89.0% vs 96.0% over the last 90 days, inside its band (false signal);
   G-012 deployed at 92.1% instead of 96.0% from 2026-06-15 (true problem).
3. State C approvals take about twice as long; Provider N waits there.
4. Novelty effect on every new game.
5. Provider H moves from Aggregator X to direct on 2026-04-01 (lower latency, errors and fees).
6. 30 of its 40 old aggregator entries stay live (duplicates, 35% of the traffic of each pair).
7. Provider K: 8-15% failed rollbacks on 7 days in July-August.
8. Promotion PR06: 20 free spins, 40,000 players, random 10% hold-out; true effect about +$4.5 GGR per player plus
   +6 points of activity; players who use their spins are the more engaged ones (selection bias).
Compliance plants: 3 Provider L games live in State B without approval, 6 Provider N games with missing documents,
2 supplier licences expiring within 60 days.

## What the roadmap score assumes
- Elasticity of a game type's GGR to its number of games: 0.15 x demand/supply ratio, capped 0.05-0.5.
- Effort: integration estimate + 0.1 person-week per game per state submission. Confidence: 0.5 + 0.2 + 0.2 + 0.1.
These are judgement calls; the sensitivity analysis (one-at-a-time and 5,000 randomised runs) tests them.
