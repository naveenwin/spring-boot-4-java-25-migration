# 09 — Spring Boot test surface

Boot 4’s own test stack: focused test starters, `@MockitoBean` / `@MockitoSpyBean`, MockMvc and RestTestClient autoconfig, Jackson 3 in tests, faker, tracing test beans, and the unit-vs-Cucumber task split.

JUnit 4 removal is [36-junit-jupiter.md](36-junit-jupiter.md) and runs first. When legacy `com.squareup.okhttp3:mockwebserver` is present, [28-okhttp-5.md](28-okhttp-5.md) runs after 36 and before this phase (Stage B order in [PHASE-CATALOG.md](../references/PHASE-CATALOG.md)). Library majors stay in their own phases: Testcontainers [25](25-testcontainers-2.md), Rest Assured [26](26-rest-assured-6.md), MockServer [27](27-mockserver-9.md), Cucumber [16](16-cucumber-8.md).

## Detect

Apply when tests use Spring Boot test APIs: `spring-boot-starter-test`, `@SpringBootTest`, `@MockBean` / `@MockitoBean`, MockMvc, `TestRestTemplate`, or JsonPath in tests.

If `org.junit.Test`, `junit:junit`, `junit-vintage-engine`, a `junit-jupiter` / `junit-platform` version pin, or legacy `com.squareup.okhttp3:mockwebserver` is still present, stop. Finish [36-junit-jupiter.md](36-junit-jupiter.md) until its handoff contains `junit6=bom`, then [28-okhttp-5.md](28-okhttp-5.md) when the remainder is the mock server. Skip when the service has no tests.

### Phase 36 gate

Do not start this phase until all of these hold:

1. The phase 36 handoff reads `junit4=removed` or `junit4=n/a` (not `blocked`) and `junit4Jar=absent`.
2. When the service had a mock server, the phase 28 handoff reads `mockwebserver=mockwebserver3`.
3. This grep returns nothing. There is no allowed `junit:junit` line:

```bash
rg -nP 'org\.junit\.(?!jupiter\b|platform\b)|junit\.framework|junit-vintage|migrationsupport|junit:junit' \
  --glob '*.java' --glob '*.kt' --glob '*.gradle*' --glob 'pom.xml' .
```

If any of these fail, hand back to phase 36 or phase 28. Do not finish JUnit 4 work here.

## Before → After

### Spring Boot test starters

```gradle
// Before (Boot 3)
testImplementation 'org.springframework.boot:spring-boot-starter-test'
// @AutoConfigureMockMvc from spring-boot-test-autoconfigure

// After (Boot 4 naming — use what the Boot 4.x line provides)
testImplementation 'org.springframework.boot:spring-boot-starter-test-classic' // transitional; OK during migrate
testImplementation 'org.springframework.boot:spring-boot-starter-webmvc-test'
testImplementation 'org.springframework.boot:spring-boot-starter-security-test' // if security tests need it
```

```java
// MockMvc autoconfig package may move to webmvc-test
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;

// When security filters break unauthenticated MockMvc unit / slice tests:
@AutoConfigureMockMvc(addFilters = false)
// Prefer security-test / @WithMockUser when the test is meant to exercise security
```

### `@MockBean` → `@MockitoBean`

```java
// Before (Boot 3)
import org.springframework.boot.test.mock.mockito.MockBean;
@MockBean FooClient fooClient;

// After (Boot 4)
import org.springframework.test.context.bean.override.mockito.MockitoBean;
@MockitoBean FooClient fooClient;
// @SpyBean → @MockitoSpyBean
```

**Do not** declare `@MockitoBean` / `@MockitoSpyBean` as **fields inside `@Configuration` / `@TestConfiguration` classes**. Use type-level declarations or a composed annotation for shared mocks (`ASK_HUMAN` if many tests shared one config class).

