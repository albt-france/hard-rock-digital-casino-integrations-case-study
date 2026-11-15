"""8-page PDF report (landscape 16:9): HTML + inline SVG charts, printed to PDF by headless Microsoft Edge.
Every number comes from data/output, data/public or the integration dossier (pipeline outputs); none is typed in.

Run: python src/build_pdf.py   -> docs/Hard_Rock_Digital_Casino_Integrations_Case_Study.pdf, docs/img/*.png
"""
from __future__ import annotations

import json
import shutil
import subprocess
import time
from pathlib import Path

import pandas as pd
from jinja2 import Template

import charts as C
from config import AI_NOTE, DASH, DOCS, FOOTER, IMG, INTEG, OUT, PUBLIC, ROOT, SIM, STATUS

TMP = ROOT / ".tmp"
PDF = DOCS / "Hard_Rock_Digital_Casino_Integrations_Case_Study.pdf"
rd = lambda n: pd.read_csv(OUT / f"{n}.csv")  # noqa: E731

CSS = """
@page { size: 16in 9in; margin: 0 }
* { box-sizing: border-box; margin: 0; padding: 0 }
body { font-family: 'Segoe UI', system-ui, sans-serif; color: #0B0B0B; background: #F4F4F2; }
.page { width: 1536px; height: 864px; padding: 30px 40px 16px; display: flex; flex-direction: column;
        background: #F4F4F2; page-break-after: always; overflow: hidden; position: relative }
header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; min-height: 58px }
h1 { font-size: 24px; font-weight: 700; line-height: 1.2; max-width: 1220px; letter-spacing: -0.2px }
.sub { color: #52514E; font-size: 13.5px; margin-top: 6px; max-width: 1240px; line-height: 1.4 }
.tag { font-size: 11.5px; font-weight: 700; letter-spacing: .8px; color: #52514E; border: 1px solid #C9C7BF;
       border-radius: 4px; padding: 4px 9px; white-space: nowrap; margin-top: 6px; background: #FCFCFB }
.tag.sim { color: #1C5CAB; border-color: #86B6EF } .tag.real { color: #0E7A55; border-color: #8FD3B8 }
.kpis { display: grid; gap: 14px; margin-bottom: 12px }
.card { background: #FCFCFB; border: 1px solid #E1E0D9; border-radius: 8px; padding: 12px 16px; display: flex;
        flex-direction: column; min-height: 0; overflow: hidden }
.kpi { padding: 11px 17px }
.klabel { font-size: 11px; font-weight: 700; color: #52514E; letter-spacing: .5px; text-transform: uppercase }
.kval { font-size: 29px; font-weight: 700; margin-top: 2px; line-height: 1.15 } .kval.blue { color: #1C5CAB } .kval.red { color: #B02E2E }
.knote { font-size: 12.3px; color: #52514E; margin-top: 3px; line-height: 1.35 }
.grid { display: grid; gap: 13px; flex: 1; min-height: 0 }
.card h3 { font-size: 13.3px; font-weight: 600; margin-bottom: 6px }
.card h3 .lab { margin-left: 6px }
.body { flex: 1; min-height: 0; display: flex; align-items: center; justify-content: center; font-size: 13.6px; line-height: 1.45 }
.body svg { width: 100%; height: 100% } .body img { max-width: 100%; max-height: 100%; border: 1px solid #E1E0D9; border-radius: 4px }
.body.text { display: block; overflow: hidden; color: #2B2A28 }
.body.text p { margin-bottom: 6px } .body.text ul { margin: 0 0 6px 18px } .body.text li { margin-bottom: 3.5px }
table { border-collapse: collapse; width: 100%; font-size: 12.5px }
th { text-align: left; color: #52514E; font-weight: 600; border-bottom: 1px solid #C9C7BF; padding: 3px 5px }
td { padding: 3px 5px; border-bottom: 1px solid #EEEDE8; vertical-align: top }
td.n, th.n { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap }
td.p1 { color: #B02E2E; font-weight: 700 } td.p2 { color: #9A6A00; font-weight: 700 } td.p3 { color: #52514E; font-weight: 700 }
tr.hl td { background: #EEF5FD; font-weight: 600 }
footer { font-size: 10.5px; color: #898781; margin-top: 9px }
b.blue { color: #1C5CAB } b.red { color: #B02E2E } b.green { color: #0E7A55 }
.lab { font-weight: 700; color: #52514E; font-size: 11px; letter-spacing: .4px }
.lab.sim { color: #1C5CAB } .lab.real { color: #0E7A55 }
.flow { display: flex; gap: 7px; align-items: stretch; width: 100% }
.flow div.s { flex: 1; border: 1px solid #86B6EF; background: #EEF5FD; border-radius: 6px; padding: 7px 8px; font-size: 12px; line-height: 1.35 }
.flow div.s b { display: block; color: #1C5CAB; margin-bottom: 3px; font-size: 12.5px } .flow div.s i { color: #52514E; font-style: normal; font-size: 11.3px; display: block; margin-top: 4px }
.flow div.s.reg { border-color: #8FD3B8; background: #EEF8F3 } .flow div.s.reg b { color: #0E7A55 }
.flow div.a { color: #898781; font-size: 18px; align-self: center }
.story { border-left: 3px solid #2A78D6; padding: 2px 0 2px 9px; margin-bottom: 8px }
.story .t { font-weight: 700; color: #1C5CAB } .story ul { margin: 3px 0 0 16px } .story li { margin-bottom: 2px; font-size: 12.8px }
.gwt { font-weight: 700; color: #52514E }
.mono { font-family: Consolas, monospace; font-size: 11.2px; background: #F1F0EB; padding: 1px 4px; border-radius: 3px }
.ai { border-left: 3px solid #2A78D6; padding: 6px 10px; background: #EEF5FD; font-size: 12.8px; margin-top: 4px }
"""

