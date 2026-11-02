# 26 — Rest Assured 5.x → 6.x

## Detect

Apply when:

- `io.rest-assured:rest-assured` (or `json-path` / `spring-mock-mvc` / `kotlin-extensions`) at **5.4 / 5.5**
- Boot 4 present (Groovy 5 on classpath — RA 5 is not a durable fit)
- Custom `Jackson2ObjectMapperFactory` / `ObjectMapperType.JACKSON_2` in Rest Assured config
- Used with `openapi-request-validator-restassured` / old `swagger-request-validator-restassured`
- Rest Assured declared in `implementation` / `api` / compile scope instead of test scope

Skip when already on **6.2.x** with aligned modules.

Catalog target: **6.2.0**. Boot 4 BOM does **not** manage Rest Assured — pin explicitly.

Pair with approved OpenAPI validator rename in [DEPENDENCY-CATALOG.md](../references/DEPENDENCY-CATALOG.md) when present.

### Dependency scope

Check which configuration declares Rest Assured before bumping it:

```bash
rg -n 'rest-assured|restassured' --glob '*.gradle*' --glob 'pom.xml' --glob '*.toml' .
rg -l 'io\.restassured' src/main
```

| Finding | Action |
|---------|--------|
| Only `testImplementation` / test scope | Normal path for this phase |
| `implementation` / `api` / compile scope, and no `io.restassured` import under `src/main` | Misplaced scope. Move it to test scope in the same commit as the bump; record the change |
| `implementation` / `api` in a module that ships test fixtures or a shared test-support library | Consumers inherit the version. Treat the bump as a published-artifact change (`ASK_HUMAN`) |
| Arrives only transitively (for example through an OpenAPI validator) | Force alignment of all `io.rest-assured:*` modules; do not add an unused direct coordinate |

Rest Assured on the main runtime classpath also drags Groovy 5 into the deployed artifact. Do not leave it there to make the bump simpler.

### Inventory deserialization before touching mapper config

Rest Assured needs an object mapper only when a response body is turned into an object. Body matchers, `jsonPath().getString(...)`, and status/header assertions do not use it. Inventory first:

```bash
rg -n '\.as\(|\.as<|extract\(\)\.as|getObject\(|getList\(.*\.class|ObjectMapperType|ObjectMapperConfig|objectMapperConfig|RestAssuredConfig|RestAssured\.config' \
  --glob '*.java' --glob '*.kt' --glob '*.groovy' src
```

Record each `.as(...)` / `getObject(...)` site and the spec/config it runs under. If there are none, leave the mapper configuration alone; the bump alone is the change.

## Before → After

```gradle
// BEFORE — Boot 3 often BOM-managed 5.5.x
testImplementation 'io.rest-assured:rest-assured'

// AFTER — Boot 4: pin all RA modules to the same 6.2.0
testImplementation 'io.rest-assured:rest-assured:6.2.0'
testImplementation 'io.rest-assured:spring-mock-mvc:6.2.0' // if used
// Force over Atlassian ORV’s transitive 5.5.7 if needed
```

```java
// BEFORE — Jackson 2 mapper
config(RestAssuredConfig.config()
  .objectMapperConfig(objectMapperConfig()
    .defaultObjectMapperType(ObjectMapperType.JACKSON_2)
    .jackson2ObjectMapperFactory((type, charset) -> new ObjectMapper())));

// AFTER — Jackson 3, reusing Spring's configured JsonMapper bean,
// applied only to the spec(s) whose responses are deserialized
import tools.jackson.databind.json.JsonMapper;
import static io.restassured.mapper.ObjectMapperType.JACKSON_3;

@Autowired JsonMapper jsonMapper; // Boot's bean, same settings as the app under test

RestAssuredConfig jsonConfig = RestAssuredConfig.config()
  .objectMapperConfig(objectMapperConfig()
    .defaultObjectMapperType(JACKSON_3)
    .jackson3ObjectMapperFactory((cls, charset) -> jsonMapper));

given().config(jsonConfig)
  .when().get("/x")
  .then().extract().as(Dto.class);
// or once on a shared spec: new RequestSpecBuilder().setConfig(jsonConfig).build()
```

- Configure `JACKSON_3` only on the specs or helper that deserialize; leave assertion-only specs on defaults.
- Reuse Spring's `JsonMapper` bean so tests read responses with the same features, modules, and naming as the application. A fresh `JsonMapper.builder().build()` uses plain Jackson 3 defaults and can hide or invent differences (see the mapper buckets in [04-jackson-3.md](04-jackson-3.md)).
- Outside a Spring context (plain unit test), build the mapper with the same customizations the application applies, or keep the test on assertion-only checks.
- Do not set `RestAssured.config = …` or other static `RestAssured.*` state by default. Static config leaks between test classes and races under parallel forks. Use it only when a human approves and the suite does not run in parallel; reset it in `@AfterAll`.