Plain Mockito `@Mock` / `@Captor` fields that previously relied on a Boot Mockito listener need `@ExtendWith(MockitoExtension.class)` (or equivalent) when they stop initializing.

### Safe mechanical rewrite recipe (rg + for loop)

Use this shape for pure import/annotation renames, such as `@MockBean` → `@MockitoBean`, `@SpyBean` → `@MockitoSpyBean`, or the `LocalServerPort` package move. It is safe only for 1:1 renames. Anything that needs judgment stays manual.

```bash
# 1. Dry run — list the files and review the list before touching anything
old='org\.springframework\.boot\.test\.mock\.mockito\.MockBean'
rg -l --glob '*.java' --glob '*.kt' "$old" src/test src/integrationTest 2>/dev/null

# 2. Exclude files that need manual work (fields inside @Configuration / @TestConfiguration,
#    or attributes such as reset = / answer = whose types moved)
rg -l --glob '*.java' --glob '*.kt' '@(Test)?Configuration' src/test

# 3. Rewrite one pattern per loop; newline-only IFS keeps paths with spaces intact
IFS=$'\n'
for f in $(rg -l --glob '*.java' --glob '*.kt' "$old" src/test); do
  perl -pi -e 's/\Qorg.springframework.boot.test.mock.mockito.MockBean\E\b/org.springframework.test.context.bean.override.mockito.MockitoBean/g; s/\@MockBean\b/\@MockitoBean/g' "$f"
done
unset IFS

# 4. Review, then re-grep: the residual must be empty or exactly the excluded files
git diff --stat
rg -n --glob '*.java' --glob '*.kt' "$old|@MockBean\b" src
```

Rules:

- Scope to test source sets. Never run the loop over `build/`, `target/`, generated sources, or the whole repository root.
- Anchor each pattern (`\b`, escaped dots, `\Q…\E`) so `@MockBeans` or similarly named types are not rewritten by accident.
- Use `perl -pi -e` rather than `sed -i`; the `sed -i` flag syntax differs between macOS and GNU.
- Use one rename per loop and review `git diff` before the next. Do not chain unrelated renames into one command.
- Remove files from the loop when the dry-run list includes a file the rename does not fit; fix those by hand.

### Jackson in tests

Inject `JsonMapper`, not Jackson 2 `ObjectMapper`. Update JsonPath providers to Jackson 3 variants (see [04-jackson-3.md](04-jackson-3.md)):

```java
// Before
new JacksonJsonProvider(objectMapper, objectMapper.reader() /* … */)
new JacksonMappingProvider(objectMapper)

// After — one-arg Jackson 3 providers
new Jackson3JsonProvider(jsonMapper)
new Jackson3MappingProvider(jsonMapper)
```

Shared `UnitTestBase` / `@TestConfiguration` should hold the `JsonMapper` field rename + JsonPath defaults (`@PostConstruct` if the project already configures them there).

### Faker

```text
javafaker → net.datafaker:datafaker (2.x)
```

When faker randomly picks enums used as **status** (e.g. `IN_PROGRESS`) or amounts that can round to **0**, async “success” tests can flake. **Stabilize at shared test data generators first** (positive amounts + deterministic starting status); avoid one-off pins in a single flaky test while the factory stays random.

### Unit vs Cucumber isolation

If Cucumber reuses unit helpers, let `integrationTest` (or equivalent) share `sourceSets.test.output` so `TestConfig` / JsonPath / faker beans stay in one place.

Prefer a dedicated `cucumberTest` task (`*CucumberRunner`, `maxParallelForks = 1`, `shouldRunAfter test`) so Cucumber does not share a parallel Test JVM with unit tests that race on DB / WireMock / emulators. JaCoCo on unit tests only is fine. CI: unit job (`-x cucumberTest`) vs Cucumber job (WireMock up + `cucumberTest`). Details: [16-cucumber-8.md](16-cucumber-8.md).

### Tracing mocks

