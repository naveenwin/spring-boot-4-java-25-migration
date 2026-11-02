#!/usr/bin/env python3
"""Read-only view of .joker/java-spring-migration/. Never opens raw.log."""
from __future__ import annotations

import json
import re
from pathlib import Path

JOKER = "java-spring-migration"
SKIP_LOGS = {"raw.log"}
STAGE_LABELS = {
    "planning": "Planning",
    "0": "Baseline",
    "A": "Library versions",
    "B": "Code fixes",
    "C": "Runtime check",
    "good": "Good tier",
    "closeout": "Closeout",
    "done": "Done",
}
OVERALL_LABELS = {
    "planning": "Planning",
    "waiting-catalog-gaps": "Waiting on catalog gaps",
    "waiting-plan-approval": "Waiting on you",
    "executing": "Agent working",
    "waiting-human": "Waiting on you",
    "waiting-new-chat": "Waiting for a new chat",
    "done": "Done",
}
KIND_LABELS = {
    "baseline": "Baseline suite",
    "context": "Context load",
    "resolve": "Library resolve",
    "compile": "Compile",
    "test": "Full suite",
    "pipeline": "Pipeline",
}
TITLE_FIX = {
    "webflux": "WebFlux",
    "jpa": "JPA",
    "gcp": "GCP",
    "junit": "JUnit",
    "openapi": "OpenAPI",
    "json": "JSON",
    "http": "HTTP",
    "ci": "CI",
}


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def load_yaml(text: str):
    if not text.strip():
        return {}
    try:
        import yaml  # type: ignore
        data = yaml.safe_load(text)
        return data if isinstance(data, dict) else {}
    except Exception:
        return _mini_yaml(text)


def _scalar(raw: str):
    s = raw.strip()
    if s in ("", "~", "null", "Null"):
        return None
    if s in ("true", "True", "yes"):
        return True
    if s in ("false", "False", "no"):
        return False
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    if re.fullmatch(r"-?\d+", s):
        return int(s)
    if s.startswith("{") and s.endswith("}"):
        inner = s[1:-1].strip()
        out = {}
        if inner:
            for part in inner.split(","):
                if ":" not in part:
                    continue
                k, v = part.split(":", 1)
                out[k.strip()] = _scalar(v)
        return out
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        if not inner:
            return []
        return [_scalar(p) for p in inner.split(",")]
    return s


def _mini_yaml(text: str):
    lines = []
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        lines.append((indent, line.strip()))
    if not lines:
        return {}
    val, _ = _parse_map(lines, 0, lines[0][0])
    return val if isinstance(val, dict) else {}


def _parse_map(lines, i, base):
    out = {}
    while i < len(lines):
        indent, raw = lines[i]
        if indent < base:
            break
        if indent > base:
            i += 1
            continue
        if raw.startswith("- "):
            lst, i = _parse_list(lines, i, base)
            return lst, i
        if ":" not in raw:
            i += 1
            continue
        key, rest = raw.split(":", 1)
        key = key.strip()
        rest = rest.strip()
        i += 1
        if rest:
            out[key] = _scalar(rest)
            continue
        if i < len(lines) and lines[i][0] > base:
            child, i = _parse_map(lines, i, lines[i][0])
            out[key] = child
        else:
            out[key] = None
    return out, i


def _parse_list(lines, i, base):
    items = []
    while i < len(lines):
        indent, raw = lines[i]
        if indent < base:
            break
        if not raw.startswith("- "):
            break
        body = raw[2:].strip()
        i += 1
        if body and ":" in body:
            k, v = body.split(":", 1)
            item = {k.strip(): _scalar(v)}
            if i < len(lines) and lines[i][0] > indent:
                extra, i = _parse_map(lines, i, lines[i][0])
                if isinstance(extra, dict):
                    item.update(extra)
            items.append(item)
        elif body:
            items.append(_scalar(body))
        else:
            if i < len(lines) and lines[i][0] > indent:
                child, i = _parse_map(lines, i, lines[i][0])
                items.append(child)
            else:
                items.append(None)
    return items, i


def yaml_block(text: str) -> dict:
    m = re.search(r"```yaml\s*(.*?)```", text, re.S)
    chunk = m.group(1) if m else text
    data = load_yaml(chunk)
    return data if isinstance(data, dict) else {}


def title_of(phase_id: str) -> str:
    parts = phase_id.split("-")
    words = parts[1:] if parts and re.fullmatch(r"\d{2}", parts[0]) else parts
    out = []
    for w in words:
        out.append(TITLE_FIX.get(w.lower(), w[:1].upper() + w[1:] if w else w))
    return " ".join(out) or phase_id


