# %% [markdown]
# # Hard Rock Digital: a data-driven playbook for casino content integrations
# One notebook, five parts. Part 1 uses **PUBLIC DATA** (New Jersey DGE and Pennsylvania PGCB reports).
# Parts 2-5 use the **SIMULATED** catalogue, pipeline and logs (fictional providers and states, seed 42).
# The SQL in `sql/` runs first (`python src/run_sql.py`); this notebook reads its outputs in `data/output/`.
#
# 1. The real market: US online casino revenue by state, named operators
# 2. Catalogue health: the planted events, RTP bounds, the life curve of a game
# 3. Integration pipeline: cycle times, the slow state, Monte-Carlo launch forecasts
# 4. Roadmap: which provider to integrate next (RICE-style score + sensitivity)
# 5. Free-spin promotion vs a random hold-out; then detection scored against the hidden answer key

# %%
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
sys.path.insert(0, str(ROOT / "src"))
from config import AS_OF, OUT, PUBLIC, SEED, SIM  # noqa: E402

rng = np.random.default_rng(SEED)
o = lambda n: pd.read_csv(OUT / f"{n}.csv")  # noqa: E731
R = {}                                         # every number quoted in the report is stored here

# %% [markdown]
# ## 1. The real market (PUBLIC DATA)
# **New Jersey**: monthly Internet gaming win by casino licensee (form DGE-105). "Other authorized games" = casino
# games; peer-to-peer = poker. **Pennsylvania**: monthly interactive gaming report by operator (slots, tables, poker).
# Hard Rock figures are quoted only where the reports name them: the licensee *Hard Rock Atlantic City* and its skin
# *Hard Rock Bet* (the brand Hard Rock Digital uses for its online casino on its own website).

# %%
nj = pd.read_csv(PUBLIC / "nj_internet_gaming_by_licensee.csv")
hr = pd.read_csv(PUBLIC / "nj_hard_rock_skin.csv")
pa = pd.read_csv(PUBLIC / "pa_interactive_gaming_by_operator.csv")
nj_m = nj.groupby("month").casino_win_usd.sum()
last12, prev12 = nj_m.index[-12:], nj_m.index[-24:-12]
R["nj"] = dict(casino_win_12m=nj_m[last12].sum(), casino_win_prev12m=nj_m[prev12].sum(),
               growth=nj_m[last12].sum() / nj_m[prev12].sum() - 1, first=last12[0], last=last12[-1],
               poker_share=nj[nj.month.isin(last12)].poker_win_usd.sum() / nj[nj.month.isin(last12)].total_win_usd.sum())
hr_l = hr.set_index("month")
R["hard_rock"] = dict(
    skin_12m=hr_l.loc[last12, "hard_rock_bet_casino_win_usd"].sum(),
    skin_prev12m=hr_l.loc[prev12, "hard_rock_bet_casino_win_usd"].sum(),
    licensee_12m=hr_l.loc[last12, "licensee_casino_win_usd"].sum(),
    skin_share_nj=hr_l.loc[last12, "hard_rock_bet_casino_win_usd"].sum() / nj_m[last12].sum(),
    licensee_share_nj=hr_l.loc[last12, "licensee_casino_win_usd"].sum() / nj_m[last12].sum())
R["hard_rock"]["skin_growth"] = R["hard_rock"]["skin_12m"] / R["hard_rock"]["skin_prev12m"] - 1
lic = nj[nj.month.isin(last12)].groupby("licensee").casino_win_usd.sum().sort_values(ascending=False)
lic_share = (lic / lic.sum()).rename("share").reset_index()
lic_share.to_csv(OUT / "nb_nj_licensee_share.csv", index=False)
R["nj"]["hard_rock_rank"] = int(lic_share.licensee.tolist().index("Hard Rock Atlantic City") + 1)
R["nj"]["n_licensees"] = int(len(lic_share))

