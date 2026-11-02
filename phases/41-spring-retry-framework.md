# 41 — Spring Retry → Framework 7 resilient methods

Boot 4 ships on **Spring Framework 7**. The managed and recommended retry API is built into **`spring-core`** / **`spring-context`** (`@EnableResilientMethods`, `org.springframework.resilience.annotation`, `org.springframework.core.retry`). Boot no longer manages `org.springframework.retry:spring-retry` or `spring-boot-starter-retry`.

An explicit `spring-retry` coordinate can still be declared and can still resolve as a third-party dependency. That path is possible, not managed, and not recommended. This phase removes it and moves application code onto Framework resilient methods unless a human records a written exception to keep the explicit library. Do not bump `spring-retry` onto a newer line to “support Boot 4”.

**Not this phase:** Resilience4j (`resilience4j-spring-boot3` / `boot4`) → [40-resilience4j-boot4.md](40-resilience4j-boot4.md). A service may need **both** phases when it uses Spring Retry **and** Resilience4j (uncommon but valid).

## Detect

Apply when any of:

- Dependency `org.springframework.retry:spring-retry` or `spring-boot-starter-retry`
- `@EnableRetry` (`org.springframework.retry.annotation`)
- `@Retryable` / `@Recover` / `@Backoff` from `org.springframework.retry.annotation`
- `org.springframework.retry.support.RetryTemplate` or other `org.springframework.retry.*` types in application code
- XML / Java config importing `RetryConfiguration` from Spring Retry

Skip when:

- Inventory finds **only** Resilience4j (`@Retry` from Resilience4j, `resilience4j-retry`) and **no** Spring Retry artifacts above → use [40](40-resilience4j-boot4.md) only
- No Spring Retry dependency and no `org.springframework.retry` imports in **application** code (starters like AMQP/Kafka/Integration on Boot 4 bring Framework retry transitively — do not “migrate” what the portfolio already replaced)

Catalog: `spring-retry` → **drop** / **migrate** via this phase (not [12](12-dependency-bump-queue.md)).

### Annotation-enable-only (zero call sites)

When the only signals are `@EnableRetry` plus `spring-retry` and/or `spring-boot-starter-retry`, and `src/main` plus `src/test` have **zero** `@Retryable`, `@Recover`, `@Backoff`, and `RetryTemplate`:

- `SAFE_AUTO`
- One build edit: remove the Spring Retry coordinate
- One annotation edit: `@EnableRetry` → `@EnableResilientMethods` (import `org.springframework.resilience.annotation.EnableResilientMethods`)
- `maxRetriesReconciled=n/a` — there are no attempt counts to copy
- `recoverMigrated=none`
- Do not add a `RetryTemplate`, a listener, or `proxyTargetClass` speculatively

```text
rg -n '@Retryable|@Recover|@Backoff|RetryTemplate|org\.springframework\.retry' src/main src/test
```

A hit that is only the `@EnableRetry` import and annotation is still this path. Any other hit is the full migration below, not this shortcut.

## Before → After

### Dependencies (Gradle)

```gradle
// BEFORE
implementation 'org.springframework.boot:spring-boot-starter-aop'
implementation 'org.springframework.retry:spring-retry'
// or
implementation 'org.springframework.boot:spring-boot-starter-retry'

// AFTER — recommended: no spring-retry artifact; keep AOP/aspectj only if other features need it
// Retry APIs come from spring-context on the Boot 4 BOM (no extra retry dependency)
```

Maven: remove `spring-retry` / `spring-boot-starter-retry` on the recommended path; do not pin a replacement artifact. Keeping an explicit `spring-retry` dependency is possible and is a human exception, not the default.

### Enable processing

```java
// BEFORE
import org.springframework.retry.annotation.EnableRetry;

@SpringBootApplication
@EnableRetry
public class Application { }

// AFTER
import org.springframework.resilience.annotation.EnableResilientMethods;

@SpringBootApplication
@EnableResilientMethods
public class Application { }
```