After Sleuth → Micrometer ([07-observability.md](07-observability.md)), unit/IT contexts that inject `Tracer` may need a mock `Tracer` (+ `CurrentTraceContext`) `@Bean` in shared test config.

### `@SpringBootTest` no longer implies MockMvc / TestRestTemplate

On Boot 4, add explicit autoconfigure annotations when the test needs them:

```java
@SpringBootTest
@AutoConfigureMockMvc          // or webmvc-test slice
@AutoConfigureTestRestTemplate // if still on TestRestTemplate
@AutoConfigureRestTestClient   // preferred RestTestClient path when available
```

`TestRestTemplate` may move toward `spring-boot-resttestclient` packaging — prefer `RestTestClient` for new tests. HtmlUnit options nest under `@AutoConfigureMockMvc(htmlUnit = …)` when used.

**`RANDOM_PORT` / `DEFINED_PORT` tests: do not add MockMvc blindly.** A test with `webEnvironment = RANDOM_PORT` (or `DEFINED_PORT`) starts a real server and talks to it over HTTP through `TestRestTemplate`, `RestTestClient`, `WebTestClient`, Rest Assured, or a plain HTTP client. Add the autoconfigure annotation for the client the test actually injects. Add `@AutoConfigureMockMvc` only when the class injects `MockMvc`. Do not swap a port-based test to MockMvc to make it compile: MockMvc bypasses the servlet container, so the port, the container's error handling, server-level filters, and real serialization over the wire are no longer exercised. Grep before choosing:

```bash
rg -l 'RANDOM_PORT|DEFINED_PORT' src/test | xargs rg -l 'MockMvc|TestRestTemplate|RestTestClient|WebTestClient|RestAssured|LocalServerPort'
```

`@MockitoSpyBean` replaces `@SpyBean` where applicable. Type-level / shared `@TestConfiguration` mocks that used `@MockBean` need the same MockitoBean migration — `ASK_HUMAN` if many tests shared one config class.

### Boot 4 test annotation package moves

`@LocalServerPort` for integration tests is **not** on `org.springframework.boot.web.server` (embedded container config). Import from the **test** module:

```kotlin
// Before (Boot 2/3 habit)
import org.springframework.boot.web.server.LocalServerPort

// After (Boot 4 — class lives in spring-boot-test)
import org.springframework.boot.test.web.server.LocalServerPort
```

Grep: `rg 'boot\.web\.server\.LocalServerPort' src/test`.

### Kotest 6 on JUnit Platform (with [31-kotlin.md](31-kotlin.md))

`kotest-runner-junit5` does **not** replace `kotest-assertions-core`. Add both at the same catalog version (e.g. **6.2.6**).

Boolean convenience matchers moved packages in Kotest 6 — **not** `matchers.boolean` (Kotlin keyword) and **not** top-level `io.kotest.matchers.shouldBeTrue` unless your train still exposes them there:

```kotlin
import io.kotest.matchers.booleans.shouldBeFalse
import io.kotest.matchers.booleans.shouldBeTrue
```

`shouldBe` / `shouldNotBe` remain `io.kotest.matchers.shouldBe`. Prefer JUnit `Assertions` in a test class that already uses Mockito/Jupiter only, if you want zero Kotest surface.

### `ResponseEntityExceptionHandler` overrides (Framework 7)

Subclass overrides must use `HttpStatusCode` (not `HttpStatus`) and may return `ResponseEntity<Any>?` for methods such as `handleHttpMessageNotReadable`.

Boot 4 / Framework 7 defaults many framework exceptions to **RFC 7807 ProblemDetail** (`application/problem+json`). Legacy Cucumber or integration tests often assert **HTTP status only** and an **empty body** (`""`) on 400/404 binding/validation failures.

Replacing those ProblemDetail bodies in production `@ControllerAdvice` is an API contract change. It is `ASK_HUMAN` before any production edit. The `SAFE_AUTO` path does not apply the overrides below. After the human chooses, either update the test assertions to ProblemDetail or apply the overrides and record `errorBodyContract=empty`. Name every production advice file in the phase note and in rollback.