def joker_dir(root: Path) -> Path:
    return Path(root) / ".joker" / JOKER


def _owned(summary: dict, phase_id: str) -> int:
    by = ((summary or {}).get("compile") or {}).get("byOwner") or {}
    row = by.get(phase_id) or {}
    if isinstance(row, dict):
        return int(row.get("main") or 0) + int(row.get("test") or 0) + int(row.get("build") or 0)
    try:
        return int(row)
    except (TypeError, ValueError):
        return 0


def _run_summary(joker: Path, run_id) -> dict:
    if not run_id:
        return {}
    path = joker / "verification-runs" / str(run_id) / "summary.json"
    try:
        data = json.loads(read_text(path) or "{}")
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def _context_state(summary: dict) -> str:
    if not summary:
        return "n/a"
    if summary.get("kind") and summary.get("kind") != "context":
        pass
    exit_code = summary.get("exit")
    if exit_code in (0, "0"):
        return "pass"
    if exit_code not in (None, ""):
        return "fail"
    build = str(summary.get("build") or "")
    if build in ("SUCCESS", "ok", "passed"):
        return "pass"
    if build:
        return "fail"
    return "n/a"


def _when_sort_key(run_dir: Path) -> str:
    started = read_text(run_dir / "started-at.txt").strip()
    if started.isdigit():
        return started.zfill(16)
    m = re.match(r"^(\d{8}T\d{6}Z)", run_dir.name)
    return m.group(1) if m else run_dir.name


def _when_label(run_dir: Path) -> str:
    m = re.match(r"^(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})", run_dir.name)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)} {m.group(4)}:{m.group(5)} UTC"
    started = read_text(run_dir / "started-at.txt").strip()
    if started.isdigit():
        return started
    return run_dir.name


def _exit_of(summary: dict, run_dir: Path):
    for key in ("exitCode", "exit"):
        if summary.get(key) not in (None, ""):
            try:
                return int(summary[key])
            except (TypeError, ValueError):
                return summary[key]
    raw = read_text(run_dir / "exit-code.txt").strip()
    if raw.isdigit() or (raw.startswith("-") and raw[1:].isdigit()):
        return int(raw)
    return None


def _run_headline(kind: str, summary: dict, exit_code) -> str:
    if not summary:
        return "Extractor has not run yet."
    compile_info = summary.get("compile") or {}
    tests = summary.get("tests") or {}
    resolution = summary.get("resolution") or {}
    configure = summary.get("configure") or {}
    bits = []
    if configure.get("failed"):
        bits.append("configure failed")
    n_err = compile_info.get("errors")
    if n_err is None and isinstance(compile_info.get("byOwner"), dict):
        n_err = sum(
            int(v.get("main") or 0) + int(v.get("test") or 0) + int(v.get("build") or 0)
            if isinstance(v, dict) else int(v or 0)
            for v in compile_info["byOwner"].values()
        )
    if kind == "compile" or n_err:
        if n_err:
            bits.append(f"{n_err} compile errors")
        elif kind == "compile":
            bits.append("compile clear")
    coords = resolution.get("coordinates") or resolution.get("failures") or []
    if kind == "resolve":
        bits.append("classpath resolved" if not coords else f"{len(coords)} resolve failures")
    if kind in ("context",) and exit_code is not None:
        bits.append("context loaded" if exit_code == 0 else "context failed")
    if "total" in tests:
        bits.append(
            f"tests {tests.get('passed', 0)}/{tests.get('total', 0)} passed, "
            f"{tests.get('failed', 0)} failed"
        )
    delta = summary.get("delta") or {}
    if isinstance(delta.get("newlyFailing"), int):
        bits.append(f"{delta['newlyFailing']} new failures vs baseline")
    if not bits:
        if exit_code == 0:
            bits.append("finished clean")
        elif exit_code not in (None,):
            bits.append(f"exit {exit_code}")
        else:
            bits.append(str(summary.get("build") or "extracted"))
    return " · ".join(bits)


