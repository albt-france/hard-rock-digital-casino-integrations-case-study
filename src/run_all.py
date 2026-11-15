"""Rebuild the whole study in order.

Usage: python src/run_all.py             (everything)
       python src/run_all.py --offline   (skip the download; uses data/raw and data/public as they are)
       python src/run_all.py --no-pdf    (skip the Edge steps: dashboard captures and PDF)
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent
STEPS = ["download_data", "simulate", "run_sql", "build_notebook", "compliance_alerts", "weekly_status",
         "build_backlog", "build_dashboard", "build_pdf"]


def main():
    for step in STEPS:
        if step == "download_data" and "--offline" in sys.argv:
            continue
        if step == "build_pdf" and "--no-pdf" in sys.argv:
            continue
        print(f"\n>>> python src/{step}.py", flush=True)
        subprocess.run([sys.executable, "-W", "ignore", str(SRC / f"{step}.py")], check=True, cwd=SRC.parent)


if __name__ == "__main__":
    main()