```java
// BEFORE (breaks in 6.2) — calling when() on a built spec incorrectly
RequestSpecification spec = new RequestSpecBuilder().addHeader("X", "1").build();
spec.when().get("/x");

// AFTER
given().spec(spec).when().get("/x");
```

## What breaks / how to fix

| Symptom | Cause | Fix |
|---------|--------|-----|
| Groovy / method-missing with RA 5 on Boot 4 | Groovy 5 vs RA 5 | Upgrade to **6.2.0** (do not long-term downgrade Groovy) |
| Spring 5 / javax dragged by spring-mock-mvc | RA 6.0.0 packaging | Use **≥ 6.0.1** (prefer 6.2.0); drop old exclusions |
| `as(Dto.class)` fails with only Jackson 3 | Mapper path | ≥ 6.0.1 + explicit `JACKSON_3` factory on that spec, backed by Spring's `JsonMapper` |
| Deserialized values differ from what the app sends | Test mapper built with plain defaults | Use Spring's `JsonMapper` bean instead of a fresh builder |
| Groovy 5 / Rest Assured in the deployed artifact | Rest Assured in main scope | Move it to test scope (Dependency scope table) |
| Body assert order / dates changed | Jackson 3 defaults | Compare with phase-04 baseline; adapt assertions or configure the Jackson 3 mapper with documented compatibility features |
| JsonPath `properties` / hyphen keys odd | Groovy 5 JsonPath | Ensure ≥ **6.1.0** |
| Schema tests newly fail | Draft-06+ honored from `$schema` | Fix schema/response |
| Redirect lost `Authorization`/`Cookie` | 6.1 cross-host strip | Expected; opt out only if required |
| ORV filter weird after bump | ORV 3.0 compiles against RA 5.5.7 | Force RA 6.2.0; smoke valid/invalid OpenAPI paths |
| Mixed 5.x + 6.x modules | Partial bump | Align **all** `io.rest-assured:*` |

**Do not** assume Boot BOM picks RA. **Do not** stop at 6.0.0.

## Steps

1. Inventory RA modules and their declared scope, `.as(...)` / `getObject(...)` deserialization sites, existing mapper config, OpenAPI validator, REST Docs RA usage.  
2. Fix misplaced main-scope declarations; pin all `io.rest-assured:*` to **6.2.0**; force resolution over ORV transitives.  
3. Where the inventory found deserialization, configure `JACKSON_3` on those specs only, backed by Spring's `JsonMapper` bean ([04-jackson-3.md](04-jackson-3.md)). Replace any Jackson 2 mapper config. Skip this step when there is no deserialization and no existing mapper config.  
4. If using validator: ensure `openapi-request-validator-restassured:3.0.0` (approved catalog).  
5. Fix spec-builder / redirect / JsonPath failures from the table above.  
6. Ask human to run contract / API test suites; record in verification notes.  
7. One commit for RA bump + mapper; optional second for ORV rename if not done.

## Do not

- Stay on RA 5.5 on Boot 4 + Groovy 5.  
- Mix Rest Assured module versions.  
- Add a global `RestAssured.config` / static mapper by default, or configure a mapper on specs that never deserialize.  
- Build a fresh default `JsonMapper` for Rest Assured when Spring's bean is available.  
- Leave Rest Assured in main/runtime scope when no main source imports it.  
- Roll REST Docs Rest Assured on Boot 4 / Docs 4 (integration removed — migrate docs tests separately).  
- Silent phase-12 bump without this phase when Jackson/ORV are involved.

## Risk

`ASK_HUMAN` default (contract suites + ORV). `SPIKE_FIRST` if heavy custom SSL/form-auth or large parallel static `RestAssured.*` mutation.

## Rollback

On Boot 4 + Groovy 5, roll back to **6.0.1** if 6.2-specific breaks appear — not to 5.x. Keep ORV rename separable.

## Done when

All RA modules on 6.2.0 in test scope (or an approved published-fixture scope); every deserialization site runs under a Jackson 3 config backed by Spring's `JsonMapper` (or there are none); no Jackson 2 mapper config and no unapproved static `RestAssured` config remain; human reports contract/API tests green or deferred with reason.

## Handoff

`restAssured=6.2.0; scope=test|moved-to-test|published-fixture; asSites=N; jacksonMapper=jackson3-spring-bean|none-needed; globalConfig=none|approved; orv=3.0|absent|deferred; tests=green|deferred`