def _run_facts(kind: str, meta: dict, summary: dict, exit_code, phases: list) -> list:
    facts = []
    yaml_status = str(meta.get("status") or "")
    if yaml_status:
        facts.append({"k": "Extractor", "v": yaml_status.replace("-", " ")})
    if exit_code is not None:
        facts.append({"k": "Exit", "v": str(exit_code)})
    sha = str(meta.get("sourceCommit") or "")
    if sha:
        facts.append({"k": "Commit", "v": sha[:7]})
    build = summary.get("build")
    if build:
        facts.append({"k": "Build", "v": str(build)})
    configure = summary.get("configure") or {}
    if configure.get("failed"):
        facts.append({"k": "Configure", "v": "failed"})
    compile_info = summary.get("compile") or {}
    by_owner = compile_info.get("byOwner") or {}
    if isinstance(by_owner, dict):
        for pid, counts in list(by_owner.items())[:4]:
            if isinstance(counts, dict):
                parts = []
                if counts.get("main"):
                    parts.append(f"{counts['main']} main")
                if counts.get("test"):
                    parts.append(f"{counts['test']} test")
                if counts.get("build"):
                    parts.append(f"{counts['build']} build")
                if parts:
                    facts.append({"k": title_of(str(pid)), "v": " · ".join(parts)})
    resolution = summary.get("resolution") or {}
    fails = resolution.get("failures") or []
    if kind == "resolve":
        facts.append({"k": "Classpath", "v": "resolved" if not fails else f"{len(fails)} failures"})
    tests = summary.get("tests") or {}
    if "total" in tests:
        facts.append({
            "k": "Tests",
            "v": f"{tests.get('passed', 0)} passed · {tests.get('failed', 0)} failed · {tests.get('total', 0)} total",
        })
    delta = summary.get("delta") or {}
    if isinstance(delta.get("newlyFailing"), int):
        facts.append({"k": "Vs baseline", "v": f"{delta['newlyFailing']} new failures"})
    if not summary:
        facts.append({"k": "Summary", "v": "not extracted yet"})
    if phases and not by_owner:
        facts.append({"k": "Linked work item", "v": phases[0]["title"]})
    return facts[:8]


def _run_status(meta: dict, summary: dict, exit_code) -> tuple[str, str]:
    yaml_status = str(meta.get("status") or "")
    if yaml_status == "awaiting-log" and not summary:
        return "wait", "Waiting for log"
    if yaml_status == "stale":
        return "skip", "Stale"
    if not summary:
        return "skip", "Not extracted"
    if exit_code == 0 or str(summary.get("build") or "").upper() in ("SUCCESS", "UP-TO-DATE"):
        return "done", "Passed"
    if exit_code not in (None,) or summary.get("compile", {}).get("errors"):
        return "fail", "Failed"
    if yaml_status in ("ready", "resolved"):
        return "live", "Extracted"
    return "live", "Extracted"


def collect_runs(joker: Path, items: list) -> list:
    root = joker / "verification-runs"
    if not root.is_dir():
        return []
    commit_to_phase = {}
    for it in items:
        for sha in it.get("commits") or []:
            if sha:
                commit_to_phase[str(sha)[:7]] = it
    rows = []
    for run_dir in root.iterdir():
        if not run_dir.is_dir():
            continue
        meta = load_yaml(read_text(run_dir / "run.yaml")) if (run_dir / "run.yaml").is_file() else {}
        if not isinstance(meta, dict):
            meta = {}
        summary = {}
        if (run_dir / "summary.json").is_file():
            try:
                loaded = json.loads(read_text(run_dir / "summary.json") or "{}")
                summary = loaded if isinstance(loaded, dict) else {}
            except json.JSONDecodeError:
                summary = {}
        kind = str(meta.get("kind") or summary.get("kind") or "unknown")
        m = re.search(r"-(baseline|context|resolve|compile|test|pipeline)-", run_dir.name)
        if kind == "unknown" and m:
            kind = m.group(1)
        exit_code = _exit_of(summary, run_dir)
        tone, status_label = _run_status(meta, summary, exit_code)
        phases = []
        by_owner = ((summary.get("compile") or {}).get("byOwner") or {})
        if isinstance(by_owner, dict):
            ranked = sorted(
                by_owner.items(),
                key=lambda kv: -(
                    int(kv[1].get("main") or 0) + int(kv[1].get("test") or 0) + int(kv[1].get("build") or 0)
                    if isinstance(kv[1], dict) else int(kv[1] or 0)
                ),
            )
            for pid, counts in ranked[:4]:
                n = (
                    int(counts.get("main") or 0) + int(counts.get("test") or 0) + int(counts.get("build") or 0)
                    if isinstance(counts, dict) else int(counts or 0)
                )
                phases.append({"id": pid, "title": title_of(str(pid)), "errors": n})
        if not phases:
            sha = str(meta.get("sourceCommit") or "")
            hit = commit_to_phase.get(sha[:7]) if sha else None
            if hit:
                phases.append({"id": hit["id"], "title": hit["title"], "errors": 0})
        rows.append({
            "id": run_dir.name,
            "when": _when_label(run_dir),
            "sort": _when_sort_key(run_dir),
            "kind": kind,
            "kindLabel": KIND_LABELS.get(kind, kind),
            "status": status_label,
            "tone": tone,
            "headline": _run_headline(kind, summary, exit_code),
            "phases": phases,
            "commit": str(meta.get("sourceCommit") or "")[:7],
            "facts": _run_facts(kind, meta, summary, exit_code, phases),
        })
    rows.sort(key=lambda r: r["sort"], reverse=True)
    for row in rows:
        row.pop("sort", None)
    return rows


