# 36 — Remove JUnit 4 (JUnit Jupiter)

JUnit 4 sources and the JUnit 4 dependency are removed. The suite lands on **JUnit Jupiter** as managed by the Spring Boot 4 BOM (**JUnit 6**). Jupiter’s packages stay `org.junit.jupiter` / `org.junit.platform`.

Spring Boot test starters, `@MockitoBean`, and Jackson in tests are [09-testing.md](09-testing.md). Testcontainers 2.x artifact renames stay in [25-testcontainers-2.md](25-testcontainers-2.md). MockServer 5 → 9 stays in [27-mockserver-9.md](27-mockserver-9.md). Cucumber 7 → 8 stays in [16-cucumber-8.md](16-cucumber-8.md).

## Detect

Apply when the service has any test source set, `spring-boot-starter-test` / `spring-boot-starter-test-classic`, or any `junit` / `org.junit` coordinate.

This phase **enforces Boot-managed JUnit 6** on every such service. A suite that already imports `org.junit.jupiter` is not done, and neither is an explicit Jupiter **5.x** or Platform **1.x** pin. Skip only when there are no tests and no JUnit coordinates.

The JUnit 4 rewrite runs when any of these are also present:

- Imports of `org.junit.Test`, `org.junit.Before`, `org.junit.After`, `org.junit.BeforeClass`, `org.junit.AfterClass`, `org.junit.Ignore`, `org.junit.Assert`, `org.junit.Assume`, `org.junit.runner`, `org.junit.rules`, `org.junit.experimental`, or `junit.framework`
- `@RunWith`, `@Rule`, `@ClassRule`
- Coordinates `junit:junit`, `org.junit.vintage:junit-vintage-engine`, `org.junit.jupiter:junit-jupiter-migrationsupport`, `org.junit.platform:junit-platform-runner`, `org.junit.platform:junit-platform-jfr`, `org.junit.platform:junit-platform-suite-commons`
- `io.cucumber:cucumber-junit`, `com.tngtech.archunit:archunit-junit4`, `org.powermock:*`
- Gradle `useJUnit()` (the JUnit 4 task mode) or Maven Surefire `surefire-junit47` / a JUnit 4 provider

When that list is empty, still run the JUnit 6 half below. Do not hand off `junit4=n/a` with a 5.x pin still in the build.

Run after [01-platform-baseline.md](01-platform-baseline.md) and, when `*.kt` exists, after [31-kotlin.md](31-kotlin.md). JUnit 6 requires Kotlin 2.1+.

### Runner versus glue (Cucumber and similar frameworks)

Only the **runner** class is a JUnit 4 artifact. Step definitions and hooks (the **glue**) belong to the framework and do not move to Jupiter. Classify before editing:

```bash
# Runner: JUnit 4 entry points
rg -n '@RunWith\((Cucumber|CucumberWithSerenity)|io\.cucumber\.junit\.' --glob '*.java' --glob '*.kt' src
# Glue: framework annotations — not JUnit 4, leave them alone
rg -n 'io\.cucumber\.java\.(en\.)?|@CucumberContextConfiguration' --glob '*.java' --glob '*.kt' src
# Glue that still calls JUnit 4 assertions — rewrite these
rg -l 'io\.cucumber\.java' --glob '*.java' --glob '*.kt' src | xargs rg -n 'org\.junit\.(Assert|Assume)'
```

| Kind | Signals | Action |
|------|---------|--------|
| Runner | `@RunWith(Cucumber.class)`, `@CucumberOptions`, `io.cucumber.junit.*` | Replace with a Platform `@Suite` class (below) |
| Glue | `io.cucumber.java.Before` / `After`, `@Given` / `@When` / `@Then`, `@CucumberContextConfiguration` | Leave as is. `io.cucumber.java.Before` is not `org.junit.Before` |
| Glue using JUnit 4 asserts | `org.junit.Assert` / `Assume` imports in step classes | Rewrite the assertions (message order below); do not touch the step annotations |

### Inventory table

Record the counts in phase notes before step 2. The Risk section reads this table.

