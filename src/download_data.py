"""Download the public regulator files once (politely) and derive the small PUBLIC DATA tables used in the study.

Sources (details and reuse notes in data/SOURCES.md):
- New Jersey Division of Gaming Enforcement (DGE): Monthly Internet Gaming Gross Revenue Reports (form DGE-105),
  Oct 2024 - Sep 2026, one PDF per month with one page per casino licensee and one "skin detail" page.
- Pennsylvania Gaming Control Board (PGCB): Monthly Interactive Gaming Report, fiscal years 2025-26 and 2026-27 (xlsx).
- Gaming Laboratories International (GLI): GLI-19 v4.0, GLI-11 v3.0, composite submission requirements, change
  management guide (reference documents for the certification checklist; not redistributed).
- Hard Rock Digital home page (company facts, read 2026-11-15) and the job posting (posted 2026-11-08).

Raw files stay in data/raw (git-ignored). Run: python src/download_data.py
"""
from __future__ import annotations

import re
import time
import urllib.request

import pandas as pd

from config import PUBLIC, RAW, UA

NJ_BASE = "https://www.nj.gov/oag/ge/docs/Financials/IGRTaxReturns/{y}/{m}{y}.pdf"
NJ_MONTHS = pd.period_range("2024-10", "2026-09", freq="M")
PA_FILES = {
    "FY25-26_ig.xlsx": "https://gamingcontrolboard.pa.gov/sites/default/files/2026-07/"
                       "FY25-26%20Monthly%20Interactive%20Gaming%20Report%20Summary.xlsx",
    "FY26-27_ig.xlsx": "https://gamingcontrolboard.pa.gov/sites/default/files/2026-10/"
                       "FY26-27%20Monthly%20Interactive%20Gaming%20Report%20Summary.xlsx",
}
GLI_FILES = [
    "https://gaminglabs.com/wp-content/uploads/2026/11/GLI-19-v4.0-Standards-for-Interactive-Gaming-Systems.pdf",
    "https://gaminglabs.com/wp-content/uploads/2018/09/GLI-11-Gaming-Devices-V3-0.pdf",
    "https://gaminglabs.com/wp-content/uploads/2022/01/GLI-Composite-Submission-Requirements-V2.0.pdf",
    "https://gaminglabs.com/wp-content/uploads/2020/05/GLI-Change-Management-Program-Guide-v1.0.pdf",
]

# Facts published by the company (home page, read 2026-11-15) and by the job posting (posted 2026-11-08).
HOME = "https://www.hardrockdigital.com/"
JOB = "https://himalayas.app/companies/hard-rock-digital/jobs/product-analyst-casino-integrations"
FACTS = [
    ("Products", "Sportsbook (Hard Rock Bet Sportsbook), online casino (Hard Rock Bet Casino: slots, table games, live "
     "entertainment) and online gaming (Hard Rock Games: six social gaming apps)", HOME),
    ("Ownership context", "The Seminole Tribe of Florida acquired the Hard Rock brand in 2007; Hard Rock Digital is the "
     "exclusive Hard Rock International and Seminole Gaming vehicle for interactive gaming and sports betting worldwide", HOME),
    ("Locations named on the site", "Atlantic City NJ, Hollywood FL, Austin TX", HOME),
    ("Culture", "Startup culture, work-at-home options", HOME),
    ("Ambition (job posting)", "Become the best online sportsbook, online casino and social casino company", JOB),
    ("Role (job posting)", "Product Analyst in the Casino Product organisation, supporting the Integrations team that "
     "manages third-party game providers", JOB),
]


def fetch(url: str, dest):
    if dest.exists() and dest.stat().st_size > 0:
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=90) as r:
        dest.write_bytes(r.read())
    time.sleep(3)                                   # one file every few seconds: low frequency


def download():
    for p in NJ_MONTHS:
        fetch(NJ_BASE.format(y=p.year, m=p.strftime("%B")), RAW / "nj" / f"{p.strftime('%B')}{p.year}.pdf")
    for name, url in PA_FILES.items():
        fetch(url, RAW / "pa" / name)
    for url in GLI_FILES:
        try:
            fetch(url, RAW / "gli" / url.rsplit("/", 1)[1])
        except Exception as e:                      # reference only: the study runs without them
            print("GLI download skipped:", e)


# ------------------------------------------------------------------------------------------- New Jersey
def _num(tok: str) -> float:
    if tok in ("-", ""):
        return 0.0
    v = float(re.sub(r"[^\d.]", "", tok))
    return -v if tok.startswith(("(", "-")) else v


def _values(line: str) -> list[float]:
    """Values of a DGE-105 line. The PDF text layer splits numbers after their first digit ('4 ,818,540'),
    so a lone digit followed by a digit or a comma is glued back to the next token."""
    s = re.sub(r"^\d+\s+", "", line)                 # drop the form's line number
    s = re.sub(r"\$\s*", "", s)
    s = re.sub(r"\(\s*", "(", s)
    s = re.sub(r"(?<![\d,.])(\d) (?=[\d,])", r"\1", s)
    return [_num(t) for t in s.split() if re.fullmatch(r"\(?-?[\d,]+(\.\d+)?\)?|-", t)]