def _item_filter(item: dict, questions_open: int) -> str:
    status = item.get("status") or "pending"
    gate = item.get("executionGate") or ""
    if questions_open:
        return "human"
    if status == "blocked":
        return "blocked"
    if gate == "SPIKE_FIRST" and status not in ("done", "n/a"):
        return "spike"
    if status == "in_progress":
        return "progress"
    if status == "done":
        return "done"
    if status == "deferred":
        return "pending"
    return "pending"


def build_snapshot(service_root: Path) -> dict:
    root = Path(service_root).resolve()
    joker = joker_dir(root)
    service = root.name
    empty = {
        "live": True,
        "missing": True,
        "service": service,
        "target": "—",
        "stage": "",
        "stageLabel": "No migration folder yet",
        "overall": "",
        "overallLabel": "Start a migration to fill this board",
        "counts": {"total": 0, "done": 0, "progress": 0, "human": 0, "blocked": 0},
        "gates": {"ask": 0, "spike": 0, "auto": 0},
        "stages": [
            {"id": "0", "name": "Baseline", "hint": "Build + tests recorded", "state": ""},
            {"id": "A", "name": "Library versions", "hint": "Classpath resolves", "state": ""},
            {"id": "B", "name": "Code fixes", "hint": "One topic, its own errors", "state": ""},
            {"id": "C", "name": "Runtime check", "hint": "Suite vs baseline", "state": ""},
            {"id": "X", "name": "Closeout", "hint": "You push the MR", "state": ""},
        ],
        "items": [],
        "inbox": [],
        "feed": [],
        "verificationRuns": [],
    }
    if not joker.is_dir():
        return empty

    status = load_yaml(read_text(joker / "status.yaml"))
    target = status.get("target") or {}
    if isinstance(target, dict):
        target_s = " / ".join(
            str(x) for x in (
                f"Spring Boot {target.get('boot')}" if target.get("boot") else None,
                f"Java {target.get('java')}" if target.get("java") is not None else None,
                f"Cloud {target.get('cloud')}" if target.get("cloud") else None,
            ) if x
        ) or "—"
    else:
        target_s = str(target or "—")

    stage = str(status.get("stage") or "")
    overall = str(status.get("overallStatus") or "")
    runs = status.get("runs") or {}
    compile_sum = _run_summary(joker, (runs or {}).get("compile"))
    context_sum = _run_summary(joker, (runs or {}).get("context"))
    context_state = _context_state(context_sum)

    items_out = []
    inbox = []
    ask = spike = auto = 0
    human_open_total = 0

    for raw in status.get("items") or []:
        if not isinstance(raw, dict):
            continue
        if raw.get("status") == "n/a":
            continue
        pid = str(raw.get("id") or "")
        slices = raw.get("slices") or {}
        blockers = raw.get("blockers") or []
        open_q = []
        closed_q = []
        for b in blockers:
            if not isinstance(b, dict):
                continue
            if b.get("resolveBy") != "human":
                continue
            title = str(b.get("question") or b.get("id") or "Question")
            row = {
                "open": b.get("status") == "open",
                "title": title,
                "from": f"{title_of(pid)} · {pid}",
            }
            if b.get("status") == "open":
                open_q.append(title)
                inbox.append(row)
            else:
                row["open"] = False
                row["answer"] = str(b.get("answer") or "")
                closed_q.append(row)
                inbox.append(row)

        note = yaml_block(read_text(joker / "phase-notes" / f"{pid}.md"))
        ver_txt = read_text(joker / "verifier" / f"{pid}.md")
        ver = (raw.get("verifier") or "n/a")
        if ver_txt:
            vdata = yaml_block(ver_txt)
            verdict = str(vdata.get("verdict") or "").lower()
            if verdict == "pass":
                ver = "pass"
            elif verdict == "rework":
                ver = "rework"
            elif verdict == "blocked":
                ver = "blocked"

        gate = str(raw.get("executionGate") or "")
        if gate == "ASK_HUMAN":
            ask += 1
        elif gate == "SPIKE_FIRST":
            spike += 1
        elif gate == "SAFE_AUTO":
            auto += 1

        st = str(raw.get("status") or "pending")
        filt = _item_filter(raw, len(open_q))
        owned = _owned(compile_sum, pid)
        human_open_total += len(open_q)
        items_out.append({
            "id": pid,
            "title": title_of(pid),
            "priority": str(raw.get("priority") or ""),
            "risk": str(raw.get("risk") or ""),
            "gate": gate,
            "filter": filt,
            "slices": {
                "A": str((slices or {}).get("A") or "pending"),
                "B": str((slices or {}).get("B") or "pending"),
            },
            "questions": {"open": len(open_q), "closed": len(closed_q)},
            "question": open_q[0] if open_q else "",
            "answer": (closed_q[0].get("answer") if closed_q else ""),
            "verifier": str(ver),
            "compileOwned": owned,
            "context": context_state if stage in ("C", "good", "closeout", "done") else "n/a",
            "status": st,
            "commits": list(raw.get("commits") or []),
            "handoff": str(raw.get("handoff") or note.get("handoff") or ""),
        })

    done = sum(1 for it in items_out if it["status"] == "done")
    progress = sum(1 for it in items_out if it["status"] == "in_progress")
    blocked = sum(1 for it in items_out if it["status"] == "blocked")
    total = len(items_out)

    order = ["planning", "0", "A", "B", "C", "good", "closeout", "done"]
    idx = order.index(stage) if stage in order else -1
    stages = []
    for sid, name, hint in (
        ("0", "Baseline", "Build + tests recorded"),
        ("A", "Library versions", "Classpath resolves"),
        ("B", "Code fixes", "One topic, its own errors"),
        ("C", "Runtime check", "Suite vs baseline"),
        ("X", "Closeout", "You push the MR"),
    ):
        map_id = "closeout" if sid == "X" else sid
        state = ""
        if idx >= 0:
            pos = order.index(map_id) if map_id in order else 99
            if stage in ("done",) and sid != "X":
                state = "done"
            elif pos < idx:
                state = "done"
            elif pos == idx or (stage == "closeout" and sid == "X"):
                state = "active"
        stages.append({"id": sid, "name": name, "hint": hint, "state": state})

    feed = []
    if compile_sum:
        owners = ((compile_sum.get("compile") or {}).get("byOwner") or {})
        bits = [f"{k} { _owned(compile_sum, k)}" for k in list(owners)[:3]]
        feed.append({
            "t": "compile",
            "title": "Compile finished",
            "body": "; ".join(bits) if bits else "Compile run recorded.",
            "c": "c-cyan",
        })
    if open_human := [q for q in inbox if q.get("open")]:
        feed.append({
            "t": "now",
            "title": "Waiting on you",
            "body": open_human[0]["title"],
            "c": "c-amber",
        })
    handoff_dir = joker / "handoffs"
    if handoff_dir.is_dir():
        latest = sorted(handoff_dir.glob("*.md"))
        if latest:
            text = read_text(latest[-1])
            reason = ""
            m = re.search(r"^reason:\s*(\S+)", text, re.M)
            if m:
                reason = m.group(1)
            feed.append({
                "t": latest[-1].stem[-6:] if len(latest[-1].stem) >= 6 else "handoff",
                "title": "Chat handoff",
                "body": reason or "Resume from disk.",
                "c": "c-violet",
            })

    inbox.sort(key=lambda q: (not q.get("open"), q.get("title") or ""))

    return {
        "live": True,
        "missing": False,
        "service": service,
        "target": target_s,
        "stage": stage,
        "stageLabel": STAGE_LABELS.get(stage, stage or "Planning"),
        "overall": overall,
        "overallLabel": OVERALL_LABELS.get(overall, overall or "—"),
        "counts": {
            "total": total,
            "done": done,
            "progress": progress,
            "human": human_open_total,
            "blocked": blocked,
        },
        "gates": {"ask": ask, "spike": spike, "auto": auto},
        "stages": stages,
        "items": items_out,
        "inbox": inbox,
        "feed": feed[:6],
        "verificationRuns": collect_runs(joker, items_out),
    }
