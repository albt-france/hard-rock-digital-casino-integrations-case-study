# User stories: Provider Q onboarding

> **SIMULATED scenario** (fictional provider and states). 15 stories in 5 epics, each with acceptance criteria in
> Given / When / Then form. `src/build_backlog.py` turns this file into `backlog.csv` (Jira CSV import), so the two never
> drift apart. Format of each story: `### ID | Epic | Priority | Points | Depends on | Title`.

## Epic E1: Game launch and sessions

### CI-01 | E1 | Highest | 5 | - | Game launch on desktop and mobile
**As a** player in an approved state, **I want** to open a Provider Q game from the lobby on desktop or mobile,
**so that** I can play it like any other game.
- Given a logged-in player located in State A and a game approved in State A, When the player opens the game, Then the
  platform requests a launch URL with a single-use token and the game loads in under 3 seconds (p95).
- Given a game not approved in the player's state, When the lobby loads, Then the game is not displayed and cannot be
  opened by direct URL (HTTP 403 logged).
- Given the provider returns an error at launch, When the player opens the game, Then the player sees a friendly
  message, the error is logged with the provider error code, and it counts in the launch error rate.

### CI-02 | E1 | High | 5 | CI-01 | Session validity and interrupted-game recovery
**As a** player, **I want** my game session to stay valid while I play and recover if my connection drops,
**so that** I never lose a round I paid for.
- Given an open session, When the platform session expires or the player logs out, Then the provider session is closed
  and no further debit is accepted for it.
- Given a round interrupted by a disconnection, When the player reopens the game, Then the round resumes or is settled
  according to the game rules (GLI-19 v4.0, section 6.16 "Interrupted Games").
- Given a player opens the same game on a second device, When the second session starts, Then the first is closed.

### CI-03 | E1 | Highest | 3 | CI-01 | Geolocation gate before and during play
**As** Compliance, **I want** every Provider Q session to start and continue only inside an approved state,
**so that** we never offer gaming where we are not authorised.
- Given a player whose geolocation check fails or is outside State A/B, When they try to open a game, Then the launch is
  refused with a location message and no session is created.
- Given an open session, When the periodic geolocation check fails, Then the session is ended at the end of the current
  round and the event is logged (GLI-19 v4.0, section 4.3 "Geolocation Implementation").

## Epic E2: Wallet

### CI-04 | E2 | Highest | 5 | - | Wallet debit (bet)
**As a** player, **I want** my bet to be taken from my balance exactly once,
**so that** my balance is always right.
- Given a balance of $20 and a $1 bet, When the provider sends a debit, Then the platform answers OK with the new balance
  $19 and stores transaction id, round id, game id, state and amount.
- Given a balance of $0.50 and a $1 bet, When the provider sends a debit, Then the platform answers
  ERR_INSUFFICIENT_FUNDS and the balance is unchanged.
- Given a player blocked by an RG limit or self-exclusion, When a debit arrives, Then it is refused (see CI-11).

### CI-05 | E2 | Highest | 3 | CI-04 | Wallet credit (win)
**As a** player, **I want** my winnings credited to the cent,
**so that** I am paid what the game shows.
- Given a win of $12.35 on a round with a valid debit, When the provider sends the credit, Then the balance increases by
  exactly $12.35 (no rounding, amounts in minor units).
- Given a credit for a round with no matching debit, When it arrives, Then it is rejected, logged and alerted.
- Given a credit arrives after the session closed, When it arrives, Then it is still accepted (the round was paid for).

### CI-06 | E2 | Highest | 5 | CI-04 | Wallet rollback (cancel)
**As a** player, **I want** a bet that did not complete to be refunded automatically,
**so that** I am never charged for a round that never happened.
- Given a debit that timed out on the provider side, When the provider sends a rollback for that transaction id, Then the
  debit is reversed and the balance restored.
- Given a rollback for a transaction id the platform never received, When it arrives, Then the platform answers OK
  (nothing to reverse) and stores it, so a late debit with that id is refused.
- Given more than 2% of rollbacks fail for a provider on a day (and at least 5), When the monitoring runs, Then a P1
  alert is raised to Engineering and Operations with the affected players (sql/05).

### CI-07 | E2 | Highest | 3 | CI-04, CI-05, CI-06 | Idempotent wallet calls
**As** Engineering, **I want** every wallet call to be idempotent on its transaction id,
**so that** retries never double-charge or double-pay.
- Given a debit already processed, When the same transaction id is received again, Then the platform returns the
  original result (OK_IDEMPOTENT_REPLAY) and the balance does not change.
