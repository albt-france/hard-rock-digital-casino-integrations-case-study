"""Report charts (matplotlib -> inline SVG). House style of the earlier case studies: light card background, blue = the
data, grey = the comparison, red = problems, dashed lines = thresholds, Segoe UI, one y-axis only. Game types use the
validated categorical order (blue, orange, aqua, yellow) and are always labelled, never colour-only."""
from __future__ import annotations

import io
import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

BLUE, BLUE_L, BLUE_D = "#2A78D6", "#86B6EF", "#1C5CAB"
GRAY, GRAY_D, RED, GREEN, ORANGE = "#C9C7BF", "#898781", "#D03B3B", "#0E7A55", "#EB6834"
INK, INK2, GRID, CARD = "#0B0B0B", "#52514E", "#E1E0D9", "#FCFCFB"
TYPE_COL = {"Slot": "#2A78D6", "Jackpot slot": "#EB6834", "Table": "#1BAF7A", "Live dealer": "#EDA100"}

plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans"], "font.size": 9.5, "text.color": INK2,
    "axes.edgecolor": GRID, "axes.labelcolor": INK2, "axes.facecolor": CARD, "figure.facecolor": CARD,
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
    "axes.grid": True, "axes.grid.axis": "y", "grid.color": GRID, "grid.linewidth": 0.8,
    "xtick.color": GRAY_D, "ytick.color": INK2, "xtick.labelsize": 9, "ytick.labelsize": 9,
    "xtick.major.size": 0, "ytick.major.size": 0, "legend.frameon": False, "legend.fontsize": 9,
    "svg.fonttype": "none", "axes.axisbelow": True,
})


def fig(w_px, h_px):
    return plt.subplots(figsize=(w_px / 96, h_px / 96), dpi=96)


def svg(f) -> str:
    buf = io.StringIO()
    f.savefig(buf, format="svg", bbox_inches="tight", pad_inches=0.05)
    plt.close(f)
    s = buf.getvalue()
    s = s[s.find("<svg"):]
    s = re.sub(r'width="[\d.]+pt" height="[\d.]+pt"', 'width="100%" height="100%" preserveAspectRatio="xMidYMid meet"', s, 1)
    return re.sub(r"<metadata>.*?</metadata>", "", s, flags=re.S)


def usd_m(ax, axis="y", d=0):
    fmt = matplotlib.ticker.FuncFormatter(lambda v, _: f"${v / 1e6:,.{d}f}M")
    (ax.yaxis if axis == "y" else ax.xaxis).set_major_formatter(fmt)


# ------------------------------------------------------------------ PUBLIC DATA
def market_lines(mk: pd.DataFrame, w=600, h=270):
    """NJ online casino win and PA online casino GGR (slots + tables), USD per month, same unit, one axis."""
    d = mk.assign(d=pd.to_datetime(mk.month))
    f, ax = fig(w, h)
    ax.plot(d.d, d.nj_casino_win, color=BLUE, lw=2)
    p = d.dropna(subset=["pa_casino_ggr"])
    ax.plot(p.d, p.pa_casino_ggr, color=GRAY_D, lw=2)
    ax.text(d.d.iloc[-1], d.nj_casino_win.iloc[-1] * 1.03, " New Jersey", color=BLUE_D, fontsize=9, va="bottom", ha="right")
    ax.text(p.d.iloc[0], p.pa_casino_ggr.iloc[0] * 0.95, "Pennsylvania", color=GRAY_D, fontsize=9, va="top")
    usd_m(ax)
    ax.set_ylim(0, d[["nj_casino_win", "pa_casino_ggr"]].max().max() * 1.2)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %y"))
    ax.set_ylabel("Online casino revenue per month")
    return svg(f)