| Bucket | Files | Path |
|--------|-------|------|
| Annotation-only (`@Test`, `@Before*`, `@After*`, `@Ignore`, `@Category`, redundant `SpringRunner`) | N | `SAFE_AUTO` |
| `org.junit.Assert` / `Assume` **with** a message argument | N | Human approval |
| `org.junit.Assert` without a message | N | Import swap |
| Parameterized runners | N | Human approval |
| `@Rule` / `@ClassRule` (incl. `TemporaryFolder`, `ExpectedException`, Testcontainers/WireMock/MockServer rules) | N | Human approval |
| Third-party runners (Cucumber runner, `MockitoJUnitRunner`, `SpringRunner` without a Boot test annotation) | N | Mapping table |
| PowerMock | N | Human approval |
| Theories | N | Human approval |
| Custom `Runner` / `Rule` declared in this repo | N | Human approval |
| Legacy `mockwebserver` (OkHttp 4.x or 5.x artifact) | N | Phase 28 replaces it with `mockwebserver3` in the same Stage A wave |

## Before → After

### Dependencies (Gradle)

```gradle
// BEFORE
testImplementation 'junit:junit:4.13.2'
testRuntimeOnly 'org.junit.vintage:junit-vintage-engine'
test {
    useJUnit()
}

// AFTER — no version. Boot 4.1.1 manages org.junit:junit-bom 6.0.3
// (Jupiter, Platform, and Vintage share that version). Do not set
// junit-jupiter.version, and do not pin 5.x or a newer 6.1.x.
test {
    useJUnitPlatform()
}
```

### JUnit 6 version (always)

Boot 4 moves the test starter from Jupiter 5 / Platform 1.x onto **JUnit 6**. Spring Boot **4.1.1** sets `junitJupiterVersion=6.0.3`. An explicit version in the service build wins over that BOM, so a `5.11.4` pin stays on JUnit 5 after the Boot bump and the suite never reaches 6.

```gradle
// BEFORE — the pin beats the Boot BOM
testImplementation "org.junit.jupiter:junit-jupiter:5.11.4"
ext["junit-jupiter.version"] = "5.10.2"

// AFTER
testImplementation "org.junit.jupiter:junit-jupiter"
```

Delete every version on `org.junit.jupiter:*` and `org.junit.platform:*`. Delete service properties `junit-jupiter.version`, `junit-platform.version`, and `junit-vintage.version`. Delete a direct `org.junit:junit-bom` import. Delete removed modules: `junit-platform-runner`, `junit-platform-jfr` (events now live in `junit-platform-launcher`), and `junit-platform-suite-commons` (classes now live in `junit-platform-suite`).

`spring-boot-starter-test` already brings the launcher. Add `testRuntimeOnly("org.junit.platform:junit-platform-launcher")` with **no version** only when a test task uses `useJUnitPlatform()` and does not depend on the Boot test starter.

That table is the JUnit 5 → 6 source migration. JUnit 6.0 kept the Jupiter packages, so a test that already uses `@Test`, `@BeforeEach`, and `org.junit.jupiter.api.Assertions` is already on the JUnit 6 programming model once the BOM resolves. Rewrite only the rows that match. Do not restyle the rest of the suite.

Guides that tell you to set `<version>6.0.0</version>` and to add `junit-vintage-engine` 6.0.0 are the wrong end state here. Boot **4.1.1** manages **6.0.3** with no version in the service build, and this phase removes JUnit 4 instead of keeping Vintage.

Mechanical edits, from the JUnit 6.0 release notes. These are `SAFE_AUTO`:

| Before | After |
|--------|-------|
| `MethodOrderer.Alphanumeric` | `MethodOrderer.MethodName` |
| `ExtensionContext.Store.getOrComputeIfAbsent` / `NamespacedHierarchicalStore.getOrComputeIfAbsent` | `computeIfAbsent` (same arguments) |
| `@CsvFileSource(..., lineSeparator = …)` | delete `lineSeparator`. Endings `\r`, `\n`, and `\r\n` are detected |
| `@UseTechnicalNames` on a `@Suite` | delete the annotation. The annotation was removed |
| `@EnabledOnJre` / `@DisabledOnJre` / range annotations using `JRE.JAVA_8` … `JRE.JAVA_16` | delete the annotation. It no longer selects a JDK this service runs. Deleting the test itself is `ASK_HUMAN` |
| `@EnabledForJreRange(min = JRE.JAVA_17)` (or `minVersion = 17`) | delete it. 17 is the default minimum, and declaring it is rejected |
| `junit.jupiter.tempdir.scope` in `junit-platform.properties` | delete the key |
| `junit.jupiter.params.arguments.conversion.locale.format` | delete the key. Locale conversion uses `Locale.forLanguageTag` (BCP 47) |
| `junit.platform.reflection.search.useLegacySemantics` | delete the key. Field and method lookup follows Java language rules |
| `InvocationInterceptor.interceptDynamicTest(Invocation, ExtensionContext)` | delete the override when it only calls `invocation.proceed()`. An override with its own behavior is `ASK_HUMAN` |
| Maven Surefire or Failsafe pinned below 3 | delete the pin. JUnit 6 does not run on Surefire 2. Boot's parent supplies 3.x |

