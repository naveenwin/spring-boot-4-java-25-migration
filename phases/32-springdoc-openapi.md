# 32 — springdoc-openapi / Swagger UI (runtime docs)

**Runtime** OpenAPI docs (springdoc, Swagger UI, Knife4j / Scalar). Distinct from **codegen** ([05-openapi-generator.md](05-openapi-generator.md)) and from Atlassian **request validators** ([DEPENDENCY-CATALOG.md](../references/DEPENDENCY-CATALOG.md) `openapi-request-validator-*`).

**Sources (verify current pins upstream — do not treat numbers below as forever):**

- [springdoc.org](https://springdoc.org/) — Boot 4 → springdoc **v3**; Boot 3 docs archived as v2.x; Boot 2 as v1.x  
- [springdoc CHANGELOG](https://github.com/springdoc/springdoc-openapi/blob/main/CHANGELOG.md) — major lockstep with Boot major  
- Knife4j Next [compatibility matrix](https://knife4jnext.com/reference/compatibility) — Boot×starter table  
- Jackson 3 gap: [swagger-core#4991](https://github.com/swagger-api/swagger-core/issues/4991), [springdoc#3157](https://github.com/springdoc/springdoc-openapi/issues/3157)

## Detect

Apply when any of:

- `org.springdoc:springdoc-openapi-*` (ui / api / common / webmvc / webflux)
- Knife4j / Knife4j Next: `com.github.xiaoymin:knife4j-*`, `com.baizhukui:knife4j-*`, `/doc.html`
- Springfox leftover: `springfox-swagger2`, `springfox-boot-starter`, `io.springfox`, `/v2/api-docs`
- Swagger 2 annotations in first-party code: `io.swagger.annotations.*` (`@Api`, `@ApiOperation`, …)
- OpenAPI 3 annotations / models: `io.swagger.v3.oas.annotations.*`, `io.swagger.core.v3:*`
- Scalar starters: `springdoc-openapi-starter-*-scalar`
- Failures after Boot 4: `NoSuchMethodError` on `ControllerAdviceBean` / `Schema`; `ClassNotFoundException: LiteWebJarsResourceResolver`; Jackson “conflicting setter” on `ObjectNode` while loading docs; empty or 401/403 on `/v3/api-docs` / swagger-ui

Skip when the service has **no** runtime docs stack (generator-only → phase 05 only).

### Inventory before editing

```bash
rg -n 'org\.springdoc|knife4j|springfox|io\.swagger\.annotations|io\.swagger\.v3|GroupedOpenApi|Docket|/v3/api-docs|/swagger-ui|/doc\.html' \
  --glob '*.gradle*' --glob '*.kts' --glob 'pom.xml' --glob '*.java' --glob '*.kt' --glob '*.yml' --glob '*.yaml' --glob '*.properties' .
```

Classify:

| Kind | Action |
|------|--------|
| Springfox + Swagger 2 annotations | Full migrate to springdoc 3 + OAS3 annotations (Boot 2.7→4 path) |
| springdoc **2.x** on Boot **4** | Bump to springdoc **3.x** (not a patch on 2.x) |
| springdoc **3.x** already | Align UI extension (Knife4j/Scalar) + Jackson coexistence; verify endpoints |
| Knife4j Jakarta / Boot3 starter on Boot 4 | Replace with **Boot4** starter only |
| Generator plugin only | This phase N/A — use [05](05-openapi-generator.md) |

## Version trains (Boot × springdoc × UI)

springdoc majors track Boot majors. Confirm the current patch on [springdoc.org](https://springdoc.org/) / Maven Central before pinning.

| Runtime | springdoc line | Typical UI starter | Notes |
|---------|----------------|--------------------|--------|
| Boot **2.x** | **1.x** | `springdoc-openapi-ui` (legacy coords) or Knife4j openapi3 **non-Jakarta** | Not a Boot 4 target |
| Boot **3.x** | **2.8+ / 2.9.x** | `springdoc-openapi-starter-webmvc-ui` **2.x** | Framework 6.2 / Boot 3.4+ needs recent 2.8.x+ (`ControllerAdviceBean`) |
| Boot **4.x** | **3.x** | `springdoc-openapi-starter-webmvc-ui` **3.x** (docs cite **3.1.x**; Knife4j Next may manage **3.0.3**) | **Required** for Framework 7 |

**Knife4j Next (when Detect finds Knife4j)** — starter must match Boot; wrong starter is the #1 break:

| Boot | Knife4j starter (WebMVC) | Embeds springdoc |
|------|--------------------------|------------------|
| 3.x | `knife4j-openapi3-jakarta-spring-boot-starter` | 2.x |
| **4.x** | `knife4j-openapi3-boot4-spring-boot-starter` | **3.x** |

Gateway / aggregation have separate Boot4 starters — do not mix with app WebMVC/WebFlux starters. Prefer **upstream Knife4j Next** matrix over inventing a no-op `ControllerAdviceBean` bean.

WebFlux: `springdoc-openapi-starter-webflux-ui` (same major as Boot train). See [35-webflux.md](35-webflux.md) if the app is reactive-only.

## Before → After

### A. springdoc 2.x (Boot 3) → 3.x (Boot 4)

```gradle
// BEFORE — Boot 3 train (fleet often 2.8.x)
implementation 'org.springdoc:springdoc-openapi-starter-webmvc-ui:2.8.15'

// AFTER — Boot 4 train (confirm current 3.x on springdoc.org / catalog)
implementation 'org.springdoc:springdoc-openapi-starter-webmvc-ui:3.1.1'
```

```xml
<!-- Maven: same artifact, version 3.x -->
<dependency>
  <groupId>org.springdoc</groupId>
  <artifactId>springdoc-openapi-starter-webmvc-ui</artifactId>
  <version>3.1.1</version>
</dependency>
```

API-only (no UI jar) when Security already serves a separate portal:

```gradle
implementation 'org.springdoc:springdoc-openapi-starter-webmvc-api:3.1.1'
```

Keep **one** coherent tree: exclude transitive springdoc/Swagger pulled by an old Knife4j or internal BOM if versions diverge. Align `swagger-annotations` / `swagger-models` / `swagger-core` to the **same** 2.2.x (catalog proposes **2.2.55**) when the service pins them explicitly.

### B. Knife4j on Boot 4

```gradle
// BEFORE — breaks on Boot 4 / Framework 7
implementation 'com.github.xiaoymin:knife4j-openapi3-jakarta-spring-boot-starter:4.5.0'
// or any Boot3 Jakarta starter that embeds springdoc 2.3–2.x

// AFTER — Boot4 starter (confirm current Knife4j Next version upstream)
implementation 'com.baizhukui:knife4j-openapi3-boot4-spring-boot-starter:5.7.9'
// Do not also declare springdoc-ui unless you intentionally override the managed version
```

```yaml
# Optional but recommended — make OpenAPI 3.1 intent explicit
springdoc:
  api-docs:
    path: /v3/api-docs
    version: OPENAPI_3_1
  swagger-ui:
    path: /swagger-ui.html
knife4j:
  enable: true
```

If Knife4j is optional DX only and blocks the Boot 4 cutover: **remove the extension**, keep plain springdoc 3.x UI — do not ship a broad compatibility shim.

### C. Springfox (Swagger 2) → springdoc (OpenAPI 3)

Boot 2.7→4 exception path. Remove Springfox entirely; do not run Springfox and springdoc together.

```gradle
// BEFORE
implementation 'io.springfox:springfox-boot-starter:3.0.0'
// or springfox-swagger2 + swagger-ui

// AFTER
implementation 'org.springdoc:springdoc-openapi-starter-webmvc-ui:3.1.1'
```

Annotation map (`io.swagger.annotations` → `io.swagger.v3.oas.annotations`):

| Swagger 2 / Springfox | OpenAPI 3 |
|-----------------------|-----------|
| `@Api` | `@Tag` |
| `@ApiOperation(value, notes)` | `@Operation(summary, description)` |
| `@ApiParam` | `@Parameter` |
| `@ApiImplicitParam(s)` | `@Parameter` / `@Parameters` |
| `@ApiModel` | `@Schema` |
| `@ApiModelProperty` | `@Schema` (`allowEmptyValue` → `nullable`) |
| `@ApiResponse(code, message)` | `@ApiResponse(responseCode, description)` |
| `@ApiIgnore` | `@Hidden` / `@Operation(hidden=true)` / `@Parameter(hidden=true)` |
| `Docket` beans | `GroupedOpenApi` beans or `springdoc.packages-to-scan` / `paths-to-match` |

```java
// BEFORE
@Bean
Docket publicApi() {
  return new Docket(DocumentationType.SWAGGER_2)
      .groupName("public")
      .select()
      .apis(RequestHandlerSelectors.basePackage("com.example.api"))
      .paths(PathSelectors.ant("/public/**"))
      .build();
}

// AFTER
@Bean
GroupedOpenApi publicApi() {
  return GroupedOpenApi.builder()
      .group("public")
      .pathsToMatch("/public/**")
      .packagesToScan("com.example.api")
      .build();
}
```

Single-group apps can drop `Docket` and use properties only:

```properties
springdoc.packages-to-scan=com.example.api
springdoc.paths-to-match=/api/**
```

### D. Security (docs endpoints)

Docs endpoints are **not** authenticated by springdoc. Align with [20-spring-security-7.md](20-spring-security-7.md): either permit in lower envs or keep behind auth / disable in prod.

```java
// Typical permit list (adjust to actual springdoc.path / Knife4j paths)
.pathMatchers(
    "/v3/api-docs/**",
    "/swagger-ui/**",
    "/swagger-ui.html",
    "/doc.html",
    "/webjars/**"
).permitAll()
```

```yaml
# Prod hardening examples — pick one strategy; do not embed secrets in OpenAPI JSON
springdoc:
  api-docs:
    enabled: false   # or profile-gate
  swagger-ui:
    enabled: false
# Knife4j: knife4j.production=true only protects default paths — custom api-docs.path needs extra rules
```

Never put bearer tokens, basic passwords, or internal hostnames into committed OpenAPI examples.

## What breaks / how to fix

| Symptom | Cause | Fix |
|---------|--------|-----|
| `NoSuchMethodError: ControllerAdviceBean.<init>(Object)` | springdoc **2.3–early 2.8** (or Knife4j embedding it) on Framework **6.2+ / 7** | Boot 4 → springdoc **3.x** (+ Boot4 Knife4j). Boot 3.4/3.5 → springdoc **≥ 2.8.9** (prefer current 2.9.x). Do **not** add a fake `ControllerAdviceBean` bean |
| `ClassNotFoundException: LiteWebJarsResourceResolver` | Stale Knife4j / springdoc vs Framework resource API | Upgrade UI starter to Boot-matched line |
| `NoSuchMethodError` / linkage on `io.swagger.v3.oas.models.media.Schema` | Mixed `swagger-core` / `swagger-models` versions | Force one version for annotations+models+core; exclude duplicates from BOM/Knife4j |
| Jackson `Conflicting setter definitions for property "all"` on `ObjectNode` | swagger-core still introspects with **Jackson 2** while Boot 4 app types are **Jackson 3** (`tools.jackson`) | Expected coexistence gap ([#3157](https://github.com/springdoc/springdoc-openapi/issues/3157)). Prefer: keep app on Jackson 3 ([04](04-jackson-3.md)); let swagger-core keep its Jackson 2 transitive; upgrade springdoc/swagger-core when upstream ships Jackson 3. **Do not** flip the whole app back to `spring-boot-jackson2` solely for docs. Unofficial forks (`io.github.vpelikh`) → `ASK_HUMAN` only |
| `/v3/api-docs` 401/403 or empty UI | Security / gateway strips docs paths | Permit or profile-enable; fix gateway routes; check `context-path` + `springdoc.swagger-ui.path` |
| UI 404 (`swagger-ui.html` vs `/swagger-ui/index.html`) | Path property drift across springdoc majors | Set `springdoc.swagger-ui.path` explicitly; hit both redirect and index once |
| Groups missing / wrong APIs | Old `Docket` or unscanned `GroupedOpenApi` | Ensure `@Configuration` is component-scanned; align `packages-to-scan` |
| Kotlin nullability / deprecated props wrong in schema | Older springdoc Kotlin customizers | Use current springdoc 3.x (3.0.3+ improved Kotlin nullable defaults) |
| Scalar XSS / forwarded-header issues | Scalar starters + trusted headers | Prefer current springdoc patch; set `server.forward-headers-strategy` only behind a trusted proxy; treat Scalar like swagger-ui for auth |
| Contract tests fail after rename | Atlassian `swagger-request-validator-*` → `openapi-request-validator-*` | Catalog **3.0.0** coords — not springdoc itself; fix imports + re-run tests |
| Duplicate swagger-ui + Knife4j fighting | Two UI stacks | One UI: springdoc-ui **or** Knife4j Boot4 starter, not both unmanaged |

### Jackson 3 policy for this phase

1. HTTP / app mappers stay on Boot’s Jackson 3 (`JsonMapper`) per [04-jackson-3.md](04-jackson-3.md).  
2. springdoc/swagger-core may carry isolated **transitive Jackson 2** until swagger-core completes Jackson 3. That docs-only introspection dependency is not an application bridge: do not declare `spring-boot-jackson2`, inject its mapper, or route HTTP JSON through it.
3. Record in handoff if docs still emit Jackson conflict warnings but `/v3/api-docs` is usable.  
4. Re-check [swagger-core#4991](https://github.com/swagger-api/swagger-core/issues/4991) on the next dependency-queue pass.

## Steps

1. Inventory: springdoc major, Knife4j/Springfox/Scalar, Swagger 2 vs OAS3 annotations, Security rules for docs paths, and whether any Jackson 2 dependency is app-owned versus docs-only transitive.
2. Remove Springfox / Swagger 2 deps if present; rewrite annotations + `Docket` → `GroupedOpenApi` / properties.  
3. On Boot 4: set springdoc to **3.x** (WebMVC or WebFlux starter matching the web stack). Resolve version from catalog if listed, else current stable on springdoc.org.  
4. If Knife4j: replace with **Boot4** starter only; drop Boot3 Jakarta starter; prefer disabling Knife4j over shims if blocked.  
5. Align explicit `io.swagger.core.v3:*` pins to one version; exclude stale transitive springdoc.  
6. Keep Jackson 3 for the app; do not “fix” docs by reverting the app to Jackson 2. Note known ObjectNode warnings.  
7. Wire Security / profiles for docs endpoints (lower env usable; prod strategy explicit).  
8. Human smoke (agent does not run the app): `/v3/api-docs` (+ `/v3/api-docs.yaml`), `/v3/api-docs/swagger-config`, Swagger UI or `/doc.html`, one grouped doc if used, representative schema (enum, page/nullable, error model). No credentials in the JSON.  
9. If Atlassian validators present: ensure `openapi-request-validator-* :3.0.0` (phase 12 / RestAssured notes).

## Do not

- Run springdoc **2.x** on Boot **4**.  
- Use Knife4j **Jakarta / Boot3** starter on Boot **4**.  
- Mix Springfox and springdoc.  
- Mix WebMVC and WebFlux springdoc/Knife4j starters.  
- Invent no-op Framework compatibility beans for `ControllerAdviceBean`.  
- Revert the whole service to `spring-boot-jackson2` just to silence docs introspection noise.  
- Commit unofficial Jackson-3 springdoc forks without human approval.  
- Embed secrets in OpenAPI examples or leave docs wide open in prod without an explicit decision.  
- Treat this phase as a substitute for [05-openapi-generator.md](05-openapi-generator.md) flag work (`useSpringBoot4` / `useJackson3`).

## Risk

- `SAFE_AUTO` — already on springdoc 3.x + matching UI, only patch align / property cleanup, no Springfox, no Knife4j starter swap.  
- `ASK_HUMAN` — Springfox→springdoc annotation rewrite; Knife4j starter/groupId change; prod docs exposure; adopting any non-`org.springdoc` fork for Jackson 3.  
- `SPIKE_FIRST` — custom `OpenApiCustomiser` / resource transformers / gateway aggregation; isolated docs-stack Jackson conflicts that break `/v3/api-docs` (not just log noise).

## Rollback

Revert springdoc/Knife4j coordinates (+ annotation commits if Springfox migration) together. Restore previous Security permit lists. Do not leave Boot 4 on springdoc 2.x as a “temporary” rollback.

## Done when

- Boot 4 service resolves springdoc **3.x** (or N/A).  
- No Springfox on classpath; OAS3 annotations only if docs remain.  
- Knife4j (if any) on Boot4 starter; no Boot3 Jakarta starter.  
- Human confirms `/v3/api-docs` + UI (or intentional disable) without embedding secrets.  
- Jackson 3 remains the app HTTP mapper; docs Jackson-2 coexistence documented if warnings remain.

## Handoff

`springdoc=3.x.<patch>|n/a; ui=swagger-ui|knife4j-boot4|scalar|api-only|disabled; springfoxRemoved=yes|n/a; knife4j=boot4|removed|n/a; jacksonDocsCoexist=ok|warn|blocked; docsSecurity=permit-lower|auth|disabled-prod; smoke=green|deferred`