def licensee_share(ls: pd.DataFrame, w=430, h=270):
    d = ls.sort_values("share")
    d["lab"] = d.licensee.str.replace("Caesars Interactive NJ", "Caesars Int. NJ").str.replace(
        "Caesars Interactive Entertainment New Jersey (Affiliate Of Caesars Atlantic City)", "Caesars Int. NJ (Caesars AC)")
    f, ax = fig(w, h)
    cols = [BLUE if "Hard Rock" in x else GRAY for x in d.licensee]
    ax.barh(d.lab, d.share, color=cols, height=0.62)
    for y, (v, lab) in enumerate(zip(d.share, d.licensee)):
        ax.text(v + 0.004, y, f"{v:.1%}", va="center", fontsize=8.5, color=BLUE_D if "Hard Rock" in lab else INK2)
    ax.grid(False)
    ax.set_xticks([])
    ax.set_xlim(0, d.share.max() * 1.18)
    ax.tick_params(axis="y", labelsize=8.5)
    return svg(f)


def hard_rock_skin(hr: pd.DataFrame, w=430, h=250):
    d = hr.assign(d=pd.to_datetime(hr.month))
    f, ax = fig(w, h)
    last12 = d.d >= d.d.iloc[-12]
    ax.bar(d.d, d.hard_rock_bet_casino_win_usd, width=22, color=np.where(last12, BLUE, GRAY))
    usd_m(ax)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %y"))
    ax.set_ylabel("'Hard Rock Bet' skin, casino win")
    return svg(f)


# ------------------------------------------------------------------ SIMULATED
def type_gap(gap: dict, ggr: dict, cat: dict, w=470, h=250):
    """Share of the live catalogue vs share of GGR by game type (last 90 days): paired horizontal bars."""
    types = sorted(gap, key=gap.get)
    f, ax = fig(w, h)
    y = np.arange(len(types))
    ax.barh(y + 0.19, [cat[t] for t in types], height=0.34, color=GRAY, label="Share of live catalogue")
    ax.barh(y - 0.19, [ggr[t] for t in types], height=0.34, color=[TYPE_COL[t] for t in types], label="Share of GGR")
    for i, t in enumerate(types):
        ax.text(1.0, i, f"x{gap[t]:.1f}", va="center", ha="right", fontsize=10, color=INK, fontweight="bold")
        ax.text(ggr[t] + 0.008, i - 0.19, f"{ggr[t]:.0%}", va="center", fontsize=8.5, color=INK2)
        ax.text(cat[t] + 0.008, i + 0.19, f"{cat[t]:.0%}", va="center", fontsize=8.5, color=GRAY_D)
    ax.text(1.0, len(types) - 0.45, "GGR share /\nshelf share", ha="right", va="bottom", fontsize=8, color=INK2)
    ax.set_yticks(y, types)
    ax.set_xticks([])
    ax.grid(False)
    ax.set_xlim(0, 1.0)
    ax.set_ylim(-0.6, len(types) - 0.1)
    ax.legend(loc="lower center", bbox_to_anchor=(0.42, 1.0), ncol=2, fontsize=8.5)
    return svg(f)


def stage_bars(st: pd.DataFrame, w=520, h=240):
    order = ["Commercial agreement", "Technical integration", "QA & staging tests", "Lab certification", "State approval"]
    d = st.set_index("stage").loc[order]
    f, ax = fig(w, h)
    y = np.arange(len(order))
    ax.barh(y + 0.19, d.Aggregator, height=0.34, color=BLUE, label="Via an aggregator")
    ax.barh(y - 0.19, d.Direct, height=0.34, color=GRAY_D, label="Direct integration")
    for i in range(len(order)):
        ax.text(d.Aggregator.iloc[i] + 0.8, i + 0.19, f"{d.Aggregator.iloc[i]:.0f}", va="center", fontsize=8.5)
        ax.text(d.Direct.iloc[i] + 0.8, i - 0.19, f"{d.Direct.iloc[i]:.0f}", va="center", fontsize=8.5)
    ax.set_yticks(y, ["Agreement", "Tech integration", "QA / staging", "Lab certification", "State approval"])
    ax.invert_yaxis()
    ax.set_xlabel("Median days per stage (finished stages)")
    ax.grid(axis="x")
    ax.grid(axis="y", visible=False)
    ax.legend(loc="lower right", fontsize=8.5)
    return svg(f)