`@BeforeEach`, `@AfterEach`, and `@Test` methods must not be `private`. JUnit 6 reports that as a discovery issue. Treat any discovery issue after the engine moves to 6 as a defect, whether or not JUnit 4 was present.

Two behavior changes are not source rewrites. Record them for Stage C and edit only when a test fails:

- `@Nested` classes in one enclosing type run in a deterministic order that is not the old source order. `@TestMethodOrder` on the outer class is now inherited by nested classes. Do not add `@TestClassOrder` to freeze the previous order unless a failed test needs it and the human agrees.
- `@CsvSource` / `@CsvFileSource` use FastCSV. A value with characters after the closing quote fails. `nullValues` and whitespace trimming also apply to header fields. Exception text for a bad CSV line can change. Leave passing CSV fixtures alone.

Apply the same removal on `integrationTest`, `cucumberTest`, and any other `Test` task. Maven: delete `junit:junit`, `junit-vintage-engine`, and a Surefire JUnit 4 provider; Boot’s parent already selects the JUnit Platform provider. See [stubs/maven.md](../stubs/maven.md).

After direct coordinates are gone, exclude Vintage and `junit:junit` from the **test runtime** classpath so JUnit 4 tests cannot run accidentally.

```gradle
// Runtime guard — Vintage must never execute tests
configurations.matching {
    def n = it.name.toLowerCase()
    n.contains('test') && n.endsWith('runtimeclasspath')
}.configureEach {
    exclude group: 'org.junit.vintage', module: 'junit-vintage-engine'
    exclude group: 'junit', module: 'junit'
}
```

#### MockWebServer

OkHttp **4.x** `com.squareup.okhttp3:mockwebserver` and the legacy **5.x** artifact of the same name both extend `org.junit.rules.ExternalResource`, and the **5.5.0** POM still depends on `junit:junit:4.13.2`. When that artifact is present, phase 28's Stage A slice replaces it with `mockwebserver3` in the same dependency wave that removes `junit:junit` here. No temporary JUnit 4 jar is needed. The MockWebServer test-source moves belong to phase 28's Stage B slice; compile errors in them are owned by 28, not this phase.

Fix the library that pulled JUnit 4 as a **runtime** dependency (Cucumber JUnit 4 runner, ArchUnit junit4, PowerMock). The exclude is a guard, not a reason to keep JUnit 4 **test** call sites. Discovery rules for non-private lifecycle methods are in the JUnit 6 section above.

### Annotations

| JUnit 4 | Jupiter |
|---------|---------|
| `@Before` / `@After` | `@BeforeEach` / `@AfterEach` |
| `@BeforeClass` / `@AfterClass` | `@BeforeAll` / `@AfterAll` (remain static) |
| `@Ignore` | `@Disabled` |
| `@Category` | `@Tag` |
| `@FixMethodOrder(MethodSorters.NAME_ASCENDING)` | `@TestMethodOrder(MethodOrderer.MethodName.class)` |
| `@RunWith(SpringRunner.class)` or `SpringJUnit4ClassRunner` | Delete when `@SpringBootTest` or a slice annotation is already present (those meta-annotate `SpringExtension`). Otherwise `@ExtendWith(SpringExtension.class)`. |
| `SpringClassRule` + `SpringMethodRule` | `@ExtendWith(SpringExtension.class)` |
| `@RunWith(MockitoJUnitRunner.class)` or `MockitoRule` | `@ExtendWith(MockitoExtension.class)` |
| `@Test(expected = …)` or `ExpectedException` | `Assertions.assertThrows` |
| `@Test(timeout = …)` or `Timeout` rule | `@Timeout` or `assertTimeout` |
| `TemporaryFolder` | `@TempDir` |
| `TestName` | `TestInfo` method parameter |
| `@RunWith(Enclosed.class)` | `@Nested` |
| `@RunWith(Suite.class)` + `@Suite.SuiteClasses` | `org.junit.platform.suite.api.@Suite` + `@SelectClasses` (BOM-managed `junit-platform-suite`; the old `junit-platform-runner` module is gone in JUnit 6) |
| `@RunWith(JUnitPlatform.class)` | Delete the runner. Discovery is `useJUnitPlatform()`. |