pa_t = pa[pa.operator == "Grand Total"].set_index("month")
pa_t["casino_ggr"] = pa_t.slots_ggr_usd + pa_t.tables_ggr_usd
pa12 = pa_t.index[-12:]
R["pa"] = dict(casino_ggr_12m=pa_t.loc[pa12, "casino_ggr"].sum(), first=pa12[0], last=pa12[-1],
               slot_payout=pa_t.loc[pa12, "slots_won_usd"].sum() / pa_t.loc[pa12, "slots_wagers_usd"].sum(),
               slot_payout_min=(pa_t.slots_won_usd / pa_t.slots_wagers_usd).min(),
               slot_payout_max=(pa_t.slots_won_usd / pa_t.slots_wagers_usd).max(),
               table_hold=pa_t.loc[pa12, "tables_ggr_usd"].sum() / pa_t.loc[pa12, "tables_wagers_usd"].sum(),
               slot_share=pa_t.loc[pa12, "slots_ggr_usd"].sum() / pa_t.loc[pa12, "casino_ggr"].sum())
ops = pa[(pa.operator != "Grand Total") & pa.month.isin(pa12)].copy()
ops["payout"] = ops.slots_won_usd / ops.slots_wagers_usd
op_pay = ops.groupby("operator").apply(lambda d: d.slots_won_usd.sum() / d.slots_wagers_usd.sum())
R["pa"]["op_payout_min"], R["pa"]["op_payout_max"] = op_pay.min(), op_pay.max()
mk = pd.DataFrame({"nj_casino_win": nj_m, "pa_casino_ggr": pa_t.casino_ggr}).reset_index(names="month")
mk.to_csv(OUT / "nb_market_monthly.csv", index=False)
print(json.dumps({k: R[k] for k in ("nj", "hard_rock", "pa")}, indent=1, default=float))

# %% [markdown]
# **Reading.** New Jersey online casino win grows double digits year on year; in Pennsylvania slots carry most of the
# online casino revenue and pay back ~95% of wagers to players. That real payout ratio is the calibration point for the
# simulated catalogue's theoretical RTPs (93.5%-96.2% for slots).
#
# ## 2. Catalogue health (SIMULATED)
# ### 2.1 A provider update breaks game launches (event 1)
# Rule (sql/06): provider-day error rate > 3x its trailing 28-day baseline **and** > 3%.

# %%
le = o("launch_errors")
al = le[le.alert]
R["launch"] = dict(alert_days=int(len(al)), providers=sorted(al.provider_id.unique().tolist()),
                   first=al.day.min(), last=al.day.max(), peak_rate=al.error_rate.max(),
                   baseline=al.baseline_rate.mean(), ggr_lost=al.ggr_lost_est.sum(),
                   ggr_lost_per_day=al.ggr_lost_est.mean(),
                   normal_rate=le[(le.provider_id == "F") & ~le.alert].errors.sum() / le[(le.provider_id == "F") & ~le.alert].attempts.sum(),
                   f_ggr_per_day=le[(le.provider_id == "F") & ~le.alert].ggr.mean(),
                   load_ms_alert=al.avg_load_ms.mean(),
                   load_ms_normal=le[(le.provider_id == "F") & ~le.alert].avg_load_ms.mean())
le[le.provider_id == "F"][["day", "error_rate", "baseline_rate", "alert"]].to_csv(OUT / "nb_launch_f.csv", index=False)
R["launch"]

# %% [markdown]
# ### 2.2 RTP: a false signal and a real one (event 2)
# Realised RTP over *n* rounds moves around the theoretical RTP by about `sd_per_round / sqrt(n)`. A very volatile
# slot (rare huge wins) needs millions of rounds before its realised RTP settles; a low-volatility one settles fast.
# So a gap of 7 points can be normal for one game and a defect for another. We compute z = (wins - theoretical x wagers)
# / sd(wins) over the last 90 days: |z| > 3 = watch, |z| > 4 = escalate (with ~500 games checked each week, a 3-sigma
# rule alone would raise about one false alarm every week or two).

# %%
rt = o("rtp_check")
R["rtp"] = dict(games=int(len(rt)), naive=int(rt.naive_flag.sum()),
                watch=sorted(rt[rt.stat_flag == "watch"].game_id), escalate=sorted(rt[rt.stat_flag == "escalate"].game_id))
for gid in ("C-007", "G-012"):
    r = rt.set_index("game_id").loc[gid]
    R["rtp"][gid] = dict(theo=r.rtp_theoretical, real=r.rtp_realised, z=r.z, band=r.band_3sd, rounds=r.rounds,
                         volatility=r.volatility)