def approval_box(ap: pd.DataFrame, w=430, h=240):
    d = ap[ap.status == "approved"].copy()
    d["days"] = (pd.to_datetime(d.approved) - pd.to_datetime(d.submitted)).dt.days
    f, ax = fig(w, h)
    states = ["State A", "State B", "State C"]
    data = [d[d.state == s].days for s in states]
    bp = ax.boxplot(data, vert=False, widths=0.5, patch_artist=True, showfliers=False,
                    medianprops=dict(color=INK, lw=1.5), whiskerprops=dict(color=GRAY_D), capprops=dict(color=GRAY_D))
    for b, s in zip(bp["boxes"], states):
        b.set(facecolor=RED if s == "State C" else BLUE_L, edgecolor="none", alpha=0.85)
    for i, x in enumerate(data):
        end = bp["whiskers"][2 * i + 1].get_xdata()[1]
        ax.text(end + 1.5, i + 1, f"median {x.median():.0f} d", va="center", fontsize=9,
                color=RED if i == 2 else INK2, fontweight="bold" if i == 2 else "normal")
    ax.set_xlim(0, max(bp["whiskers"][5].get_xdata()[1] + 16, 70))
    ax.set_yticks([1, 2, 3], states)
    ax.invert_yaxis()
    ax.set_xlabel("Days from state submission to approval, per game")
    ax.grid(axis="x")
    ax.grid(axis="y", visible=False)
    return svg(f)


def backlog_points(b: pd.DataFrame, w=400, h=200):
    s = b[b["Issue Type"] == "Story"].groupby("Parent")["Story Points"].sum()
    names = b[b["Issue Type"] == "Epic"].set_index("Issue ID").Summary
    f, ax = fig(w, h)
    lab = [f"{e} {names[e]}" for e in s.index]
    ax.barh(lab, s.values, color=BLUE, height=0.6)
    for i, v in enumerate(s.values):
        ax.text(v + 0.3, i, f"{v:.0f} pts", va="center", fontsize=8.5)
    ax.invert_yaxis()
    ax.set_xticks([])
    ax.grid(False)
    ax.set_xlim(0, s.max() * 1.25)
    return svg(f)


def launch_errors(lf: pd.DataFrame, w=470, h=230):
    d = lf.assign(d=pd.to_datetime(lf.day))
    d = d[(d.d >= "2026-04-01") & (d.d <= "2026-06-30")]
    f, ax = fig(w, h)
    ax.plot(d.d, d.error_rate, color=GRAY_D, lw=1.6)
    a = d[d.alert]
    ax.scatter(a.d, a.error_rate, color=RED, s=26, zorder=3, edgecolor=CARD, linewidth=1.5)
    ax.axhline(0.03, color=RED, ls=(0, (3, 3)), lw=1)
    ax.text(d.d.iloc[0], 0.034, "alert floor 3% (and 3x baseline)", color=RED, fontsize=8)
    ax.annotate("Provider F update\n6 days", (a.d.iloc[0], a.error_rate.max()), xytext=(-70, -8),
                textcoords="offset points", fontsize=8.5, color=RED, ha="right")
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1, 0))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    ax.set_ylabel("Launch error rate, Provider F")
    return svg(f)