When `@ControllerAdvice` **extends** `ResponseEntityExceptionHandler` and the human has accepted the empty-body contract, restore it with **`override` hooks**, not standalone `@ExceptionHandler` methods for exception types the base class already maps — duplicate mappings fail context startup (`handlerExceptionResolver` / ambiguous `@ExceptionHandler`).

```kotlin
// AFTER — only after the human accepts the empty-body contract
override fun handleMethodArgumentNotValid(
    ex: MethodArgumentNotValidException,
    headers: HttpHeaders,
    status: HttpStatusCode,
    request: WebRequest,
): ResponseEntity<Any>? = ResponseEntity.status(HttpStatus.BAD_REQUEST).build()

override fun handleTypeMismatch(
    ex: TypeMismatchException,
    headers: HttpHeaders,
    status: HttpStatusCode,
    request: WebRequest,
): ResponseEntity<Any>? = ResponseEntity.status(HttpStatus.BAD_REQUEST).build()

override fun handleNoResourceFoundException(
    ex: NoResourceFoundException,
    headers: HttpHeaders,
    status: HttpStatusCode,
    request: WebRequest,
): ResponseEntity<Any>? = ResponseEntity.status(HttpStatus.NOT_FOUND).build()
```

**Detect in intake / test triage:** feature tables with `body ""` and status 400; steps that deserialize error responses only when `content.isEmpty()` is false; assign/move URLs with an empty path segment (often **404** `NoResourceFound`, not 405, on MVC 7).

#### Empty path segments → 404 `NoResourceFoundException`

A request such as `/items//assign` or `/items/{id}/move` with an empty `{id}` has an empty path segment. A `{var}` pattern does not match an empty segment, so no controller method is selected. The request then falls through to static-resource handling, which raises `NoResourceFoundException` and maps to **404**. An older stack may have answered the same URL with a different status (for example 405 or 400), depending on which handlers matched.

- Treat this as a framework routing change, not a controller bug. Compare with the pre-migration response for the same URL before editing anything.
- If tests assert the old status, update the assertion to 404, or restore the old contract only through the `handleNoResourceFoundException` override above. Keeping a non-404 status for that URL is an API decision (`ASK_HUMAN`).
- Do not add a catch-all mapping, trailing-slash matching, or a new `@ExceptionHandler` to force the old status.
- The body follows the same ProblemDetail-versus-empty-body decision. Choosing an empty body for that URL is `ASK_HUMAN`, same as choosing a non-404 status.

See anti-pattern **35f**.

#### A `ServletException` handler turns that 404 into a 500

`NoResourceFoundException` extends `ServletException`. An `@ExceptionHandler(ServletException.class)`, or a broader `Exception` handler that does not let this type through, owns the 404. The client receives **500**, and every probe hit on `/` logs a stack trace. Give `NoResourceFoundException` its own outcome so the status stays 404: the `handleNoResourceFoundException` override when the advice extends `ResponseEntityExceptionHandler`, otherwise a more specific `@ExceptionHandler`. Status and body still follow the `errorBodyContract` decision. Do not add that handler on the `SAFE_AUTO` path. See anti-pattern **35h**.

> **Open / not fully analyzed** — JUnit 6 nested `SpringExtension` scope (`spring.test.extension.context.scope`); pausing test contexts (`spring.test.context.cache.pause`).

### Cucumber / WireMock

Dedicated phase: **[16-cucumber-8.md](16-cucumber-8.md)** (Cucumber 8 idioms + WireMock 3 align; WireMock 4 deferred). Do not treat a Cucumber version bump as part of this phase alone.

Exit `test-classic` via [19-modular-starters.md](19-modular-starters.md) when focused test starters cover the suite.

## Steps

