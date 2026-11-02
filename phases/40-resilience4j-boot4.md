# 40 — Resilience4j spring-boot3 → spring-boot4

Boot 4 **hard-fails** when `resilience4j-spring-boot3` is on the classpath. Swap to `resilience4j-spring-boot4` **2.4.0** (GA). Bump BOM / circuitbreaker / retry modules to **2.4.0** alongside.

Spring Retry / Framework `@Retryable` is a different stack — [41-spring-retry-framework.md](41-spring-retry-framework.md).

## Detect

Apply when any of:

- `io.github.resilience4j:resilience4j-spring-boot3`
- `resilience4j-bom` / `resilience4j-circuitbreaker` / `resilience4j-retry` without the boot4 starter on a Boot 4 service
- Startup error directing use of `resilience4j-spring-boot4`

Skip when already on `resilience4j-spring-boot4` at **2.4.0** (or newer patch) with no boot3 artifact.

Catalog: boot3 → migrate; boot4 / BOM / core modules → approved **2.4.0**.

## Before → After

```gradle
// BEFORE (Boot 3)
implementation platform('io.github.resilience4j:resilience4j-bom:2.2.0')
implementation 'io.github.resilience4j:resilience4j-spring-boot3'
implementation 'io.github.resilience4j:resilience4j-circuitbreaker'
implementation 'io.github.resilience4j:resilience4j-retry'

// AFTER (Boot 4)
implementation platform('io.github.resilience4j:resilience4j-bom:2.4.0')
implementation 'io.github.resilience4j:resilience4j-spring-boot4:2.4.0' // pin — BOM 2.4.0 may omit boot4
implementation 'io.github.resilience4j:resilience4j-circuitbreaker'
implementation 'io.github.resilience4j:resilience4j-retry'
```

Annotation / YAML binding (`@CircuitBreaker`, `@Retry`, `resilience4j.*` config) stays on the Spring6 / Boot4 auto-config path — treat as module rename first, not a rewrite.

## Steps

1. Inventory Resilience4j artifacts and annotation/YAML usage.  
2. Remove `resilience4j-spring-boot3`; add `resilience4j-spring-boot4:**2.4.0**` with **explicit version** (do not rely on BOM alone until a BOM patch lists boot4).  
3. Bump `resilience4j-bom` / circuitbreaker / retry (and any other Resilience4j modules in this service) to **2.4.0**.  
4. Keep Micrometer/Actuator wiring if already present; do not invent new dashboards.  
5. Compile via the orchestrator; name a CB/retry path for the Stage C smoke.  
6. If the service uses **only** Spring Retry (no Resilience4j) → skip this phase; use [41-spring-retry-framework.md](41-spring-retry-framework.md).

## Do not

- Leave boot3 on Boot 4 (“modules-only bump”).  
- Replace Resilience4j with Spring Retry alone when circuit breaker / bulkhead / rate limiter are in use.  
- Drop CB semantics to silence startup.  
- Silent phase-12 bump of boot3 coordinates.

## Risk

`SAFE_AUTO` for boot3→boot4 module swap + 2.4.0 alignment when annotations/YAML already match Resilience4j Spring.  
`ASK_HUMAN` if custom registries, AspectJ excludes, or multi-module version skew.  
`SPIKE_FIRST` only when dropping Resilience4j entirely for another stack.

## Rollback

Restore previous boot3 + BOM versions together.

## Done when

No `resilience4j-spring-boot3` on Boot 4; boot4 **2.4.0** present (pinned); core modules on **2.4.0**; human smoke deferred or green.

## Handoff

`resilience4j=boot4-2.4.0|n/a; boot3Removed=yes|n/a; bom=2.4.0|n/a; smoke=green|deferred`
