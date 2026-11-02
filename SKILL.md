# SKILL — Spring Boot 4 + Java 25 migration orchestrator

**On-demand only.** This pack is the `Java-boot4-migration/` folder, not a global Cursor skill. A human points a chat at this file when they want a migration.

**The orchestrator reads:** this file, [PHASE-CATALOG.md](references/PHASE-CATALOG.md), [CONTEXT-CONTROL.md](references/CONTEXT-CONTROL.md), [COMPILE-GATES.md](references/COMPILE-GATES.md), and [99-anti-patterns.md](references/99-anti-patterns.md) once. [LOG-TRIAGE.md](references/LOG-TRIAGE.md) only in Stage C. Workers get one phase doc in a capsule.

**Never read** `MANUAL.md` or `CONTRIBUTING.md`. To extend the pack, use [AGENT.md](AGENT.md).

---

## Invoke (human)

From a chat whose workspace is the service under migration:

```text
Plan and migrate this service to Java 25 / Spring Boot 4 using <path-to-pack>/SKILL.md
```

Optional pins (skip the target questions when present):

```text
Target: Boot 4.1.x, Java 25, Spring Cloud 2025.1.x
Defer: WireMock 4, Cucumber 8 until after the must tier
```

---

## How the migration runs

Half-migrated dependencies break unrelated code, so the migration does not try to keep the build green phase by phase. It moves in four stages:

| Say this to the human | What changes | Gate | File id |
|-----------------------|--------------|------|---------|
| **Baseline** | Nothing, except one context-load test if missing | Full build and context test recorded on the old code | Stage 0 |
| **Library versions** | Build files only, one commit per work item | Gradle configures and every classpath resolves | Stage A |
| **Code fixes** | Source, resources, tests, one topic at a time | Each topic clears the compile errors it owns; the stage ends when compile is green | Stage B |
| **Runtime check** | Fixes found by running | Context loads; full suite has no new failures against the baseline | Stage C |

The good tier repeats library versions → code fixes → runtime check for good items after the must tier passes.

### Speak to humans

Every message the human reads uses ordinary words first. File ids (`Stage A`, `35-webflux`) stay in YAML, commits, capsules, and handoffs. They are not how you talk.

- Never lead with "Stage A/B/C", "phase 35", or a bare number. Say what is happening, then the id in parentheses if a specialist needs it.
- Name a work item from the words after the number in `phases/NN-short-name.md`: **WebFlux** (`35-webflux`), **Jackson 3 JSON** (`04-jackson-3`), **JUnit 6** (`36-junit-jupiter`). The number is a stable id, not an order, and never a sentence on its own.
- Status and blockers: "I need a decision on how error response bodies should look (`09-testing`)" — not "ASK_HUMAN on phase 09."
- Plan table columns: **What we'll do** | **Why it applies** | **Your decision?** | Id (last). Wait for approval.
- First reply in a migration chat: one short map of the four stages in the table above. Do not quiz the human on pack jargon.

Examples:

- Bad: "Starting Stage A. Phase 35 then phase 04."
- Good: "Next I will update library versions in the build files (Stage A). First: WebFlux (`35-webflux`), then Jackson 3 JSON (`04-jackson-3`). The app is not expected to compile until we fix source later (code fixes / Stage B)."

---

## Hard rules

