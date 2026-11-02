# 18 — Configuration properties migration

## Detect

Always after Boot 4 platform bump when the service has `application*.yml` / `.properties` / env-based Spring config. Also: startup warnings from renamed keys; Actuator / Mongo / Session / Jackson property churn.

### Path matching — quote the strings before scoring

Search before calling this phase a mechanical rename:

- `spring.mvc.pathmatch.matching-strategy` set to `ant_path_matcher` (or `ANT_PATH_MATCHER`)
- `//` inside `@RequestMapping` / `@GetMapping` / `@PostMapping` / `@PutMapping` / `@DeleteMapping` / `@PatchMapping` values **or** inside path constants those annotations use
- a method-level `value` or `path` that repeats a class-level pattern which already contains a `{variable}`

Quote the mapping strings in the question. Do not paraphrase a doubled-slash constant as “single-segment” because a test calls the collapsed URL.

Any one of those hits is `ASK_HUMAN` before edits. `SAFE_AUTO` stays limited to changelog renames that do not change which URL matches.

## Before → After

### Properties migrator (temporary)

```gradle
// During migration only — remove before merge to main long-term
runtimeOnly 'org.springframework.boot:spring-boot-properties-migrator'
```

```xml
<!-- Maven: same artifact, runtime scope; delete after keys are fixed -->
```

When a context start will run in this phase: add the migrator, start once, fix reported keys, and **remove** the dependency. When the agent cannot boot the context, do not add it — see Steps.

### High-hit renames (non-exhaustive)