R["rtp"]["naive_false"] = int((rt.naive_flag & (rt.stat_flag == "ok")).sum())
rt[["game_id", "game_type", "volatility", "rounds", "rtp_theoretical", "rtp_realised", "gap", "z", "band_3sd",
    "naive_flag", "stat_flag"]].to_csv(OUT / "nb_rtp_funnel.csv", index=False)
R["rtp"]

# %% [markdown]
# ### 2.3 Life curve of a new game (event 4)
# New games get a burst of curiosity, then settle. Judging a game in its first week overstates it.

# %%
lc = o("lifecycle")
R["novelty"] = dict(week1_index=lc[lc.age < 7].index_vs_steady.mean(),
                    day_settled=int(lc[(lc.age > 7) & (lc.index_vs_steady < 1.10)].age.min()),
                    games=int(lc.games.max()))
R["novelty"]

# %% [markdown]
# ### 2.4 Aggregator vs direct, and the duplicates it left behind (events 5 and 6)

# %%
rs = o("route_switch").set_index("period")
du = o("duplicates")
g = pd.read_csv(SIM / "games.csv")
R["route"] = dict(p95_before=rs.iloc[0].debit_p95_ms, p95_after=rs.iloc[1].debit_p95_ms,
                  err_before=rs.iloc[0].launch_error_rate, err_after=rs.iloc[1].launch_error_rate,
                  margin_before=rs.iloc[0].margin_rate, margin_after=rs.iloc[1].margin_rate,
                  load_before=rs.iloc[0].avg_load_ms, load_after=rs.iloc[1].avg_load_ms)
live = g[g.status == "live"]
R["dups"] = dict(groups=int(len(du)), live_entries=int(len(live)), unique_games=int(len(live) - len(du)),
                 inflation=len(du) / (len(live) - len(du)), ggr_old=du.ggr_old_copy.sum(),
                 fees=du.aggregator_fees_since_switch.sum(), session_share_old=du.ggr_old_copy.sum() /
                 (du.ggr_old_copy.sum() + du.ggr_direct_copy.sum()))
R["route"], R["dups"]

# %% [markdown]
# ### 2.5 Rollbacks that fail (event 7)
# A rollback reverses a debit that did not complete (e.g. a timeout). If the rollback fails, the player has been
# charged for a round that never happened. The amounts are small; the issue is player-fund integrity, so it is P1.

# %%
rb = o("rollback_alerts")
wd = o("wallet_daily")
R["rollback"] = dict(days=int(len(rb)), provider=sorted(rb.provider_id.unique().tolist()), failed=int(rb.rollback_failed.sum()),
                     rate=rb.rollback_failed.sum() / rb.rollbacks.sum(), at_risk=rb.balance_at_risk_usd.sum(),
                     normal_rate=wd.rollback_failed.sum() / wd.rollbacks.sum(), first=rb.day.min(), last=rb.day.max(),
                     weekdays=sorted(pd.to_datetime(rb.day).dt.day_name().unique().tolist()))
R["rollback"]

# %% [markdown]
# ## 3. Integration pipeline (SIMULATED)
# ### 3.1 Cycle time and the slow state (event 3)

# %%
ct = o("stage_cycle_time")
at = o("approval_time")
ap = pd.read_csv(SIM / "game_approvals.csv", parse_dates=["submitted", "approved"])
done = ap[ap.status == "approved"].assign(days=lambda d: (d.approved - d.submitted).dt.days)
med = done.groupby("state").days.median()
R["cert"] = dict(median_by_state=med.to_dict(), ratio_c=med["State C"] / med[["State A", "State B"]].mean(),
                 lab_median=float(ct[ct.stage == "Lab certification"].median_days.median()),
                 pending_c=int(((ap.state == "State C") & (ap.status == "pending")).sum()))
stage_tab = (ct.groupby(["stage", "route"]).apply(lambda d: np.average(d.median_days, weights=d.n)).unstack())
stage_tab.to_csv(OUT / "nb_stage_table.csv")
R["cert"]

# %% [markdown]
# ### 3.2 Monte-Carlo launch forecast
# Each remaining stage duration is drawn from a log-normal fitted on the finished stages (same stage, same route; same
# state for approvals). A stage already open is drawn *conditional* on lasting longer than it has already lasted.
# 10,000 runs give a distribution of launch dates; we quote P50 (coin flip) and P80 (safe to commit externally).