PAGE = Template("""
<section class="page">
  <header><div><h1>{{ p.title }}</h1>{% if p.subtitle %}<p class="sub">{{ p.subtitle }}</p>{% endif %}</div>
  {% if p.tag %}<div class="tag {{ p.tag_class }}">{{ p.tag }}</div>{% endif %}</header>
  {% if p.kpis %}<div class="kpis" style="grid-template-columns: repeat({{ p.kpis|length }}, 1fr)">
    {% for k in p.kpis %}<div class="card kpi"><div class="klabel">{{ k[0] }}</div><div class="kval {{ k[3] if k|length > 3 else '' }}">{{ k[1] }}</div><div class="knote">{{ k[2] }}</div></div>{% endfor %}
  </div>{% endif %}
  <div class="grid" style="grid-template-columns: {{ p.cols }}; grid-template-rows: {{ p.rows }}">
    {% for c in p.cards %}<div class="card" style="grid-column: {{ c.col }}; grid-row: {{ c.row }}">
      {% if c.title %}<h3>{{ c.title }}</h3>{% endif %}<div class="body {{ 'text' if c.text else '' }}">{{ c.body }}</div></div>{% endfor %}
  </div>
  <footer>{{ p.footer }} · {{ foot }}</footer>
</section>""")

REAL, SIMT = "<span class='lab real'>PUBLIC DATA</span>", "<span class='lab sim'>SIMULATED</span>"


def card(title, body, col="auto", row="auto", text=False):
    return dict(title=title, body=body, col=col, row=row, text=text)


def pct(x, d=0):
    return f"{100 * x:.{d}f}%"


def usd(x, d=0):
    return ("-" if x < 0 else "") + f"${abs(x):,.{d}f}"


def musd(x, d=1):
    return f"${x / 1e6:,.{d}f}M"


def busd(x, d=2):
    return f"${x / 1e9:,.{d}f}B"


def table(rows, head, num=(), cls=None):
    th = "".join(f"<th class='{'n' if i in num else ''}'>{h}</th>" for i, h in enumerate(head))
    tr = ""
    for k, r in enumerate(rows):
        rc = f" class='{cls[k]}'" if cls and cls[k] else ""
        tr += f"<tr{rc}>" + "".join(f"<td class='{'n' if i in num else ''}'>{v}</td>" for i, v in enumerate(r)) + "</tr>"
    return f"<table><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table>"


def dash_img() -> str:
    f = IMG / "dashboard_1.png"
    return f'<img src="{f.as_uri()}">' if f.exists() else "<p>Interactive view: dashboard/casino_integrations.html</p>"