Confirm against the Boot 4 [Configuration Changelog](https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Configuration-Changelog) and [deprecated properties](https://docs.spring.io/spring-boot/4.0/appendix/deprecated-application-properties/index.html) for the target patch.

| Area | Direction (typical) |
|------|---------------------|
| Jackson | `spring.jackson.read|write.*` → JSON-specific `spring.jackson.json.*`; remove `spring.jackson2.*` because Boot 4 application JSON cuts directly to Jackson 3 ([04-jackson-3.md](04-jackson-3.md)). `write-dates-as-timestamps` is not part of that rename: move it from `spring.jackson.serialization` to `spring.jackson.datatype.datetime`. Leave other `spring.jackson.serialization.*` keys, including `indent_output`, where they are. |
| Mongo | Driver vs Data split: `spring.mongodb.*` vs `spring.data.mongodb.*` — see [stubs/mongodb.md](../stubs/mongodb.md) |
| Session | `spring.session.redis` → `spring.session.data.redis` (and similar `spring.session.data.*`) — see [stubs/spring-session.md](../stubs/spring-session.md) |
| Actuator | Endpoint `*.enabled` → access model; probes default on — see [22-actuator.md](22-actuator.md) |
| Kafka | Embedded-test ZooKeeper attributes are removed in [44-spring-kafka-4.md](44-spring-kafka-4.md). Leave `spring.kafka.consumer.properties.group.protocol` unset unless the human opts in |

> **Open / not fully analyzed** — do not paste the entire changelog into the service; link + migrator output are the source of truth when a context start exists.

### Ant-style matcher, doubled slash, and a repeated variable

Boot 4.0 deprecates `spring.mvc.pathmatch.matching-strategy=ant_path_matcher`. Boot 4.1 still accepts it. Boot 4.2 removes it. `AntPathMatcher` drops empty slash tokens, so a constant written with `//` can match the single-slash URL tests already call. `PathPattern` keeps the empty segment, so the same constant stops matching that URL.

**Decision, recorded before code** (human picks one):

1. **Keep** the deprecated strategy through the Boot 4.1 line and remove it on the 4.2 bump, or  
2. **Collapse** doubled slashes to the single-slash URLs the tests already call, then delete the property.

Do not collapse and also leave `ant_path_matcher` without saying which decision was chosen.

#### Duplicate capture and interface defaults

After `//` becomes `/`, Spring Framework 7 `PathPattern.combine` concatenates when the class pattern already captures a variable. `InternalPathPatternParser` then throws `ILLEGAL_DOUBLE_CAPTURE` if that `{variable}` appears twice. `RequestMappingHandlerMapping` keeps the nearest annotation (`SearchStrategy.TYPE_HIERARCHY`, first run of the aggregate index) — the nearest annotation wins. The worker does not need a Framework source dive to apply the table.

| Method shape | After doubled slash → single slash |
|--------------|-------------------------------------|
| Controller override with a **relative** pattern (`/{id}/move`, `/create`) | One `{variable}`. Safe. |
| Interface **default** the controller does not override, whose `value` repeats the class pattern | `{variable}` twice. Startup fails with `ILLEGAL_DOUBLE_CAPTURE`. |
| That same default rewritten to a relative path the controller already maps | Ambiguous mapping. Startup fails. |
| Default that nothing calls, while a controller method already serves that URL | Remove the mapping annotation from the default. Do not add a new relative mapping — that would publish a route that was not reachable before. |

Class-level prefix stays (single slash). Live controller methods stay relative. Non-overridden interface defaults that repeat the class path lose their mapping annotation when a controller method already serves that URL.

```java
// Before — class constant uses // ; AntPathMatcher matched /api/v1
@RequestMapping("//api//v1//widgets//{widgetId}")

// Interface default repeats the class pattern (not overridden on the controller)
@PostMapping("//api//v1//widgets//{widgetId}//create")
default Response create() { ... }

// After collapse — class prefix only; drop the default's mapping
// (a controller method already serves create). Do not add @PostMapping("/create")
// on the default.
@RequestMapping("/api/v1/widgets/{widgetId}")
```

## Steps

1. Grep `ant_path_matcher`, `//` inside mapping constants, and method patterns that repeat a class-level `{variable}`. If any hit, stop for the human decision above. Do not start the migrator while that decision is open.  
2. Add `spring-boot-properties-migrator` only for a Stage C context run, removing it in the next commit. Stage B cannot start the context, so in Stage B **leave the migrator off the classpath** and record deprecation warnings as unverified for Stage C ([13-verification.md](13-verification.md)). Do not add it “to discover keys” and leave it for later ([anti-pattern 20](../references/99-anti-patterns.md)).  
3. When a context did start, collect migrator / deprecation warnings, then remove the dependency.  
4. Rewrite in-repo YAML/properties/env docs to the new keys. For the collapse decision: single-slash constants, delete the path-match property, and apply the interface-default table. Actuator access-model and probe keys stay in [22-actuator.md](22-actuator.md).  
5. Re-smoke config load only when a human runs it. Do not edit generated architecture snapshots that still mention the old key.

## Do not

- Leave the migrator on the classpath permanently, or add it when this agent cannot boot the context.  
- Invent property names not present in the Boot 4 changelog for that patch.  
- Keep `spring.jackson2.*` or a Jackson 2 preferred-mapper property on Boot 4.
- Change production secrets hosts / URLs under the guise of “property rename.”  
- Treat doubled-slash mappings as single-segment and drop `ant_path_matcher` without the decision above.  
- Rewrite a non-overridden interface default into a new relative mapping that publishes a route or captures `{variable}` twice (`ILLEGAL_DOUBLE_CAPTURE`).  
- “Fix” generated architecture or graph files that still quote the old property.

## Risk

`SAFE_AUTO` for changelog renames that do not change which URL matches, including add → fix → remove migrator when a context start actually runs and warnings are mechanical.  
`ASK_HUMAN` when `ant_path_matcher`, a doubled slash, or a repeated `{variable}` is present (keep-through-4.1 vs collapse-then-remove), and if a rename changes external contract (k8s env, config maps) or behavior (probes, session store).

## Rollback

Revert property edits; temporarily re-add migrator only if needed to diagnose.

## Done when

No migrator dependency (never added when the agent cannot boot; removed when it was added). No unresolved Boot 4 property deprecation warnings for first-party config, or those warnings are explicitly unverified for Stage C. Path-match decision is recorded when Detect hit `ant_path_matcher`, `//`, or a repeated `{variable}`.

## Handoff

`configMigrator=removed|not-added|still-present; propsFixed=yes|partial; pathMatch=kept-ant|collapsed|n/a; deprecations=unverified|clear; deferred=[…]`