# %%
pipe = pd.read_csv(SIM / "integration_pipeline.csv", parse_dates=["start_date", "end_date", "planned_end_date"])
fin = pipe[pipe.status == "done"].assign(d=lambda x: (x.end_date - x.start_date).dt.days.clip(lower=1))


def fit(stage, route=None, state=None):
    x = fin[fin.stage == stage]
    if route and stage not in ("State approval", "Launch", "Lab certification"):
        x = x[x.route == route]
    if state:
        x = x[x.state == state]
    lg = np.log(x.d)
    return lg.mean(), max(lg.std(), 0.15)


def draw(stage, route=None, state=None, elapsed=0, n=10000):
    mu, sd = fit(stage, route, state)
    out = np.exp(rng.normal(mu, sd, n))
    if (out > elapsed).mean() < 0.01:          # older than 99% of history: treated as stuck, a full new cycle once escalated
        return out
    for _ in range(50):                        # rejection sampling for stages already open
        bad = out <= elapsed
        if not bad.any():
            break
        out[bad] = np.exp(rng.normal(mu, sd, bad.sum()))
    out[out <= elapsed] = elapsed + 1
    return out - elapsed


asof = pd.Timestamp(AS_OF)
N = 10000
fc = []
# Provider Q (direct): technical integration open, then QA, lab, approvals in A and B (no State C licence yet)
q = pipe[pipe.project_id == "Q-DIR"]
q_open = q[q.status.isin(["in_progress", "blocked"])].iloc[0]
elapsed = (asof - q_open.start_date).days
rest = draw(q_open.stage, "Direct", elapsed=elapsed)
after = q_open.stage
seq = ["Commercial agreement", "Technical integration", "QA & staging tests", "Lab certification"]
t = rest.copy()
for s in seq[seq.index(after) + 1:]:
    t += draw(s, "Direct")
for st in ("State A", "State B", "State C"):
    tl = t + 2 + draw("State approval", state=st) + draw("Launch")
    fc.append(("Provider Q", st if st != "State C" else "State C (once licensed)", tl))
# Provider N (aggregator): A and B approved; launch pending; State C approval open since its submission
n_c = pipe[(pipe.project_id == "N-AGG") & (pipe.stage == "State approval") & (pipe.state == "State C")].iloc[0]
tc = draw("State approval", state="State C", elapsed=(asof - n_c.start_date).days) + draw("Launch")
fc.append(("Provider N", "State C", tc))
fc.append(("Provider N", "States A+B (if released now)", draw("Launch")))
rows = []
for prov, st, x in fc:
    p50, p80 = np.percentile(x, [50, 80])
    rows.append(dict(provider=prov, state=st, p50_days=p50, p80_days=p80,
                     p50_date=(asof + pd.Timedelta(days=p50)).date(), p80_date=(asof + pd.Timedelta(days=p80)).date()))
fcast = pd.DataFrame(rows)
fcast.to_csv(OUT / "nb_forecast.csv", index=False)
q_ab = np.maximum(fc[0][2], fc[1][2])
q_abc = np.maximum(q_ab, fc[2][2])
R["forecast"] = dict(q_open_stage=after, q_ab_p50=(asof + pd.Timedelta(days=np.percentile(q_ab, 50))).date(),
                     q_ab_p80=(asof + pd.Timedelta(days=np.percentile(q_ab, 80))).date(),
                     q_abc_p50=(asof + pd.Timedelta(days=np.percentile(q_abc, 50))).date(),
                     q_abc_p80=(asof + pd.Timedelta(days=np.percentile(q_abc, 80))).date(),
                     c_delay_p50=float(np.percentile(q_abc, 50) - np.percentile(q_ab, 50)),
                     n_c_p50=str(fcast.iloc[3].p50_date), n_c_p80=str(fcast.iloc[3].p80_date))
# the cost of a slow state for a typical new aggregator provider: launch all three states together vs A+B first
base = draw("Commercial agreement", "Aggregator") + draw("Technical integration", "Aggregator") + \
    draw("QA & staging tests", "Aggregator") + draw("Lab certification")