If `@Retryable` on **concrete classes** that implement interfaces and retries do not fire (proxy gap on Boot 4), try `@EnableResilientMethods(proxyTargetClass = true)` or `@Proxyable` on affected beans — confirm with human smoke ([Framework resilience docs](https://docs.spring.io/spring-framework/reference/core/resilience.html)).

### Declarative `@Retryable` (import + attributes)

```java
// BEFORE (Spring Retry)
import org.springframework.retry.annotation.Backoff;
import org.springframework.retry.annotation.Retryable;

@Retryable(
    retryFor = RemoteAccessException.class,
    maxAttempts = 4,
    backoff = @Backoff(delay = 100, multiplier = 2, maxDelay = 1000))
public void callRemote() { ... }

// AFTER (Framework 7)
import org.springframework.resilience.annotation.Retryable;

@Retryable(
    includes = RemoteAccessException.class,
    maxRetries = 3,          // owner-accepted example only — not an automatic rewrite of maxAttempts
    delay = 100,
    multiplier = 2,
    maxDelay = 1000)
public void callRemote() { ... }
```

| Spring Retry | Framework 7 `@Retryable` |
|--------------|---------------------------|
| `retryFor` / `value` | `includes` (or single-type shortcut `@Retryable(RemoteAccessException.class)`) |
| `noRetryFor` | `excludes` |
| `maxAttempts` | **`maxRetries`** — **different meaning** (see below) |
| `@Backoff(delay, multiplier, maxDelay, …)` | `delay`, `multiplier`, `maxDelay`, `jitter` on `@Retryable` (ms for delay attributes) |
| `exceptionExpression` | `predicate` → `MethodRetryPredicate` or SpEL string variants on annotation |
| Reactive return types | Supported on Framework `@Retryable` (Reactor `Retry` decoration) |

**Attempt semantics (ASK_HUMAN when copying numbers):**

- **Spring Retry `maxAttempts`:** total invocations including the first try (e.g. `maxAttempts = 3` → up to **3** calls).
- **Framework `maxRetries`:** retries **after** the first failure; total invocations = **1 + maxRetries** (e.g. `maxRetries = 3` → up to **4** calls).

When migrating, **reconcile counts with the service owner** — do not assume `maxAttempts` maps 1:1 to `maxRetries`.

### `@Recover` (no direct replacement)

Spring Retry’s `@Recover` methods are **not** ported to Framework 7.

```java
// BEFORE
@Retryable(retryFor = SQLException.class, maxAttempts = 3)
public Data load() { ... }

@Recover
public Data recover(SQLException ex) {
    return Data.empty();
}
```

**After — pick one pattern (human choice):**

1. **Logging / metrics only** — listen for `MethodRetryEvent`; when `event.isRetryAborted()`, handle final failure (does not change return value).
2. **Fallback return value** — use programmatic `RetryTemplate` and `try` / `catch` around `invoke`, or inline `try` / `catch` in the method (separate retry policy from non-retryable fallback).
3. **Complex recovery** — `SPIKE_FIRST` with human; do not fake `@Recover` with unrelated aspects.

### Programmatic `RetryTemplate`

```java
// BEFORE
import org.springframework.retry.backoff.ExponentialBackOffPolicy;
import org.springframework.retry.policy.SimpleRetryPolicy;
import org.springframework.retry.support.RetryTemplate;

RetryTemplate template = new RetryTemplate();
// ...

// AFTER
import org.springframework.core.retry.RetryPolicy;
import org.springframework.core.retry.RetryTemplate;

RetryPolicy policy = RetryPolicy.builder()
    .includes(RemoteAccessException.class)
    .maxRetries(3)
    .delay(java.time.Duration.ofMillis(100))
    .multiplier(2)
    .maxDelay(java.time.Duration.ofSeconds(1))
    .build();

RetryTemplate template = new RetryTemplate(policy);
template.invoke(() -> { ... });
```

Use `invoke` when the **last** exception should propagate; use `execute` when the caller handles `org.springframework.core.retry.RetryException` and inspects all attempts. Register `RetryListener` on the template for per-attempt tracing (replaces some Spring Retry listener use cases).

### Configuration properties

Remove `spring.retry.*` if present. Framework resilient methods are configured via annotation attributes (and SpEL string variants), not the old Boot RetryProperties namespace. If the service externalized retry via `spring.retry`, map keys to `@ConfigurationProperties` on a dedicated bean or document env changes — **`ASK_HUMAN`**.

### Portfolio starters (Boot 4)

Spring AMQP, Kafka, Integration, and Batch on Boot 4 already target Framework retry internally. After removing `spring-retry`, **recompile** and fix **application** imports only; do not duplicate retry libraries to “help” a starter. Kafka's test starter, `@EmbeddedKafka`, and `BackOff` on Kafka types are [44-spring-kafka-4.md](44-spring-kafka-4.md). A listener `@Retryable` stays in this phase.

## Steps

1. Inventory: Gradle/Maven deps, `@EnableRetry`, `@Retryable` / `@Recover`, `RetryTemplate` beans, XML, tests using `org.springframework.retry`. If the only hits are the dependency and `@EnableRetry`, use the annotation-enable-only path and stop after steps 2–3.  
2. Remove `spring-retry` and `spring-boot-starter-retry` on the recommended path. Do not add a new retry dependency. An explicit keep is a recorded human exception, not a version bump.  
3. Replace `@EnableRetry` with `@EnableResilientMethods` on the main `@Configuration` / `@SpringBootApplication` (or register `RetryAnnotationBeanPostProcessor` only if the service already used low-level Spring Retry wiring). On the zero-call-site path, `maxRetriesReconciled=n/a`.  
4. When call sites exist: bulk-replace imports `org.springframework.retry.annotation` → `org.springframework.resilience.annotation`; map annotation attributes per table; **reconcile `maxAttempts` → `maxRetries` with human**.  
5. Migrate each `@Recover` usage per human-approved pattern (event listener vs programmatic vs inline catch).  
6. Migrate `RetryTemplate` / policies to `org.springframework.core.retry.*`.  
7. Drop unused `spring.retry` properties; document any env contract changes in phase notes.  
8. Compile via the orchestrator; name **one** retry path (declarative + programmatic if both exist) for the Stage C smoke.  
9. If Resilience4j is also present, run [40](40-resilience4j-boot4.md) separately — do not merge the two stacks.

## Do not

- Bump `spring-retry` to a newer line “for Boot 4”. An explicit dependency is possible, but Boot does not manage it and this pack does not recommend it.  
- Treat the zero-call-site path as a full `@Retryable` migration (no `maxRetries` math, no invented `RetryTemplate`).  
- Confuse Resilience4j `@Retry` with Framework `@Retryable` — different annotations and modules.  
- Copy `maxAttempts` to `maxRetries` without semantic review.  
- Remove circuit breakers / bulkheads because Spring Retry was removed — use Resilience4j or other policy, not silent deletion.  
- Rely on self-invocation (`this.retryableMethod()`) — same proxy limitation as before; fix call paths or inject self.  
- File Spring Retry bumps in [12](12-dependency-bump-queue.md).

## Risk

`SAFE_AUTO` only for the annotation-enable-only path (`@EnableRetry` + dependency, zero `@Retryable` / `@Recover` / `@Backoff` / `RetryTemplate`): dependency removal plus `@EnableResilientMethods`, `maxRetriesReconciled=n/a`.

`ASK_HUMAN` before any `maxAttempts` → `maxRetries` edit, including annotation-only `@Retryable` with simple `includes` and no `@Recover`. The same gate covers any `@Recover`, stateful retry, custom `RetryListener` / `RetryContext`, XML retry config, property-driven policies, reactive pipelines with custom recovery, or proxy/CGLIB issues after cutover. Do not apply `maxRetries = maxAttempts` or `maxRetries = maxAttempts - 1` until the owner accepts that call count.

`SPIKE_FIRST` when recovery changes business outcomes (fallback return values, idempotent + integrity-violation combos, or replacing Spring Integration stateful retry advice).

## Rollback

Restore `spring-retry` / `spring-boot-starter-retry` and Spring Retry imports together with pre-migration `@EnableRetry` in one revert commit.

## Done when

On the recommended path, no `org.springframework.retry` on the application classpath (an explicit keep is a recorded human exception, not the default). `@EnableResilientMethods` (or explicit post-processors) enabled. Zero-call-site path: one build line and the enable-annotation swap, `maxRetriesReconciled=n/a`, `recoverMigrated=none`. Otherwise application code compiles against Framework resilience APIs; human smoke deferred or green; `@Recover` either removed with approved replacement or explicitly deferred with sign-off.

## Handoff

`springRetry=removed|explicit-exception|n/a; path=enable-only|full; enableResilientMethods=yes|n/a; recoverMigrated=count|none|deferred; maxRetriesReconciled=yes|human_pending|n/a; smoke=green|deferred`