Leave test methods `public` if they already are. `@BeforeAll` / `@AfterAll` stay static.

### Assertions (message argument order)

`org.junit.Assert` and `org.junit.Assume` ship in `junit:junit`. They cannot stay once that jar is removed.

```java
// BEFORE — failure message is the first argument
import static org.junit.Assert.assertEquals;
assertEquals("size", 2, actual.size());

// AFTER — failure message is the last argument
import static org.junit.jupiter.api.Assertions.assertEquals;
assertEquals(2, actual.size(), "size");
```

`assertEquals(expected, actual)` with no message keeps that order. `org.junit.Assert.assertThat` moves to `org.hamcrest.MatcherAssert.assertThat`. AssertJ (`assertThat` from AssertJ) can stay; it is already on `spring-boot-starter-test`.

### Parameterized

```java
// BEFORE
@RunWith(Parameterized.class)
public class PriceTest {
    @Parameterized.Parameters(name = "{0}")
    public static Collection<Object[]> data() {
        return Arrays.asList(new Object[][] {{1, 2}});
    }
    @Parameterized.Parameter(0) public int input;
    @Parameterized.Parameter(1) public int expected;

    @Test public void converts() { assertEquals(expected, input + 1); }
}

// AFTER
class PriceTest {
    @ParameterizedTest(name = "{0}")
    @MethodSource("data")
    void converts(int input, int expected) {
        assertEquals(expected, input + 1);
    }
    static Stream<Arguments> data() {
        return Stream.of(Arguments.of(1, 2));
    }
}
```

`@Theory` / `@DataPoint` have no Jupiter equivalent. Stop and ask the human.

### Library runners that are JUnit 4 (coordinate bumps stay in their phases)

```java
// Testcontainers — still 1.x types. Module renames are phase 25.
@Testcontainers
class ExampleIT {
    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16-alpine");
}

// WireMock 3 — stay on the 3.x line (WireMock 4 is deferred)
@RegisterExtension
static WireMockExtension wireMock = WireMockExtension.newInstance()
    .options(wireMockConfig().port(8089))
    .build();

// MockServer — same major's Jupiter module. The 5 → 9 bump is phase 27.
@ExtendWith(MockServerExtension.class)
class UpstreamContractTest { }
```

```gradle
// Cucumber — stay on the current 7.x line. Cucumber 8 idioms are phase 16.
// BEFORE: io.cucumber:cucumber-junit  (JUnit 4 runner)
// AFTER:
testImplementation "io.cucumber:cucumber-junit-platform-engine:${cucumberVersion}"
testImplementation 'org.junit.platform:junit-platform-suite' // BOM version
```

```java
@Suite
@IncludeEngines("cucumber")
@SelectClasspathResource("features")
@ConfigurationParameter(key = GLUE_PROPERTY_NAME, value = "com.example")
public class CucumberRunner {}
```

`@SelectClasspathResource("features")` resolves against the **test runtime classpath**, not a filesystem path. Feature files must be on the classpath of the task that runs the suite:

```text
src/test/resources/features/orders.feature      → classpath "features"            (test task)
src/cucumberTest/resources/features/…            → classpath "features"            (cucumberTest source set)
src/test/resources/com/example/features/…        → @SelectClasspathResource("com/example/features")
```

```gradle
// Dedicated task: only the suite engine (which launches Cucumber), only the suite class
tasks.register('cucumberTest', Test) {
    testClassesDirs = sourceSets.test.output.classesDirs   // or the cucumberTest source set
    classpath = sourceSets.test.runtimeClasspath
    useJUnitPlatform { includeEngines 'junit-platform-suite' }
    filter { includeTestsMatching '*CucumberRunner' }
}
```

If the suite runs but reports zero scenarios, check that the selected resource path exists on that task's runtime classpath, and that the glue package in `GLUE_PROPERTY_NAME` matches the step-definition package.

