"""Shared paths and constants. Every script imports from here (run scripts as `python src/<name>.py`)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"            # regulator files as downloaded (not committed, see data/SOURCES.md)
PUBLIC = ROOT / "data" / "public"      # small derived tables from public sources (PUBLIC DATA, cited)
SIM = ROOT / "data" / "simulated"      # SIMULATED catalogue, pipeline, wallet logs, promotions
OUT = ROOT / "data" / "output"         # SQL and notebook outputs
SQL = ROOT / "sql"
DOCS = ROOT / "docs"
IMG = DOCS / "img"
INTEG = DOCS / "integration"
STATUS = DOCS / "status"
DASH = ROOT / "dashboard" / "casino_integrations.html"

SEED = 42
START, END = "2025-10-01", "2026-09-30"     # 12 simulated months, aligned with the latest regulator month
AS_OF = "2026-11-13"                          # "today" for the pipeline, tracker and weekly status (a Friday)
STATES = ["State A", "State B", "State C"]   # fictional jurisdictions
GAME_TYPES = ["Slot", "Table", "Live dealer", "Jackpot slot"]

COMPANY = "Hard Rock Digital"
FOOTER = "Independent case study based on public data · not affiliated with or endorsed by Hard Rock Digital"
AI_NOTE = ("AI-assisted workflow: I used Claude, mainly to write scripts faster. I drove the project: I defined the "
           "questions, chose and validated the data sources, made the analytical decisions and checked every result.")
UA = "Mozilla/5.0 (independent case-study research; low frequency)"