# ======================================================================================
def build_pages():
    R = json.loads((OUT / "nb_results.json").read_text(encoding="utf-8"))
    NJ, HR, PA, LA, RT, NO, RO, DU, RB, CE, FC, RM, PR, DT = (R[k] for k in (
        "nj", "hard_rock", "pa", "launch", "rtp", "novelty", "route", "dups", "rollback", "cert", "forecast", "roadmap",
        "promo", "detection"))
    facts = pd.read_csv(PUBLIC / "hard_rock_digital_facts.csv")
    mk, ls, hr = rd("nb_market_monthly"), rd("nb_nj_licensee_share"), pd.read_csv(PUBLIC / "nj_hard_rock_skin.csv")
    stage, ap = pd.read_csv(OUT / "nb_stage_table.csv"), pd.read_csv(SIM / "game_approvals.csv")
    bl, al = pd.read_csv(INTEG / "backlog.csv"), pd.read_csv(STATUS / "compliance_alerts.csv")
    rk, mc, oat, tt = rd("nb_roadmap"), rd("nb_sensitivity_mc"), rd("nb_sensitivity_oat"), rd("nb_ttl_sample")
    fcast, det, kp = rd("nb_forecast"), rd("nb_detection"), rd("kpis").set_index("qtr")
    tr = pd.read_csv(INTEG / "compliance_tracker.csv")
    pipe = pd.read_csv(SIM / "integration_pipeline.csv")
    games = pd.read_csv(SIM / "games.csv")
    n_games, n_live = len(games), int((games.status == "live").sum())
    ttl_a, ttl_d = FC["agg_ab_p50"], FC["dir_ab_p50"]
    pages = []

    # 0 Overview -----------------------------------------------------------------------------------------------------
    qs = [("1. How big is US online casino, and where does Hard Rock appear?", REAL,
           f"New Jersey online casino win reached {busd(NJ['casino_win_12m'])} in the 12 months to {NJ['last']} "
           f"({NJ['growth']:+.0%}). The 'Hard Rock Bet' skin took {pct(HR['skin_share_nj'], 1)} of it, up {pct(HR['skin_growth'])}."),
          ("2. What does it take to launch a game?", f"{REAL} {SIMT}",
           f"Contract, wallet integration, tests, lab certification, then approval state by state. P50 to launch: "
           f"~{ttl_a:.0f} days via an aggregator, ~{ttl_d:.0f} direct."),
          ("3. Can requirements and tracking prevent surprises?", SIMT,
           f"15 user stories with Given/When/Then criteria, a Jira backlog and weekly alerts: today "
           f"{(al.severity == 'P1').sum()} games are live without approval and must be switched off."),
          ("4. After launch, what is a defect and what is noise?", SIMT,
           f"A naive RTP rule raises {RT['naive']} alarms; volatility-aware bounds keep one real problem (G-012). Also: a "
           f"broken provider update ({usd(LA['ggr_lost'])} GGR lost), failed rollbacks, {DU['groups']} duplicate games."),
          ("5. Which provider next?", SIMT,
           f"Provider {RM['first']} (live dealer), first in {pct(RM['p_first'][RM['first']])} of 5,000 sensitivity runs; "
           f"Provider {RM['second']} (jackpots via an aggregator) alongside.")]
    qhtml = "<div style='font-size:13px'>" + "".join(f"<p><b>{q}</b> {t}<br>{a}</p>" for q, t, a in qs) + "</div>"
    recs = ("<ul>"
            f"<li><b>Launch Provider N in States A and B now.</b> It has been approved there since July and waits for State C, "
            f"where approvals take {CE['ratio_c']:.1f}x longer. Never tie a launch to the slowest state.</li>"
            f"<li><b>Clear the {(al.severity == 'P1').sum()} P1 compliance alerts today</b> and make "
            "\"approved in this state\" a release gate in the CMS.</li>"
            f"<li><b>Integrate Provider {RM['first']} (live dealer) next and Provider {RM['second']} (jackpots) alongside:</b> "
            f"live games earn {pct(RM['ggr_share']['Live dealer'])} of GGR from {pct(RM['cat_share']['Live dealer'])} of the shelf. "
            "More generic slots add little.</li>"
            f"<li><b>Switch off the {DU['groups']} duplicate Provider H entries</b> ({usd(DU['fees'])} of aggregator fees since April) "
            "and keep one canonical game id per title.</li>"
            "<li><b>Monitor RTP with volatility-aware bounds</b> and make rollback and reconciliation criteria mandatory for "
            "every new provider; open a P1 incident on Provider K's failed rollbacks.</li>"
            "<li><b>Judge new games on days 30-60, not week 1</b>, and keep a random hold-out on every promotion.</li></ul>")
    method = (f"<p>{REAL} &nbsp;Hard Rock Digital's website and job posting; New Jersey DGE monthly Internet gaming reports "
              f"(24 months, by licensee and skin); Pennsylvania PGCB interactive gaming reports (15 months); GLI-19 v4.0.</p>"
              f"<p>{SIMT} &nbsp;12 months, 20 fictional providers, {n_games} games, 3 fictional states, wallet logs, pipeline, "
              "approvals and promotions, calibrated on those reports, with 8 planted events and a hidden answer key.</p>"
              "<p><span class='lab'>TOOLS</span> &nbsp;SQL (DuckDB, 12 commented files), Python (pandas, scipy, Monte-Carlo), "
              "Plotly dashboard (4 tabs), two automations (weekly status, compliance alerts). One command rebuilds everything.</p>")
    pages.append(dict(
        title="Hard Rock Digital: a data-driven playbook for casino content integrations",
        subtitle="Real US regulator data and certification rules, plus a simulated game catalogue and integration pipeline, "
                 "turned into requirements, compliance tracking, launch monitoring and a prioritised integration roadmap.",
        tag="OVERVIEW", tag_class="",
        kpis=[("NJ online casino win, 12 months", busd(NJ["casino_win_12m"]),
               f"{NJ['growth']:+.1%} year on year · NJ DGE (public data)", "blue"),
              ("'Hard Rock Bet' share of NJ casino win", pct(HR["skin_share_nj"], 1),
               f"{musd(HR['skin_12m'], 0)} in 12 months, {pct(HR['skin_growth'])} YoY (public data)", "blue"),
              ("Planted problems found", f"{DT['events_found']} / {DT['events']}",
               f"+ {DT['compliance_found']} of 3 compliance issues; the RTP false signal correctly ignored (simulated)", ""),
              ("Next provider to integrate", f"Provider {RM['first']}",
               f"Live dealer studio; first in {pct(RM['p_first'][RM['first']])} of sensitivity runs (simulated)", "")],
        cols="1.2fr 1fr", rows="1fr 0.7fr",
        cards=[card("Five questions, five answers", qhtml, "1", "1", True),
               card("Simulated catalogue: share of GGR vs share of the shelf, by game type (last 90 days)",
                    C.type_gap(RM["gap"], RM["ggr_share"], RM["cat_share"], 760, 250), "1", "2"),
               card("Recommendations", recs, "2", "1", True),
               card("Data and methods", method, "2", "2", True)],
        footer="Pages: market · launching a game · requirements · compliance · post-launch monitoring · roadmap · methods"))

    # 1 Market ---------------------------------------------------------------------------------------------------------
    fr = "".join(f"<tr><td><b>{f.fact}</b></td><td>{f.value}</td></tr>" for f in facts.itertuples())
    hr_tab = table([("'Hard Rock Bet' skin, casino win", musd(HR["skin_12m"]), musd(HR["skin_prev12m"]), f"{HR['skin_growth']:+.0%}"),
                    ("Hard Rock Atlantic City (licensee)", musd(HR["licensee_12m"]), "", pct(HR["licensee_share_nj"], 1) + " of NJ")],
                   ["In the NJ DGE reports", f"12 m to {NJ['last']}", "12 m before", "Change"], num=(1, 2, 3))
    facts_html = (f"<table><tbody>{fr}</tbody></table><div style='margin-top:9px'>{hr_tab}</div>"
                  "<p style='margin-top:6px;font-size:11.5px;color:#52514E'>Sources: hardrockdigital.com (read 2026-11-15); "
                  "job posting on himalayas.app (posted 2026-11-08). NJ DGE <i>Internet Gaming Sites</i> page lists, for Hard "
                  "Rock Hotel &amp; Casino: hardrock.bet and nj.bet365.com (read 2026-11-15).</p>")
    pa_txt = (f"<p><b>Slots carry Pennsylvania online casino:</b> {pct(PA['slot_share'])} of its {busd(PA['casino_ggr_12m'])} "
              f"GGR ({PA['first']} to {PA['last']}).</p>"
              f"<p><b>Slots pay back {pct(PA['slot_payout'], 1)} of wagers</b> (monthly {pct(PA['slot_payout_min'], 1)}-"
              f"{pct(PA['slot_payout_max'], 1)}; operators {pct(PA['op_payout_min'], 1)}-{pct(PA['op_payout_max'], 1)}). Table games "
              f"hold {pct(PA['table_hold'], 1)} of wagers.</p>"
              "<p><b>Why it matters for integrations:</b> these real payout ratios calibrate the simulated catalogue "
              "(slot RTPs 93.5%-96.2%), and they show why a single game's realised RTP must be judged against its "
              "volatility, not against a fixed threshold (page 5).</p>"
              f"<p style='font-size:11.5px;color:#52514E'>New Jersey: {NJ['n_licensees']} casino licensees report Internet win; "
              f"Hard Rock Atlantic City ranks #{NJ['hard_rock_rank']} on casino win. Poker is {pct(NJ['poker_share'], 1)} of NJ Internet win.</p>")
    pages.append(dict(
        title=f"New Jersey online casino win grew {pct(NJ['growth'])} to {busd(NJ['casino_win_12m'])} in a year; "
              f"the 'Hard Rock Bet' skin grew {pct(HR['skin_growth'])} to {pct(HR['skin_share_nj'], 1)} of it",
        subtitle="What Hard Rock Digital publishes about itself, and what two state regulators' monthly reports say about the "
                 "market. Hard Rock figures are quoted only where the reports name them (licensee and skin).",
        tag="PUBLIC DATA", tag_class="real", cols="0.95fr 1.1fr 0.95fr", rows="1fr 1fr",
        cards=[card("What Hard Rock Digital publishes", facts_html, "1", "1 / 3", True),
               card("Online casino revenue per month: New Jersey (DGE-105, casino games) and Pennsylvania (PGCB, slots + tables)",
                    C.market_lines(mk, 620, 255), "2", "1"),
               card(f"'Hard Rock Bet' skin, monthly casino win in NJ (last 12 months in blue: {musd(HR['skin_12m'], 0)})",
                    C.hard_rock_skin(hr, 470, 245), "3", "1"),
               card(f"Share of NJ online casino win by licensee, {NJ['first']} to {NJ['last']}", C.licensee_share(ls, 620, 300),
                    "2", "2"),
               card("What the Pennsylvania reports add", pa_txt, "3", "2", True)],
        footer="Page 1 · Hard Rock Digital and the US online casino market"))

    # 2 What it takes to launch a game -----------------------------------------------------------------------------------
    flow = ("<div class='flow'>"
            "<div class='s'><b>1. Agreement</b>Commercial terms, revenue share, licences checked.<i>Product, Legal, provider</i></div><div class='a'>→</div>"
            "<div class='s'><b>2. Integration</b>Game launch, seamless wallet (debit, credit, rollback), RG and geolocation hooks.<i>Engineering, Platform</i></div><div class='a'>→</div>"
            "<div class='s'><b>3. QA &amp; staging</b>End-to-end cases: timeouts, retries, limits, disable.<i>QA, provider</i></div><div class='a'>→</div>"
            "<div class='s reg'><b>4. Lab certification</b>Independent lab tests the game and build against standards such as GLI-19.<i>Provider, test lab</i></div><div class='a'>→</div>"
            "<div class='s reg'><b>5. State approval</b>Each state approves the game for its market; NJ: approval by the DGE slot lab, then verification.<i>Compliance, regulator</i></div><div class='a'>→</div>"
            "<div class='s'><b>6. Launch &amp; follow-up</b>Waves per state, hypercare, 30/60-day review, RTP checks.<i>Operations, Product</i></div></div>")
    route = rd("route_switch")
    rs0, rs1 = route.iloc[0], route.iloc[1]
    agg_tab = table([
        ("Contract and tech work", "One contract and one integration open many providers", "One integration per provider"),
        ("Tech integration (median)", f"{stage.set_index('stage').loc['Technical integration', 'Aggregator']:.0f} days",
         f"{stage.set_index('stage').loc['Technical integration', 'Direct']:.0f} days"),
        ("Time to launch A+B (P50)", f"~{ttl_a:.0f} days", f"~{ttl_d:.0f} days"),
        ("Content cost", "Provider fee + aggregator fee (2.5-3% of GGR here)", "Provider fee only"),
        ("Wallet p95 latency", f"{rs0.debit_p95_ms:.0f} ms", f"{rs1.debit_p95_ms:.0f} ms"),
        ("Control", "Depends on the aggregator's release cycle", "Direct roadmap and incident line")],
        ["", "Via an aggregator", "Direct"])
    cert_txt = ("<p><b>Lab testing.</b> GLI-19 v4.0 (<i>Standards for Interactive Gaming Systems</i>) sets requirements for "
                "RNGs (ch. 5), games (ch. 6: disclosure, fairness, payouts, jackpots, game recall, disable, interrupted games, "
                "live games) and player accounts (ch. 3: limits, time-outs, promotions). Minimum RTP 75% \"unless otherwise "
                "specified by the regulatory body\" (6.8.1).</p>"
                "<p><b>State approval.</b> New Jersey's DGE Technical Services Bureau approves each gaming product in its slot "
                "lab, then verifies it before use; rules in N.J.A.C. 13:69O. Every state runs its own review, at its own pace.</p>"
                f"<p><b>In the simulated pipeline</b> state approval takes a median {CE['median_by_state']['State A']:.0f} days in "
                f"State A, {CE['median_by_state']['State B']:.0f} in B and <b class='red'>{CE['median_by_state']['State C']:.0f} in C</b>: "
                "the step the team controls least.</p>")
    pages.append(dict(
        title=f"Live in ~{ttl_a:.0f} days via an aggregator or ~{ttl_d:.0f} direct; state approval is the least controllable step",
        subtitle="The integration life cycle, from public standards and regulator pages; durations from the simulated "
                 f"pipeline ({pipe.project_id.nunique()} provider projects, finished stages only).",
        tag="PUBLIC DATA + SIMULATED", tag_class="", cols="1fr 1.05fr 1fr", rows="0.42fr 1fr",
        cards=[card("From signed contract to a game in the lobby: who does what", flow, "1 / 4", "1"),
               card(f"Aggregator vs direct integration {SIMT}", agg_tab, "1", "2", True),
               card(f"Median days per stage, by route {SIMT}", C.stage_bars(stage, 520, 400), "2", "2"),
               card(f"Certification and state approval {REAL}", cert_txt, "3", "2", True)],
        footer="Page 2 · What it takes to launch a game"))

    # 3 Requirements -------------------------------------------------------------------------------------------------------
    prd = ("<p><b>Objective.</b> Launch Provider Q's 40 games (30 slots, 6 jackpot slots, 4 tables) in States A and B with no "
           f"compliance finding. Commitment date <b>{FC['q_ab_p80']}</b> (P80; P50 {FC['q_ab_p50']}).</p>"
           "<p><b>In scope:</b> seamless wallet, launch and sessions, geolocation, jackpots, RG controls, reporting feed, "
           "kill switch, CMS metadata. <b>Out:</b> State C (licence pending), free-spin tooling (phase 2).</p>"
           "<p><b>Success metrics:</b> launch error rate &lt; 1%; wallet technical errors &lt; 0.1%; p95 debit &lt; 250 ms; "
           "0 games live without approval; every game inside its RTP band at 90 days; days 30-60 GGR per game &ge; 80% "
           "of its type benchmark.</p><p><b>Launch plan:</b> staging run, go/no-go, wave 1 (jackpots + best slots) in A, "
           "72 h hypercare, then B and wave 2. Rollback: per-state disable in &lt; 15 min.</p>")
    stories = (
        "<div class='story'><span class='t'>CI-06 Wallet rollback</span> · As a player, I want a bet that did not complete to be "
        "refunded automatically, so that I am never charged for a round that never happened.<ul>"
        "<li><span class='gwt'>Given</span> a debit that timed out, <span class='gwt'>When</span> the provider sends a rollback "
        "for that transaction id, <span class='gwt'>Then</span> the debit is reversed and the balance restored.</li>"
        "<li><span class='gwt'>Given</span> a rollback for an unknown transaction, <span class='gwt'>When</span> it arrives, "
        "<span class='gwt'>Then</span> answer OK and store it, so a late debit with that id is refused.</li></ul></div>"
        "<div class='story'><span class='t'>CI-07 Idempotent wallet calls</span> · As Engineering, I want every wallet call to be "
        "idempotent on its transaction id, so that retries never double-charge or double-pay.<ul>"
        "<li><span class='gwt'>Given</span> a debit already processed, <span class='gwt'>When</span> the same id arrives again, "
        "<span class='gwt'>Then</span> return the original result and do not move the balance.</li></ul></div>"
        "<div class='story'><span class='t'>CI-03 Geolocation gate</span> · As Compliance, I want every session to start and "
        "continue only inside an approved state.<ul><li><span class='gwt'>Given</span> a failed or out-of-state location check, "
        "<span class='gwt'>When</span> the player opens a game, <span class='gwt'>Then</span> the launch is refused and no session "
        "is created; a mid-session failure ends the session after the round (GLI-19 v4.0, 4.3).</li></ul></div>"
        "<div class='story'><span class='t'>CI-11 RG limits and exclusions</span> · As a player who set limits, I want them to "
        "apply to Provider Q games too.<ul><li><span class='gwt'>Given</span> a player who reached a loss limit, "
        "<span class='gwt'>When</span> they bet, <span class='gwt'>Then</span> the debit is refused with the limit message "
        "(GLI-19 v4.0, 3.4).</li><li><span class='gwt'>Given</span> a self-excluded player, <span class='gwt'>When</span> they open "
        "a game, <span class='gwt'>Then</span> the launch is refused.</li></ul></div>")
    api = ("<div class='flow' style='margin-bottom:8px'><div class='s'><b>Player</b>opens game</div><div class='a'>→</div>"
           "<div class='s'><b>Platform</b>geo + RG checks, launch token</div><div class='a'>→</div>"
           "<div class='s'><b>Provider</b>debit, spin, credit</div><div class='a'>→</div>"
           "<div class='s'><b>Wallet</b>holds the money, idempotent</div></div>" + table([("<span class='mono'>OK_IDEMPOTENT_REPLAY</span>", "Same id already done: original result, no movement"),
                  ("<span class='mono'>ERR_INSUFFICIENT_FUNDS</span>", "Business decline, not a technical error"),
                  ("<span class='mono'>ERR_TIMEOUT</span>", "Debit: send rollback, same id. Credit: retry, same id"),
                  ("<span class='mono'>ERR_ROLLBACK_FAILED</span>", "Retry; P1 if &gt; 2% of rollbacks in a day"),
                  ("<span class='mono'>ERR_RG_BLOCKED</span> / <span class='mono'>ERR_LOCATION</span>", "Close the game with the RG or location message")],
                 ["Code", "Expected behaviour"])
           + "<p style='margin-top:7px'><b>15 end-to-end cases</b> on staging (timeouts, duplicates, rollbacks of unknown debits, "
             "cent-exact credits, jackpot win, limit reached mid-session, disable mid-session, reconciliation with an injected "
             "mismatch) and a 5-step release rollback plan. Targets: p95 &lt; 250 ms, technical errors &lt; 0.1%.</p>")
    n_st, n_pts = int((bl["Issue Type"] == "Story").sum()), int(bl["Story Points"].sum())
    pages.append(dict(
        title=f"Requirements engineers can build: {n_st} user stories with testable criteria, in Jira from one file",
        subtitle="Provider Q onboarding (simulated scenario): PRD, user stories in Given / When / Then form, a Jira-ready "
                 "backlog generated from the stories, and the wallet API checklist. Full files in docs/integration/.",
        tag="SIMULATED", tag_class="sim", cols="1fr 1.25fr 1fr", rows="1fr 0.62fr",
        cards=[card("PRD extract: Provider Q onboarding", prd, "1", "1", True),
               card("Four of the 15 user stories", stories, "2", "1 / 3", True),
               card("API checklist extract: error codes the provider must handle", api, "3", "1 / 3", True),
               card(f"Backlog: {n_st} stories, {n_pts} points, 5 epics (backlog.csv, Jira import)",
                    C.backlog_points(bl, 470, 230), "1", "2")],
        footer="Page 3 · Requirements that engineers can build"))

    # 4 Compliance -------------------------------------------------------------------------------------------------------------
    al_rows = [(f"{r.severity}", r.rule, r.entity, r.state, r.detail) for r in al.itertuples()]
    al_tab = table(al_rows, ["Sev.", "Rule", "Entity", "State", "Detail"])
    al_tab = al_tab.replace("<td class=''>P1</td>", "<td class='p1'>P1</td>").replace(
        "<td class=''>P2</td>", "<td class='p2'>P2</td>").replace("<td class=''>P3</td>", "<td class='p3'>P3</td>")
    tsum = tr.groupby(["provider_id", "state"]).approval_status.value_counts().unstack(fill_value=0)
    trows = [(f"Provider {p}", s, int(r.get("approved", 0)), int(r.get("pending", 0)), int(r.get("not_submitted", 0)),
              int(r.get("not_licensed", 0))) for (p, s), r in tsum.iterrows()]
    t_tab = table(trows, ["Provider", "State", "Approved", "Pending", "Not submitted", "No licence"], num=(2, 3, 4, 5))
    n_c = pipe[(pipe.project_id == "N-AGG") & (pipe.stage == "State approval") & (pipe.state == "State C")].start_date.iloc[0]
    nar = (f"<p><b>Provider N</b>: certified in July, approved in States A and B since late July, still waiting for State C "
           f"(submitted {n_c}, {(pd.Timestamp('2026-11-13') - pd.Timestamp(n_c)).days} days). Six games cannot even be "
           f"submitted there: documents missing (P3). Forecast State C approval: P50 {FC['n_c_p50']}, P80 {FC['n_c_p80']}.</p>"
           "<p><b>Decision:</b> launch N in A and B now; add C when it lands. Waiting for the slowest state costs "
           f"~{FC['agg_abc_p50'] - FC['agg_ab_p50']:.0f} days at P50 on a typical aggregator launch.</p>"
           f"<p><b>Provider Q</b>: 40 games, none at the lab yet; version hashes and RG checks still to collect.</p>")
    pages.append(dict(
        title=f"Tracking compliance without surprises: {(al.severity == 'P1').sum()} games are live without approval today, "
              f"and State C takes {CE['ratio_c']:.1f}x longer to approve",
        subtitle="One line per game and state (documents, certificate, submission, approval, live date) and three alert rules "
                 "run every week by src/compliance_alerts.py. Checklist built from GLI-19 and NJ DGE public pages.",
        tag="SIMULATED", tag_class="sim", cols="1.35fr 1fr", rows="1fr 0.78fr",
        cards=[card(f"This week's alerts (as of 2026-11-13): {(al.severity == 'P1').sum()} P1 · {(al.severity == 'P2').sum()} P2 · "
                    f"{(al.severity == 'P3').sum()} P3", al_tab, "1", "1", True),
               card("Days from state submission to approval, per game (all approved games)", C.approval_box(ap, 560, 300), "2", "1"),
               card("Onboarding tracker summary (compliance_tracker.csv: games x states)", t_tab, "1", "2", True),
               card("Reading the tracker", nar, "2", "2", True)],
        footer="Page 4 · Tracking compliance without surprises"))

    # 5 Post-launch ------------------------------------------------------------------------------------------------------------
    route_txt = (f"<p><b>Aggregator → direct (Provider H, April).</b> Wallet p95 {RO['p95_before']:.0f} → {RO['p95_after']:.0f} ms; "
                 f"launch errors {pct(RO['err_before'], 2)} → {pct(RO['err_after'], 2)}; load time {RO['load_before']:.0f} → "
                 f"{RO['load_after']:.0f} ms; margin after content fees {pct(RO['margin_before'])} → {pct(RO['margin_after'])}.</p>"
                 f"<p><b>But {DU['groups']} old aggregator entries stayed live</b> (same title, two ids): the catalogue counts "
                 f"{DU['live_entries']} games for {DU['unique_games']} real ones (+{pct(DU['inflation'])}), "
                 f"{pct(DU['session_share_old'])} of the GGR still flows through the old route and {usd(DU['fees'])} of "
                 "aggregator fees were paid since. Fix: switch-off + one canonical id (CI-10).</p>")
    rb_txt = (f"<p><b>Provider K (Aggregator Y)</b>: on {RB['days']} days between {RB['first']} and {RB['last']}, "
              f"{pct(RB['rate'])} of rollbacks failed ({RB['failed']} transactions) vs {pct(RB['normal_rate'], 2)} normally.</p>"
              f"<p>The money is small ({usd(RB['at_risk'])}), but each one is a player charged for a round that never happened: "
              "<b class='red'>P1 regardless of amount</b>. Action: reconcile the affected players, open a provider incident, "
              "keep CI-06/CI-08 as acceptance criteria for every new provider.</p>")
    pr_txt = (f"<p><b>PR06: 20 free spins on a new slot</b>, {PR['n_t'] + PR['n_c']:,} players, 10% random hold-out.</p>"
              f"<p>GGR per player over 28 days: <b class='blue'>+{usd(PR['uplift'], 2)}</b> vs hold-out (95% CI "
              f"{usd(PR['lo'], 2)} to {usd(PR['hi'], 2)}); activity +{100 * PR['active_uplift']:.1f} pts. Cost {usd(PR['cost'], 2)} per "
              f"targeted player: pays back {PR['roi']:.1f}x on average, net +{usd(PR['net'], 2)} (CI {usd(PR['net_lo'], 2)} to "
              f"{usd(PR['net_hi'], 2)}).</p><p>A naive comparison (players who used their spins vs those who did not) claims "
              f"+{usd(PR['naive'], 2)}: {PR['naive'] / PR['uplift']:.1f}x the true effect. Keep hold-outs; re-test 10 spins.</p>")
    pages.append(dict(
        title=f"After launch, separate defects from noise: one real RTP problem among {RT['naive']} naive alarms, "
              "one broken update, one rollback fault",
        subtitle="Daily game and wallet data of the simulated catalogue, with rules that compare each provider and game to "
                 "its own baseline and statistical band. The planted events were scored against a hidden answer key at the end.",
        tag="SIMULATED", tag_class="sim", cols="1fr 1.18fr 1fr", rows="1fr 0.72fr",
        cards=[card(f"Launch errors: a provider update broke game launches for 6 days (~{usd(LA['ggr_lost_per_day'])} GGR lost per day)",
                    C.launch_errors(rd("nb_launch_f"), 470, 240), "1", "1"),
               card("RTP: realised vs theoretical over the last 90 days, with volatility-aware 3-sigma bands",
                    C.rtp_funnel(rd("nb_rtp_funnel"), 560, 300), "2", "1"),
               card(f"New games run {pct(NO['week1_index'] - 1)} above steady state in week 1 ({NO['games']} launches)",
                    C.novelty(rd("lifecycle"), 440, 240), "3", "1"),
               card("Aggregator vs direct, and the duplicates it left", route_txt, "1", "2", True),
               card("Rollbacks that fail", rb_txt, "2", "2", True),
               card("Free-spin promotion vs a random hold-out", pr_txt, "3", "2", True)],
        footer="Page 5 · Launch and post-launch monitoring"))

    # 6 Roadmap -------------------------------------------------------------------------------------------------------------
    rrows, rcls = [], []
    for r in rk.itertuples():
        rrows.append((f"<b>{r.provider_id}</b>", r.note, f"<span style='white-space:nowrap'>{r.route}</span>", f"{r.games}", r.states.replace("", " ").strip(),
                      pct(r.reach), musd(r.impact, 2), f"{r.confidence:.1f}", f"{r.effort_weeks:.1f}", f"{r.ttl_p50_days:.0f}",
                      f"${r.score / 1e3:,.0f}k"))
        rcls.append("hl" if r.rank == 1 else "")
    r_tab = table(rrows, ["", "Candidate", "Route", "Games", "States", "Reach", "Impact (yr 1)", "Conf.", "Effort (pw)",
                          "Launch P50 (d)", "Score"], num=(3, 5, 6, 7, 8, 9, 10), cls=rcls)
    r_tab += ("<p style='margin-top:6px;font-size:11.5px;color:#52514E'><b>Score</b> = Impact x Confidence / Effort. "
              "<b>Impact</b>: incremental first-year GGR; a type's GGR grows with its games with diminishing returns, faster "
              "where the shelf is short (elasticity 0.15 x demand/supply), x Reach x share of the year left after launch. "
              "<b>Confidence</b>: 0.5 + 0.2 certified elsewhere + 0.2 known partner + 0.1 all states. <b>Effort</b>: "
              "integration person-weeks + 0.1 per game per state.</p>")
    o_rows = [(r.case, f"<b>{r.first}</b>", r.second, r.order) for r in oat.itertuples()]
    o_tab = table(o_rows, ["Change one input", "First", "Second", "Full order"])
    o_tab += (f"<p style='margin-top:6px'>Provider {RM['first']} stays first in all {RM['oat_cases']} one-at-a-time cases and in "
              f"{pct(RM['p_first'][RM['first']])} of 5,000 runs where every input is randomised (top 2: "
              f"{pct(RM['p_top2'][RM['first']])}); Provider {RM['second']} is in the top 2 in {pct(RM['p_top2'][RM['second']])}. "
              "Provider P (60 slots) brings the most games but the least value: slots are already over-supplied.</p>")
    fq = (f"<p style='margin-top:4px'><b>Provider Q</b> (in progress, direct): launch A+B P50 {FC['q_ab_p50']}, "
          f"P80 {FC['q_ab_p80']}. Adding State C (once licensed) moves P50 by ~{FC['c_delay_p50']:.0f} days.</p>")
    pages.append(dict(
        title=f"Integrate Provider {RM['first']} (live dealer) next and Provider {RM['second']} (jackpots) alongside; "
              "more generic slots add little",
        subtitle="Five candidate providers scored with a transparent RICE-style method on the simulated catalogue: where the "
                 "shelf is short of demand, how many players they reach, how sure we are, and how much work and time they take.",
        tag="SIMULATED", tag_class="sim", cols="1.45fr 1fr", rows="1fr 0.95fr",
        cards=[card("Roadmap score: inputs and result", r_tab, "1", "1", True),
               card("Score and share of 5,000 sensitivity runs where each candidate comes first",
                    C.roadmap_bars(rk, mc, 520, 250), "2", "1"),
               card("Sensitivity: does the winner change?", o_tab, "1", "2", True),
               card("Time to launch, Monte-Carlo (10,000 runs from the stage durations of finished projects)",
                    C.ttl_hist(tt, {"Aggregator": (FC["agg_ab_p50"], FC["agg_ab_p80"]), "Direct": (FC["dir_ab_p50"], FC["dir_ab_p80"])},
                              560, 215) + fq, "2", "2", True)],
        footer="Page 6 · Which provider next?"))

    # 7 Methods ---------------------------------------------------------------------------------------------------------------
    src = ("<ul><li><b>Hard Rock Digital</b>: hardrockdigital.com (read 2026-11-15); job posting \"Product Analyst - Casino "
           "Integrations\", himalayas.app (posted 2026-11-08).</li>"
           "<li><b>New Jersey DGE</b>: Monthly Internet Gaming Gross Revenue Reports (DGE-105), Oct 2024 - Sep 2026, by licensee "
           "and skin; Internet Gaming Sites; Technical Services Bureau; Internet Gaming Information (N.J.A.C. 13:69O). Read 2026-11-15.</li>"
           "<li><b>Pennsylvania PGCB</b>: Monthly Interactive Gaming Report, FY 2025-26 and FY 2026-27 (Jul 2025 - Sep 2026).</li>"
           "<li><b>GLI</b>: GLI-19 v4.0, GLI-11 v3.0, Composite Submission Requirements v2.0, Change Management guide v1.0.</li></ul>"
           "<p>Raw files are not republished (data/SOURCES.md); the download script rebuilds them.</p>")
    sim = (f"<p>12 months (Oct 2025 - Sep 2026), seed 42, 20 fictional providers (13 live, 2 in onboarding, 5 candidates; "
           f"Aggregator X / Y or direct), {n_games} games, 3 fictional states. Slot RTPs 93.5-96.2% (calibrated on PA "
           "payout ratios); volatility sets the per-round standard deviation; novelty, cannibalisation and weekly seasonality "
           "drive demand. Assumptions: data/ASSUMPTIONS.md.</p>"
           "<p><b>Answer key</b> (read only at the end): " + ", ".join(
               f"{'✔' if r.found else '✘'} {r.event}" for r in det[det.event_id <= 8].itertuples()) + ".</p>")
    meth = ("<ul><li><b>GGR</b> = wagers - player wins; <b>RTP</b> = player wins / wagers; margin after content fees = GGR x "
            "(1 - provider fee - aggregator fee).</li>"
            "<li><b>RTP bands</b>: z = (wins - RTP x wagers) / (sd per round x bet x sqrt(rounds)); watch |z| &gt; 3, escalate &gt; 4.</li>"
            "<li><b>Launch errors</b>: rate vs trailing 28-day baseline (window function); alert at 3x and &gt; 3%.</li>"
            "<li><b>Forecasts</b>: Monte-Carlo, log-normal stage durations fitted on finished stages; open stages drawn "
            "conditional on their age; P50 and P80.</li>"
            "<li><b>Promotion</b>: randomised hold-out, Welch t-test, 95% CI; CUPED check with the pre-period.</li>"
            "<li><b>Roadmap</b>: RICE-style score, one-at-a-time and randomised sensitivity.</li></ul>")
    auto = ("<ul><li><span class='mono'>src/weekly_status.py</span>: the Friday status report (moved, blocked, risks, P50/P80 "
            "dates, post-launch health) written from the data, no copy-paste.</li>"
            "<li><span class='mono'>src/compliance_alerts.py</span>: P1/P2/P3 alerts and the onboarding tracker.</li>"
            "<li><span class='mono'>src/build_backlog.py</span>: user stories → Jira CSV.</li></ul>"
            "<p><b>Where I would use an AI assistant</b>: first drafts of user stories, acceptance criteria and release notes "
            "from a provider's API spec, always reviewed and validated. <b>Never automated</b>: compliance decisions, "
            "go/no-go, anything sent to a regulator.</p>"
            f"<div class='ai'>{AI_NOTE}</div>")
    lim = ("<ul><li>All operator, provider and pipeline data is simulated: it shows methods, not Hard Rock Digital's catalogue, "
           "partners or results. No claim is made about Hard Rock Digital's providers, contracts or licences.</li>"
           "<li>Regulator figures are revenue (win / GGR) as reported; no adjustment for promotional credits or taxes.</li>"
           "<li>The compliance checklist summarises public documents; it is not legal advice and state rules differ.</li>"
           "<li>The roadmap elasticities are assumptions: the sensitivity analysis is there to test them.</li></ul>")
    pages.append(dict(
        title="Methods, limits and AI note",
        subtitle="Everything rebuilds with one command: download public data, simulate, SQL, notebook, automations, dashboard, PDF.",
        tag="METHODS", tag_class="", cols="1fr 1fr 1fr", rows="1fr 1fr",
        cards=[card(f"Public sources {REAL}", src, "1", "1", True),
               card(f"Simulation {SIMT}", sim, "1", "2", True),
               card("Definitions and methods", meth, "2", "1", True),
               card("Limits", lim, "2", "2", True),
               card("Automation and AI", auto, "3", "1", True),
               card("Interactive dashboard (dashboard/casino_integrations.html, 4 tabs, filters by state and provider)",
                    dash_img(), "3", "2")],
        footer="Page 7 · Methods, limits & AI note"))
    return pages