def rtp_funnel(rt: pd.DataFrame, w=520, h=260):
    """Gap to theoretical RTP vs rounds played (log x), with the 3-sigma band for a medium and a very-high volatility slot."""
    f, ax = fig(w, h)
    d = rt[rt.game_type.isin(["Slot", "Jackpot slot"])]
    ax.scatter(d.rounds, d.gap * 100, s=9, color=GRAY, alpha=0.8, linewidths=0)
    n = np.logspace(np.log10(d.rounds.min()), np.log10(d.rounds.max() * 1.3), 100)
    for sd, lab, col in ((6, "3-sigma band, medium volatility", BLUE), (25, "3-sigma band, very high volatility", GRAY_D)):
        ax.plot(n, -300 * sd / np.sqrt(n), color=col, ls=(0, (3, 3)), lw=1.1, label=lab)
        ax.plot(n, 300 * sd / np.sqrt(n), color=col, ls=(0, (3, 3)), lw=1.1)
    ax.axhline(-3, color=ORANGE, lw=1, ls=(0, (1, 2)), label="naive rule: 3 pts below theory")
    rr = rt.set_index("game_id")
    for gid, col, txt, xy in (("C-007", BLUE_D, f"C-007: {rr.loc['C-007'].rtp_realised:.1%} vs {rr.loc['C-007'].rtp_theoretical:.1%}\n"
                               "inside its band: noise", (-150, -32)),
                              ("G-012", RED, f"G-012: {rr.loc['G-012'].rtp_realised:.1%} vs {rr.loc['G-012'].rtp_theoretical:.1%}\n"
                               f"z = {rr.loc['G-012'].z:.1f}: wrong config", (12, -30))):
        r = rr.loc[gid]
        ax.scatter(r.rounds, r.gap * 100, s=50, color=col, zorder=4, edgecolor=CARD, linewidth=1.5)
        ax.annotate(txt, (r.rounds, r.gap * 100), xytext=xy, textcoords="offset points", fontsize=8.3, color=col,
                    fontweight="bold", arrowprops=dict(arrowstyle="-", color=col, lw=0.8))
    ax.legend(loc="upper left", fontsize=7.8, ncol=1)
    ax.set_xscale("log")
    ax.set_ylim(-18, 16)
    ax.set_xlabel("Rounds played, last 90 days (log scale)")
    ax.set_ylabel("Realised - theoretical RTP (pts)")
    return svg(f)


def novelty(lc: pd.DataFrame, w=420, h=230):
    f, ax = fig(w, h)
    ax.plot(lc.age, lc.index_vs_steady, color=BLUE, lw=2)
    ax.axhline(1, color=GRAY_D, ls=(0, (3, 3)), lw=1)
    ax.axvspan(0, 7, color=BLUE_L, alpha=0.18, lw=0)
    ax.axvspan(30, 60, color=GRAY, alpha=0.22, lw=0)
    ax.text(8, lc.index_vs_steady.max(), "week 1: looks great", fontsize=8.5, color=BLUE_D, va="top")
    ax.text(31, lc.index_vs_steady.max() * 0.98, "judge here\n(days 30-60)", fontsize=8, color=INK2, va="top")
    ax.set_xlabel("Days since release")
    ax.set_ylabel("Sessions vs steady state (=1)")
    return svg(f)


def roadmap_bars(rk: pd.DataFrame, mc: pd.DataFrame, w=460, h=230):
    d = rk.merge(mc, on="provider_id").sort_values("score")
    f, ax = fig(w, h)
    cols = [BLUE if r == 1 else (BLUE_L if r == 2 else GRAY) for r in d["rank"]]
    ax.barh("Provider " + d.provider_id, d.score / 1e3, color=cols, height=0.6)
    for i, r in enumerate(d.itertuples()):
        ax.text(r.score / 1e3 + 4, i, f"${r.score / 1e3:,.0f}k / person-week · first in {r.p_first:.0%} of runs",
                va="center", fontsize=8.3, color=INK2)
    ax.set_xticks([])
    ax.grid(False)
    ax.set_xlim(0, d.score.max() / 1e3 * 2.0)
    return svg(f)


def ttl_hist(tt: pd.DataFrame, pct: dict, w=420, h=220):
    """pct = {route: (p50, p80)} from the full 10,000-run simulation (the histogram shows a 4,000-run sample)."""
    f, ax = fig(w, h)
    bins = np.arange(40, 320, 10)
    for route, col in (("Aggregator", BLUE), ("Direct", GRAY_D)):
        x = tt[tt.route == route].days
        ax.hist(x, bins=bins, color=col, alpha=0.65, label=f"{route}: P50 {pct[route][0]:.0f} d, P80 {pct[route][1]:.0f} d")
    ax.set_xlabel("Days from decision to launch in States A + B (Monte-Carlo)")
    ax.set_yticks([])
    ax.grid(False)
    ax.legend(loc="upper right", fontsize=8.3)
    return svg(f)