1. Pass the phase 36 gate (handoff plus residual grep above).
2. Align test starters/imports with Boot 4 ([19-modular-starters.md](19-modular-starters.md) for classic → focused).  
3. Replace `@MockBean` / `@SpyBean` with `@MockitoBean` / `@MockitoSpyBean` using the mechanical recipe; hand-fix the excluded files.  
4. Add explicit autoconfigure where tests relied on Boot 3 defaults: `@AutoConfigureMockMvc` only where `MockMvc` is injected; the matching HTTP-client autoconfigure for `RANDOM_PORT` / `DEFINED_PORT` tests.  
5. Migrate test JSON helpers to `JsonMapper` + JsonPath 3 (one-arg providers).  
6. Fix MockMvc / security test annotations packages; use `addFilters = false` only when filters block unauthenticated slice tests.  
7. Harden faker-driven success paths at **shared generators**.  
8. Split unit vs Cucumber Gradle tasks / CI jobs when both exist.  
9. If tests assert empty error bodies, ask the human to choose `errorBodyContract=empty` or `problem-detail` before editing production advice. On `problem-detail`, update test assertions only. On `empty`, apply the approved overrides and list the production files in the handoff. When advice handles `ServletException` or `Exception`, include `NoResourceFoundException` in that same decision so a 404 does not become a 500.  
10. If Cucumber/WireMock present → schedule [16-cucumber-8.md](16-cucumber-8.md) (ASK_HUMAN for first Cucumber 8 cutover).

## Do not

- Rewrite JUnit 4 (`org.junit.Test`, `org.junit.Assert`, runners, rules), add `junit-vintage-engine`, or pin Jupiter 5.x in this phase ([36-junit-jupiter.md](36-junit-jupiter.md)).
- Treat `test-classic` removal as mandatory in the same PR as Boot 4.  
- Leave `@MockBean` after Boot 4 cutover.  
- Assume `@SpringBootTest` alone wires MockMvc / TestRestTemplate.  
- Add `@AutoConfigureMockMvc` to every `@SpringBootTest`, or convert a port-based test to MockMvc to get it compiling.  
- Run a rewrite loop without the dry-run list, over build/generated output, or with unanchored patterns.  
- Force a pre-migration status for empty-segment URLs with catch-all mappings or duplicate `@ExceptionHandler` methods.
- Leave a `ServletException` or `Exception` handler owning `NoResourceFoundException`.  
- Change production error bodies, or apply the empty-body `ResponseEntityExceptionHandler` overrides, before the human chooses `errorBodyContract`.  
- Fold a full Cucumber 8 modernization into this phase without using phase 16.  
- Pin faker only in one test while generators still randomize status/amount.  
- Run Cucumber in the same parallel worker / CI job as unit tests when they share DB/WireMock/emulator state.

## Risk

`SAFE_AUTO` for starters / MockitoBean / JsonMapper / faker pins, after phase 36, and for test-assertion updates after the human chooses `errorBodyContract=problem-detail`. `ASK_HUMAN` before any production `@ControllerAdvice` override that changes an error body or status. Cucumber 8 → phase 16.

## Rollback

Revert the test dependency and import commit. If a human-approved advice override landed, revert those production `@ControllerAdvice` files in the same rollback set.

## Done when

The latest compile ran test compilation (`compileTestKotlin` / `compileTestJava` on JDK **25**) and shows no errors owned by this phase. Test outcomes are judged in Stage C ([13-verification.md](13-verification.md)). Cucumber tracked via phase 16 handoff if applicable.

## Handoff

`phase36Gate=pass; testsCompile=yes|no; mockitoBean=yes|n/a; mockBeanResidual=0|[files]; portTestsMockMvc=none-added|[files]; errorBodyContract=empty|problem-detail|n/a; adviceFiles=[production paths]|n/a; emptySegment404=asserted|override|n/a; servlet404=specific|left|n/a; jsonPath=3.x|n/a; cucumberPhase=16|n/a`