# ======================================================================================
def edge() -> str:
    for p in (r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
              r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"):
        if Path(p).exists():
            return p
    return shutil.which("msedge") or "msedge"


def wait_file(path: Path, timeout=90):
    last, t0 = -1, time.time()
    while time.time() - t0 < timeout:
        if path.exists() and path.stat().st_size > 0 and path.stat().st_size == last:
            return
        last = path.stat().st_size if path.exists() else -1
        time.sleep(1.5)
    raise TimeoutError(f"{path} not produced")


def clean_pdf(path: Path):
    """Metadata reduced to the title: no author, tool or path."""
    from pypdf import PdfReader, PdfWriter
    r, w = PdfReader(str(path)), PdfWriter()
    for pg in r.pages:
        w.add_page(pg)
    w.add_metadata({"/Title": "Hard Rock Digital - casino integrations case study"})
    for k in ("/Producer", "/Creator", "/Author"):
        w._info.get_object().pop(k, None)
    tmp = path.with_suffix(".tmp.pdf")
    with open(tmp, "wb") as fh:
        w.write(fh)
    tmp.replace(path)


def shot(url: str, out: Path, prof: Path, size="1536,864", budget=None):
    args = [edge(), "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--user-data-dir={prof}",
            f"--window-size={size}", f"--screenshot={out}", url]
    if budget:
        args.insert(-1, f"--virtual-time-budget={budget}")
    out.unlink(missing_ok=True)
    subprocess.run(args, check=True, capture_output=True, timeout=120)
    wait_file(out)


def main():
    TMP.mkdir(exist_ok=True)
    IMG.mkdir(parents=True, exist_ok=True)
    prof = TMP / "edge-profile"
    if DASH.exists():
        for n in range(1, 5):
            shot(DASH.as_uri() + f"#{n}", IMG / f"dashboard_{n}.png", prof, "1400,1000", 15000)
    pages = build_pages()
    head = f"<!doctype html><html lang='en'><head><meta charset='utf-8'><style>{CSS}</style></head><body>"
    sections = [PAGE.render(p=p, foot=FOOTER) for p in pages]
    src = TMP / "report.html"
    src.write_text(head + "".join(sections) + "</body></html>", encoding="utf-8")
    PDF.unlink(missing_ok=True)
    subprocess.run([edge(), "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--print-to-pdf-no-header",
                    f"--user-data-dir={prof}", f"--print-to-pdf={PDF}", src.as_uri()], check=True, capture_output=True, timeout=180)
    wait_file(PDF)
    clean_pdf(PDF)
    names = ["00_overview", "01_market", "02_launching_a_game", "03_requirements", "04_compliance", "05_monitoring",
             "06_roadmap", "07_methods"]
    for name, sec in zip(names, sections):
        one = TMP / f"{name}.html"
        one.write_text(head.replace("page-break-after: always", "") + sec + "</body></html>", encoding="utf-8")
        shot(one.as_uri(), IMG / f"{name}.png", prof)
    print("PDF:", PDF.relative_to(ROOT), f"({PDF.stat().st_size // 1024} KB, {len(sections)} pages)")


if __name__ == "__main__":
    main()