1. **One repo only.** Never open sibling services.
2. **Builds.** Only the parent starts a build. It runs the pinned Gradle or Maven command with output redirected into the verification run directory, then runs `scripts/extract_run.py`. It never opens `raw.log` and never runs the full test suite. The human runs `baseline` and Stage C `test`, and runs CI. Procedure: [COMPILE-GATES.md](references/COMPILE-GATES.md).
3. **Logs stay on disk.** The parent keeps the extractor's one summary line per run and never opens `raw.log`, `summary.json`, or the tsv files. After four runs in one chat it writes a handoff and stops ([CONTEXT-CONTROL.md](references/CONTEXT-CONTROL.md#chat-reset--new-chat-handoff)). A pasted log triggers the same reset.
4. **Ready before code.** No slice is spawned while its item has an open blocker ([Readiness](references/CONTEXT-CONTROL.md#readiness)). Workers that hit a new unknown stop and report it; they never guess.
5. **Own your errors only.** A worker fixes the errors its phase owns. It never edits a file to silence another phase's errors, and never adds bridges or shims to get green (Jackson 2, compile-only jars, Vintage, JVM caps, disabled checks).
6. **Versions come from** [DEPENDENCY-CATALOG.md](references/DEPENDENCY-CATALOG.md) and the migration's `catalog-approvals.yaml`. `approved` rows apply without asking. Do not research a pinned coordinate again.
7. **Direct Jackson 3.** Boot 4 never runs application JSON through `spring-boot-jackson2` ([04](phases/04-jackson-3.md)).
8. **Commits.** One phase id per commit, subject `<phase-id> <A|B|fix>: <summary>` (the extractor attributes build errors by that prefix). Never push. Never commit `.joker/` or a `.gitignore` edit for it.
9. **Fresh worker per slice.** Stage A is serial. Elsewhere, at most two writers with disjoint files and no shared build manifest.
10. **Catalog gap gate** before plan approval ([CATALOG-GAP.md](references/CATALOG-GAP.md)).
11. **Bounded lookup** only through the ladder in [COMPILE-GATES.md](references/COMPILE-GATES.md#bounded-external-lookup).
12. **Speak to humans** in the section above. Jargon-only updates are an anti-pattern ([99-anti-patterns.md](references/99-anti-patterns.md) 41).

An upstream version the human already named is a gate on this repository. Do not open other repositories to discover one.

---

## Item fields

| Field | Values |
|-------|--------|
| `priority` | `must` (required for Boot 4 / Java 25), `good` (after the must tier), `bad` (only on an explicit human request) |
| `risk` | `low` \| `medium` \| `high` — blast radius |
| `executionGate` | `SAFE_AUTO` \| `ASK_HUMAN` \| `SPIKE_FIRST`, from the phase's Risk section |
| `readiness` / `blockers` | `ready` only when no blocker is open |
| `dependsOn`, `filesLikely` | Phase ids; globs |

Defaults and conditional priorities are in [PHASE-CATALOG.md](references/PHASE-CATALOG.md). Seed `bad` list: WireMock 4 while beta, any Jackson 2 bridge, Undertow on Boot 4, disabling CSRF/TLS/migrations to get green, classic starters as an end state, a Jupiter 5 or Platform 1.x pin kept because tests already import `org.junit.jupiter`.

---

## Workspace (`.joker/java-spring-migration/`, never committed)

```text
00-target-contract.md      # Boot / Java / Cloud pins and deferrals
01-intake.md               # Detect inventory
catalog-map.yaml, catalog-gaps.yaml, catalog-gaps.md, catalog-approvals.yaml, enhance-prompts.md
status.yaml                # the only state file: plan, readiness, blockers, runs, progress
phase-notes/<phase-id>.md  # one current handoff YAML per phase
baseline/                  # Stage 0 captures (wire probes, allocator, …)
verification-runs/<run-id>/
verifier/<phase-id>.md
handoffs/<timestamp>.md
findings.md                # deferrals, residual risk, ownership and pack gaps
```

Add `.joker/` to `.gitignore` locally if missing; do not commit that edit. When the human wants a readable view, print a table from `status.yaml`; do not keep a second state file.

### `status.yaml`

```yaml
target: { boot: "4.1.x", java: 25, cloud: "2025.1.x", kotlin: "2.3.21" }
stage: planning | 0 | A | B | C | good | closeout | done
overallStatus: planning | waiting-catalog-gaps | waiting-plan-approval | executing | waiting-human | waiting-new-chat | done
planApprovedAt: null
baselineCommit: null
baselineJdk: null
commands: { baseline: "", context: "", resolve: "", compile: "" }
suiteRunner: human               # baseline and Stage C test. Never the agent
runs: { baseline: null, context: null, resolve: null, compile: null, test: null }
latestChatHandoff: null
catalogGapStatus: open | waiting-enhance | ready | n/a
items:
  - id: 04-jackson-3
    order: 4
    priority: must
    risk: medium
    executionGate: ASK_HUMAN
    dependsOn: ["01-platform-baseline"]
    filesLikely: ["src/**/*Json*", "build.gradle*"]
    readiness: ready | blocked
    blockers: []            # shape in CONTEXT-CONTROL.md#readiness
    slices: { A: pending | done | none, B: pending | done | n/a }
    status: pending | in_progress | done | blocked | deferred | n/a
    commits: []
    verifier: required | pass | rework | blocked | n/a
    handoff: ""
    notes: ""
```

---

## Orchestration loop

### 1. Target contract

Write `00-target-contract.md` from the invoke message, or ask briefly. Boot 4.1 with Java 25 means Kotlin 2.3.x when `*.kt` exists.

### 2. Intake

Run [00-intake.md](phases/00-intake.md). Write `01-intake.md` and the `commands` block.

### 3. Catalog gap preflight

Follow [CATALOG-GAP.md](references/CATALOG-GAP.md). Do not present the plan while a `blocksPlan` gap is open.

### 4. Plan

Write `items` into `status.yaml` in PHASE-CATALOG order: fields above, plus blockers raised from each applicable phase's Detect and Steps. Close `repo` blockers now by reading code. Schedule [23-over-engineer-gate](phases/23-over-engineer-gate.md) only when the human asks or the Stage B (code fixes) diff is large. List `bad` items as deferred. Present the plan as a human-readable table ([Speak to humans](#speak-to-humans)) and wait for approval. Set `planApprovedAt`.

### 5. Stage 0 — baseline

Spawn [42-baseline.md](phases/42-baseline.md). The human runs `kind: baseline`. The parent runs `kind: context` ([COMPILE-GATES.md](references/COMPILE-GATES.md#stage-0--baseline)) on the old JDK. Pre-existing failures go to the human once. Reset the chat.

### 6. Stage A — dependency wave

For each must item in order: if it is not ready, close its blockers first. Spawn an A slice. Commit `<phase-id> A: …`, or record `slices.A: none`. After each commit, run `kind: resolve` and route any failure to a fresh A-slice fix for the attributed phase. The stage is done when `resolve` is green after the last slice. Compile is expected to fail. Reset the chat.

### 7. Stage B — source phases

For each must item in order (main-side phases before test-side ones):

1. Close blockers until `readiness: ready`.
2. Spawn a B slice naming the latest compile run. The worker reads its own rows from that run's `errors.tsv`.
3. Commit, run `kind: compile`, and apply the ownership table in [COMPILE-GATES.md](references/COMPILE-GATES.md#stage-b--source-phases). The table decides done, retry, reopen, or ignore.
4. Write the handoff into `phase-notes/<id>.md` and `status.yaml`. Fill in the real commit SHA.
5. Run the verifier when the phase is on the behavior list in [CONTEXT-CONTROL.md](references/CONTEXT-CONTROL.md#independent-verifier).
6. Reset the chat on any hard trigger.

The stage is done when `compile` exits 0. Reset the chat.

### 8. Stage C — runtime

Run the context test with the pinned command. The human runs the full suite. Compare it with the baseline ([COMPILE-GATES.md](references/COMPILE-GATES.md#stage-c--runtime)). Cluster and route failures through [LOG-TRIAGE.md](references/LOG-TRIAGE.md). A good or missing phase that turns out to be the fix joins the must tier immediately. The must tier passes when the context loads, `newlyFailing=0`, every `missing` test is explained, and the human has seen the accumulated `unverified` claims.

### 9. Good tier

Repeat stages A → B → C for `good` items. Then the same gate.

### 10. Closeout

Update `findings.md` and `status.yaml`: done, deferred, residual risk, commits (not pushed), ownership gaps. The migration cannot close while `spring-boot-jackson2`, `spring.jackson2.*`, application-owned Jackson 2 databind, `junit:junit`, `junit-vintage-engine`, or a service pin of `org.junit.jupiter` / `org.junit.platform` remains. Resolved JUnit is the Boot BOM line (**6.0.3** on Boot **4.1.1**), from [36-junit-jupiter.md](phases/36-junit-jupiter.md). A suite that already imports `org.junit.jupiter` does not satisfy that. Leave `MigrationContextLoadsTest` in place unless the human removes it. Generic, verified fixes become notes for an enhance pass against [MIGRATION-EVIDENCE.md](references/MIGRATION-EVIDENCE.md); do not edit the pack from a service migration unless asked.

---

## Phase steps that mention the human

A phase step that says "ask the human to compile" means the orchestrator's next compile run covers it. A step that asks the human to run the application, a container, or a smoke against real infrastructure becomes a Stage C check, or an `unverified` claim when the environment cannot run it.

---

## Done when

- The baseline exists, and the Stage A, B, and C gates passed for the must tier (and the good tier if any good work landed).
- Every `must` item is done or explicitly deferred by the human; `bad` items ran only on request.
- Required verifiers are `pass`; no open `REWORK`.
- `status.yaml` and `findings.md` are current; nothing under `.joker/` is committed; commits exist locally and are not pushed.