`com.tngtech.archunit:archunit-junit4` → `archunit-junit5` (the artifact id keeps the “junit5” name on the JUnit 6 line). Version pin, if needed, comes from [DEPENDENCY-CATALOG.md](../references/DEPENDENCY-CATALOG.md) via [12-dependency-bump-queue.md](12-dependency-bump-queue.md).

## Steps

1. Stage A, every service this phase applies to: strip JUnit versions and the removed modules in the JUnit 6 section. Switch every test task to `useJUnitPlatform()`. Add the Vintage / `junit:junit` runtime exclude. Do not add a 6.x pin.
2. Inventory every JUnit 4 import, `@RunWith` / `@Rule` / `@ClassRule`, and the coordinates in Detect. Classify runner versus glue, then fill the inventory table in phase notes. When the JUnit 4 list is empty, record zeros and continue at step 7.
3. Annotation-only buckets (JUnit 4 `@Test` / `@Before*` / `@After*` / `@Ignore` / `@Category`, plus `SpringRunner` deleted because a Boot test annotation is present) proceed in this phase.
4. Stop for a human before rewriting message-first asserts, `@RunWith(Parameterized.class)`, `@Rule` / `@ClassRule`, Theories, PowerMock, or a custom runner/rule. List each file. PowerMock has no Jupiter runner; the usual replacement for static mocks is Mockito’s `MockedStatic`, and that is a behavior change the human accepts.
5. Rewrite approved files with the mappings above. Convert Testcontainers rules, `WireMockRule`, `MockServerRule`, and `cucumber-junit` here. Leave Testcontainers 2.x renames, MockServer 9, Cucumber 8, and `@MockBean` → `@MockitoBean` to their phases.
6. Remove `junit:junit`, `junit-vintage-engine`, `junit-jupiter-migrationsupport`, `junit-platform-runner`, `junit-platform-jfr`, `junit-platform-suite-commons`, and `cucumber-junit`. Add the replacement coordinates named above (`junit-platform-suite`, `cucumber-junit-platform-engine`, `archunit-junit5`) with no JUnit version.
7. Apply every row of the JUnit 6 API table, including `junit-platform.properties`. Rewrite `MethodOrderer.Alphanumeric`, `getOrComputeIfAbsent`, `@CsvFileSource` `lineSeparator`, and `@UseTechnicalNames`. Delete the three removed configuration keys. Remove redundant Java-17 JRE conditions. Stop before deleting a test whose only reason to exist was `@EnabledOnJre` on Java 8–16, and before replacing an `interceptDynamicTest` override that does more than `invocation.proceed()`.
8. Grep sources and build files. Both greps are empty.

```bash
rg -n 'org\.junit\.Test|org\.junit\.Assert|org\.junit\.Assume|org\.junit\.runner|org\.junit\.rules|org\.junit\.experimental|junit\.framework|MethodOrderer\.Alphanumeric|getOrComputeIfAbsent|UseTechnicalNames|lineSeparator|interceptDynamicTest|tempdir\.scope|arguments\.conversion\.locale\.format|useLegacySemantics' \
  --glob '*.java' --glob '*.kt' --glob '*.properties' src
rg -n -g '*.gradle*' -g '*.kts' -g '*.toml' -g 'gradle.properties' -g 'pom.xml' \
  -e 'junit-jupiter(\.version)?[^#\n]{0,40}5\.' \
  -e 'junit-platform(\.version)?[^#\n]{0,40}1\.' \
  -e 'junit-jupiter\.version' \
  -e 'junit-platform\.version' \
  -e 'junit-vintage\.version' \
  -e 'org\.junit:junit-bom' \
  -e 'junit:junit' \
  -e 'junit-vintage' \
  -e 'junit-platform-runner' \
  -e 'junit-platform-jfr' \
  -e 'junit-platform-suite-commons' \
  -e 'migrationsupport'
```

The second grep is empty except the two `exclude` lines in the runtime guard (`org.junit.vintage:junit-vintage-engine` and `junit:junit`). A comment that names `junit-jupiter.version` still fails the grep: delete the pin and rephrase the comment so it does not contain the property name. `lineSeparator` hits that are not `@CsvFileSource` belong to their own phase; record them and do not edit them here.

9. The orchestrator's next compile shows this phase's remaining test-compile errors once main compiles. A resolved `org.junit.jupiter:junit-jupiter-api` on 5.x means a pin is still winning; return to step 1. The Boot **4.1.1** line is **6.0.3**.