la = {st: base + 2 + draw("State approval", state=st) + draw("Launch") for st in ("State A", "State B", "State C")}
R["forecast"]["agg_ab_p50"] = float(np.percentile(np.maximum(la["State A"], la["State B"]), 50))
R["forecast"]["agg_abc_p50"] = float(np.percentile(np.maximum(la["State B"], la["State C"]), 50))
direct = draw("Commercial agreement", "Direct") + draw("Technical integration", "Direct") + \
    draw("QA & staging tests", "Direct") + draw("Lab certification")
ld = {st: direct + 2 + draw("State approval", state=st) + draw("Launch") for st in ("State A", "State B", "State C")}
R["forecast"]["dir_ab_p50"] = float(np.percentile(np.maximum(ld["State A"], ld["State B"]), 50))
R["forecast"]["agg_ab_p80"] = float(np.percentile(np.maximum(la["State A"], la["State B"]), 80))
R["forecast"]["dir_ab_p80"] = float(np.percentile(np.maximum(ld["State A"], ld["State B"]), 80))
TTL = {"Aggregator": np.maximum(la["State A"], la["State B"]), "Direct": np.maximum(ld["State A"], ld["State B"])}
pd.DataFrame({"route": ["Aggregator"] * N + ["Direct"] * N,
              "days": np.r_[TTL["Aggregator"], TTL["Direct"]]}).sample(4000, random_state=SEED).to_csv(OUT / "nb_ttl_sample.csv", index=False)
print(fcast)
R["forecast"]

# %% [markdown]
# ## 4. Which provider next? (SIMULATED)
# Five candidates. A RICE-style score, every input visible:
# - **Reach**: share of our player-days in the states where the candidate is licensed.
# - **Impact**: incremental first-year GGR. A game type's GGR grows with the number of its games, with diminishing
#   returns: GGR_type x ((n + k) / n)^e - 1, where k = games added and e (elasticity) is higher for under-supplied
#   types: e = clip(0.15 x demand/supply ratio, 0.05, 0.5). Scaled by Reach and by the share of the first year left
#   after the P50 time-to-launch of its route (Monte-Carlo above).
# - **Confidence**: 0.5 + 0.2 if its portfolio is already lab-certified elsewhere + 0.2 if we already work with it
#   through an aggregator + 0.1 if licensed in all three states.
# - **Effort** (person-weeks): integration and QA estimate + 0.1 week per game per state submission.
# - **Score** = Impact x Confidence / Effort, in incremental GGR dollars per person-week.

# %%
cand = pd.read_csv(SIM / "candidate_providers.csv")
tg = o("type_gap").set_index("game_type")
annual = tg.ggr * 365 / 90                         # annualised GGR by type from the last 90 days
gd = pd.read_parquet(SIM / "game_daily.parquet")
st_share = gd.groupby("state").players.sum() / gd.players.sum()
TYPES = {"n_slot": "Slot", "n_table": "Table", "n_live": "Live dealer", "n_jackpot": "Jackpot slot"}


def score(c, elastic_k=0.15, effort_mult=1.0, ttl_shift=0.0, conf_w=(0.2, 0.2, 0.1), bench=1.0):
    states = [f"State {x}" for x in c.licensed_states]
    reach = st_share[states].sum()
    e = (elastic_k * tg.demand_supply_ratio).clip(0.05, 0.5)
    inc = sum(bench * annual[t] * (((tg.live_games[t] + c[k]) / tg.live_games[t]) ** e[t] - 1) for k, t in TYPES.items() if c[k])
    ttl = np.percentile(TTL["Direct" if c.route == "Direct" else "Aggregator"], 50) + ttl_shift
    year_left = max(0.0, 1 - ttl / 365)
    impact = inc * reach * year_left
    conf = 0.5 + conf_w[0] * c.portfolio_certified_elsewhere + conf_w[1] * c.known_partner + \
        conf_w[2] * (len(states) == 3)
    games = sum(c[k] for k in TYPES)
    effort = (c.integration_effort_weeks + 0.1 * games * len(states)) * effort_mult
    return dict(provider_id=c.provider_id, route=c.route if c.route == "Direct" else c.aggregator, games=games,
                states=c.licensed_states, reach=reach, incremental_full_year=inc * reach, ttl_p50_days=ttl,
                impact=impact, confidence=conf, effort_weeks=effort, score=impact * conf / effort, note=c.note)


