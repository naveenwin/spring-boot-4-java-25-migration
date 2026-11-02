# 42 — Pre-migration baseline (Stage 0)

## Detect

Always. Runs after plan approval and before any build or source edit, on the unmodified pre-migration commit and on the JDK the service builds with today (not JDK 25).

## Before → After

Production code and build files do not change. The phase adds at most one test class, `MigrationContextLoadsTest`, when the suite has no single test class that boots the full application context and can run alone.

Match the test engine that is already in the repository. Phase 36 later migrates this class with every other JUnit 4 test.

```java
// JUnit 4 service
import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.junit4.SpringRunner;

@RunWith(SpringRunner.class)
@SpringBootTest
public class MigrationContextLoadsTest {
    @Test
    public void contextLoads() {
    }
}
```

```kotlin
// JUnit Jupiter service (Kotlin)
import org.junit.jupiter.api.Test
import org.springframework.boot.test.context.SpringBootTest

@SpringBootTest
class MigrationContextLoadsTest {
    @Test
    fun contextLoads() {
    }
}
```

An empty `@SpringBootTest` method fails when the application context does not refresh. That failure is the signal.

Copy the class-level setup of the class that owns the context today, so this test boots the same application the suite boots:

```java
// The context owner is a Cucumber configuration class or the smallest @SpringBootTest
@CucumberContextConfiguration
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("test")
@AutoConfigureMockMvc
public class CucumberSpringConfiguration extends IntegrationTestBase { }

// MigrationContextLoadsTest copies the same annotations (not the Cucumber one) and the same base class
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("test")
@AutoConfigureMockMvc
public class MigrationContextLoadsTest extends IntegrationTestBase {
    @Test
    public void contextLoads() {
    }
}
```

Run it alone:

```bash
./gradlew test --tests '<package>.MigrationContextLoadsTest'
mvn -Dtest=MigrationContextLoadsTest -Dsurefire.failIfNoSpecifiedTests=false test
```

Use the test task or source set that already runs the context owner (`integrationTest`, `cucumberTest`, …) when `test` excludes it.

## Steps

1. Confirm a clean working tree. Record the HEAD SHA as `baselineCommit` and the current JDK path as `baselineJdk` in `status.yaml`.
2. Find the context owner: the `@CucumberContextConfiguration` class, otherwise the smallest `@SpringBootTest` class. Note its annotations, base class, profiles, and any static container or emulator setup.
3. If a single existing test class already boots that context and runs alone (for example `*ApplicationTests.contextLoads`), record its selector as `contextTest` and skip step 4.
4. Otherwise add `MigrationContextLoadsTest` in the context owner's source set and package. Copy its class-level annotations, extend its base class when setup lives there, and match its language and test engine. Do not invent a lighter context, mock beans, or exclude auto-configuration. Commit `42-baseline B: add context-load test`.
5. Run the pre-edit captures of every applicable phase whose steps say they must happen before any edit. Store them under `.joker/java-spring-migration/baseline/`:
   - [04-jackson-3.md](04-jackson-3.md) step 1 (mapper inventory and wire-contract baseline)
   - [35-webflux.md](35-webflux.md) Netty version and allocator baseline
6. Return to the orchestrator. The human runs the baseline suite. The orchestrator runs the context test with the pinned command ([COMPILE-GATES.md](../references/COMPILE-GATES.md#stage-0--baseline)).

## Do not

- Fix, skip, or delete failing tests. A baseline failure is a pre-existing fact.
- Edit build files, production code, or test configuration other than the one new class.
- Run the baseline on JDK 25 or after any migration commit.
- Skip the baseline suite because it is slow. The human runs it once, before any migration commit.

## Risk

`SAFE_AUTO`.

`ASK_HUMAN` when the context test needs infrastructure the environment does not have (Docker, an emulator started by a separate task, network access), or when the baseline has failures. The human acknowledges each pre-existing failure once.

## Rollback

Revert the context-test commit.

## Done when

- A `kind: baseline` run exists with `summary.json` and `tests.tsv`, at `baselineCommit`.
- A `kind: context` run shows the context test green on the old code, or its failure is recorded and acknowledged by the human.
- Every pre-edit capture from step 5 is stored.

## Handoff

`baselineRun=<run-id>; baselineCommit=<sha>; tests=<passed>/<total>; preexistingFailures=<n>; contextTest=existing:<selector>|added:<class>; contextRun=green|red-acknowledged; preCaptures=[04,35]|none`
