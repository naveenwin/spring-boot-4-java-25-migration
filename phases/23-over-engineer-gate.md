# 23 — Over-engineer gate (critic)

## Detect

**Not scheduled by default** ([PHASE-CATALOG.md](../references/PHASE-CATALOG.md#conditional-priority-the-only-place-these-rules-live)). The human asks for it, or the planner adds it once as `priority: good` when the Stage B diff is large. It is never a fixed step after every phase.

Good points to run it:

- after Stage B's persistence cluster (33 when JPA ran, otherwise 03), when the diff is already large;
- after Stage B finishes, before Stage C, as one review of the whole source diff;
- whenever the human asks for a critic pass.

Skip while the change set is still tiny (a single mechanical bump). Do not use the critic chat to land Micrometer, retry, or tracing edits; those stay in their phases.

## Before → After

This phase does **not** migrate framework APIs. It reviews the **diff produced so far** (and the plan's remaining items) and argues for simplicity.

Output under `.joker/java-spring-migration/critic/<timestamp>.md`:

| Finding | Required fields |
|---------|-----------------|
| Overdone / over-engineered | What was done; why it is heavier than needed; simpler alternative |
| Keep as-is | What looks appropriately minimal and why |
| Risky complexity | Coupled refactors that should have been deferred |

Tone: **debate and push back**, not rubber-stamp. Prefer deleting speculative helpers, extra abstractions, “while we are here” cleanups, and dual-path compatibility that the pack already forbids as permanent.

### Zero findings

`findings=0` is a finished critic (`humanDecisionNeeded=false`, no simplify-now commit). The report still lists **deferred** work this chat must not “simplify”, limited to items the plan still has open:

| Later phase | Leave untouched in this critic |
|-------------|-------------------------------|
| [08-flyway-db.md](08-flyway-db.md) | Flyway plugin, migration SQL, locations |
| [25-testcontainers-2.md](25-testcontainers-2.md) | Testcontainers source |
| [26-rest-assured-6.md](26-rest-assured-6.md) | Client scope |
| [28-okhttp-5.md](28-okhttp-5.md), [30-launchdarkly-7.md](30-launchdarkly-7.md) | HTTP client and feature-flag SDK call sites |
| [22-actuator.md](22-actuator.md), [07-observability.md](07-observability.md), [41-spring-retry-framework.md](41-spring-retry-framework.md) | Micrometer, Sleuth, retry |

Also name accepted debt that is intentionally not a Boot-bump refactor (duplicate test configuration, two hand-built mappers) so the next critic does not reopen it. An empty findings list without that deferred list is incomplete.

## Steps

1. Read `status.yaml` and the commits/diff since the last critic (or since `baselineCommit`).  
2. List concrete over-engineering findings with simpler alternatives (code-shaped, generic).  
3. Separate: (a) recommend revert/simplify now, (b) accept debt with reason, (c) out of scope.  
4. Present to human; **do not** auto-revert or rewrite.  
5. Each approved simplification becomes a slice of the phase that made the change, committed as `<phase-id> fix: simplify …`. The next compile run checks it.  
6. Update `status.yaml` / `findings.md` with the critic outcome, including the deferred list when `findings=0`.

## Do not

- Run at every phase by default.  
- Treat critic as a license to redesign the domain.  
- Auto-apply simplifications without human OK.  
- Expand scope into unrelated cleanups.  
- Commit anything under `.joker/`.

## Risk

`ASK_HUMAN` for any code change that comes out of the critic. The analysis itself is read-only.

## Rollback

Revert follow-up simplify commits; keep critic report in `.joker` for history.

## Done when

Critic report written. Human accepted, deferred, or rejected each finding. When `findings=0`, the deferred list is present and no simplify-now commit exists. Approved simplifications landed or explicitly skipped.

## Handoff

`critic=done; point=after-persistence|after-stage-b|on-request; findings=<n>; simplifyNow=<n>; deferredPins=listed|none`

When later Flyway / Micrometer / retry / tracing / Testcontainers work is intentionally left for later phases, write `simplifyNow=0; deferredPins=listed` even if critic findings are zero.
