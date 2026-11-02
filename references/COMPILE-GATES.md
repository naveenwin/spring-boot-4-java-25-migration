# Build gates, ownership, and bounded lookup

How the orchestrator proves each stage with a build, and how it routes what the build reports. Test-failure clustering in Stage C is [LOG-TRIAGE.md](LOG-TRIAGE.md). Extend this file rather than adding parallel docs.

---

## Commands (pinned at intake)

Intake records these in `status.yaml` under `commands`. Every run reuses the exact string. A phase that changes the build layout updates the command and says so in its handoff.

| Key | Gradle default | Maven default | Used in |
|-----|----------------|---------------|---------|
| `baseline` | `./gradlew cleanTest test` (add `clean<Task> <task>` for each extra test task the service runs, e.g. `cleanCucumberTest cucumberTest`) | `mvn -B clean verify` | Stage 0, Stage C |
| `context` | `./gradlew test --tests '<package>.MigrationContextLoadsTest'` | `mvn -B -Dtest=MigrationContextLoadsTest -Dsurefire.failIfNoSpecifiedTests=false test` | Stage 0, Stage C |
| `resolve` | `./gradlew --init-script <pack-root>/scripts/migration.init.gradle --no-configuration-cache --continue migrationResolve` | `mvn -B -q dependency:resolve dependency:resolve-plugins` | Stage A |
| `compile` | `./gradlew --init-script <pack-root>/scripts/migration.init.gradle --continue testClasses` | `mvn -B -fae test-compile` | Stage B |

Multi-module or unusual builds: replace `testClasses` with `:<module>:testClasses` or the explicit `compile*` tasks listed by `./gradlew tasks --group=build`. Do not use `compileKotlin` alone; it skips Java sources.

The init script lifts the javac 100-error cap and adds `migrationResolve`. It lives in the pack, so the service build files stay untouched. Maven keeps javac's cap; the next compile shows the rest.

---

## Running a build

Only the orchestrator starts a build, and only one at a time. Implementers and verifiers never do.

The agent runs the pinned Gradle or Maven command itself. Redirect stdout and stderr into the run directory. Do not paste the log into the chat, and do not open `raw.log`.

```bash
RUN=".joker/java-spring-migration/verification-runs/<run-id>"
mkdir -p "$RUN"
date -u +%s > "$RUN/started-at.txt"
JAVA_HOME="<jdk>" PATH="$JAVA_HOME/bin:$PATH" <pinned command> > "$RUN/raw.log" 2>&1
echo $? > "$RUN/exit-code.txt"
```

`<jdk>` is `baselineJdk` in Stage 0 and JDK 25 from Stage A on. On Gradle `resolve` and `compile`, pass the init script as an absolute `--init-script` path and add `--no-daemon`. Never change the developer's default SDK.

The agent runs `resolve`, `compile`, and `context`. It does not run the full suite. Refused agent tasks: `check`, `build`, `cucumberTest`, `integrationTest`, `test` without exactly one `--tests` class, and any `--tests` value that contains `*`. Context load is one test class.

`kind: baseline` and `kind: test` are the human, with the same redirect. The human replies `Verification run <run-id> is ready.` The agent then runs only the extractor.

```bash
RUN=".joker/java-spring-migration/verification-runs/<run-id>"
mkdir -p "$RUN"
date -u +%s > "$RUN/started-at.txt"
JAVA_HOME="<jdk>" PATH="$JAVA_HOME/bin:$PATH" <commands.baseline> > "$RUN/raw.log" 2>&1
echo $? > "$RUN/exit-code.txt"
```

After `exit-code.txt` exists and the run is not truncated, the orchestrator runs:

```bash
python3 "<pack-root>/scripts/extract_run.py" --run-dir "$RUN" --repo . \
  [--baseline ".joker/java-spring-migration/verification-runs/<baseline-run-id>"]
```

`<run-id>` is `YYYYMMDDTHHMMSSZ-<kind>-<short-sha>`. Write `run.yaml` first:

```yaml
runId: 20261023T120000Z-compile-a1b2c3d
kind: baseline | context | resolve | compile | test | pipeline
sourceCommit: a1b2c3d
command: "<the pinned command>"
status: awaiting-log | ready | resolved | stale
```

### Reading the result

The parent keeps the one line the extractor prints. It does not open `raw.log`, `summary.json`, `errors.tsv`, or `tests.tsv`, and it does not paste them into the chat. A worker that needs rows reads the file named in its capsule.

