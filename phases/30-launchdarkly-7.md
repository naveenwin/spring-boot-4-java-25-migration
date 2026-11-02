# 30 — LaunchDarkly Java Server SDK 6.x → 7.x

## Detect

Apply when:

- `com.launchdarkly:launchdarkly-java-server-sdk:6.x`
- Residual `LDUser` / `LDUser.Builder` / `boolVariation(..., LDUser, ...)`
- Legacy artifact `com.launchdarkly:launchdarkly-client` (old name of the **same** server SDK — multi-hop, not a drop-in to 7)
- Ops: LaunchDarkly **Relay Proxy** in path (must be **≥ 8.0** before SDK 7)
- First-party Gson usage that may have resolved through the SDK's dependency graph (see below)

### First-party Gson

```bash
rg -l 'com\.google\.gson' --glob '*.java' --glob '*.kt' src
rg -n 'com\.google\.code\.gson' --glob '*.gradle*' --glob 'pom.xml' --glob '*.toml' .
```

If first-party code imports `com.google.gson` without declaring `com.google.code.gson:gson` directly, it may depend on a transitive path that changes with the SDK bump. Record that as a risk; do **not** add a direct Gson coordinate pre-emptively. Add one (version from [DEPENDENCY-CATALOG.md](../references/DEPENDENCY-CATALOG.md) or the platform BOM) only after an observed resolution failure, meaning an unresolved `com.google.gson` import at compile time or a `NoClassDefFoundError` / `ClassNotFoundException` for a `com.google.gson` class at test or runtime. Note the failure in phase notes. Do not code against the SDK's internal or shaded JSON types.

Skip when already on **7.17.x** with `LDContext` only and no `LDUser`.

Catalog target: **7.17.3**.

Official: [6→7 migration](https://launchdarkly.com/docs/sdk/server-side/java/migration-6-to-7).

## Before → After

```gradle
// BEFORE
implementation 'com.launchdarkly:launchdarkly-java-server-sdk:6.1.0'
// LEGACY (separate epic): com.launchdarkly:launchdarkly-client:4.6.3

// AFTER
implementation 'com.launchdarkly:launchdarkly-java-server-sdk:7.17.3'
```

```java
// BEFORE (6.x — LDUser deprecated then removed in 7)
LDUser user = new LDUser.Builder("key")
    .name("Sandy")
    .email("sandy@example.com")
    .build();
boolean on = client.boolVariation("flag-key", user, false);

// AFTER (7.x)
LDContext context = LDContext.builder("key")
    .name("Sandy")
    .set("email", "sandy@example.com")
    .build();
boolean on = client.boolVariation("flag-key", context, false);
```

`LDClient` / `LDConfig` init shape is unchanged — keep a **singleton** `@Bean`, never per-request.

Built-ins on context: `kind`, `key`, `name`, `anonymous`. Other attrs via `.set(...)`.

## What breaks / how to fix

| Symptom | Cause | Fix |
|---------|--------|-----|
| Compile errors at `LDUser` call sites, typically an unresolved type or no matching `*Variation` / `identify` / `track` overload (the exact message depends on the patch and compiler) | Client APIs no longer accept `LDUser` | Replace with `LDContext` everywhere (incl. tests/mocks) |
| Unresolved `com.google.gson` import or `NoClassDefFoundError` for a Gson class after the bump | First-party code relied on a transitive Gson path | Add a direct Gson coordinate (catalog/BOM version) only now, and record it |
| Wrong targeting after remap | Still using nested `custom` bag | `.set("attr", value)` |
| Multi-kind flags mis-evaluate | Wrong / missing kind | `LDContext.create(ContextKind.of("…"), key)` or multi contexts |
| Stale / broken flags behind Relay | Relay Proxy &lt; 8 | Upgrade Relay **before** SDK 7 |
| Jump from `launchdarkly-client:4.6.x` fails | Years of API/package renames | Artifact rename + 5→6 contexts + then this phase — do not one-step 4→7 |
| Per-request `new LDClient` | Anti-pattern | Singleton bean; build **context** per evaluation |

Prefer fixing all `LDUser` deprecations on **latest 6.x** first, then bump to 7.17.3.

## Steps

1. Inventory SDK artifact, `LDUser`/`LDContext`, Relay Proxy version, and first-party Gson imports without a direct coordinate.  
2. If Relay used: confirm **≥ 8.0** with ops (gate).  
3. On 6.x: migrate call sites to `LDContext`; clear deprecations.  
4. Bump to **7.17.3**; fix test matchers (`any(LDUser.class)` → `LDContext`). If compile or test runs then show a Gson resolution failure, add the direct Gson coordinate and record the failure.  
5. Smoke: offline defaults, online stream, no per-request client.  
6. Ask human to verify flag eval in lower env; roll services.  
7. For `launchdarkly-client:4.6.x`: park as separate migrate path (ask human); do not pretend it is this phase alone.

## Do not

- Keep `LDUser` on SDK 7.  
- Treat `LDContext.fromUser` as the end state.  
- Upgrade SDK 7 before Relay Proxy 8 when Relay is in path.  
- One-step `launchdarkly-client:4.6.3` → `7.17.3`.  
- Instantiate `LDClient` per request.  
- Silent phase-12 version bump when `LDUser` remains — use this phase.
- Add a direct Gson coordinate "just in case", without an observed resolution failure.

## Risk

`ASK_HUMAN` default (flag targeting + Relay). `SPIKE_FIRST` for legacy `launchdarkly-client` 4.x or multi-kind / private-attribute heavy setups. `SAFE_AUTO` only if already clean `LDContext` on 6.x and no Relay — still prefer human flag smoke.

## Rollback

Revert dependency (+ code if needed) to last good 6.x or prior 7.x **together**. Do not half-revert to `LDUser` while staying on 7. Relay 8 can remain if other services already on SDK 7.

## Done when

On **7.17.3** with `LDContext` only (or legacy 4.x explicitly deferred); Relay gate satisfied or N/A; human flag smoke green or deferred.

## Handoff

`launchDarkly=7.17.3; ldUserRemoved=yes|deferred; gson=direct-added-on-failure|already-direct|not-used|transitive-ok; relayProxy=ge8|n/a|blocked; legacyClient4=deferred|n/a; smoke=green|deferred`
