# 07 — Observability (Sleuth → Micrometer)

## Detect

Any of:

- `spring-cloud-sleuth` / `spring-cloud-starter-sleuth`
- Imports under `org.springframework.cloud.sleuth.*` (`Tracer`, `CurrentTraceContext`, `TraceContext`, `@NewSpan`)
- `TraceableExecutorService` from Sleuth
- Logging config keys under `org.springframework.cloud.sleuth`
- YAML `spring.sleuth.*`

Skip full starter swap on Boot 3→4 services that already use Micrometer Tracing only — still grep for leftover Sleuth packages (`@NewSpan`, logger names).

### Dependency-only path (zero Sleuth imports)

Apply this path when the Sleuth starter is declared and all of the following are true:

- `rg 'org\.springframework\.cloud\.sleuth' src/main src/test` is empty
- no `TraceableExecutorService`
- no `spring.sleuth.*` and no `logging.level.org.springframework.cloud.sleuth`

Then remove the starter and add the unversioned platform bridge (Brave unless the plan already chose OTel) plus `context-propagation`. Do not rewrite imports, logging keys, YAML, Feign interceptors, or test `Tracer` mocks — there is nothing to rewrite. An OTel bridge, or any existing exporter / baggage customization, stays `ASK_HUMAN`.

### Direct Micrometer pin and the actuator exclude

Coordinate with the pin recipe in [22-actuator.md](22-actuator.md). Boot **4.1.1** manages Micrometer **1.17.1**. A direct **1.9.x** pin on `micrometer-core` / `micrometer-registry-prometheus`, often paired with an actuator `exclude` of `micrometer-core`, must leave in the **same** change as each other:

- If phase 22 already removed the pins and the exclude, this phase only adds the unversioned tracing bridge on that Boot-managed line.
- If this phase runs first, drop the 1.9 pins and the actuator `micrometer-core` exclude in the same commit as the Sleuth removal, and hand off `micrometerPins=removed` so phase 22 does not edit those lines again.
- Do not leave a 1.9 pin next to an unversioned bridge. Do not leave the exclude after the pin is gone — the exclude hides Boot’s managed `micrometer-core`.
- Do not replace the old pin with a new direct 1.17 pin.

Prefer order: phase 22 pin/exclude recipe, then this phase, so tracing dependencies resolve from the Boot BOM.

## Before → After

### Dependencies

```gradle
// Before
implementation 'org.springframework.cloud:spring-cloud-starter-sleuth'

// After
implementation 'io.micrometer:micrometer-tracing-bridge-brave' // or otel bridge
implementation 'io.micrometer:context-propagation'
// keep feign-micrometer if OpenFeign metrics were already present
```

### Async executor bean

```java
// Before
import org.springframework.cloud.sleuth.instrument.async.TraceableExecutorService;
@Bean
ExecutorService tracedExecutor(BeanFactory beanFactory, ThreadPoolTaskExecutor delegate) {
  return new TraceableExecutorService(beanFactory, delegate.getThreadPoolExecutor());
}

// After
import io.micrometer.context.ContextExecutorService;
import io.micrometer.context.ContextSnapshotFactory;
@Bean
ExecutorService tracedExecutor(ThreadPoolTaskExecutor delegate) {
  return ContextExecutorService.wrap(
      delegate.getThreadPoolExecutor(),
      ContextSnapshotFactory.builder().build()::captureAll);
}
// Injected field type: ExecutorService (not TraceableExecutorService)
```

### Types and annotations

```java
// Before
import org.springframework.cloud.sleuth.Tracer;
import org.springframework.cloud.sleuth.CurrentTraceContext;
import org.springframework.cloud.sleuth.TraceContext;
import org.springframework.cloud.sleuth.annotation.NewSpan;

// After
import io.micrometer.tracing.Tracer;
import io.micrometer.tracing.CurrentTraceContext;
import io.micrometer.tracing.TraceContext;
import io.micrometer.tracing.annotation.NewSpan;
```

