#!/usr/bin/env python3
"""Summarize one migration verification run so nobody has to read raw.log.

Reads <run-dir>/raw.log, exit-code.txt, started-at.txt and the JUnit XML reports
under the service checkout. Writes into <run-dir>:

  summary.json  build outcome, configure/resolution failures, compile errors per
                owning phase, test counts, and (with --baseline) the test delta
  errors.tsv    every compile error: owner, scope, file:line, message
  tests.tsv     every test case: status, class, name
  delta.tsv     with --baseline: change, class, name

Prints one line on stdout for the orchestrator. Standard library only; Python 3.8+.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
ERROR_PATTERNS = [
    re.compile(r"^(?P<path>/.+?\.java):(?P<line>\d+): error: (?P<msg>.+)$"),
    re.compile(r"^e: (?:file://)?(?P<path>/.+?\.kts?):(?P<line>\d+):(?P<col>\d+):? (?P<msg>.+)$"),
    re.compile(r"^e: (?P<path>/.+?\.kts?): \((?P<line>\d+), (?P<col>\d+)\): (?P<msg>.+)$"),
    re.compile(r"^\[ERROR\] (?P<path>/.+?\.(?:java|kt)):\[(?P<line>\d+),(?P<col>\d+)\] (?P<msg>.+)$"),
]
JAVAC_DETAIL = re.compile(r"^\s+(symbol|location|required|found|reason):")
RESOLVE_MARKER = re.compile(r"MIGRATION-RESOLVE-FAIL (?P<project>\S+) (?P<config>\S+) (?P<msg>.+)$")
COORDINATE = re.compile(r"Could not (?:find|resolve) (?P<coord>[\w.\-]+:[\w.\-]+(?::[\w.\-+]+)?)")
TASK_LINE = re.compile(r"^> Task (?P<task>\S+)(?: (?P<state>[A-Z\-]+))?\s*$")
COMPILE_TASK = re.compile(r":?(compile\w*(Java|Kotlin|Groovy)|kaptKotlin|kaptTestKotlin)$")
GRADLE_TESTS = re.compile(r"(?P<total>\d+) tests? completed, (?P<failed>\d+) failed(?:, (?P<skipped>\d+) skipped)?")
MAVEN_TESTS = re.compile(r"Tests run: (?P<total>\d+), Failures: (?P<failures>\d+), Errors: (?P<errors>\d+), Skipped: (?P<skipped>\d+)")
PHASE_ID = re.compile(r"^(\d{2}-[a-z0-9][a-z0-9-]*?)(?=\s|:|$)")
BUILD_FILE_NAMES = {
    "build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts",
    "gradle.properties", "pom.xml", "libs.versions.toml",
}
PRUNE = {".git", ".gradle", ".idea", ".joker", "node_modules", "out", ".kotlin"}
REPORT_DIRS = {"test-results", "surefire-reports", "failsafe-reports"}
SAMPLES_PER_OWNER = 3
LIST_CAP = 50


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def run_kind(run_dir: Path, override: str | None) -> str:
    if override:
        return override
    match = re.search(r"^kind:\s*(\S+)", read_text(run_dir / "run.yaml"), re.M)
    return match.group(1) if match else "unknown"


def load_rules(path: Path) -> list[dict]:
    data = json.loads(read_text(path))
    rules = []
    for rule in data["rules"]:
        rules.append({
            "phase": rule["phase"],
            "path": re.compile(rule["path"]) if rule.get("path") else None,
            "text": re.compile(rule["text"]) if rule.get("text") else None,
        })
    return rules


def match_owner(rules: list[dict], relpath: str, text: str) -> str:
    for rule in rules:
        if rule["path"] is None and rule["text"] is None:
            continue
        if rule["path"] is not None and not rule["path"].search(relpath):
            continue
        if rule["text"] is not None and not rule["text"].search(text):
            continue
        return rule["phase"]
    return "unowned"


def git(repo: Path, *args: str) -> str | None:
    try:
        done = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout if done.returncode == 0 else None


def blame_phase(repo: Path, relpath: str, line: int) -> str:
    out = git(repo, "blame", "-L", f"{line},{line}", "--porcelain", "--", relpath)
    if not out:
        return "build-script:unattributed"
    sha = out.split()[0]
    if set(sha) == {"0"}:
        return "build-script:uncommitted"
    subject = (git(repo, "log", "-1", "--format=%s", sha) or "").strip()
    match = PHASE_ID.match(subject)
    return match.group(1) if match else "build-script:unattributed"


def iter_build_files(repo: Path):
    for root, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in PRUNE and d not in ("build", "target")]
        for name in files:
            if name in BUILD_FILE_NAMES:
                yield Path(root) / name


def coordinate_owner(repo: Path, coord: str) -> str:
    parts = coord.split(":")
    group, artifact = parts[0], parts[1]
    for build_file in iter_build_files(repo):
        for number, text in enumerate(read_text(build_file).splitlines(), 1):
            joined = f"{group}:{artifact}" in text
            split = artifact in text and group in text
            pom = f"<artifactId>{artifact}</artifactId>" in text
            if joined or split or pom:
                return blame_phase(repo, build_file.relative_to(repo).as_posix(), number)
    return "unowned"


def relative(repo: Path, path: str) -> str:
    try:
        return Path(path).resolve().relative_to(repo.resolve()).as_posix()
    except (ValueError, OSError):
        return path


def scope_of(relpath: str) -> str:
    if Path(relpath).name in BUILD_FILE_NAMES:
        return "build"
    match = re.search(r"(?:^|/)src/([^/]+)/", relpath)
    if match:
        return "main" if match.group(1) == "main" else "test"
    return "main"


class SourceCache:
    def __init__(self) -> None:
        self.files: dict[str, list[str]] = {}

    def line(self, path: str, number: int) -> str:
        if path not in self.files:
            self.files[path] = read_text(Path(path)).splitlines()
        lines = self.files[path]
        return lines[number - 1].strip() if 0 < number <= len(lines) else ""


def what_went_wrong(lines: list[str]) -> list[list[str]]:
    blocks, i = [], 0
    while i < len(lines) and len(blocks) < 5:
        if lines[i].strip() == "* What went wrong:":
            block, i = [], i + 1
            while i < len(lines) and not lines[i].startswith("* Try:") and len(block) < 8:
                if lines[i].strip():
                    block.append(lines[i].strip()[:240])
                i += 1
            blocks.append(block)
        else:
            i += 1
    return blocks


def parse_log(lines: list[str], repo: Path, rules: list[dict]) -> dict:
    sources = SourceCache()
    errors, coords, resolve_lines = [], {}, []
    tasks_ran, tasks_failed = set(), set()
    i = 0
    while i < len(lines):
        line = lines[i]
        task = TASK_LINE.match(line)
        if task:
            state = task.group("state") or "EXECUTED"
            if state == "FAILED":
                tasks_failed.add(task.group("task"))
            if COMPILE_TASK.search(task.group("task")) and state not in ("SKIPPED", "NO-SOURCE"):
                tasks_ran.add(task.group("task"))
        marker = RESOLVE_MARKER.search(line)
        if marker:
            resolve_lines.append(f"{marker.group('project')} {marker.group('config')}: {marker.group('msg')[:200]}")
        for found in COORDINATE.finditer(line):
            coords.setdefault(found.group("coord").rstrip("."), None)
        for pattern in ERROR_PATTERNS:
            match = pattern.match(line)
            if not match:
                continue
            detail = []
            j = i + 1
            while j < len(lines) and len(detail) < 4 and JAVAC_DETAIL.match(lines[j]):
                detail.append(lines[j].strip())
                j += 1
            path, number = match.group("path"), int(match.group("line"))
            relpath = relative(repo, path)
            source = sources.line(path, number)
            text = " ".join([match.group("msg"), *detail, source])
            owner = match_owner(rules, relpath, text)
            if owner == "build-script":
                owner = blame_phase(repo, relpath, number)
            errors.append({
                "owner": owner,
                "scope": scope_of(relpath),
                "location": f"{relpath}:{number}",
                "message": (match.group("msg") + (" | " + " | ".join(detail) if detail else ""))[:300],
            })
            break
        i += 1
    return {
        "errors": errors,
        "coordinates": {coord: coordinate_owner(repo, coord) for coord in coords},
        "resolveLines": resolve_lines,
        "tasksRan": sorted(tasks_ran),
        "tasksFailed": sorted(tasks_failed),
    }


def iter_report_files(repo: Path):
    for root, dirs, files in os.walk(repo):
        here = Path(root)
        base = here.name
        if base == "build":
            dirs[:] = [d for d in dirs if d == "test-results"]
        elif base == "target":
            dirs[:] = [d for d in dirs if d in ("surefire-reports", "failsafe-reports")]
        else:
            dirs[:] = [d for d in dirs if d not in PRUNE]
        if REPORT_DIRS & set(here.relative_to(repo).parts):
            for name in files:
                if name.startswith("TEST-") and name.endswith(".xml"):
                    yield here / name


def collect_tests(repo: Path, since: float | None) -> tuple[dict, int]:
    results: dict[tuple[str, str], str] = {}
    stale = 0
    for report in iter_report_files(repo):
        try:
            if since is not None and report.stat().st_mtime < since - 2:
                stale += 1
                continue
            root = ET.parse(report).getroot()
        except (ET.ParseError, OSError):
            continue
        for case in root.iter("testcase"):
            cls, name = case.get("classname") or "", case.get("name") or ""
            if case.find("failure") is not None or case.find("error") is not None:
                status = "failed"
            elif case.find("skipped") is not None:
                status = "skipped"
            else:
                status = "passed"
            key, n = (cls, name), 2
            while key in results:
                key, n = (cls, f"{name} #{n}"), n + 1
            results[key] = status
    return results, stale


def console_test_counts(lines: list[str]) -> dict | None:
    gradle = [m for m in (GRADLE_TESTS.search(l) for l in lines) if m]
    if gradle:
        m = gradle[-1]
        total, failed, skipped = int(m["total"]), int(m["failed"]), int(m["skipped"] or 0)
        return {"total": total, "failed": failed, "skipped": skipped, "passed": total - failed - skipped}
    maven = [m for m in (MAVEN_TESTS.search(l) for l in lines) if m]
    if maven:
        m = maven[-1]
        total, failed = int(m["total"]), int(m["failures"]) + int(m["errors"])
        skipped = int(m["skipped"])
        return {"total": total, "failed": failed, "skipped": skipped, "passed": total - failed - skipped}
    return None


def read_tsv(path: Path) -> dict[tuple[str, str], str]:
    rows = {}
    for line in read_text(path).splitlines()[1:]:
        parts = line.split("\t")
        if len(parts) == 3:
            rows[(parts[1], parts[2])] = parts[0]
    return rows


def write_tsv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    clean = [[str(v).replace("\t", " ").replace("\n", " ") for v in row] for row in rows]
    path.write_text("\n".join(["\t".join(header), *["\t".join(r) for r in clean]]) + "\n", encoding="utf-8")


def compute_delta(current: dict, baseline: dict) -> dict:
    newly_failing = sorted(k for k, s in current.items() if s == "failed" and baseline.get(k) != "failed")
    fixed = sorted(k for k, s in current.items() if s == "passed" and baseline.get(k) == "failed")
    missing = sorted(k for k, s in baseline.items() if k not in current and s != "skipped")
    added = sorted(k for k in current if k not in baseline)
    still = sorted(k for k, s in current.items() if s == "failed" and baseline.get(k) == "failed")
    return {"newlyFailing": newly_failing, "fixed": fixed, "missing": missing, "added": added, "stillFailing": still}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--repo", default=".", type=Path, help="service checkout root")
    parser.add_argument("--ownership", type=Path,
                        default=Path(__file__).resolve().parent.parent / "references" / "ownership.json")
    parser.add_argument("--baseline", type=Path, help="baseline run directory holding tests.tsv")
    parser.add_argument("--kind", help="override kind from run.yaml")
    args = parser.parse_args()

    run_dir, repo = args.run_dir.resolve(), args.repo.resolve()
    raw = run_dir / "raw.log"
    if not raw.exists():
        print(f"run={run_dir.name} status=awaiting-log (no raw.log)")
        return 2
    lines = [ANSI.sub("", l) for l in read_text(raw).splitlines()]
    exit_text = read_text(run_dir / "exit-code.txt").strip()
    exit_code = int(exit_text) if exit_text.lstrip("-").isdigit() else None
    started = read_text(run_dir / "started-at.txt").strip()
    since = float(started) if re.fullmatch(r"\d+(\.\d+)?", started) else None

    joined = "\n".join(lines)
    if "BUILD FAILED" in joined or "BUILD FAILURE" in joined:
        build = "failed"
    elif "BUILD SUCCESSFUL" in joined or "BUILD SUCCESS" in joined:
        build = "successful"
    else:
        build = "unknown"

    blocks = what_went_wrong(lines)
    configure_failed = any(
        re.search(r"problem occurred (configuring|evaluating)|Script compilation error|build file '.*' line", " ".join(b))
        for b in blocks
    )
    parsed = parse_log(lines, repo, load_rules(args.ownership))

    by_owner: dict[str, dict] = {}
    for error in parsed["errors"]:
        entry = by_owner.setdefault(error["owner"], {"main": 0, "test": 0, "build": 0, "samples": []})
        entry[error["scope"]] += 1
        if len(entry["samples"]) < SAMPLES_PER_OWNER:
            entry["samples"].append(f"{error['location']} {error['message']}")
    write_tsv(run_dir / "errors.tsv", ["owner", "scope", "location", "message"],
              [[e["owner"], e["scope"], e["location"], e["message"]] for e in parsed["errors"]])

    tests, stale_reports = collect_tests(repo, since)
    if tests:
        counts = {s: sum(1 for v in tests.values() if v == s) for s in ("passed", "failed", "skipped")}
        test_summary = {"source": "junit-xml", "total": len(tests), **counts,
                        "failedNames": [f"{c} > {n}" for (c, n), s in sorted(tests.items()) if s == "failed"][:LIST_CAP]}
        write_tsv(run_dir / "tests.tsv", ["status", "class", "name"],
                  [[s, c, n] for (c, n), s in sorted(tests.items())])
    else:
        console = console_test_counts(lines)
        test_summary = {"source": "console", **console} if console else {"source": "none"}
    test_summary["staleReportsIgnored"] = stale_reports
    if since is None:
        test_summary["warning"] = "no started-at.txt; reports from earlier runs may be included"

    summary = {
        "runId": run_dir.name,
        "kind": run_kind(run_dir, args.kind),
        "exitCode": exit_code,
        "build": build,
        "configure": {"failed": configure_failed, "whatWentWrong": blocks},
        "resolution": {
            "failures": parsed["resolveLines"][:LIST_CAP],
            "coordinates": parsed["coordinates"],
        },
        "compile": {
            "errors": len(parsed["errors"]),
            "tasksRan": parsed["tasksRan"],
            "tasksFailed": parsed["tasksFailed"],
            "byOwner": dict(sorted(by_owner.items(), key=lambda kv: -(kv[1]["main"] + kv[1]["test"] + kv[1]["build"]))),
        },
        "tests": test_summary,
    }

    delta_text = ""
    if args.baseline:
        baseline = read_tsv(args.baseline.resolve() / "tests.tsv")
        if baseline and tests:
            delta = compute_delta(tests, baseline)
            summary["delta"] = {
                "baselineRunId": args.baseline.resolve().name,
                **{k: len(v) for k, v in delta.items()},
                "newlyFailingNames": [f"{c} > {n}" for c, n in delta["newlyFailing"][:LIST_CAP]],
                "missingNames": [f"{c} > {n}" for c, n in delta["missing"][:LIST_CAP]],
            }
            write_tsv(run_dir / "delta.tsv", ["change", "class", "name"],
                      [[change, c, n] for change, keys in delta.items() for c, n in keys])
            d = summary["delta"]
            delta_text = (f" delta[newlyFailing={d['newlyFailing']} missing={d['missing']} "
                          f"fixed={d['fixed']} stillFailing={d['stillFailing']} added={d['added']}]")
        else:
            summary["delta"] = {"baselineRunId": args.baseline.name, "error": "baseline or current tests.tsv missing"}
            delta_text = " delta=unavailable"

    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    owners = " ".join(f"{o}:{v['main'] + v['test'] + v['build']}" for o, v in summary["compile"]["byOwner"].items())
    t = summary["tests"]
    tests_text = (f"tests={t['passed']}/{t['total']} failed={t['failed']} skipped={t['skipped']}"
                  if "total" in t else "tests=n/a")
    resolve_n = len(parsed["resolveLines"]) or len(parsed["coordinates"])
    compile_n = len(parsed["errors"])
    cause = ""
    if exit_code not in (0, None) and resolve_n == 0 and compile_n == 0:
        bits = list(parsed["tasksFailed"])
        if blocks and blocks[0]:
            bits.append(blocks[0][0])
        if bits:
            cause = " cause=" + " | ".join(bits)[:240]
    print(f"run={run_dir.name} kind={summary['kind']} exit={exit_code} build={build} "
          f"configure={'failed' if configure_failed else 'ok'} resolve={resolve_n} "
          f"compile={compile_n}" + (f" [{owners}]" if owners else "") + f" {tests_text}{delta_text}{cause}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
