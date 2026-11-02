# 22 — Actuator / health probes / management

## Detect

`spring-boot-starter-actuator`, custom `@Endpoint` / `@EndpointWebExtension`, Kubernetes probes, management port, Micrometer metrics/tracing exporters beyond Sleuth ([07-observability.md](07-observability.md)).

Skip if Actuator is absent.

### Valid config is a no-op

When first-party config already matches the Boot 4 names this phase would write:

- exposure list has no `httptrace` (it is already `httpexchanges`, or the platform set such as `health`, `info`, `prometheus`)
- no `management.metrics.export.prometheus`
- probe keys are already explicit, or the platform accepts the Boot 4 default and nobody asked to disable probes

then do not edit YAML or Java. Complete the phase with `filesTouched=[]` and handoff `actuatorProps=unchanged`. Write the phase note so a later agent does not “fix” a valid exposure list. Runtime routes stay unverified until the human gate.

## Before → After

### Probes

Liveness / readiness are **enabled by default** on Boot 4. Disable only with an explicit product reason.

The default `readiness` group contains only `readinessState`. A probe on `/actuator/health/readiness` can stay up while the database or broker is down. A probe on `/actuator/health` includes those contributors and can flap the pod. Record which path the deployment already uses. Do not retarget the probe or add contributors. This pack does not edit the deployment manifest.

`management.endpoint.health.validate-group-membership` defaults to **true**. Startup fails when a group names a contributor this process does not register (`Health contributors [kafka, mongo] in group 'readiness' do not exist`). Point the group at contributors that exist. Contributor ids follow Boot 4 names (`mongodb`, not `mongo`). Do not set the validation property to `false` to get past startup.

```yaml
# Only if the platform must turn them off
management:
  endpoint:
    health:
      probes:
        enabled: false # confirm exact key for the Boot patch via docs/changelog
```

### Endpoint access model

Prefer the Boot 4 **access** property model over legacy `*.enabled` toggles where the changelog requires it. Confirm keys with [18-config-properties.md](18-config-properties.md) / the Configuration Changelog.

### Modular metrics / tracing starters

Boot 4 splits some metrics/tracing/OTel/Zipkin pieces into focused starters. Add what the service actually uses (do not add every exporter “just in case”). Coordinate Brave/OTel bridge choice with phase 07.

When the service exports traces with Brave (a direct `micrometer-tracing-bridge-brave`, or `spring-cloud-gcp-starter-trace`), declare `org.springframework.boot:spring-boot-micrometer-tracing-brave` with no version. Boot 4 does not publish a Brave starter. Do not add `spring-boot-starter-micrometer-metrics` when `spring-boot-starter-actuator` is already declared. Leave `management.metrics.enable.*` and `management.health.*.enabled` as they are; they are not in the Boot 4.0 rename table. Whether a `Tracer` bean and the exporter actually start is a Stage C check.

### Endpoint and Prometheus property renames

```yaml
# Before
management:
  endpoints:
    web:
      exposure:
        include: health,info,httptrace,prometheus
  metrics:
    export:
      prometheus:
        enabled: true

# After
management:
  endpoints:
    web:
      exposure:
        include: health,info,httpexchanges,prometheus
  prometheus:
    metrics:
      export:
        enabled: true
```

Confirm exact property paths against the target Boot patch and phase 18 migrator output. These can fail silently: a green build does not prove `/actuator/prometheus` still exports or that `httpexchanges` is exposed. If the keys are already the Boot 4 names, the no-op above applies — do not rewrite them for symmetry.

### HTTP metric tags

These change with no compile error. Dashboards and alerts that filter the old tag go empty.

| Before | After |
|--------|--------|
| `http.server.requests` tag `exception="None"` | `exception="none"` |
| `http.client.requests` tag `clientName` | `client.name` (Prometheus `client_name`) |

A `WebMvcTagsProvider` or `WebMvcTagsContributor` bean is ignored. URI-tag suppression stops and cardinality grows. Replacing it with an `ObservationPredicate` or `ObservationFilter` changes which requests are tagged and is `ASK_HUMAN`. Do not delete the old bean and leave suppression off.

### Micrometer pin and the actuator `micrometer-core` exclude

Boot **4.1.1** manages Micrometer **1.17.1**. A Boot 2/3 service often pins **1.9.x** on `micrometer-core` and `micrometer-registry-prometheus` and excludes `micrometer-core` from the actuator starter so the pin wins. Remove the exclude and both pins in **one** change. Keep Prometheus by declaring it **without** a version when the service already exports it. Do not add a new direct 1.17 pin.

Coordinate with [07-observability.md](07-observability.md): land this recipe before the Sleuth → tracing bridge so the bridge resolves from the Boot BOM. If phase 07 already handed off `micrometerPins=removed`, do not edit those lines again.

