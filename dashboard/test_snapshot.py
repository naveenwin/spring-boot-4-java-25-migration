#!/usr/bin/env python3
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from snapshot import build_snapshot

STATUS = """\
target: { boot: "4.1.x", java: 25, cloud: "2025.1.x" }
stage: B
overallStatus: waiting-human
runs:
  compile: 20261031T120000Z-compile
  context: null
items:
  - id: 04-jackson-3
    priority: must
    risk: high
    executionGate: ASK_HUMAN
    readiness: ready
    blockers:
      - id: B-04-1
        question: "Which enums cross an HTTP boundary?"
        resolveBy: human
        status: closed
        answer: "OrderStatus, PaymentState"
    slices: { A: done, B: in_progress }
    status: in_progress
    commits: ["a1b2c3d"]
    verifier: required
    handoff: "jackson3=sole"
  - id: 09-testing
    priority: must
    risk: medium
    executionGate: ASK_HUMAN
    blockers:
      - id: B-09-1
        question: "How should HTTP error bodies look after Boot 4?"
        resolveBy: human
        status: open
        answer: ""
    slices: { A: done, B: pending }
    status: blocked
    verifier: n/a
    handoff: ""
  - id: 36-junit-jupiter
    priority: must
    risk: medium
    executionGate: SAFE_AUTO
    blockers: []
    slices: { A: done, B: pending }
    status: pending
    verifier: n/a
  - id: 99-skip-me
    status: n/a
    executionGate: SAFE_AUTO
    slices: { A: none, B: n/a }
"""

NOTE = """\
```yaml
phase: 04-jackson-3
handoff: "jackson3=sole; wireContracts=approved-diff"
```
"""

VERIFIER = """\
```yaml
verdict: PASS
phaseIds: ["04-jackson-3"]
```
"""

COMPILE_SUMMARY = """\
{
  "kind": "compile",
  "exit": 1,
  "compile": {
    "errors": 42,
    "byOwner": {
      "04-jackson-3": { "main": 40, "test": 2, "build": 0 }
    }
  }
}
"""

RESOLVE_SUMMARY = """\
{
  "kind": "resolve",
  "exitCode": 0,
  "build": "SUCCESS",
  "resolution": { "failures": [], "coordinates": [] },
  "compile": { "errors": 0, "byOwner": {} }
}
"""


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.service = self.tmp / "service"
        base = self.service / ".joker" / "java-spring-migration"
        write(base / "status.yaml", STATUS)
        write(base / "phase-notes" / "04-jackson-3.md", NOTE)
        write(base / "verifier" / "04-jackson-3.md", VERIFIER)
        write(base / "handoffs" / "20261031T180000Z.md", "# Chat handoff\n\nreason: waiting-human\nstage: B\n")
        runs = base / "verification-runs"
        write(runs / "20261031T120000Z-compile" / "run.yaml", "runId: 20261031T120000Z-compile\nkind: compile\nsourceCommit: a1b2c3d\nstatus: resolved\n")
        write(runs / "20261031T120000Z-compile" / "summary.json", COMPILE_SUMMARY)
        write(runs / "20261031T120000Z-compile" / "raw.log", "THIS MUST NEVER APPEAR IN THE SNAPSHOT\n")
        write(runs / "20261031T100000Z-resolve" / "run.yaml", "runId: 20261031T100000Z-resolve\nkind: resolve\nsourceCommit: a1b2c3d\nstatus: resolved\n")
        write(runs / "20261031T100000Z-resolve" / "summary.json", RESOLVE_SUMMARY)
        write(runs / "20261031T090000Z-context" / "run.yaml", "runId: 20261031T090000Z-context\nkind: context\nstatus: awaiting-log\n")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_fixture(self):
        snap = build_snapshot(self.service)
        blob = json.dumps(snap)
        self.assertNotIn("THIS MUST NEVER APPEAR", blob)
        self.assertNotIn("raw.log", blob)
        self.assertFalse(snap["missing"])
        self.assertEqual(snap["stageLabel"], "Code fixes")
        self.assertEqual(snap["overallLabel"], "Waiting on you")
        ids = [i["id"] for i in snap["items"]]
        self.assertIn("04-jackson-3", ids)
        self.assertNotIn("99-skip-me", ids)
        jackson = next(i for i in snap["items"] if i["id"] == "04-jackson-3")
        self.assertEqual(jackson["title"], "Jackson 3")
        self.assertEqual(jackson["compileOwned"], 42)
        self.assertEqual(jackson["slices"]["A"], "done")
        self.assertEqual(jackson["verifier"], "pass")
        self.assertEqual(jackson["questions"]["closed"], 1)
        testing = next(i for i in snap["items"] if i["id"] == "09-testing")
        self.assertEqual(testing["filter"], "human")
        self.assertTrue(any(q["open"] and "error bodies" in q["title"] for q in snap["inbox"]))
        self.assertEqual(snap["counts"]["human"], 1)
        runs = snap["verificationRuns"]
        self.assertEqual([r["kind"] for r in runs], ["compile", "resolve", "context"])
        self.assertEqual(runs[0]["status"], "Failed")
        self.assertEqual(runs[0]["phases"][0]["id"], "04-jackson-3")
        self.assertIn("42 compile errors", runs[0]["headline"])
        self.assertTrue(any(f["k"] == "Exit" for f in runs[0]["facts"]))
        self.assertEqual(runs[1]["status"], "Passed")
        self.assertEqual(runs[1]["phases"][0]["id"], "04-jackson-3")
        self.assertEqual(runs[2]["status"], "Waiting for log")

    def test_missing_joker(self):
        snap = build_snapshot(self.tmp)
        self.assertTrue(snap["missing"])
        self.assertEqual(snap["items"], [])
        self.assertEqual(snap["verificationRuns"], [])


if __name__ == "__main__":
    unittest.main()