rk = pd.DataFrame([score(c) for _, c in cand.iterrows()]).sort_values("score", ascending=False)
rk["rank"] = range(1, len(rk) + 1)
rk.to_csv(OUT / "nb_roadmap.csv", index=False)
print(rk[["provider_id", "route", "games", "states", "reach", "impact", "confidence", "effort_weeks", "score"]].round(3))

# %% [markdown]
# **Sensitivity.** (a) One input at a time: does the winner change? (b) 5,000 runs where every input is multiplied by
# random noise (log-normal, sd 0.3) and the confidence weights are redrawn: how often is each candidate first?

# %%
cases = {"base": {}, "elasticity x0.5": dict(elastic_k=0.075), "elasticity x1.5": dict(elastic_k=0.225),
         "effort x1.5 for direct": "direct_effort", "time-to-launch +60 days": dict(ttl_shift=60),
         "GGR benchmark x0.7": dict(bench=0.7), "confidence = 1 for all": dict(conf_w=(0, 0, 0))}
oat = []
for name, kw in cases.items():
    res = []
    for _, c in cand.iterrows():
        k = dict(effort_mult=1.5 if c.route == "Direct" else 1.0) if kw == "direct_effort" else kw
        res.append(score(c, **k))
    s = pd.DataFrame(res).sort_values("score", ascending=False)
    oat.append(dict(case=name, first=s.iloc[0].provider_id, second=s.iloc[1].provider_id, order=" > ".join(s.provider_id)))
oat = pd.DataFrame(oat)
oat.to_csv(OUT / "nb_sensitivity_oat.csv", index=False)
wins = {c: 0 for c in cand.provider_id}
top2 = {c: 0 for c in cand.provider_id}
for i in range(5000):
    res = []
    w = tuple(rng.uniform(0.05, 0.35, 3))
    for _, c in cand.iterrows():
        r = score(c, elastic_k=0.15 * np.exp(rng.normal(0, 0.3)), effort_mult=np.exp(rng.normal(0, 0.3)),
                  ttl_shift=rng.normal(0, 30), conf_w=w, bench=np.exp(rng.normal(0, 0.3)))
        res.append((r["score"], c.provider_id))
    res.sort(reverse=True)
    wins[res[0][1]] += 1
    top2[res[0][1]] += 1
    top2[res[1][1]] += 1
mc = pd.DataFrame({"provider_id": list(wins), "p_first": [wins[k] / 5000 for k in wins],
                   "p_top2": [top2[k] / 5000 for k in top2]}).sort_values("p_first", ascending=False)
mc.to_csv(OUT / "nb_sensitivity_mc.csv", index=False)
R["roadmap"] = dict(order=rk.provider_id.tolist(), first=rk.iloc[0].provider_id, second=rk.iloc[1].provider_id,
                    p_first=mc.set_index("provider_id").p_first.to_dict(), p_top2=mc.set_index("provider_id").p_top2.to_dict(),
                    oat_first_stable=int((oat["first"] == rk.iloc[0].provider_id).sum()), oat_cases=int(len(oat)),
                    table=rk.set_index("provider_id")[["impact", "confidence", "effort_weeks", "score", "ttl_p50_days",
                                                       "reach", "incremental_full_year"]].to_dict("index"),
                    gap=tg.demand_supply_ratio.to_dict(), ggr_share=tg.ggr_share.to_dict(), cat_share=tg.catalogue_share.to_dict())
print(oat, mc, sep="\n")

# %% [markdown]
# ## 5. Free-spin promotion vs a random hold-out (event 8)
# PR06: 20 free spins on a new Provider B slot, 40,000 eligible players, 10% randomly held out. Outcome: GGR per
# player over 28 days from the start. Welch t-test for the difference; the pre-period GGR is used as a covariate
# (CUPED: post - theta x (pre - mean pre), theta = cov(post, pre) / var(pre)) to tighten the interval. The naive comparison (players who used their spins vs those who
# did not) is shown to make the selection bias visible.

# %%
pp = pd.read_csv(SIM / "promo_players.csv")
tr, co = pp[pp.group == "treatment"], pp[pp.group == "control"]