```gradle
// Before
implementation('org.springframework.boot:spring-boot-starter-actuator') {
    exclude group: 'io.micrometer', module: 'micrometer-core'
}
implementation 'io.micrometer:micrometer-core:1.9.17'
implementation 'io.micrometer:micrometer-registry-prometheus:1.9.17'

// After — Boot BOM manages Micrometer; Prometheus stays only if the service already exports it
implementation 'org.springframework.boot:spring-boot-starter-actuator'
implementation 'io.micrometer:micrometer-registry-prometheus'
```

Maven: delete the exclusion and the versioned Micrometer dependencies; keep Prometheus unversioned under the Boot BOM when it was a direct dependency. This recipe is independent of the YAML no-op: pins can change while `actuatorProps=unchanged`.

### Health contributor package move

```java
// Before
import org.springframework.boot.actuate.health.ReactiveHealthIndicator;

// After
import org.springframework.boot.health.contributor.ReactiveHealthIndicator;
```

Align the focused health/Actuator module when a custom indicator no longer compiles. Apply the same package review to related contributor types rather than adding compatibility wrappers.

### Custom endpoints

Optional parameters / nullability → JSpecify ([21-null-safety-jspecify.md](21-null-safety-jspecify.md)).

> **Open / not fully analyzed** — full management-port security filter-chain patterns; point to [20-spring-security-7.md](20-spring-security-7.md) when securing Actuator.

## Steps

1. Inventory Actuator usage (health, info, metrics, custom endpoints, management port) and any direct Micrometer version or actuator `micrometer-core` exclude.  
2. If exposure, probes, and Prometheus keys already match Boot 4, record `filesTouched=[]` for config and `actuatorProps=unchanged`. Do not rewrite YAML. Separately apply the Micrometer pin recipe when those pins or the exclude exist.  
3. Otherwise align properties via migrator / changelog ([18](18-config-properties.md)), including `httptrace` → `httpexchanges` and Prometheus export keys.
4. Confirm probe defaults match platform expectations (k8s). Record whether readiness is the `readinessState`-only group. Fix a group that names a missing contributor. Do not disable group-membership validation.  
5. Add modular metrics/tracing starters required after the Boot 4 split. Tracing bridge dependency swaps stay in [07](07-observability.md).  
6. Fix custom endpoint and health-contributor package/module moves (JSpecify / API moves).
7. Ask the human to verify health, readiness/liveness, `httpexchanges` (if intended), metrics, and Prometheus endpoints at runtime.
8. ASK_HUMAN before changing which endpoints are exposed publicly.  
9. If a `WebMvcTagsContributor` or `WebMvcTagsProvider` bean exists, stop for the human before moving it to the Observation API. Tell the human the `exception` and `client.name` tag changes so dashboard owners can update queries. Do not edit the dashboards from this repo.

## Do not

- Expose sensitive endpoints while “fixing” access properties.  
- Duplicate Sleuth removal work — use phase 07 for Sleuth→Micrometer type swaps.  
- Change probe semantics in production without platform approval.
- Assume a successful compile proves renamed endpoints or metrics exports still work.  
- Edit YAML that already uses Boot 4 endpoint and Prometheus keys.  
- Drop the Micrometer pin and leave the actuator `micrometer-core` exclude, or the reverse.  
- Pin Micrometer 1.17 directly instead of letting the Boot BOM manage it.
- Set `validate-group-membership=false`, or point a readiness probe at a different path, to make a group look healthy.
- Delete a `WebMvcTagsContributor` / `WebMvcTagsProvider` bean because Boot ignores it.

## Risk

`SAFE_AUTO` for the valid-config no-op (`filesTouched=[]`, `actuatorProps=unchanged`), for the Micrometer pin + exclude removal above, and for property/probe alignment and starter adds that restore prior metrics.  
`ASK_HUMAN` for custom endpoints, security on management port, probe disablement, retargeting a readiness probe, or moving a tags contributor to the Observation API.

## Rollback

Revert Actuator property / starter commit.

## Done when

Management context starts, or the no-op is recorded: first-party keys were already Boot 4 names, `filesTouched=[]` for config, `actuatorProps=unchanged`. Direct Micrometer 1.9 pins and the actuator `micrometer-core` exclude are absent (removed here or already removed). No unresolved Actuator property deprecations for first-party config. Intended metrics/Prometheus/HTTP-exchange endpoints are runtime-smoked or explicitly deferred.

## Handoff

`actuator=ok|n/a; actuatorProps=unchanged|updated; filesTouched=<n>; probes=default|custom; readinessGroup=readinessState-only|custom|n/a; groupMembership=valid|fixed|n/a; metricTags=recorded|asked|n/a; healthImports=updated|n/a; micrometerPins=removed|n/a; metricsSmoke=green|deferred|n/a; askedHuman=yes|no`