- Given the same transaction id with a different amount, When it arrives, Then it is rejected and alerted.

### CI-08 | E2 | High | 3 | CI-04, CI-05, CI-06 | Daily round and transaction reconciliation
**As** Finance, **I want** a daily reconciliation of rounds and transactions between Provider Q and the platform,
**so that** any mismatch is found within a day.
- Given the provider's daily round file, When the reconciliation runs at 06:00, Then rounds, debits, credits and
  rollbacks match the platform to the cent, or each mismatch is listed with its transaction id.
- Given an unresolved mismatch older than 48 hours, When the daily report is produced, Then it is escalated to the
  integration owner.

## Epic E3: Content and jackpots

### CI-09 | E3 | High | 5 | CI-05 | Jackpot contributions, wins and reporting
**As a** player, **I want** jackpot values and jackpot wins to be shown and paid correctly,
**so that** I can trust the jackpot.
- Given a jackpot slot, When a round is played, Then the jackpot contribution is recorded per round and reported daily.
- Given a jackpot win, When the provider sends the win, Then the credit is paid, the jackpot resets to its seed value and
  the win appears in the regulatory report (GLI-19 v4.0, section 6.10).

### CI-10 | E3 | High | 3 | - | Canonical game metadata and approved states (CMS)
**As** Casino Operations, **I want** each game to have one canonical id, its certified version and its approved states
in the CMS, **so that** the lobby only shows approved games and reports count each game once.
- Given a game imported from Provider Q, When it is saved, Then it carries provider, title, type, theoretical RTP,
  volatility, certified version hash and approved states.
- Given a title that already exists for the same provider (e.g. through an aggregator), When it is imported, Then the
  import is blocked until one entry is chosen as canonical (duplicate rule as in sql/08).

## Epic E4: Responsible gaming

### CI-11 | E4 | Highest | 3 | CI-04 | Responsible-gaming limits and exclusions
**As a** player who set limits, **I want** them to apply to Provider Q games too,
**so that** my limits work everywhere on the site.
- Given a player who reached a loss, wager or deposit limit, When they place a bet in a Provider Q game, Then the debit
  is refused with the limit message (GLI-19 v4.0, section 3.4 "Limitations, Time-Outs, and Suspensions").
- Given a player on a time-out or self-excluded, When they try to open a Provider Q game, Then the launch is refused.

### CI-12 | E4 | High | 2 | CI-02 | Reality-check session reminders
**As a** player, **I want** session reminders while I play,
**so that** I keep track of time and money spent.
- Given a player with reality checks every 60 minutes, When 60 minutes of play pass, Then a reminder showing session
  time and net result is displayed inside the game and play pauses until acknowledged.

## Epic E5: Compliance, reporting and monitoring

### CI-13 | E5 | High | 5 | CI-04, CI-05, CI-09 | Daily regulatory and finance reporting feed
**As** Compliance and Finance, **I want** daily per-game, per-state reporting of wagers, wins and GGR,
**so that** regulatory and finance reports are right.
- Given a reporting day, When the feed is produced, Then wagers, player wins, jackpot contributions and GGR per game and
  state match the wallet ledger to the cent.
- Given a game not approved in a state, When the feed shows activity for it there, Then a P1 alert is raised (compliance
  rule P1).

### CI-14 | E5 | Highest | 3 | CI-10 | Per-state game disable (kill switch)
**As** Operations, **I want** to disable a game in one state in minutes,
**so that** we can act at once on a compliance or technical issue.
- Given an operator with the right role, When they disable a game for State B, Then it disappears from the State B lobby
  within 15 minutes, open rounds are settled, and the action is logged with user and reason (GLI-19 v4.0, section 6.15).

### CI-15 | E5 | Medium | 3 | CI-13 | Post-launch monitoring and alerts
**As** the Integrations team, **I want** post-launch dashboards and alerts for Provider Q,
**so that** problems are found by us before players or regulators find them.
- Given the daily data, When launch errors exceed 3x their 28-day baseline and 3%, Then an alert goes to the integration
  owner with the GGR lost so far.
- Given 90 days of rounds, When a game's realised RTP is more than 4 standard deviations from its certified RTP, Then it is
  escalated to Compliance and the provider; between 3 and 4, it is put on watch.
