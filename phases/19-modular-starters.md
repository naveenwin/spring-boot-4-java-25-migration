# 19 — Boot 4 modular starters (classic → focused)

## Detect

Any of:

- `spring-boot-starter-web` (Boot 3 name) while targeting Boot 4
- Bare `flyway-core` / `liquibase-core` / Jackson / RestClient usage without the matching Boot 4 starter
- Compile / runtime “auto-config not found” after the Boot 4 bump
- Security / web tests inert because companion `*-test` starters are missing
- Still on `spring-boot-starter-classic` / `test-classic` with no exit plan

## Before → After

### Planner mode (choose before the writer starts)

The planner records one mode. The worker executes it and does not re-evaluate the choice.

| Mode | What this phase changes | What it leaves |
|------|-------------------------|----------------|
| `focused-now` | Boot 3 starter names → focused Boot 4 coordinates, including `spring-boot-starter-web` → `spring-boot-starter-webmvc` when that is the stack | No classic dependency |
| `classic-bridge-with-exit` | Only the unversioned classic pair below, plus a tracked exit | Existing `spring-boot-starter-web` stays. Do not mix `webmvc` into the bridge commit |

Official guidance: [Spring Boot 4.0 Migration Guide](https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide).

#### Classic bridge (minimal)

```gradle
implementation 'org.springframework.boot:spring-boot-starter-classic' // classicExit=deferred — focused starters replace this
testImplementation 'org.springframework.boot:spring-boot-starter-test-classic' // classicExit=deferred
```

Record `classicExit=deferred` in the build comment, in findings, and in the handoff. A classic coordinate with no exit record is [anti-pattern 19](../references/99-anti-patterns.md).

Dedicated phases still own their starters. Do not infer them from the dependency list during the bridge:

| Concern | Owner |
|---------|--------|
| Flyway | [08-flyway-db.md](08-flyway-db.md) |
| AspectJ / locks | [11-distributed-lock.md](11-distributed-lock.md) |
| Security | [20-spring-security-7.md](20-spring-security-7.md) |
| Test companions (`webmvc-test` and the like) | [09-testing.md](09-testing.md) |

Declaring an unversioned coordinate beside the Boot BOM is static evidence. Dependency resolution and context startup stay unverified until the human gate.

### Two-step strategy

1. **Unblock (`classic-bridge-with-exit`):** add the classic pair when the focused cutover is too large for one commit.  
2. **Exit classic (`focused-now`, or a later pass):** replace with focused starters so classic is not the permanent end state.

### Common renames

| Before (Boot 3) | After (Boot 4 focused) |
|-----------------|------------------------|
| `spring-boot-starter-web` | `spring-boot-starter-webmvc` |
| `spring-boot-starter-aop` | `spring-boot-starter-aspectj` |
| Implicit RestClient / WebClient support | Add the focused RestClient or WebClient starter when used |
| `spring-boot-starter-batch` + DB job metadata | `spring-boot-starter-batch-jdbc` when persistence is required ([stubs/batch.md](../stubs/batch.md)) |
| `org.springframework.kafka:spring-kafka-test` | `spring-boot-starter-kafka-test` ([44-spring-kafka-4.md](44-spring-kafka-4.md)). `spring-boot-starter-kafka` keeps its name |
| OAuth2 client / resource starter names | Boot 4 OAuth2 starter coordinates (confirm BOM) |
| Tech pulled transitively | Explicit starter for Flyway, Liquibase, Jackson, RestClient, etc. when auto-config disappears |

Do not infer the full replacement set from a single missing class — use the official Boot 4 starter/module tables for the selected patch.

### Test companions

```gradle
testImplementation 'org.springframework.boot:spring-boot-starter-webmvc-test'
testImplementation 'org.springframework.boot:spring-boot-starter-security-test' // if security tests
// transitional:
testImplementation 'org.springframework.boot:spring-boot-starter-test-classic'
```

Package moves often follow `org.springframework.boot.<module>…` (e.g. MockMvc autoconfigure under webmvc-test) — see [09-testing.md](09-testing.md).

Embedded Tomcat customization moved out of `org.springframework.boot.web.embedded.tomcat`:

```kotlin
// Before
import org.springframework.boot.web.embedded.tomcat.TomcatConnectorCustomizer
import org.springframework.boot.web.embedded.tomcat.TomcatServletWebServerFactory

// After (Boot 4 spring-boot-tomcat module)
import org.springframework.boot.tomcat.TomcatConnectorCustomizer
import org.springframework.boot.tomcat.servlet.TomcatServletWebServerFactory
```

`WebServerFactoryCustomizer` remains `org.springframework.boot.web.server.WebServerFactoryCustomizer`.

### Packaging / runtime (platform adjacency)

Folded here only as Detect pointers; fix under [01-platform-baseline.md](01-platform-baseline.md) when present:

- Undertow unsupported on Boot 4 servlet stack  
- WAR: `spring-boot-starter-tomcat-runtime`  
- Classic loader / embedded launch-script removals  

## Steps

1. Read the planner mode. Do not switch `focused-now` and `classic-bridge-with-exit` in the worker.  
2. `classic-bridge-with-exit`: add only the unversioned classic pair, keep `spring-boot-starter-web`, and record the exit. Stop. Flyway, AspectJ, security, and test companions stay with their phases.  
3. `focused-now`: list starters in use vs Boot 4 focused names. Swap `starter-web` → `webmvc` (and other renames). Add a tech starter here only when this phase owns it; otherwise link [08](08-flyway-db.md), [11](11-distributed-lock.md), [20](20-spring-security-7.md), [09](09-testing.md).  
4. Align test starters / imports when mode is `focused-now` ([09-testing.md](09-testing.md)).  
5. Remove classic when the focused set is the approved mode, or leave it deferred with the exit record.  
6. Confirm packages for autoconfigure imports still resolve. Handoff `web=` names the coordinate that is actually declared.

## Do not

- Ship classic starters as the long-term end state without a tracked exit.  
- Re-decide an approved bridge inside the worker.  
- Mix `spring-boot-starter-webmvc` into the classic-bridge commit, or drop `spring-boot-starter-web` in that commit.  
- Add Flyway, AspectJ, security, or test-webmvc starters because they appear in the dependency list.  
- Assume Boot 3 transitive auto-config still appears without a Boot 4 starter.  
- Dual-publish custom org starters for Boot 3+4 in one artifact (officially discouraged) without human design.  
- Treat a declared unversioned coordinate as proof that resolution or context startup succeeded.

## Risk

`SAFE_AUTO` for an approved `classic-bridge-with-exit` (the two unversioned coordinates plus the exit record) and for mechanical focused renames once that mode was chosen.  
`ASK_HUMAN` when dropping classic changes which auto-configurations load (security, actuators, data), or when the planner has not recorded a mode.

## Rollback

Restore previous starter coordinates (classic or Boot 3 names) in one commit.

## Done when

Approved mode is applied. `focused-now`: focused starters declared. `classic-bridge-with-exit`: classic pair declared, exit recorded in the build comment and the handoff, and `spring-boot-starter-web` still present when that was the pre-bridge coordinate. Test companions match the web/security stack only when this phase owned them. Resolution and context start stay unverified until the human gate.

## Handoff

`starters=focused|classic-bridge; mode=focused-now|classic-bridge-with-exit; web=mvc-legacy-name|webmvc|webflux|none; classicExit=done|deferred`

`web=mvc-legacy-name` means `spring-boot-starter-web` is still the declared coordinate. `web=webmvc` means `spring-boot-starter-webmvc` is declared. Do not write `web=mvc`.
