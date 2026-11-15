# API integration checklist: Provider Q (seamless wallet)

> **SIMULATED scenario.** A generic seamless-wallet contract, written from public descriptions of how casino content
> providers connect to operator platforms. Endpoint names are illustrative; the real contract is the provider's API
> specification, reviewed with Engineering and Platform.

## 1. How a round flows
```
Player ──opens game──▶ Platform (lobby, geolocation, RG checks) ──launch request + token──▶ Provider Q
Provider Q ──debit(bet)──▶ Platform wallet ──OK / ERR──▶ Provider Q ──spins the game (RNG)──▶ result
Provider Q ──credit(win)──▶ Platform wallet      (timeout on debit? ──rollback(txn)──▶ Platform wallet)
Platform ──daily reporting feed──▶ Compliance / Finance        Provider Q ──daily round file──▶ reconciliation
```
The **platform holds the money**; the provider runs the game and asks the platform to move balances. That is why the
wallet calls must be exact, idempotent and reconciled every day.

## 2. Contract
| Call | Direction | Key fields | Must |
|---|---|---|---|
| `launch` | Platform -> Provider | player token (single use), game id, state, language, currency, RG flags | Token valid 60 s; game id must be approved in that state |
| `authenticate` | Provider -> Platform | token | Returns player id, balance, currency; token cannot be reused |
| `balance` | Provider -> Platform | player id, session id | Read-only |
| `debit` | Provider -> Platform | transaction id, round id, player id, game id, amount (minor units), currency, jackpot contribution | Idempotent on transaction id; refused if RG limit, self-exclusion, session closed or geolocation failed |
| `credit` | Provider -> Platform | transaction id, round id, amount, jackpot win flag | Idempotent; must match a known round |
| `rollback` | Provider -> Platform | transaction id of the debit to cancel, round id | Idempotent; OK if the debit is unknown (store it so a late debit is refused) |
| `round file` | Provider -> Platform (daily) | all rounds and transactions of the day | Input of the reconciliation (CI-08) |

## 3. Error codes (the same codes as in `wallet_api_logs`)
| Code | Meaning | Provider behaviour expected | Counted as technical error? |
|---|---|---|---|
| `OK` | Done | Continue | No |
| `OK_IDEMPOTENT_REPLAY` | Same transaction id already processed; original result returned | Continue, no new movement | No |
| `ERR_INSUFFICIENT_FUNDS` | Balance too low | Show the message, no round | No (business decline) |
| `ERR_RG_BLOCKED` | Limit reached, time-out or self-exclusion | Close the game with the RG message | No |
| `ERR_LOCATION` | Geolocation failed | End the session after the round | No |
| `ERR_TIMEOUT` | No answer within 3 s | Debit: send `rollback` with the same transaction id. Credit: retry with the same id (exponential back-off, up to 24 h) | Yes |
| `ERR_ROLLBACK_FAILED` | Rollback could not be applied | Retry; if still failing, the reconciliation flags it | Yes, P1 if > 2% of rollbacks in a day |
| `ERR_UNKNOWN_ROUND` | Credit for a round with no debit | Stop, alert | Yes |

## 4. Non-functional targets
- Wallet p95 latency < 250 ms for debit and credit (direct integrations in this study run ~160 ms at p95; aggregator
  routes ~430-480 ms).
- Technical error rate < 0.1% of calls; failed rollbacks < 0.1% of rollbacks.
- Game launch < 3 s at p95; launch error rate < 1%.
- Every call logged with transaction id, round id, latency and status (feeds sql/05 and sql/06).

## 5. Environments
| Environment | Used for | Exit criterion |
|---|---|---|
| Provider sandbox | Contract tests against the provider's mock wallet | All contract cases green |
| Platform staging | End-to-end tests with the real wallet, geolocation and RG services | Section 6 all pass, signed by QA |
| Certification build | The exact build sent to the test lab | Version hash recorded in the compliance tracker |
| Production | Launch, wave by wave, behind a per-state feature flag | Go / no-go signed |

## 6. End-to-end test cases (staging)
| # | Case | Expected |
|---|---|---|
| 1 | Happy path: launch, debit, credit | Balance moves exactly; round in the daily feed |
| 2 | Insufficient funds | `ERR_INSUFFICIENT_FUNDS`, no movement |
| 3 | Debit timeout, provider sends rollback | Debit reversed, balance restored |
| 4 | Same debit sent twice | Second answer `OK_IDEMPOTENT_REPLAY`, one movement |
| 5 | Same transaction id, different amount | Rejected and alerted |
| 6 | Rollback for an unknown debit, then the late debit | Rollback OK; late debit refused |
| 7 | Credit after the session closed | Accepted |
| 8 | Credit to the cent ($12.35) and large win | Exact amount, no rounding (open blocker on Provider Q) |
| 9 | Jackpot contribution and jackpot win | Contribution per round; win paid; jackpot reset; in the report |
| 10 | Player reaches a loss limit mid-session | Next debit `ERR_RG_BLOCKED`, RG message shown |
| 11 | Self-excluded player opens a game | Launch refused |
| 12 | Geolocation fails mid-session | Session ends after the round |
| 13 | Game disabled for State B mid-session | Open round settles, game leaves the lobby within 15 min |
| 14 | Network drop during a round | Round resumed or settled per the game rules |
| 15 | Daily reconciliation with one injected mismatch | Mismatch listed with its transaction id |

## 7. Release rollback plan
1. **Disable** the game (or all Provider Q games) per state with the kill switch (CI-14): < 15 minutes.
2. **Revert** only to the previous *certified* build (never to an uncertified one); confirm the version hash.
3. **Settle** open rounds; run the reconciliation for the incident window.
4. **Inform** Compliance (they decide on any regulator notification), Support (macro), Operations.
5. **Write** the incident note within 24 hours: timeline, players affected, money affected, fix, prevention.
