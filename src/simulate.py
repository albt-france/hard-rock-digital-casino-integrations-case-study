"""SIMULATED data for the casino-integrations playbook (seed 42, 12 months, 20 fictional providers, ~600 games,
3 fictional states). Orders of magnitude are calibrated on the public regulator data (data/ASSUMPTIONS.md).
Nothing here is Hard Rock Digital data; providers, aggregators, games and states are fictional.

Tables written to data/simulated/:
  providers.csv             20 providers: status (live / pipeline / candidate), route, aggregator, fees
  games.csv                 catalogue: provider, type, theoretical RTP, volatility, release date, approved states
  game_daily.parquet        game x state x day: launches, launch errors, sessions, players, rounds, wagers, wins, GGR, load time
  integration_pipeline.csv  provider projects: stages (agreement -> launch), dates, blockers
  game_approvals.csv        game x state: lab certificate, documents, state submission and approval, live date
  provider_licences.csv     provider x state supplier licence status and expiry
  wallet_api_logs.csv       daily aggregated wallet calls (debit / credit / rollback) by provider route and status
  promotions.csv            free-spin promotions; promo_players.csv = player-level results of the one with a hold-out
  candidate_providers.csv   the five providers not yet integrated (inputs of the roadmap score)
  _hidden_truth.csv         the planted events (answer key, read only at the end to score detection)
Run: python src/simulate.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from config import AS_OF, END, SEED, SIM, START, STATES

rng = np.random.default_rng(SEED)
DAYS = pd.date_range(START, END, freq="D")
D0 = DAYS[0]

# ------------------------------------------------------------------------------------------------ providers
# id, status, route, aggregator, slots, tables, live, jackpot, provider fee (% GGR), launch, licensed states, volatility tilt
PROV = [
    ("A", "live", "Direct", None, 70, 0, 0, 10, 0.12, "2024-03-11", "ABC", 0),
    ("B", "live", "Direct", None, 45, 0, 0, 15, 0.12, "2024-04-15", "ABC", 0),
    ("C", "live", "Aggregator", "Aggregator X", 45, 0, 0, 0, 0.11, "2024-05-20", "ABC", 2),
    ("D", "live", "Direct", None, 0, 0, 30, 0, 0.14, "2024-06-17", "ABC", 0),
    ("E", "live", "Aggregator", "Aggregator X", 0, 25, 0, 0, 0.10, "2024-08-05", "ABC", 0),
    ("F", "live", "Aggregator", "Aggregator Y", 50, 0, 0, 0, 0.11, "2024-10-07", "AB", 0),
    ("G", "live", "Aggregator", "Aggregator X", 35, 0, 0, 0, 0.11, "2025-01-13", "ABC", 0),
    ("H", "live", "Aggregator", "Aggregator X", 40, 0, 0, 0, 0.12, "2025-02-10", "ABC", 1),
    ("I", "live", "Aggregator", "Aggregator Y", 0, 0, 0, 20, 0.12, "2025-04-14", "ABC", 0),
    ("K", "live", "Aggregator", "Aggregator Y", 22, 8, 0, 0, 0.11, "2025-07-07", "AB", 0),
    ("J", "live", "Direct", None, 45, 0, 0, 0, 0.12, "2026-01-12", "ABC", 1),
    ("L", "live", "Aggregator", "Aggregator X", 25, 0, 0, 0, 0.11, "2026-03-09", "ABC", 0),
    ("M", "live", "Direct", None, 0, 0, 15, 0, 0.14, "2026-06-08", "AB", 0),
    ("N", "pipeline", "Aggregator", "Aggregator Y", 20, 5, 0, 0, 0.11, None, "ABC", 0),
    ("Q", "pipeline", "Direct", None, 30, 4, 0, 6, 0.12, None, "AB", 1),
    ("O", "candidate", "Direct", None, 0, 2, 22, 0, 0.14, None, "ABC", 0),
    ("P", "candidate", "Direct", None, 60, 0, 0, 0, 0.12, None, "AB", 0),
    ("R", "candidate", "Aggregator", "Aggregator Y", 8, 0, 0, 14, 0.12, None, "ABC", 1),
    ("S", "candidate", "Aggregator", "Aggregator X", 6, 18, 0, 0, 0.10, None, "A", 0),
    ("T", "candidate", "Aggregator", "Aggregator X", 25, 0, 0, 0, 0.11, None, "ABC", 2),
]
AGG_FEE = {"Aggregator X": 0.030, "Aggregator Y": 0.025}
H_SWITCH = pd.Timestamp("2026-04-01")          # event 5: Provider H moves from Aggregator X to a direct integration
H_DIRECT_FEE = 0.11

TYPE_CFG = {  # rounds per session, average bet, RTP range, win frequency (credit calls), sd per round by volatility
    "Slot": dict(rounds=110, bet=1.25, rtp=(0.935, 0.962), winf=0.30),
    "Jackpot slot": dict(rounds=100, bet=1.40, rtp=(0.920, 0.950), winf=0.28),
    "Table": dict(rounds=45, bet=9.0, rtp=(0.973, 0.995), winf=0.45),
    "Live dealer": dict(rounds=32, bet=16.0, rtp=(0.975, 0.990), winf=0.45),
}
VOL_SD = {"Low": 3.0, "Medium": 6.0, "High": 12.0, "Very high": 22.0}
TYPE_WEIGHT = {"Slot": 0.72, "Jackpot slot": 1.35, "Table": 1.30, "Live dealer": 2.40}   # demand per game vs catalogue
STATE_SIZE = {"State A": 1.0, "State B": 0.72, "State C": 0.48}
APPROVAL_DAYS = {"State A": 14, "State B": 17, "State C": 31}   # median days; event 3: State C takes ~2x longer

ADJ = ["Amber", "Basalt", "Cobalt", "Dune", "Ember", "Frost", "Granite", "Harbor", "Indigo", "Juniper", "Kestrel",
       "Lumen", "Marble", "Nimbus", "Onyx", "Prairie", "Quartz", "Russet", "Saffron", "Tundra", "Umber", "Velvet",
       "Willow", "Zephyr", "Copper", "Midnight", "Paper", "Thunder", "Silver", "Crimson"]
NOUN = ["Atlas", "Beacon", "Canyon", "Delta", "Echo", "Fjord", "Grove", "Harvest", "Island", "Jetty", "Kiln",
        "Lantern", "Meadow", "Nomad", "Orchard", "Parade", "Quarry", "Relay", "Summit", "Tide", "Vault", "Wharf",
        "Yard", "Compass", "Lighthouse", "Carousel", "Comet", "Garden", "Rocket", "Voyage"]


def lognorm(median, sigma, size=None):
    return median * np.exp(rng.normal(0, sigma, size))


def providers() -> pd.DataFrame:
    p = pd.DataFrame(PROV, columns=["provider_id", "status", "route", "aggregator", "n_slot", "n_table", "n_live",
                                    "n_jackpot", "provider_fee", "launch_date", "licensed_states", "vol_tilt"])
    p["provider_name"] = "Provider " + p.provider_id
    p["aggregator_fee"] = p.aggregator.map(AGG_FEE).fillna(0.0)
    p["route_change"] = np.where(p.provider_id == "H", f"Direct from {H_SWITCH.date()} (fee {H_DIRECT_FEE:.0%})", "")
    return p


# ------------------------------------------------------------------------------------------------ games
def games(p: pd.DataFrame) -> pd.DataFrame:
    rows, used = [], set()
    for r in p[p.status != "candidate"].itertuples():
        launch = pd.Timestamp(r.launch_date) if pd.notna(r.launch_date) else None
        n = 0
        for gtype, k in (("Slot", r.n_slot), ("Table", r.n_table), ("Live dealer", r.n_live), ("Jackpot slot", r.n_jackpot)):
            for _ in range(k):
                n += 1
                while True:
                    title = f"{rng.choice(ADJ)} {rng.choice(NOUN)}"
                    if title not in used:
                        used.add(title)
                        break
                if gtype in ("Slot",):
                    vol = rng.choice(list(VOL_SD), p=np.roll([0.2, 0.45, 0.25, 0.10], r.vol_tilt))
                elif gtype == "Jackpot slot":
                    vol = "Very high"
                else:
                    vol = "Low"
                cfg = TYPE_CFG[gtype]
                rtp = round(rng.uniform(*cfg["rtp"]), 3)
                sd = VOL_SD[vol] * (1.15 if gtype == "Jackpot slot" else 1) if gtype in ("Slot", "Jackpot slot") \
                    else (1.1 if gtype == "Table" else 1.4)
                # release on the platform (first state live date)
                if r.status == "pipeline":
                    rel = pd.NaT
                elif launch < D0:
                    rel = launch + pd.Timedelta(days=int(rng.integers(0, 40))) if rng.random() < 0.45 else \
                        launch + pd.Timedelta(days=int(rng.integers(0, (DAYS[-1] - launch).days - 20)))
                else:
                    rel = launch if rng.random() < 0.6 else launch + pd.Timedelta(days=int(rng.integers(7, (DAYS[-1] - launch).days - 10)))
                rows.append(dict(game_id=f"{r.provider_id}-{n:03d}", provider_id=r.provider_id, title=title, game_type=gtype,
                                 volatility=vol, rtp_theoretical=rtp, sd_per_round=round(sd, 2),
                                 avg_bet=round(cfg["bet"] * lognorm(1, 0.25), 2), release_date=rel,
                                 route=r.route if r.provider_id != "H" else "Aggregator",
                                 aggregator=r.aggregator, status="live" if r.status == "live" else "in_certification",
                                 popularity=lognorm(1, 0.75) * TYPE_WEIGHT[gtype]))
    g = pd.DataFrame(rows)
    # event 2: the planted RTP cases. One very-high-volatility slot runs far below theory by chance (false signal),
    # one medium slot was deployed with the wrong RTP configuration after a version update (true problem).
    g.loc[g.game_id == "C-007", ["volatility", "sd_per_round", "rtp_theoretical", "release_date", "popularity"]] = \
        ["Very high", 25.0, 0.960, pd.Timestamp("2026-05-04"), 0.55]
    g.loc[g.game_id == "G-012", ["volatility", "sd_per_round", "rtp_theoretical", "release_date", "popularity"]] = \
        ["Medium", 6.0, 0.960, pd.Timestamp("2025-03-03"), 1.6]
    # event 8: the promoted game (new Provider B slot)
    g.loc[g.game_id == "B-031", ["release_date", "popularity", "game_type", "volatility", "sd_per_round"]] = \
        [pd.Timestamp("2026-05-25"), 1.3, "Slot", "Medium", 6.0]
    # events 5 + 6: Provider H re-onboarded directly; 30 of its 40 old aggregator entries were never switched off
    h = g[g.provider_id == "H"].copy()
    new = h.copy()
    new["game_id"] = "HD-" + new.game_id.str[2:]
    new["route"], new["aggregator"], new["release_date"] = "Direct", None, H_SWITCH
    g = pd.concat([g, new], ignore_index=True)
    keep_old = set(rng.choice(h.game_id, 30, replace=False))
    g["retired_date"] = pd.NaT
    g.loc[(g.provider_id == "H") & ~g.game_id.str.startswith("HD") & ~g.game_id.isin(keep_old), "retired_date"] = H_SWITCH
    g.loc[g.retired_date.notna(), "status"] = "retired"
    g["orig_release"] = g.release_date
    for hid in h.game_id:                                           # novelty is a property of the game, not of the copy
        g.loc[g.game_id == "HD-" + hid[2:], "orig_release"] = g.loc[g.game_id == hid, "release_date"].iloc[0]
    return g


# ------------------------------------------------------------------------------------------------ approvals
def approvals(g: pd.DataFrame, p: pd.DataFrame):
    lic = p.set_index("provider_id").licensed_states
    rows = []
    for r in g.itertuples():
        direct_copy = r.game_id.startswith("HD-")
        if r.status == "live":
            live_a = r.release_date
            approved_a = live_a - pd.Timedelta(days=int(rng.integers(1, 6)))
            sub_a = approved_a - pd.Timedelta(days=max(4, int(lognorm(APPROVAL_DAYS["State A"], 0.35))))
            cert = sub_a - pd.Timedelta(days=int(rng.integers(1, 5)))
        else:                                                        # pipeline: certification under way
            cert = pd.Timestamp("2026-07-07") - pd.Timedelta(days=int(rng.integers(0, 20))) if r.provider_id == "N" else pd.NaT
        lab_sub = cert - pd.Timedelta(days=max(8, int(lognorm(21, 0.3)))) if pd.notna(cert) else pd.NaT
        for s in STATES:
            code = s[-1]
            row = dict(game_id=r.game_id, provider_id=r.provider_id, state=s, lab="Independent test lab 1"
                       if ord(r.provider_id) % 2 else "Independent test lab 2", lab_submitted=lab_sub,
                       cert_date=cert, cert_ref=f"CERT-{r.game_id}-{code}" if pd.notna(cert) else None,
                       par_sheet=True, rules_paytable=True, version_hash=True, rg_messaging_check=True,
                       submitted=pd.NaT, approved=pd.NaT, live_date=pd.NaT, status="not_submitted")
            if code not in lic[r.provider_id]:
                row.update(status="not_licensed")
            elif r.status == "live":
                if s == "State A":
                    sub, appr = sub_a, approved_a
                else:
                    sub = cert + pd.Timedelta(days=int(rng.integers(1, 8)))
                    appr = sub + pd.Timedelta(days=max(4, int(lognorm(APPROVAL_DAYS[s], 0.35))))
                    if direct_copy:   # re-submission of an already approved game: same delays, same states
                        pass
                live = max(appr + pd.Timedelta(days=int(rng.integers(1, 5))), r.release_date)
                if s != "State A" and rng.random() < (0.05 if s == "State B" else 0.12):
                    row.update(submitted=sub, status="pending")        # still in review
                    if sub > DAYS[-1]:
                        row.update(submitted=pd.NaT, status="not_submitted")
                elif appr > pd.Timestamp(AS_OF):
                    row.update(submitted=sub, status="pending")
                else:
                    row.update(submitted=sub, approved=appr, live_date=live, status="approved")
            elif r.provider_id == "N":
                sub = cert + pd.Timedelta(days=int(rng.integers(1, 6)))
                appr = sub + pd.Timedelta(days=max(4, int(lognorm(APPROVAL_DAYS[s], 0.35))))
                if appr <= pd.Timestamp(AS_OF) and s != "State C":
                    row.update(submitted=sub, approved=appr, status="approved")
                else:
                    row.update(submitted=sub, status="pending")
            rows.append(row)
    a = pd.DataFrame(rows)
    # compliance plants (found by src/compliance_alerts.py): 3 Provider L games live in State B with the approval still pending
    plant = a[(a.provider_id == "L") & (a.state == "State B") & (a.status == "approved")].game_id.head(3).tolist()
    m = a.game_id.isin(plant) & (a.state == "State B")
    a.loc[m, "approved"] = pd.NaT
    a.loc[m, "status"] = "pending"
    # 6 Provider N games with missing submission documents; their State C submission cannot go out
    miss = a[(a.provider_id == "N")].game_id.drop_duplicates().iloc[[2, 5, 9, 14, 18, 21]].tolist()
    for gid, col in zip(miss, ["par_sheet", "version_hash", "par_sheet", "rg_messaging_check", "rules_paytable", "version_hash"]):
        a.loc[a.game_id == gid, col] = False
        a.loc[(a.game_id == gid) & (a.state == "State C"), ["submitted", "status"]] = [pd.NaT, "not_submitted"]
    # Provider Q (onboarding, Direct): nothing certified yet, documents being collected
    q = a.provider_id == "Q"
    a.loc[q, ["par_sheet", "version_hash", "rg_messaging_check"]] = [True, False, False]
    return a, plant, miss


def licences(p: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for r in p[p.status != "candidate"].itertuples():
        for s in STATES:
            if s[-1] in r.licensed_states:
                exp = pd.Timestamp(AS_OF) + pd.Timedelta(days=int(rng.integers(120, 900)))
                status = "active"
            else:
                exp, status = pd.NaT, "pending" if r.provider_id == "Q" and s == "State C" else "none"
            rows.append((r.provider_id, s, status, exp))
    lic = pd.DataFrame(rows, columns=["provider_id", "state", "licence_status", "expiry_date"])
    lic.loc[(lic.provider_id == "C") & (lic.state == "State B"), "expiry_date"] = pd.Timestamp("2026-12-04")
    lic.loc[(lic.provider_id == "G") & (lic.state == "State A"), "expiry_date"] = pd.Timestamp("2026-12-22")
    lic.loc[(lic.provider_id == "Q") & (lic.state == "State C"), "licence_status"] = "pending"
    return lic


# ------------------------------------------------------------------------------------------------ daily performance
def daily(g: pd.DataFrame, a: pd.DataFrame, p: pd.DataFrame) -> pd.DataFrame:
    live = a[a.live_date.notna() | ((a.status == "pending") & a.game_id.isin(PLANT_LIVE))].copy()
    live.loc[live.live_date.isna(), "live_date"] = live.submitted + pd.Timedelta(days=3)   # plants: launched anyway
    live = live.merge(g[["game_id", "game_type", "rtp_theoretical", "sd_per_round", "avg_bet", "popularity", "retired_date",
                         "orig_release", "route", "aggregator"]], on="game_id")
    live = live[live.live_date <= DAYS[-1]]
    starts = live.live_date.clip(lower=D0)
    ends = live.retired_date.fillna(DAYS[-1] + pd.Timedelta(days=1)).clip(upper=DAYS[-1] + pd.Timedelta(days=1))
    n = ((ends - starts).dt.days).clip(lower=0).to_numpy()
    idx = np.repeat(np.arange(len(live)), n)
    offs = np.concatenate([np.arange(k) for k in n])
    d = live.iloc[idx].reset_index(drop=True)
    d["date"] = starts.iloc[idx].to_numpy() + pd.to_timedelta(offs, unit="D")
    d = d[["date", "game_id", "provider_id", "state", "game_type", "rtp_theoretical", "sd_per_round", "avg_bet",
           "popularity", "orig_release", "route", "aggregator"]]
    N = len(d)
    dow = d.date.dt.day_of_week.map({0: 0.92, 1: 0.90, 2: 0.92, 3: 0.95, 4: 1.08, 5: 1.18, 6: 1.12}).to_numpy()
    trend = 1 + 0.012 * ((d.date - D0).dt.days / 30.4).to_numpy()
    age = (d.date - d.orig_release).dt.days.clip(lower=0).to_numpy()
    novelty = 1 + 1.4 * np.exp(-age / 10.0)                                        # event 4: novelty effect
    share = np.ones(N)
    hd = d.game_id.str.startswith("HD-").to_numpy()
    dup_old = (d.provider_id.eq("H") & ~d.game_id.str.startswith("HD-") & (d.date >= H_SWITCH)).to_numpy()
    share[hd], share[dup_old] = 0.65, 0.35                                           # event 6: traffic split
    promo = (d.game_id.eq("B-031") & d.state.isin(["State A", "State B"]) &
             d.date.between("2026-06-08", "2026-06-21")).to_numpy()
    # a bigger catalogue splits the same players across more games (cannibalisation)
    n_live = d.groupby(["state", "date"]).game_id.transform("size").to_numpy()
    crowd = (n_live / 300.0) ** -0.55
    lam = 70 * crowd * d.popularity.to_numpy() * d.state.map(STATE_SIZE).to_numpy() * dow * trend * novelty * share
    lam *= np.where(promo, 1.45, 1.0)
    attempts = rng.poisson(lam * lognorm(1, 0.15, N))
    base_err = np.select([d.route.eq("Direct"), d.aggregator.eq("Aggregator X")], [0.004, 0.009], 0.011)
    f_bug = (d.provider_id.eq("F") & d.date.between("2026-05-12", "2026-05-17")).to_numpy()   # event 1
    err = np.where(f_bug, 0.14, base_err * lognorm(1, 0.3, N))
    errors = rng.binomial(attempts, np.clip(err, 0, 1))
    sessions = attempts - errors
    rounds_ps = d.game_type.map({k: v["rounds"] for k, v in TYPE_CFG.items()}).to_numpy()
    rounds = np.round(sessions * rounds_ps * lognorm(1, 0.10, N)).astype(np.int64)
    bet = d.avg_bet.to_numpy() * lognorm(1, 0.08, N)
    wagers = rounds * bet
    rtp = d.rtp_theoretical.to_numpy().copy()
    g12 = (d.game_id.eq("G-012") & (d.date >= "2026-06-15")).to_numpy()                 # wrong RTP config deployed
    rtp[g12] = 0.921
    noise = rng.normal(0, 1, N) * d.sd_per_round.to_numpy() * bet * np.sqrt(np.maximum(rounds, 0))
    wins = np.maximum(wagers * rtp + noise, 0)
    # the false signal: C-007 (very high volatility) lands ~2.2 sd below its theoretical RTP over the last 90 days
    c7 = (d.game_id.eq("C-007") & (d.date >= DAYS[-1] - pd.Timedelta(days=89))).to_numpy()
    if c7.any():
        W = wagers[c7].sum()
        wins[c7] += (0.890 * W - wins[c7].sum()) * wagers[c7] / W
    load = np.select([d.route.eq("Direct")], [1350.0], 1850.0) * lognorm(1, 0.12, N)
    load = np.where(f_bug, load * 2.6, load)
    out = pd.DataFrame(dict(date=d.date.dt.date, game_id=d.game_id, provider_id=d.provider_id, state=d.state,
                            launch_attempts=attempts, launch_errors=errors, sessions=sessions,
                            players=np.round(sessions / rng.uniform(1.35, 1.8, N)).astype(int), rounds=rounds,
                            wagers=wagers.round(2), player_wins=wins.round(2), ggr=(wagers - wins).round(2),
                            avg_load_ms=load.round(0)))
    return out


# ------------------------------------------------------------------------------------------------ wallet API
def wallet(gd: pd.DataFrame, g: pd.DataFrame) -> pd.DataFrame:
    gg = g.set_index("game_id")
    x = gd.assign(route=gd.game_id.map(gg.route), aggregator=gd.game_id.map(gg.aggregator),
                  winf=gd.game_id.map(gg.game_type).map({k: v["winf"] for k, v in TYPE_CFG.items()}))
    x["route_label"] = np.where(x.route == "Direct", "Direct", x.aggregator)
    x["credits"] = x.rounds * x.winf
    agg = x.groupby(["date", "provider_id", "route_label"], as_index=False)[["rounds", "credits"]].sum()
    rows = []
    lat = {"Direct": (70, 160), "Aggregator X": (185, 430), "Aggregator Y": (205, 480)}
    k_days = {pd.Timestamp(s).date() for s in ["2026-07-02", "2026-07-09", "2026-07-15", "2026-07-16", "2026-07-23",
                                               "2026-08-04", "2026-08-05"]}           # event 7
    for r in agg.itertuples():
        p50, p95 = lat[r.route_label]
        j = lognorm(1, 0.08)
        deb = int(r.rounds)
        to = rng.binomial(deb, 0.0004 if r.route_label == "Direct" else 0.0009)
        insuf = rng.binomial(deb, 0.008)
        dup = rng.binomial(deb, 0.0002)
        rb = to + rng.binomial(deb, 0.0001)
        rb_fail_p = rng.uniform(0.08, 0.15) if (r.provider_id == "K" and r.date in k_days) else 0.0005
        rb_fail = rng.binomial(rb, rb_fail_p)
        cred = int(r.credits)
        cto = rng.binomial(cred, 0.0003)
        for ctype, status, n, l50, l95 in (
                ("debit", "OK", deb - to - insuf - dup, p50 * j, p95 * j),
                ("debit", "ERR_INSUFFICIENT_FUNDS", insuf, p50 * j * 0.8, p95 * j * 0.8),
                ("debit", "OK_IDEMPOTENT_REPLAY", dup, p50 * j * 0.6, p95 * j * 0.6),
                ("debit", "ERR_TIMEOUT", to, 3000, 3000),
                ("credit", "OK", cred - cto, p50 * j * 1.05, p95 * j * 1.05),
                ("credit", "ERR_TIMEOUT", cto, 3000, 3000),
                ("rollback", "OK", rb - rb_fail, p50 * j * 1.2, p95 * j * 1.2),
                ("rollback", "ERR_ROLLBACK_FAILED", rb_fail, p95 * j * 2.5, 3000)):
            if n > 0:
                rows.append((r.date, r.provider_id, r.route_label, ctype, status, int(n), round(l50), round(l95)))
    return pd.DataFrame(rows, columns=["date", "provider_id", "route", "call_type", "status", "n_calls",
                                       "latency_p50_ms", "latency_p95_ms"])


# ------------------------------------------------------------------------------------------------ pipeline
STAGES = ["Commercial agreement", "Technical integration", "QA & staging tests", "Lab certification",
          "State approval", "Launch"]
BLOCKERS = {
    "Commercial agreement": ["Contract redlines on liability clause", "Revenue-share tier negotiation"],
    "Technical integration": ["Wallet idempotency test failed (duplicate debit on retry)", "Game launch URL token expiry",
                              "Geolocation check not passed to provider session", "Currency/decimal mismatch on credits"],
    "QA & staging tests": ["Rollback not sent after timeout", "Jackpot contribution not reported in round data",
                           "Responsible-gaming session reminder missing on mobile"],
    "Lab certification": ["Lab requested PAR sheet re-submission", "Version hash mismatch with submitted build"],
    "State approval": ["State requested additional RG messaging evidence", "Supplier licence renewal pending",
                       "Reviewer backlog"],
}


def pipeline(p: pd.DataFrame) -> pd.DataFrame:
    rows = []
    asof = pd.Timestamp(AS_OF)

    def dur(stage, route, state=None):
        med = {"Commercial agreement": 28 if route == "Direct" else 14,
               "Technical integration": 56 if route == "Direct" else 16,
               "QA & staging tests": 21 if route == "Direct" else 10,
               "Lab certification": 24, "Launch": 4}.get(stage)
        if stage == "State approval":
            med = APPROVAL_DAYS[state] * 1.1
        return max(2, int(lognorm(med, 0.3)))

    projects = [(r.provider_id, r.route, pd.Timestamp(r.launch_date) if pd.notna(r.launch_date) else None, r.licensed_states)
                for r in p[p.status.isin(["live", "pipeline"])].itertuples()]
    projects.append(("H", "Direct", H_SWITCH, "ABC"))                                  # re-integration project
    for pid, route, launch, states in projects:
        proj = f"{pid}-{'DIR' if route == 'Direct' else 'AGG'}"
        if pid == "H" and route == "Aggregator":
            proj = "H-AGG"
        sts = [f"State {c}" for c in states]
        # build forward from a start date so that State A launch lands on the known launch date
        d = {s: dur(s, route) for s in STAGES[:4]}
        appr = {s: dur("State approval", route, s) for s in sts}
        lead = sum(d.values()) + appr["State A"] + dur("Launch", route)
        if launch is not None:
            start = launch - pd.Timedelta(days=lead)
        else:
            start = {"N": pd.Timestamp("2026-04-20"), "Q": pd.Timestamp("2026-09-07")}[pid]
        t = start
        for s in STAGES[:4]:
            b = rng.random() < 0.25
            reason = rng.choice(BLOCKERS[s]) if b else ""
            bdays = int(rng.integers(3, 15)) if b else 0
            end = t + pd.Timedelta(days=d[s] + bdays)
            planned = t + pd.Timedelta(days=d[s])
            rows.append(dict(project_id=proj, provider_id=pid, route=route, stage=s, state=None, start_date=t,
                             end_date=end, planned_end_date=planned, blocker=reason, blocked_days=bdays))
            t = end
        cert_end = t
        for s in sts:
            sub = cert_end + pd.Timedelta(days=int(rng.integers(1, 4)))
            b = rng.random() < (0.45 if s == "State C" else 0.2)
            reason = ("Reviewer backlog" if s == "State C" else rng.choice(BLOCKERS["State approval"])) if b else ""
            bdays = int(rng.integers(4, 18)) if b else 0
            end = sub + pd.Timedelta(days=appr[s] + bdays)
            rows.append(dict(project_id=proj, provider_id=pid, route=route, stage="State approval", state=s,
                             start_date=sub, end_date=end, planned_end_date=sub + pd.Timedelta(days=APPROVAL_DAYS[s] + 3),
                             blocker=reason, blocked_days=bdays))
            l0 = end + pd.Timedelta(days=dur("Launch", route))
            rows.append(dict(project_id=proj, provider_id=pid, route=route, stage="Launch", state=s, start_date=end,
                             end_date=l0, planned_end_date=end + pd.Timedelta(days=4), blocker="", blocked_days=0))
    x = pd.DataFrame(rows)
    # status as of AS_OF: anything ending after it is in progress / not started
    x["status"] = np.select([x.end_date <= asof, x.start_date <= asof], ["done", "in_progress"], "not_started")
    x.loc[x.status != "done", "end_date"] = pd.NaT
    x.loc[x.status == "not_started", ["blocker", "blocked_days"]] = ["", 0]
    x.loc[(x.status == "in_progress") & (x.blocker != ""), "status"] = "blocked"
    # Provider N: certification done, States A and B approved, State C stuck in the reviewer backlog
    n_c = (x.project_id == "N-AGG") & (x.stage == "State approval") & (x.state == "State C")
    x.loc[n_c, ["status", "blocker", "end_date"]] = ["blocked", "Reviewer backlog", pd.NaT]
    n_l = (x.project_id == "N-AGG") & (x.stage == "Launch")       # N launches A and B together after approval
    x.loc[n_l, ["status", "start_date", "end_date"]] = ["not_started", pd.NaT, pd.NaT]
    return x


# ------------------------------------------------------------------------------------------------ promotions
def promotions(g: pd.DataFrame):
    promos = []
    for i, (pid, gid, st, start, days, spins, val, n, hold) in enumerate([
            ("A", "A-004", "State A", "2025-11-21", 10, 10, 0.20, 15000, False),
            ("J", "J-002", "State A|State B", "2026-01-16", 14, 25, 0.20, 22000, False),
            ("C", "C-019", "State B", "2026-02-13", 7, 10, 0.50, 8000, False),
            ("I", "I-003", "State A|State B|State C", "2026-03-20", 10, 15, 0.40, 26000, False),
            ("L", "L-001", "State A", "2026-04-10", 14, 20, 0.25, 12000, False),
            ("B", "B-031", "State A|State B", "2026-06-08", 14, 20, 0.50, 40000, True),
            ("D", "D-005", "State A", "2026-07-24", 7, 0, 0.0, 9000, False),
            ("F", "F-020", "State B", "2026-09-04", 10, 10, 0.30, 10000, False)]):
        promos.append(dict(promo_id=f"PR{i + 1:02d}", provider_id=pid, game_id=gid, states=st, start_date=start,
                           end_date=(pd.Timestamp(start) + pd.Timedelta(days=days - 1)).date(),
                           mechanic="Free spins" if spins else "Live-table cashback", spins_per_player=spins,
                           spin_value_usd=val, players_targeted=n, has_holdout=hold))
    pr = pd.DataFrame(promos)
    # player-level results of PR06 (random 10% hold-out). Outcome window: 28 days from the start; pre-period 28 days.
    n = 40000
    grp = np.where(rng.random(n) < 0.10, "control", "treatment")
    t = grp == "treatment"
    engaged = rng.random(n)                                           # latent engagement drives both use and play
    pre_act = rng.random(n) < 0.45 + 0.35 * engaged
    pre_ggr = np.where(pre_act, lognorm(55, 0.9, n) * (0.5 + engaged) + rng.normal(0, 25, n), 0)
    post_act = rng.random(n) < 0.42 + 0.35 * engaged + 0.06 * t
    post_ggr = np.where(post_act, lognorm(55, 0.9, n) * (0.5 + engaged) + rng.normal(0, 25, n), 0) + 4.5 * t
    # selection: players who actually used their spins were already the more engaged ones (biases naive comparisons)
    used = t & (rng.random(n) < 0.35 + 0.55 * engaged)
    spins_used = np.where(used, rng.integers(5, 21, n), 0)
    cost = spins_used * 0.50 * 0.96                                    # expected payout of the free spins
    pp = pd.DataFrame(dict(promo_id="PR06", player_id=[f"PL{100000 + i}" for i in range(n)], group=grp,
                           state=rng.choice(["State A", "State B"], n, p=[0.58, 0.42]), spins_used=spins_used,
                           free_spin_cost_usd=cost.round(2), active_pre_28d=pre_act.astype(int),
                           ggr_pre_28d=pre_ggr.round(2), active_post_28d=post_act.astype(int),
                           ggr_post_28d=post_ggr.round(2)))
    pr["players_reached"] = pr.players_targeted.mul(rng.uniform(0.55, 0.72, len(pr))).round().astype(int)
    pr.loc[pr.promo_id == "PR06", "players_reached"] = int((pp.spins_used > 0).sum())
    pr["cost_usd"] = (pr.players_reached * pr.spins_per_player.clip(lower=10) * 0.6 * pr.spin_value_usd.clip(lower=0.2) * 0.96).round(0)
    pr.loc[pr.promo_id == "PR06", "cost_usd"] = round(pp.free_spin_cost_usd.sum(), 0)
    return pr, pp


def candidates(p: pd.DataFrame) -> pd.DataFrame:
    c = p[p.status == "candidate"].copy()
    extra = pd.DataFrame({
        "provider_id": ["O", "P", "R", "S", "T"],
        "integration_effort_weeks": [14, 12, 4, 3, 3],                 # engineering + QA person-weeks
        "portfolio_certified_elsewhere": [True, True, True, False, True],
        "known_partner": [False, False, True, True, True],             # already used via this aggregator
        "note": ["Live dealer studio (blackjack, roulette, game shows)", "Large slot studio, strong brand in other markets",
                 "Network jackpot slots", "RNG table games, only licensed in State A", "Small high-volatility slot studio"],
    })
    return c.drop(columns=["launch_date", "vol_tilt", "route_change", "status"]).merge(extra, on="provider_id")


PLANT_LIVE: list[str] = []


def main():
    global PLANT_LIVE
    SIM.mkdir(parents=True, exist_ok=True)
    p = providers()
    g = games(p)
    a, plant, miss = approvals(g, p)
    PLANT_LIVE = plant
    gd = daily(g, a, p)
    w = wallet(gd, g)
    pipe = pipeline(p)
    lic = licences(p)
    pr, pp = promotions(g)
    cand = candidates(p)
    approved = a[a.status == "approved"].groupby("game_id").state.apply(lambda s: "|".join(sorted(s)))
    g["states_approved"] = g.game_id.map(approved).fillna("")
    pf = p.set_index("provider_id")
    g["provider_fee"] = np.where(g.game_id.str.startswith("HD-"), H_DIRECT_FEE, g.provider_id.map(pf.provider_fee))
    g["aggregator_fee"] = g.aggregator.map(AGG_FEE).fillna(0.0)
    cols = ["game_id", "provider_id", "title", "game_type", "volatility", "rtp_theoretical", "sd_per_round", "avg_bet",
            "release_date", "retired_date", "route", "aggregator", "provider_fee", "aggregator_fee", "status",
            "states_approved"]
    g[cols].to_csv(SIM / "games.csv", index=False, date_format="%Y-%m-%d")
    p.drop(columns=["vol_tilt"]).to_csv(SIM / "providers.csv", index=False)
    gd.to_parquet(SIM / "game_daily.parquet", index=False)
    a.to_csv(SIM / "game_approvals.csv", index=False, date_format="%Y-%m-%d")
    lic.to_csv(SIM / "provider_licences.csv", index=False, date_format="%Y-%m-%d")
    w.to_csv(SIM / "wallet_api_logs.csv", index=False)
    pipe.to_csv(SIM / "integration_pipeline.csv", index=False, date_format="%Y-%m-%d")
    pr.to_csv(SIM / "promotions.csv", index=False)
    pp.to_csv(SIM / "promo_players.csv", index=False)
    cand.to_csv(SIM / "candidate_providers.csv", index=False)
    truth = pd.DataFrame([
        (1, "Provider update breaks game launches", "Provider F", "2026-05-12", "2026-05-17", "launch error rate ~14% vs <1%"),
        (2, "RTP false signal (variance)", "C-007", "2026-07-03", END, "very high volatility, realised RTP 89.0% vs 96.0%, inside 3-sigma bounds"),
        (2, "RTP true deviation (wrong config)", "G-012", "2026-06-15", END, "realised RTP ~92.1% vs 96.0% certified"),
        (3, "Certification bottleneck", "State C", START, END, f"median approval {APPROVAL_DAYS['State C']} days vs "
         f"{APPROVAL_DAYS['State A']}-{APPROVAL_DAYS['State B']}"),
        (4, "Novelty effect", "all new games", START, END, "launch demand x2.4 decaying with a 10-day time constant"),
        (5, "Aggregator to direct switch", "Provider H", str(H_SWITCH.date()), END, "p95 latency 430 -> 160 ms; fee 12%+3% -> 11%"),
        (6, "Duplicate catalogue entries", "Provider H", str(H_SWITCH.date()), END, "30 old aggregator copies left live"),
        (7, "Intermittent rollback failures", "Provider K", "2026-07-02", "2026-08-05", "7 days with 8-15% failed rollbacks"),
        (8, "Free-spin promotion with hold-out", "PR06 / B-031", "2026-06-08", "2026-07-05", "true uplift +$4.5 GGR + 6 pts activity"),
        (9, "Compliance: live without approval", "|".join(plant), "", "", "Provider L games live in State B, approval pending"),
        (10, "Compliance: missing documents", "|".join(miss), "", "", "Provider N, blocks State C submission"),
        (11, "Compliance: supplier licences expiring", "C (State B), G (State A)", "", "", "expiry 2026-12-04 and 2026-12-22"),
    ], columns=["event_id", "event", "entity", "start", "end", "detail"])
    truth.to_csv(SIM / "_hidden_truth.csv", index=False)
    print(f"games {len(g)} ({(g.status == 'live').sum()} live) | game_daily {len(gd):,} rows | wallet {len(w):,} rows | "
          f"pipeline {len(pipe)} rows | approvals {len(a)} | monthly GGR ${gd.ggr.sum() / 12 / 1e6:.1f}M")


if __name__ == "__main__":
    main()
