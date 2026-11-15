"""Turn docs/integration/user_stories.md into docs/integration/backlog.csv (Jira CSV import).

Epics become rows of type Epic; stories point to their epic through the "Parent" column. Acceptance criteria keep their
Given / When / Then lines. Run: python src/build_backlog.py
"""
from __future__ import annotations

import csv
import re

from config import INTEG

SRC, OUT = INTEG / "user_stories.md", INTEG / "backlog.csv"


def main():
    text = SRC.read_text(encoding="utf-8")
    epics = re.findall(r"^## Epic (E\d): (.+)$", text, flags=re.M)
    rows = [dict(issue_id=e, issue_type="Epic", summary=name, parent="", priority="", story_points="",
                 labels="provider-q;casino-integrations", description=f"Epic {e}: {name}", acceptance_criteria="",
                 depends_on="") for e, name in epics]
    for block in re.split(r"^### ", text, flags=re.M)[1:]:
        head, _, body = block.partition("\n")
        sid, epic, prio, pts, dep, title = [x.strip() for x in head.split("|")]
        body = body.split("\n## ")[0]                  # drop the next epic heading
        story = re.search(r"(\*\*As.+?)(?=\n- )", body, flags=re.S).group(1)
        story = re.sub(r"\*\*", "", " ".join(story.split()))
        ac = [re.sub(r"\s+", " ", a).strip() for a in re.findall(r"^- (Given.+?)(?=^- |\Z)", body, flags=re.M | re.S)]
        rows.append(dict(issue_id=sid, issue_type="Story", summary=title, parent=epic,
                         priority=prio, story_points=pts, labels="provider-q;casino-integrations", description=story,
                         acceptance_criteria="\n".join(ac), depends_on="" if dep == "-" else dep))
    head = {"issue_id": "Issue ID", "issue_type": "Issue Type", "summary": "Summary", "parent": "Parent",
            "priority": "Priority", "story_points": "Story Points", "labels": "Labels", "description": "Description",
            "acceptance_criteria": "Acceptance Criteria", "depends_on": "Depends On"}
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(head))
        fh.write(",".join(head.values()) + "\n")
        w.writerows(rows)
    n = sum(r["issue_type"] == "Story" for r in rows)
    print(f"backlog: {len(epics)} epics, {n} stories, {sum(int(r['story_points'] or 0) for r in rows)} points -> "
          f"docs/integration/backlog.csv")


if __name__ == "__main__":
    main()
