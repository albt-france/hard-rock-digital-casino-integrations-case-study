# PRD: Provider Q onboarding (direct integration)

> **SIMULATED scenario.** Provider Q, the states and every figure are fictional and come from this study's simulation.
> The structure follows the job: one provider, from requirements to launch and post-launch follow-up.
> Regulatory references are to public documents (GLI-19 v4.0, New Jersey DGE pages); they are not legal advice.

| | |
|---|---|
| **Status** | In delivery: technical integration (blocked: currency/decimal mismatch on credits) |
| **Author** | Product Analyst, Casino Integrations |
| **Approvers** | Product Manager (Casino Integrations), Engineering lead, Compliance lead |
| **Consulted** | Platform (wallet, player account, geolocation), QA, Casino Operations, Marketing (promotions), Customer Support |
| **External** | Provider Q integration manager and account manager; independent test lab |
| **Last update** | 2026-11-13 |

## 1. Objective
Launch Provider Q's portfolio of **40 games** (30 slots, 6 jackpot slots, 4 RNG table games) in **States A and B**,
with no compliance finding, and keep it healthy for the first 60 days. State C follows once Provider Q's supplier
licence there is granted.

**Commitment date (external): 2027-03-14** (P80 of the Monte-Carlo forecast; P50 is 2027-02-25).

## 2. Why now (data)
- The contract was signed in October 2026, before this roadmap analysis. Provider Q mainly adds slots, and slots are
  already **over-supplied** (77% of the live catalogue for 54% of GGR, last 90 days). Expect a modest gain from its
  slots; its **6 jackpot slots** fill a real gap (jackpot slots: 8.5% of the catalogue for 12% of GGR).
- So the launch plan **puts the jackpot slots and the best-rated slots (from the provider's data in other markets)
  in wave 1**, and waits for 30 days of steady state before judging the rest (new games run ~40% above their steady
  level in week 1 and settle after about three weeks).
- Next providers after Q (roadmap score): Provider O (live dealer studio), then Provider R (jackpot network via
  Aggregator Y). See `docs/` report, page 6.

## 3. Scope
**In scope**
1. Seamless wallet integration: balance, debit, credit, rollback; idempotent on transaction id (user stories CI-04 to CI-08).
2. Game launch on desktop and mobile web/app; session token, session expiry, interrupted-game recovery (CI-01, CI-02).
3. Geolocation check before launch and during the session; games available only in approved states (CI-03, CI-10).
4. Jackpot contributions, jackpot wins and jackpot reporting (CI-09).
5. Responsible-gaming controls applied to Provider Q games: limits, time-outs, reality checks, self-exclusion (CI-11, CI-12).
6. Regulatory and finance reporting feeds per game, per state, per day (CI-13).
7. Per-state game disable ("kill switch") and post-launch monitoring (CI-14, CI-15).
8. Catalogue (CMS) metadata: one canonical game id per game, certified version, approved states (CI-10).

**Out of scope (this release)**
- State C launch (supplier licence pending). Tracked as a follow-up release.
- Free-spin / bonus tooling for Provider Q games (phase 2, after the provider's promotions API is certified).
- Tournaments, live dealer (not in the portfolio).

## 4. Dependencies
| Dependency | Owner | Needed by | Status |
|---|---|---|---|
| Supplier licence, States A and B | Provider Q / Compliance | Before state submission | Active |
| Supplier licence, State C | Provider Q / Compliance | State C release | Pending |
| Lab certification of 40 games (GLI-19 based) | Provider Q / test lab | Before state submission | Not started (package incomplete: version hashes, RG messaging check) |
| Wallet API v2 (idempotency keys, rollback endpoint) | Platform | Technical integration | Available |
| Geolocation service | Platform | QA | Available |
| CMS game metadata import | Casino Product | QA | To build (CI-10) |

## 5. Risks and mitigations
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| State approval slower than planned (State C runs at 2.1x the others) | High for C, low for A/B | Launch slips | Plan A+B first; do not tie launches to the slowest state; commit the P80 date |
| Credits rounded wrongly (open blocker) | Known | Wrong balances | Fix + regression on all credit cases before QA exit (CI-05 acceptance criteria) |
| Rollback not sent or failing after a timeout (seen with another provider) | Medium | Player charged for a round that never happened | CI-06 + daily reconciliation CI-08; P1 alert at >2% failed rollbacks |
| Deployed math differs from the certified version | Low | Compliance finding, wrong RTP | Version-hash check at launch, RTP bounds monitoring (CI-15) |
| Duplicate entries if some games later also come through an aggregator | Low | Inflated catalogue, extra fees | One canonical game id per title (CI-10); duplicate check in SQL (sql/08) |
| Novelty effect read as success | High | Wrong roadmap decisions | Judge games on days 30-60, not week 1 |

## 6. Success metrics
| Metric | Target | Source |
|---|---|---|
| Launch date (States A+B) | On or before 2027-03-14 | Pipeline tracker |
| Compliance findings | 0 games live without approval; 0 missing documents at submission | `src/compliance_alerts.py` |
| Game launch error rate | < 1% daily, alert at 3x baseline and > 3% | sql/06 |
| Wallet technical error rate | < 0.1% of calls; failed rollbacks < 0.1% | sql/05 |
| Wallet latency | p95 debit < 250 ms | sql/05 |
| RTP | Every game inside its 3-sigma band after 90 days | sql/07 |
| Commercial | Days 30-60 GGR per game >= 80% of the type benchmark; jackpot slots >= 100% | sql/02, sql/03 |

## 7. Launch plan
1. **Staging certification run** with the provider: the end-to-end cases of `api_integration_checklist.md` (all pass).
2. **Go / no-go** (Product, Engineering, Compliance, Operations): approvals in hand per game and state, version hashes
   match the certificates, RG controls tested, support macros ready, monitoring live.
3. **Wave 1, State A**: 6 jackpot slots + 8 slots; 72 hours of hypercare (launch errors, wallet errors, rollbacks).
4. **Wave 1, State B**, then **wave 2** (remaining games) one week later if wave 1 meets the targets.
5. **Post-launch**: daily health for 2 weeks, weekly afterwards in the status report; 30/60-day performance review
   against the type benchmark; RTP check at 90 days.
6. **Rollback plan**: disable per game and per state (CI-14) within 15 minutes; revert to the previous certified build
   only; inform Compliance and Support; incident note within 24 hours.