def diff_ci(a, b):
    d = a.mean() - b.mean()
    se = np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    return d, d - 1.96 * se, d + 1.96 * se, stats.ttest_ind(a, b, equal_var=False).pvalue


d, lo, hi, p = diff_ci(tr.ggr_post_28d, co.ggr_post_28d)
theta = np.cov(pp.ggr_post_28d, pp.ggr_pre_28d)[0, 1] / pp.ggr_pre_28d.var()
adj = pp.ggr_post_28d - theta * (pp.ggr_pre_28d - pp.ggr_pre_28d.mean())
dd, dlo, dhi, dp = diff_ci(adj[pp.group == "treatment"], adj[pp.group == "control"])
adj_net = adj - pp.free_spin_cost_usd
cn, cnlo, cnhi, _ = diff_ci(adj_net[pp.group == "treatment"], adj[pp.group == "control"])
cost = tr.free_spin_cost_usd.mean()
net = tr.ggr_post_28d - tr.free_spin_cost_usd
n_, nlo, nhi, npv = diff_ci(net, co.ggr_post_28d)
a_, alo, ahi, _ = diff_ci(tr.active_post_28d, co.active_post_28d)
used = tr[tr.spins_used > 0]
R["promo"] = dict(n_t=int(len(tr)), n_c=int(len(co)), uplift=d, lo=lo, hi=hi, p=p, cuped=dd, cuped_lo=dlo, cuped_hi=dhi,
                  cuped_net=cn, cuped_net_lo=cnlo, cuped_net_hi=cnhi, theta=theta,
                  cost=cost, net=n_, net_lo=nlo, net_hi=nhi, roi=d / cost, active_uplift=a_, active_lo=alo, active_hi=ahi,
                  naive=used.ggr_post_28d.mean() - tr[tr.spins_used == 0].ggr_post_28d.mean(),
                  reach=len(used) / len(tr), total_cost=tr.free_spin_cost_usd.sum(),
                  incr_total=d * len(tr))
R["promo"]

# %% [markdown]
# ## 6. Detection scored against the hidden answer key
# Read only now, after every rule above has been fixed.

# %%
truth = pd.read_csv(SIM / "_hidden_truth.csv")
ca = o("compliance_alerts")
found = {
    1: R["launch"]["providers"] == ["F"] and R["launch"]["first"] == "2026-05-12",
    2: R["rtp"]["escalate"] == ["G-012"] and "C-007" not in R["rtp"]["watch"],
    3: R["cert"]["ratio_c"] > 1.6,
    4: R["novelty"]["week1_index"] > 1.25,
    5: R["route"]["p95_after"] < 0.5 * R["route"]["p95_before"],
    6: R["dups"]["groups"] == 30,
    7: R["rollback"]["provider"] == ["K"] and R["rollback"]["days"] == 7,
    8: R["promo"]["lo"] > 0,
    9: set(ca[ca.alert.str.startswith("P1")].entity) == set(truth.loc[truth.event_id == 9, "entity"].iloc[0].split("|")),
    10: set(ca[ca.alert.str.startswith("P3")].entity) == set(truth.loc[truth.event_id == 10, "entity"].iloc[0].split("|")),
    11: len(ca[ca.alert.str.startswith("P2")]) == 2,
}
truth["found"] = truth.event_id.map(found)
how = {1: "sql/06 baseline rule", 2: "sql/07 z-score bounds", 3: "sql/04 approval time", 4: "sql/03 life curve",
       5: "sql/09 before/after", 6: "sql/08 title key", 7: "sql/05 rollback rule", 8: "hold-out test",
       9: "compliance alert P1", 10: "compliance alert P3", 11: "compliance alert P2"}
truth["method"] = truth.event_id.map(how)
truth.to_csv(OUT / "nb_detection.csv", index=False)
R["detection"] = dict(planted=int(truth.event_id.le(8).sum()), found=int(truth[truth.event_id <= 8].found.sum()),
                      events=8, events_found=int(truth[truth.event_id <= 8].groupby("event_id").found.all().sum()),
                      compliance_found=int(truth[truth.event_id > 8].found.sum()))
(OUT / "nb_results.json").write_text(json.dumps(R, indent=1, default=lambda x: x.item() if hasattr(x, "item") else str(x)),
                                     encoding="utf-8")
truth[["event_id", "event", "entity", "found", "method"]]