Each run of this block counts toward the four-run chat limit in [CONTEXT-CONTROL.md](CONTEXT-CONTROL.md#chat-reset--new-chat-handoff), whether the parent ran it or the human did. `baseline`, `context`, `resolve`, `compile`, `test`, and `pipeline` all count. After the fourth line is in the chat, the parent writes the handoff and stops.

The extractor writes:

| File | Content |
|------|---------|
| `summary.json` | build outcome, configure blocks, resolution failures with owning phase, compile errors per owner with three samples, compile tasks that ran, test counts, and the baseline delta |
| `errors.tsv` | every compile error: `owner`, `scope` (main/test/build), `file:line`, message |
| `tests.tsv` | every test case and its status |
| `delta.tsv` | `newlyFailing`, `fixed`, `missing`, `added`, `stillFailing` against the baseline |

A missing `exit-code.txt` is not a result. Set `status: ready` once it exists, `resolved` when the stage gate below passes, and `stale` after any fix commit.

---

## Stage gates

### Stage 0 — baseline

Two runs at `baselineCommit` on `baselineJdk`. The human runs `kind: baseline` (the full suite). The orchestrator runs `kind: context` with the pinned command. Record both run ids in `status.yaml` `runs`. The baseline `tests.tsv` is the comparison point for the Stage C suite. Do not rerun the suite after migration commits exist.

### Stage A — dependency wave

After every A-slice commit, run `kind: resolve`. The stage gate is green when configure succeeds and every classpath resolves. Compile errors are expected and are not checked.

Configure and resolution failures belong to Stage A. The extractor attributes a build-script line or an unresolved coordinate to the phase id in the subject of the commit that last touched it (`git blame`). Route each failure to a fresh A-slice implementer for that phase. A failure attributed to `build-script:unattributed` predates the migration; the orchestrator assigns it to the phase whose build edits made it surface.

### Stage B — source phases

After every B-slice commit, run `kind: compile`. The owner counts on the extractor line (`04-jackson-3:22`) are enough to apply this table. The worker reads the rows.

| Count on the extractor line | Meaning | Action |
|-----------------------------|---------|--------|
| Errors owned by the phase that just ran | Not finished | Same phase, fresh implementer. It reads its rows. Two rounds, then `blocked` |
| Zero for that phase | Done for now | Mark done; continue |
| Errors owned by a later phase | Expected | Ignore |
| Errors owned by a done phase | Reopened | Fresh implementer for the owning phase. It reads its rows |
| `unowned` | Unknown owner | A fresh worker reads those rows, names an owner, and stops. The orchestrator records that owner in the item's `notes` and adds an ownership gap to `findings.md` |

Zero owned errors is provisional while a compile task that covers the phase's files did not run. Gradle skips Java when Kotlin fails in the same module, and skips test compilation while main fails. `compile.tasksRan` shows what ran. Later errors reopen the phase through the table above.

The stage gate is green when `compile` exits 0. Main and test compile are proven at that commit, and claims can cite the run id.

### Stage C — runtime

1. `kind: context` with the pinned command. Fix failures through [LOG-TRIAGE.md](LOG-TRIAGE.md). Re-run after each fix wave.
2. When the context loads, the human runs `kind: test` with the `baseline` command. The orchestrator extracts it with `--baseline`. Stage C needs `newlyFailing=0` and every `missing` name explained (renamed parameterized display names, deleted JUnit 4 duplicates) or accepted by the human. The agent does not run this suite.
3. Pipeline runs stay human-led (`kind: pipeline`).

---

## Bounded external lookup

Phases and the catalog cover most work. When a pattern is missing, the parent orchestrator (or one read-only lookup subagent) follows this ladder. Implementers request answers through their capsule.

**Ladder (do not skip):** (1) active phase doc → (2) catalog, closed blockers in `status.yaml`, matching [MIGRATION-EVIDENCE.md](MIGRATION-EVIDENCE.md) title → (3) in-repo grep → (4) a lookup subagent reads the latest `summary.json` and reports the relevant lines → (5) one blocking human question → (6) bounded lookup → (7) `findings.md` pack gap.

**Step 6 is allowed when** a blocker is still open after steps 1–5 and it is one factual gap (a package rename, an official migration bullet). Budget: at most two WebSearch/WebFetch calls per gap, official hosts (`docs.spring.io`, `github.com/spring-projects/*`, `kotlinlang.org`, `cloud.google.com/java`, catalog-linked vendor docs). No sibling repos, no version shopping when the catalog pins one. Record the answer as `unverified` until a build proves it, and add a `packGap` row to `findings.md`.