def short_nj(n: str) -> str:
    n = n.upper()
    for key, lab in (("BALLY", "Bally's AC"), ("BORGATA", "Borgata"), ("GOLDEN NUGGET", "Golden Nugget AC"),
                     ("HARD ROCK", "Hard Rock Atlantic City"), ("HARRAH", "Caesars Interactive NJ (Harrah's)"),
                     ("TROPICANA", "Caesars Interactive NJ (Tropicana)"), ("OCEAN", "Ocean Casino Resort"),
                     ("RESORTS DIGITAL", "Resorts Digital"), ("RESORTS", "Resorts Casino Hotel")):
        if key in n:
            return lab
    return n.title()


def nj():
    import pdfplumber
    lic, skins = [], []
    for p in NJ_MONTHS:
        with pdfplumber.open(RAW / "nj" / f"{p.strftime('%B')}{p.year}.pdf") as pdf:
            for page in pdf.pages:
                lines = (page.extract_text(x_tolerance=6) or "").splitlines()
                if len(lines) < 4:
                    continue
                name = lines[0].strip() + (" " + lines[1].strip() if lines[1].startswith("(AFFILIATE") else "")
                get = lambda k: next((l for l in lines if l.startswith(k)), None)  # noqa: E731
                if not any("SKIN DETAIL" in l for l in lines[:4]):
                    p2p, other, tot = (_values(get(k))[-1] for k in ("1 Peer-to-Peer", "2 Other Authorized", "3 Total"))
                    lic.append((str(p), short_nj(name), other, p2p, tot))
                elif "HARD ROCK" in name.upper():
                    head = next(l for l in lines if l.endswith("Total") and "Win" not in l)
                    vals = _values(get("2 Other Authorized"))
                    skins.append((str(p), head.replace(" Total", ""), vals[0], vals[-1]))
    d = pd.DataFrame(lic, columns=["month", "licensee", "casino_win_usd", "poker_win_usd", "total_win_usd"])
    d.to_csv(PUBLIC / "nj_internet_gaming_by_licensee.csv", index=False)
    s = pd.DataFrame(skins, columns=["month", "skins_listed", "hard_rock_bet_casino_win_usd", "licensee_casino_win_usd"])
    assert s.skins_listed.str.startswith("Hard Rock Bet").all(), "skin order changed: check the Hard Rock page"
    s.insert(1, "licensee", "Hard Rock Atlantic City")
    s.to_csv(PUBLIC / "nj_hard_rock_skin.csv", index=False)
    return d, s


# ------------------------------------------------------------------------------------------- Pennsylvania
def short_pa(n: str) -> str:
    return {"BALLY'S PENNSYLVANIA, LLC": "Bally's Pennsylvania", "LIVE! PHILADELPHIA": "Live! Philadelphia",
            "THE RIVERS-PHILADELPHIA": "Rivers Philadelphia"}.get(n, n.title())


def pa():
    rows = []
    for name in PA_FILES:
        raw = pd.read_excel(RAW / "pa" / name, header=None)
        months = {c: pd.to_datetime(v.strip()).strftime("%Y-%m") for c, v in raw.iloc[3].items()
                  if isinstance(v, str) and re.match(r"[A-Z][a-z]+ \d{4}$", v.strip())}
        op = section = None
        for _, r in raw.iterrows():
            lab = str(r[0]).strip() if pd.notna(r[0]) else ""
            if lab and lab.isupper() and r.drop(0).isna().all():
                op = lab
            elif lab in ("Interactive Slots", "Banking Tables 2", "Non-Banking Tables (Poker) 3"):
                section = {"Interactive Slots": "slots", "Banking Tables 2": "tables"}.get(lab, "poker")
            elif lab in ("Wagers Received", "Amount Won", "Gross Revenue", "Revenue (Rake & Tournament Fees)"):
                metric = {"Wagers Received": "wagers", "Amount Won": "won"}.get(lab, "ggr")
                for c, m in months.items():
                    if pd.notna(r[c]):
                        rows.append((m, short_pa(op), f"{section}_{metric}_usd", float(r[c])))
    d = (pd.DataFrame(rows, columns=["month", "operator", "metric", "value"])
         .pivot_table(index=["month", "operator"], columns="metric", values="value", aggfunc="sum").reset_index())
    d.columns.name = None
    d = d[d.drop(columns=["month", "operator"]).fillna(0).abs().sum(axis=1) > 0]     # months not yet reported
    d.to_csv(PUBLIC / "pa_interactive_gaming_by_operator.csv", index=False)
    return d


def main():
    PUBLIC.mkdir(parents=True, exist_ok=True)
    download()
    d, _ = nj()
    p = pa()
    pd.DataFrame(FACTS, columns=["fact", "value", "source_url"]).assign(
        accessed=lambda x: x.source_url.map({HOME: "read 2026-11-15", JOB: "posted 2026-11-08"})
    ).to_csv(PUBLIC / "hard_rock_digital_facts.csv", index=False)
    print(f"NJ: {d.month.nunique()} months, {d.licensee.nunique()} licensees; PA: {p.month.nunique()} months, "
          f"{p.operator.nunique() - 1} operators + total. Tables in data/public/")


if __name__ == "__main__":
    main()
