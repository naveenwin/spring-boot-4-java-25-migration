# Log triage — Stage C failure clustering and routing

Stage C runs (`kind: context`, `test`, `pipeline`) fail for runtime reasons the compiler cannot see. The extractor ([COMPILE-GATES.md](COMPILE-GATES.md#reading-the-result)) gives counts and the baseline delta; the log triager turns failing tests into root-cause clusters; the parent routes clusters to phases. Configure, resolution, and compile failures never come here. They are routed by attribution and [ownership.json](ownership.json).

The parent never loads `raw.log`. A phase implementer never reads it either; it receives cluster files.

---

## Run layout

```text
verification-runs/<run-id>/
  run.yaml  started-at.txt  raw.log  exit-code.txt     # run procedure in COMPILE-GATES.md
  summary.json  tests.tsv  delta.tsv                    # extractor
  triage.yaml  triage.md  clusters/C001.md              # log triager
  routing.yaml                                          # parent
```

Exactly one Gradle or Maven process writes a run. Mark the run `stale`, discard its `routing.yaml`, and request a clean run when:

1. overlap or concurrent writes are suspected, or
2. triage shows mass `NoClassDefFoundError` together with Kotlin-daemon or `EOFException` fingerprints.

Do not salvage clusters from a stale run.

---

## Log triager

A fresh, read-only subagent. Capsule:

- this document
- `run.yaml`, `exit-code.txt`, `summary.json`
- `delta.tsv` rows for `newlyFailing` and `missing` (only these need a cause; `stillFailing` matches the baseline)
- the plan's phase ids and handoff lines
- [MIGRATION-EVIDENCE.md](MIGRATION-EVIDENCE.md) titles only, until a symptom matches
- permission to search `raw.log` and the failing tests' XML reports, reading bounded ranges

Search for `Caused by`, the first failure under `Failed to load ApplicationContext`, and failed test names. Do not load the log in one read.

An ApplicationContext failure under Cucumber or `@SpringBootTest` is **one** cluster even when 300 scenarios fail. Read the first root `Caused by:`; pickle repeats, hook wrappers, and failure-threshold skips are the same cause.

`missing` tests are a cluster of their own: a test that existed in the baseline and no longer runs was either renamed (parameterized display names), deliberately removed, or silently undiscovered (JUnit 4 classes without Vintage). Name which.

```yaml
runId: 20261023T120000Z-test-a1b2c3d
sourceCommit: a1b2c3d
summary: { newlyFailing: 100, missing: 4, rootCauseClusters: 3, infrastructureClusters: 1 }
clusters:
  - id: C001
    count: 62
    layer: context | unit | integration | runtime | discovery | infrastructure
    rootCause: "Enum serialization changed"
    candidatePhases:
      - { id: 04-jackson-3, likelihood: high }
    cascadeOf: null
    filesLikely: ["src/main/java/**/Json*.java"]
    sharedBuildFiles: false
    codeChangeRecommended: true
```

Each `clusters/C00N.md` holds the count, a few affected tests, one or two causal stacks, the normalized root cause, source locations, `raw.log` line ranges, and the candidate phase. Redact tokens, passwords, and authorization headers. `triage.md` is a few lines: counts, cluster ids, phase ids, infrastructure yes/no. No stacks.

---

## Parent routing

The parent reads `triage.yaml` and `triage.md` only, and writes `routing.yaml`.

1. Drop `codeChangeRecommended: false` clusters. Tell the human once if infrastructure must be fixed before a rerun.
2. A code cluster with no candidate phase becomes a `triage_unmapped` row in `catalog-gaps.yaml` ([CATALOG-GAP.md](CATALOG-GAP.md)), or a `findings.md` pack gap when it is not a dependency. Do not invent a version.
3. When a cluster's top two candidates are equally likely and the fixes differ in behavior, ask the human which phase owns it.
4. Order clusters: context, unit, integration, runtime. Ties follow `dependsOn`, then catalog Order.
5. A cluster marked `cascadeOf` another waits for a new run that shows it still fails.
6. Group the remaining clusters by phase. One phase is one fix task, however many clusters it has, with a fresh implementer. The parent never fixes code itself.
7. At most two tasks run in parallel, and only when neither is a cascade of the other, their `filesLikely` do not overlap, and neither touches a shared build manifest. Otherwise run them one after the other; the second rereads files after the first commit.

```yaml
runId: 20261023T120000Z-test-a1b2c3d
waves:
  - wave: 1
    tasks:
      - { phase: 03-hibernate-7, clusters: [C001, C003] }
      - { phase: 09-testing, clusters: [C002] }
  - wave: 2
    tasks:
      - { phase: 20-spring-security-7, clusters: [C004], state: pendingConfirmation }
```

After the wave commits, run the verifier where [CONTEXT-CONTROL.md](CONTEXT-CONTROL.md#independent-verifier) requires it, mark the run `stale`, and start a new run (context first if any context cluster was fixed).

Stop after **two** fix-and-rerun rounds on the same root cause. Mark the phase `blocked` and ask the human.

### Implementer capsule for a fix

```text
Phase doc: <one phase>
Cluster files: verification-runs/<run-id>/clusters/C00N.md
Predecessor handoff lines; filesLikely from the clusters
Commit subject: "<phase-id> fix: <summary>"
Constraint: fix this root cause only; no Gradle/Maven; no push; no browsing (ask the parent for a bounded lookup)
Do not read raw.log. If a cited range is needed, read only that range.
```

Each fix adds a claim `evidence: unverified` naming the next run. A stale run supports nothing.
