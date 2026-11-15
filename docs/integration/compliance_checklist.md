# Compliance checklist: certification and state approval of casino games

> What a game needs before it can go live in a US state, and how the tracker follows it. Built from **public
> documents** (listed at the end). It is a working checklist for a product analyst, **not legal advice**: each state
> has its own rules and the Compliance team decides. Provider, game and state names in the tracker are **SIMULATED**.

## 1. The path of one game
```
Provider builds game ─▶ Submission package ─▶ Independent test lab ─▶ Certificate ─▶ State submission ─▶ Approval ─▶ Live
                         (math, rules, build)    (tests vs GLI-19 etc.)   (per version)    (per state)          (per state)
                                                                                        After launch: changes go back through the lab
```
- **Lab testing.** Independent laboratories test interactive games and systems against published technical standards
  such as GLI-19 (interactive gaming systems). GLI-19 v4.0 covers, among others, RNG (chapter 5), game requirements
  (chapter 6: information and disclosure 6.4, fairness 6.7, payouts and minimum RTP 6.8, progressive jackpots 6.10,
  game recall 6.14, disable 6.15, interrupted games 6.16, live games 6.18) and player accounts (chapter 3, including
  limits, time-outs and suspensions 3.4 and promotional offers 3.5). Its minimum RTP is 75% "unless otherwise specified
  by the regulatory body" (6.8.1).
- **State approval.** Each state approves games for its own market. New Jersey, for example, states that every gaming
  product "must be approved by our slot lab and then must undergo verification prior to its use" (DGE Technical
  Services Bureau page), and lists the Internet gaming sites approved to operate (Hard Rock Hotel & Casino:
  hardrock.bet and nj.bet365.com, read 2026-11-15). Rules: N.J.A.C. 13:69O (Internet and mobile gaming).
- **Changes after launch.** A new version of a game is a new submission: the change-management process
  (GLI Change Management Program guide) decides how much re-testing it needs. The live build must keep matching the
  approved version (version hash).

## 2. Documents per game (columns of `compliance_tracker.csv`)
| Item | Why | Tracker column |
|---|---|---|
| Math report / PAR sheet | Shows the theoretical RTP and hit frequencies the lab verifies | `par_sheet` |
| Game rules and paytable as shown to players | Disclosure requirements (GLI-19 6.4) | `rules_paytable` |
| Certified build and its version hash | Proves the live build is the certified one | `version_hash` |
| Responsible-gaming messaging check | RG information shown in the game client | `rg_messaging_check` |
| Lab certificate reference and date | Input of every state submission | `cert_ref`, `cert_date` |
| State submission date, status, approval date | One line per game and state | `submitted`, `approval_status`, `approved` |
| Live date | Must never exist without an approval in that state | `live_date` |

## 3. Per provider
- Supplier licence (or registration) in each state, with expiry date (`data/simulated/provider_licences.csv`).
- Lab relationship and certification history (which games are already certified elsewhere: this shortens onboarding
  and raises the roadmap confidence score).
- Contacts for compliance questions and for incidents (kept outside this repository).

## 4. Alert rules (run weekly by `src/compliance_alerts.py`, also in `sql/11_compliance.sql`)
| Severity | Rule | Action |
|---|---|---|
| P1 | A game has a live date in a state where it is not approved | Disable it there now (kill switch), inform Compliance |
| P2 | A supplier licence expires within 60 days | Confirm the renewal filing; plan disablement if late |
| P3 | A submission package is incomplete | Request the missing items; nothing is submitted until complete |

Current run (2026-11-13, simulated): **3 P1** (three Provider L games live in State B with the approval still
pending), **2 P2** (Provider C in State B, Provider G in State A), **6 P3** (Provider N games blocked for State C).
Full list: `docs/status/compliance_alerts.md`.

## 5. Post-launch monitoring that supports compliance
- **RTP within statistical bounds** (sql/07): realised vs certified RTP with a band that depends on volatility and
  volume; escalate beyond 4 standard deviations (one game in this study: deployed with the wrong RTP configuration).
- **Version hash check** at every release, against the certificate.
- **Duplicate entries** (sql/08): one canonical game id, so that reports to regulators count each game once.
- **Disable drill**: test the per-state kill switch every quarter.

## 6. Public sources
- Gaming Laboratories International, *GLI-19: Standards for Interactive Gaming Systems*, v4.0 (downloaded 2026-11-15
  from gaminglabs.com/gli-standards).
- GLI, *GLI-11: Gaming Devices*, v3.0; *Composite Submission Requirements*, v2.0; *Change Management Program Guide*, v1.0.
- New Jersey Division of Gaming Enforcement: *Slot Laboratory - Technical Services Bureau*; *Internet Gaming Sites*;
  *Internet Gaming Information* (citing N.J.A.C. 13:69O), njoag.gov, read 2026-11-15.