Optional accelerator for the JUnit 4 half: OpenRewrite `org.openrewrite.java.testing.junit5.JUnit4to5Migration`, then the same greps. The recipe can leave `org.junit.Assert` and does not delete Vintage or a Jupiter 5 pin. The greps are the exit gate.

## Do not

- Pin `org.junit.jupiter` or `org.junit.platform` to 5.x, to Platform 1.x, to **6.0.0** because a guide shows that version, or to a 6.1.x patch ahead of the Boot BOM. Boot **4.1.1** manages **6.0.3**. Omit the version.
- Add `junit-vintage-engine` because a JUnit 6 guide still lists it for leftover JUnit 4 tests. This phase removes those tests.
- Rewrite Jupiter tests that do not match the JUnit 6 API table. `@Test` and `org.junit.jupiter.api.Assertions` stay as they are.
- Skip this phase because sources already use `org.junit.jupiter`. That suite is still on JUnit 5 until the pin is gone and the BOM line resolves.
- Add `junit-vintage-engine` or `junit-jupiter-migrationsupport` (`@EnableRuleMigrationSupport`) so JUnit 4 keeps running. Vintage is deprecated on JUnit 6 and is not this phase’s outcome. A green `useJUnitPlatform()` run does not count while `org.junit.Test` classes remain: without Vintage they are silently undiscovered.
- Treat `org.junit.jupiter` or `org.junit.platform` as JUnit 4 and delete them.
- Swap assertion argument order without checking whether the original call passed a message first.
- Change test method visibility as a drive-by.
- Take Testcontainers 2, MockServer 9, Cucumber 8, WireMock 4, or `@MockitoBean` in this phase.
- Hand off while PowerMock, Theories, or a custom runner is still on the classpath.
- Keep `junit:junit` for MockWebServer in any form (`testImplementation`, `testCompileOnly`, or a dropped exclude). Phase 28 replaces the artifact instead.
- Rewrite Cucumber glue annotations (`io.cucumber.java.*`) as if they were JUnit 4.

## Risk

`ASK_HUMAN` when the inventory contains message-first asserts, `@Rule` / `@ClassRule`, parameterized runners, Theories, PowerMock, or a custom runner/rule.

`SAFE_AUTO` for the JUnit 6 version strip and the API table, and for the annotation-only JUnit 4 bucket, after the inventory shows nothing else in the human-approval buckets.

On Boot 4, `spring-boot-starter-test` no longer brings Vintage. Leaving JUnit 4 in place drops those tests from discovery. An older IDE test launcher may also fail to start JUnit Platform 6 tests even when the Gradle/Maven run is green; that calls for an IDE upgrade, not a reason to pin JUnit 5. Record the actual error the IDE showed rather than assuming a specific one.

## Rollback

Revert this phase’s commits as one set (test sources and test dependencies together). Restoring `org.junit` imports after `junit:junit` is removed does not compile. Re-adding Vintage is not the rollback.

## Done when

- Both step 8 greps are empty.
- No first-party source imports JUnit 4 types (`org.junit.*` outside `org.junit.jupiter` / `org.junit.platform`, or `junit.framework`).
- Every test task uses `useJUnitPlatform()`.
- `junit:junit`, `junit-vintage-engine`, `junit-jupiter-migrationsupport`, `junit-platform-runner`, `junit-platform-jfr`, and `junit-platform-suite-commons` are absent from direct dependencies and from every test runtime classpath.
- No service build file sets `junit-jupiter.version`, `junit-platform.version`, or a version on `org.junit.jupiter` / `org.junit.platform`. Resolved `junit-jupiter-api` is **6.x** (Boot **4.1.1** → **6.0.3**).
- The inventory table is recorded in phase notes, and every human-approval bucket is approved and rewritten, or the handoff reads `blocked`.
- The latest compile shows no errors owned by this phase, with test compilation having run.

## Handoff

`junit4=removed|n/a|blocked; junit6=bom|blocked; vintage=absent; junit4Jar=absent; assertMessages=rewritten|n/a; rules=rewritten|n/a; powermock=removed|n/a; cucumberRunner=platform|n/a; glueAsserts=rewritten|n/a`

`junit6=bom` only when the step 8 pin grep is empty and resolution is JUnit 6. `junit4=n/a` is allowed when no JUnit 4 signals existed. `junit6=n/a` is not.
