# 11 — Distributed lock libraries

## Detect

Any of:

- Coordinates such as `com.github.alturkovic:distributed-lock` (JitPack aggregate), `com.github.alturkovic.distributed-lock:*` (module group), ShedLock, or custom JDBC locks
- Annotations / enables: `@JdbcLocked` / `@Locked` / `@EnableJdbcDistributedLock`
- AOP starter: `spring-boot-starter-aop` (Boot 3 name), `spring-boot-starter-aspectj` (Boot 4), **or neither declared** while annotation locks are used
- Messaging + lock together (Pub/Sub, Kafka, etc.) — extra `TaskScheduler` beans risk lock-refresh ambiguity

## Before → After

### Prefer a Boot 4–compatible major before replacing the library

For **alturkovic/distributed-lock**, a Boot 4 line exists:

| Library line | Spring Boot | Java |
|--------------|-------------|------|
| `3.0.0+` | 4.0.2+ | 21+ |
| `2.0.0+` | 3.1.x | 17+ |
| `1.5.x` | 2.4.x | 8 |

**GroupId shape**

| Before (common) | After (Boot 4 JDBC path) |
|-----------------|--------------------------|
| JitPack aggregate `com.github.alturkovic:distributed-lock` + excludes | Module group `com.github.alturkovic.distributed-lock` + `distributed-lock-jdbc` |
| Same module group with redis/mongo siblings | Prefer the single module the service uses (`*-jdbc` / `*-redis` / `*-mongo`) |

```gradle
// BEFORE — JitPack aggregate + excludes (Boot 2/3-era)
implementation('com.github.alturkovic:distributed-lock:1.5.x') {
  exclude group: 'com.github.alturkovic.distributed-lock', module: 'distributed-lock-mongo'
  exclude group: 'com.github.alturkovic.distributed-lock', module: 'distributed-lock-redis'
  exclude group: 'com.github.alturkovic.distributed-lock', module: 'distributed-lock-example'
}

// AFTER — Boot 4: depend on the JDBC module only
implementation 'com.github.alturkovic.distributed-lock:distributed-lock-jdbc:3.0.0'
```

`@EnableJdbcDistributedLock`, `@JdbcLocked`, and `@Interval` keep the same packages/attributes for the common JDBC path (`prefix`, `expression`, `expiration`, `timeout`, `retry`, `refresh`). Optional new attribute on 2.1+/3.x: `throwing` (default `true`).

### Boot 4 AOP starter (required for annotation locks)

Three cases — pick the one that matches Detect:

```gradle
// (a) Rename — Boot 3 declared starter-aop
// BEFORE
implementation 'org.springframework.boot:spring-boot-starter-aop'
// AFTER
implementation 'org.springframework.boot:spring-boot-starter-aspectj'

// (b) Add — Boot 2.7 / lean builds often declare NO AOP starter while using @JdbcLocked
// AFTER (add on Boot 4)
implementation 'org.springframework.boot:spring-boot-starter-aspectj'

// (c) Already on aspectj — leave alone
```

Leaving `spring-boot-starter-aop` on Boot 4 yields empty managed version / missing artifact. Annotation lock advice needs AspectJ on the classpath.

### TaskScheduler `@Primary` when multiple schedulers exist

**Detect:** lock library + another component that registers a `TaskScheduler` (messaging starters are a common source). Context failure often looks like `NoUniqueBeanDefinitionException` for `TaskScheduler`.

**When to add:** only if the app context fails (or lock refresh cannot resolve a unique scheduler). Do **not** change `@JdbcLocked` intervals, keys, TTL, or refresh while adding this wiring.

```java
// AFTER — wiring-only; bean name used by alturkovic JDBC auto-config
@Bean
static BeanFactoryPostProcessor preferDistributedLockTaskScheduler() {
  return beanFactory -> {
    if (beanFactory.containsBeanDefinition("distributedLockTaskScheduler")) {
      beanFactory.getBeanDefinition("distributedLockTaskScheduler").setPrimary(true);
    }
  };
}
```

If a service already has an equivalent `@Primary` / BFPP for that bean, keep it — do not invent a second workaround or new lock semantics.

### When a compatible major does **not** exist

```text
Options (human chooses):
A) Pin current version if compile/runtime works on Boot 4 — document debt
B) Replace with a maintained library (e.g. ShedLock) in a dedicated change
C) In-house lock table + Spring advice — only with design approval
```

Re-check for a Boot 4 major of the **same** library before parking the work as “replace.”

## Steps

1. Detect which lock library and version are in use (aggregate vs module group).  
2. If alturkovic: prefer **3.0.0+** `distributed-lock-jdbc` (or the module the service actually uses) over aggregate+excludes.  
3. AOP: rename `starter-aop` → `starter-aspectj`, **or add** `starter-aspectj` if missing while annotation locks are used.  
4. If context fails with multiple `TaskScheduler` beans, add the primary BFPP for `distributedLockTaskScheduler` (wiring only).  
5. Compile; smoke one locked code path if the human asks for tests.  
6. If no Boot 4–compatible release exists or compile fails, **ASK_HUMAN** with pin vs replace options — do not invent a half-port.

## Do not

- Quietly rewrite lock key / TTL / refresh semantics during the Boot 4 migration (including while fixing TaskScheduler wiring).  
- Add a second lock framework alongside the existing one.  
- Leave `spring-boot-starter-aop` on Boot 4, or stay on aggregate `1.5.x` + excludes when `distributed-lock-jdbc:3.0.0+` exists.  
- Skip TaskScheduler `@Primary` after a reproduced multi-scheduler failure.

## Risk

`ASK_HUMAN` for replace-or-pin when no Boot 4 major exists.  
In-place alturkovic `1.5.x` → `3.0.0` (jdbc module) + aspectj starter (+ optional scheduler primary after failure): `SAFE_AUTO` after compile succeeds; still one dedicated commit.

## Rollback

Restore previous lock coordinates and `spring-boot-starter-aop` / prior config (including any BFPP).

## Done when

Human decision recorded when needed (`pin` / `upgrade=<coords>` / `replace=<lib>`); service compiles with that choice; AOP starter is `aspectj` when annotation locks are used.

## Handoff

`lock=pin|upgrade|replace; lib=<coords>; aop=aspectj|added|renamed; schedulerPrimary=yes|no|n/a`