Common call shapes such as `tracer.currentTraceContext().context().traceId()` stay similar after the package move.

### Logging

```yaml
# Before
logging.level.org.springframework.cloud.sleuth: TRACE   # or Feign Sleuth logger keys

# After
logging.level.io.micrometer.tracing: TRACE
# drop dead Sleuth logger keys
```

### Properties (Boot 2.7 path)

> **Open / not fully analyzed** — confirm against the Boot version’s Micrometer Tracing docs before bulk-rewriting YAML.

| Before (Sleuth) | After (typical Micrometer / Boot) |
|-----------------|-------------------------------------|
| `spring.sleuth.*` | Prefer `management.tracing.*` (sampling, baggage, propagation) |
| Sleuth sampler rate keys | `management.tracing.sampling.probability` (name may vary by Boot line) |
| Custom exporters | Platform Brave vs OTel bridge choice — `ASK_HUMAN` |

HTTP server and client metric tag renames, and a `WebMvcTagsContributor` bean Boot no longer calls, belong to [22-actuator.md](22-actuator.md). This phase does not edit them.

### Tests

When components inject `Tracer` and Sleuth auto-config is gone, provide a test `@Bean` mock `Tracer` (and `CurrentTraceContext` if required) in `@TestConfiguration` / shared test config.

## Steps

1. Classify: dependency-only (zero `org.springframework.cloud.sleuth` imports) or import migration.  
2. Remove Sleuth starters. In the same change, apply the Micrometer pin + actuator `micrometer-core` exclude removal when phase 22 has not already done it ([22-actuator.md](22-actuator.md)).  
3. Add the Micrometer Tracing bridge (Brave for the dependency-only platform path, or the bridge the plan already chose) + `context-propagation`, unversioned.  
4. On the import path only: replace `TraceableExecutorService` with `ContextExecutorService.wrap(...)`; rewrite Sleuth imports / `@NewSpan`; update Feign interceptors and exception handlers that read trace IDs; update logging keys; migrate `spring.sleuth.*` when grep hits.  
5. On the dependency-only path: skip steps that rewrite imports, YAML, and logging keys.  
6. Add test `Tracer` mocks only where a component injects `Tracer` and context load fails after Sleuth removal.  
7. Keep log correlation patterns (`traceId`, etc.) working via Micrometer.

## Do not

- Keep both Sleuth and Micrometer Tracing “just in case.”  
- Change sampling / exporter / baggage customizations without human approval.  
- Add the tracing bridge while a direct Micrometer 1.9 pin or an actuator `micrometer-core` exclude is still present.  
- Rewrite YAML or logging keys on the zero-import path.

## Risk

`SAFE_AUTO` for the dependency-only Brave path (zero Sleuth imports, no Sleuth YAML) and for import/annotation/logging swaps + `ContextExecutorService` wrap, including the coordinated pin/exclude removal when it is the same mechanical diff as phase 22.  
`ASK_HUMAN` for sampling / exporter / baggage, an OTel bridge choice, and any non-standard Sleuth instrumentation.  
Property table above is `SPIKE_FIRST` until verified for the target Boot patch.

## Rollback

Restore Sleuth starter (only viable on older Boot — emergency may mean revert whole Boot bump).

## Done when

No Sleuth dependencies or first-party Sleuth imports. Dependency-only path: starter removed, unversioned bridge + `context-propagation` declared, no source or YAML edit. Import path: async bean (if any) is still an `ExecutorService`. Direct 1.9 Micrometer pins and the actuator `micrometer-core` exclude are gone (here or already done in phase 22). Context start stays unverified until the human gate.

## Handoff

`tracing=micrometer; sleuthRemoved=yes|n/a; path=dependency-only|imports; asyncExecutor=context-propagating|n/a; micrometerPins=removed|already-removed|n/a`
