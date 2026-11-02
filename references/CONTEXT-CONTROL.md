# Context control — capsules, handoffs, verifier, chat reset

The orchestrator keeps the plan. Each worker gets a small capsule. `.joker/java-spring-migration/status.yaml` is the only state file; chat history is disposable.

Anything the human will read follows [SKILL.md Speak to humans](../SKILL.md#speak-to-humans): ordinary words first, file ids in parentheses. Capsules, commit subjects, and YAML keep `Stage A` / `<phase-id>` unchanged.

Phase docs keep their one-line **Handoff**. Evidence claims live only in `phase-notes/<id>.md`.

---

## Capsules

Spawn a **new** subagent per slice (A, B, or fix). Never continue a subagent that worked on another slice or phase. Before editing, it rereads every file it will change and checks `git status`.

### A slice (Stage A — build files only)

```text
Service root: <workspace>
Phase doc: <pack-root>/phases/<phase-id>.md
Slice: A — edit only build files (build.gradle*, settings.gradle*, gradle.properties,
  gradle/libs.versions.toml, gradle/wrapper/*, pom.xml, .gitlab-ci.yml for phase 37).
  Apply this phase's build steps with targets from DEPENDENCY-CATALOG.md and
  .joker/java-spring-migration/catalog-approvals.yaml. Skip every source step.
  If the phase has no build edits for this service, change nothing and report `buildEdits=none`.
Item: <status.yaml item: priority, risk, executionGate, dependsOn, filesLikely>
Resolve failures to fix (fix capsule only): read summary.json in
  .joker/java-spring-migration/verification-runs/<run-id>/ for phase <phase-id>.
  Do not expect the rows to be pasted here.
Commit subject: "<phase-id> A: <summary>"
Constraint: one repo; no Gradle/Maven; no push; no .joker commits; no browsing.
```

### B slice (Stage B — source)

```text
Service root: <workspace>
Phase doc: <pack-root>/phases/<phase-id>.md
Slice: B — the phase's source, resource, and test edits. Build edits already landed in Stage A;
  change a build file only when this phase's own compile errors require it.
Item: <status.yaml item, including closed blockers and their answers>
Predecessor handoff lines: <one line each>
Your compile errors: read errors.tsv in
  .joker/java-spring-migration/verification-runs/<run-id>/ and keep rows whose owner is <phase-id>.
  Do not expect the rows to be pasted here.
Commit subject: "<phase-id> B: <summary>"
Constraint: fix only errors owned by this phase. Do not edit a file to silence another phase's
  errors. No bridges or shims to get green (Jackson 2, compile-only jars, Vintage, JVM caps,
  disabled checks). One repo; no Gradle/Maven; no push; no .joker commits; no browsing.
```

### Fix (Stage C)

The B capsule plus the cluster files routed to this phase ([LOG-TRIAGE.md](LOG-TRIAGE.md#implementer-capsule-for-a-fix)). Commit subject `"<phase-id> fix: <summary>"`.

After each slice the orchestrator keeps `status.yaml` and the new handoff line. A worker reports that line and the files it touched, not the error list or a diff. If the worker writes a line the human will see, it uses the phase title (for example "Jackson 3 JSON"), not "phase 04" alone. The orchestrator does not paste `raw.log`, `summary.json`, `errors.tsv`, or `tests.tsv` into the chat or into a capsule.

Parallelism: Stage A is always serial (every slice touches build manifests). In Stage B and C, at most **2** writers, only with disjoint `filesLikely` and no shared build manifest. A verifier is read-only and runs after the writer.

---

## Phase notes

One current YAML block per phase in `phase-notes/<id>.md`. Replace it on each slice; older slices go in dated prose above it.

```yaml
phase: 04-jackson-3
status: done | blocked | deferred
slices: { A: done | none, B: done | n/a }
commits: ["<sha>"]          # parent fills the real SHA after committing
filesTouched: []            # product and build files only; never .joker/**
handoff: "jackson3=sole; wireContracts=green|approved-diff|blocked"
claims:
  - claim: "Application Jackson 2 databind coordinates are gone"
    evidence: observed
    sources: ["build.gradle:42"]
  - claim: "Main and test compile"
    evidence: run
    sources: ["verification-runs/20261023T120000Z-compile-a1b2c3d"]
  - claim: "Wire JSON matches the pre-migration baseline at runtime"
    evidence: unverified
    check: "Stage C contract tests"
notes: ""
```

| Evidence | Meaning |
|----------|---------|
| `observed` | Read from an in-repo file or diff this turn. `sources` names the file and line. Jar internals and web pages are not `observed`. |
| `run` | A verification run supports it. `sources` names the run directory. |
| `unverified` | Waits for a later run. `check` names it. These are listed once at the end of Stage C, not per phase. |

A missing fact is not a claim. It is a blocker on the item in `status.yaml`.

Rules:

- A handoff token that contradicts an `observed` claim in the same note is a defect.
- Predecessor handoff tokens are not facts. Re-check them against HEAD before relying on them.
- One phase id per commit. A commit that must span two phases lists the other id in both notes under `notes`.

---

## Readiness

Every item in `status.yaml` carries `readiness` and `blockers`. A blocker is a named unknown that would change what the implementer writes:

```yaml
blockers:
  - id: B-04-1
    question: "Which enums cross an HTTP or message boundary?"
    resolveBy: repo | human | lookup
    status: open | closed | deferred
    answer: "OrderStatus, PaymentState (src/main/java/.../dto)"
```

- The orchestrator raises blockers from the phase's Detect and Steps while planning, and again just before spawning the slice.
- It closes `repo` blockers itself by grep or reading code, `lookup` blockers through the bounded ladder ([COMPILE-GATES.md](COMPILE-GATES.md#bounded-external-lookup)), and asks the human only for `human` blockers.
- `readiness: ready` means every blocker is `closed` or `deferred` by the human. Only then is a slice spawned.
- An implementer that finds a new unknown stops, reports it as a blocker, and does not guess. The orchestrator adds it and sets `readiness: blocked`.

---

## Independent verifier

A fresh, read-only subagent that did not implement the phase. It does not edit, commit, or run builds. Compile, resolution, context startup, and test results are proven by runs, not by the verifier.

Run it immediately after the B slice (or the fix) of a phase that can change behavior while every build stays green:

| Phase | What it checks |
|-------|----------------|
| [04-jackson-3](../phases/04-jackson-3.md) | Wire baseline compared; every diff accepted or fixed on the Jackson 3 mapper |
| [03-hibernate-7](../phases/03-hibernate-7.md), [33-jpa-spring-data](../phases/33-jpa-spring-data.md) | Session/merge semantics, generator allocation, no schema edits without approval |
| [08-flyway-db](../phases/08-flyway-db.md) | Only when SQL or locations changed |
| [18-config-properties](../phases/18-config-properties.md) | Only when route matching changed (`ant_path_matcher`, empty segments) |
| [20-spring-security-7](../phases/20-spring-security-7.md) | Filter chain, CSRF, matcher semantics |
| [34-spring-cloud-gcp](../phases/34-spring-cloud-gcp.md) | Bootstrap, auth, non-Pub/Sub futures |
| [43-pubsub](../phases/43-pubsub.md) | Ack-lease decision, converter wired to Boot's `JsonMapper`, health contributor |
| [35-webflux](../phases/35-webflux.md) | Codecs, allocator decision |
| [41-spring-retry-framework](../phases/41-spring-retry-framework.md) | Attempt counts, recovery |
| [44-spring-kafka-4](../phases/44-spring-kafka-4.md) | Serializer mapper is Jackson 3; `group.protocol` unchanged unless approved |
| [11-distributed-lock](../phases/11-distributed-lock.md) | Lock key, TTL, scheduler |
| [09-testing](../phases/09-testing.md) | Only when production error bodies changed |

Capsule: this document, the target contract, the phase doc, the phase diff, `phase-notes/<id>.md`, `catalog-approvals.yaml`, the item's closed blockers, and only the files cited in `claims` and `filesTouched`.

It checks:

1. The phase's **Do not** list and [99-anti-patterns.md](99-anti-patterns.md) were not violated.
2. Every behavior change in the diff was approved (closed blocker or `catalog-approvals.yaml`) or is listed as `unverified` for Stage C.
3. The diff stays inside the phase.
4. Every `observed` claim matches its cited line at HEAD.

Each finding quotes the line it objects to.

```yaml
verdict: PASS | REWORK | BLOCKED
phaseIds: ["04-jackson-3"]
findings:
  - severity: blocker | should-fix | note
    quote: "src/main/java/.../JsonConfig.java:31  .disable(WRITE_ENUMS_USING_TO_STRING)"
    issue: ""
humanDecisionNeeded: false
```

`REWORK` goes to a fresh implementer for that phase (max two rounds, then `blocked`). Only `BLOCKED` with `humanDecisionNeeded: true` reaches the human. Write the verdict to `verifier/<phase-id>.md` and set `verifier` on the item.

---

## Chat reset — new-chat handoff

### Hard triggers

| Trigger | Action |
|---------|--------|
| Any build, test, or pipeline log is pasted into chat | Do not analyze it. Point at a verification run. Write a handoff. Ask for a new chat. |
| A stage gate just passed (0, A, B, C) | Write a handoff. Ask for a new chat. |
| Four build runs completed in this chat | Write a handoff. Ask for a new chat. Do not start a fifth run or another slice. |
| Two fix rounds on the same root cause in this chat | Write a handoff before a third attempt. |
| Conflicting memory of the same file | Stop editing. Write a handoff. Ask for a new chat. |

### Handoff file

`.joker/java-spring-migration/handoffs/<YYYYMMDDTHHMMSSZ>.md` — short, no logs, no diffs:

```markdown
# Chat handoff <timestamp>

reason: pasted-log | stage-gate | run-batch | fix-limit | context-conflict | waiting-human
stage: 0 | A | B | C | good | closeout
sourceCommit: <short-sha>

## Next action
<one concrete step; if the next item is blocked, name the blocker to close first>

## Blockers for that action
- <only those>
```

Set `latestChatHandoff` in `status.yaml` to that file.

### Resume prompt for the human

```text
Resume the Boot 4 migration using <path-to-pack>/SKILL.md.
Read .joker/java-spring-migration/status.yaml and the latest file under
.joker/java-spring-migration/handoffs/. Do not rely on prior chat history.
```

After a pasted log, add: `A log was pasted earlier by mistake — ignore it. I will reply "Verification run <run-id> is ready."`

---

## What reaches the human

Phrase every item in this list so a reader who does not know the pack still understands it ([SKILL.md Speak to humans](../SKILL.md#speak-to-humans)).

1. Catalog-gap enhance chat when blocking gaps exist ([CATALOG-GAP.md](CATALOG-GAP.md)).
2. Plan approval (plain-language table).
3. `human` blockers, asked as real questions, not phase numbers.
4. Pre-existing baseline failures, once.
5. The full test suite at the baseline and at the runtime check (Stage C). CI stays with the human.
6. Tier gates: the delta against the baseline and the accumulated `unverified` claims.
7. Verifier `BLOCKED` with `humanDecisionNeeded: true`.
8. Chat-reset requests with the resume prompt.
