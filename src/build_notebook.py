"""Turn notebooks/analysis.py (cells separated by '# %%') into notebooks/analysis.ipynb and execute it.

Run: python src/build_notebook.py
"""
from __future__ import annotations

import re

import nbformat as nbf
from nbconvert.preprocessors import ExecutePreprocessor

from config import ROOT

SRC = ROOT / "notebooks" / "analysis.py"


def cells(text: str):
    for block in re.split(r"^# %%", text, flags=re.M)[1:]:
        head, _, body = block.partition("\n")
        if head.strip() == "[markdown]":
            md = "\n".join(line[2:] if line.startswith("# ") else line.lstrip("#") for line in body.strip().splitlines())
            yield nbf.v4.new_markdown_cell(md)
        else:
            yield nbf.v4.new_code_cell(body.strip())


def main():
    nb = nbf.v4.new_notebook()
    nb.cells = list(cells(SRC.read_text(encoding="utf-8")))
    nb.metadata = {"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"}}
    ExecutePreprocessor(timeout=900, kernel_name="python3").preprocess(nb, {"metadata": {"path": str(ROOT / "notebooks")}})
    nbf.write(nb, ROOT / "notebooks" / "analysis.ipynb")
    print("notebook: notebooks/analysis.ipynb executed,", len(nb.cells), "cells")


if __name__ == "__main__":
    main()
