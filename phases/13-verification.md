# 13 — Verification (Stage C)

## Detect

Always, once Stage B's gate passes: the compile has zero errors and every Stage B item is `done` or `skipped` ([COMPILE-GATES.md](../references/COMPILE-GATES.md#stage-gates)).

## Philosophy

The orchestrator runs the context-load test with the pinned command. The human runs the full suite, the same command as the Stage 0 baseline, and the orchestrator compares that result with the baseline. The agent never runs the suite.

A successful compile or package is necessary but not sufficient for claiming production readiness. Treat the upgrade as a staged runtime migration when the human wants that bar.

## Levels (apply as far as the human asks)

1. **Context load:** `commands.context` (the context-load test from [42-baseline.md](42-baseline.md)).
2. **Full suite:** `commands.baseline`, which runs every test task the baseline ran.
3. **Runtime smoke:** start each deployable and exercise representative API, security, JSON, DB, and observability paths.
4. **Container / platform:** the actual image, env, probes, and rollout ([stubs/jvm-containers.md](../stubs/jvm-containers.md), [stubs/k8s-startup.md](../stubs/k8s-startup.md)).

## Steps

1. Run `kind: context` on JDK 25 with the pinned command. When it fails, triage it ([LOG-TRIAGE.md](../references/LOG-TRIAGE.md)) and route the clusters. Do not ask for the full suite until the context loads.
2. The human runs `kind: test`. Extract it with `--baseline <baselineRun>`. The delta lists `newlyFailing`, `fixed`, `missing`, and `added`.
3. Triage and route `newlyFailing` and `missing`. `stillFailing` rows match the baseline and are not migration work.
4. Repeat until `newlyFailing=0` and every `missing` row is explained (renamed, deliberately removed, or undiscovered and fixed).
5. Skim build output for Jackson 2 `[removal]` warnings. They should be gone after phase 04.
6. If coverage gates fail on OpenAPI generator support types, exclude `org.openapitools.**` (see [05-openapi-generator.md](05-openapi-generator.md)). Do not lower global thresholds.
7. On linkage or missing-class failures, use [stubs/dependency-diagnosis.md](../stubs/dependency-diagnosis.md).
8. Do not edit CI or runtime images. Compiler and test JVM for agent runs use `JAVA_HOME` from the pinned command ([COMPILE-GATES.md](../references/COMPILE-GATES.md)).
9. Confirm phase 04's wire-contract evidence against the baseline captured in Stage 0: representative HTTP and message payloads, risky literal values, and every hand-built mapper. Reusable failure patterns belong in [MIGRATION-EVIDENCE.md](../references/MIGRATION-EVIDENCE.md), not service-specific notes.
10. Keep `MigrationContextLoadsTest` when phase 42 added it. It is the fastest future signal that the context still loads.

## Do not

- Block the migration on flaky env-specific integration suites the baseline already marked failing.
- Expand scope into performance testing.
- Claim "migration complete" when only compile is green and the human asked for runtime or deploy verification.
- Disable CSRF, TLS, DB migrations, or Cloud compatibility checks as a generic fix.
- Delete or `@Disabled` a test to clear `newlyFailing`.

## Risk

`SAFE_AUTO` for the context and suite runs. Runtime and container levels follow the human's request (`ASK_HUMAN` for prod-like smoke).

## Rollback

N/A

## Done when

The latest `kind: test` run's delta shows `newlyFailing=0` and every `missing` row explained; the context run passed; every run in `status.yaml` `runs` has its status set (`summarized` or `stale`); any runtime or container level the human asked for is recorded with commands and outcomes.

## Handoff

`contextRun=<run-id>:pass; testRun=<run-id>; delta=newlyFailing:0,missing:N-explained,fixed:N; runtimeSmoke=ran|skipped; notes=…`
