# 24 — Tomcat: remove embed pins (Boot-managed)

## Detect

Apply when any of these appear:

- Explicit versions on `org.apache.tomcat.embed:tomcat-embed-core|el|websocket|jasper`
- `tomcat.version=` / `ext['tomcat.version']` / resolutionStrategy forcing `org.apache.tomcat*`
- `dependencyInsight` shows a non-Boot source for `tomcat-embed-core`
- WAR still using old `provided` `spring-boot-starter-tomcat` instead of `spring-boot-starter-tomcat-runtime`

Skip when Tomcat is only transitive from Boot starters and all embed jars share one Boot-BOM version.

## Before → After

| Before | After |
|--------|--------|
| `implementation 'org.apache.tomcat.embed:tomcat-embed-core:10.1.55'` (and siblings) | **No** direct versioned `tomcat-embed-*` deps |
| `ext['tomcat.version'] = '10.1.x'` left forever after a CVE chase | Removed (or temporary + dated expiry comment only if Security forces) |
| WAR: `providedRuntime 'spring-boot-starter-tomcat'` | WAR: `providedRuntime 'spring-boot-starter-tomcat-runtime'` |
| Jar app: direct embed deps | Rely on `spring-boot-starter-webmvc` / web starter |

```gradle
// BEFORE — pin fights Boot 4 (Tomcat 11)
implementation 'org.apache.tomcat.embed:tomcat-embed-core:10.1.55'
implementation 'org.apache.tomcat.embed:tomcat-embed-el:10.1.55'

// AFTER — Boot BOM owns Tomcat (jar)
implementation 'org.springframework.boot:spring-boot-starter-webmvc'
// no tomcat-embed-* lines
```

```gradle
// AFTER — deployable WAR (Boot 4)
providedRuntime 'org.springframework.boot:spring-boot-starter-tomcat-runtime'
```

## What breaks / how to fix

| Symptom | Cause | Fix |
|---------|--------|-----|
| `NoSuchMethodError` / `AbstractMethodError` in Catalina | Mixed pin + Boot Tomcat 11 | Remove **all** embed pins; one version only |
| Jakarta / Servlet mismatch under Boot 4 | Stuck on Tomcat 10.1 pin | Remove pin; Boot 4 → Tomcat 11.x |
| Still old Tomcat after “fix” | `gradle.properties` / platform BOM / `enforcedPlatform` | Grep + `dependencyInsight`; clear every override |
| Tests fail after `compileOnly` Tomcat | Wrong WAR scope | Use `providedRuntime` for `tomcat-runtime` |
| Duplicate Tomcat in WAR | Starter not `providedRuntime` | Switch to `spring-boot-starter-tomcat-runtime` |
| Jasper/JSP missing | Rare JSP need | Add `tomcat-embed-jasper` **without** version |

## Steps

1. Grep build files for `tomcat-embed`, `tomcat.version`, `org.apache.tomcat`.  
2. The orchestrator runs `dependencyInsight --dependency tomcat-embed-core` (a run of its own, `kind: resolve`); record who forces the version.  
3. Delete explicit embed versions and Tomcat resolution forces.  
4. Prefer starters only (webmvc / web); for WAR use `spring-boot-starter-tomcat-runtime` as `providedRuntime`.  
5. Confirm all `tomcat-embed-*` resolve to the **same** Boot-BOM version (human: `dependencies` / insight).  
6. Smoke HTTP path (`bootRun` or IT); for WAR, note external-container deploy is human-owned.

## Do not

- Pin a single embed artifact while leaving siblings on another version.  
- “Bump Tomcat to 11.x manually” instead of removing the pin.  
- Leave a permanent `tomcat.version` override after a CVE without an expiry note.  
- Use Undertow on Boot 4 servlet stack ([01-platform-baseline.md](01-platform-baseline.md)).

## Risk

`ASK_HUMAN` when WAR packaging or a Security-forced pin exists; otherwise `SAFE_AUTO` for deleting unused version pins after insight shows Boot can manage them.

## Rollback

Restore previous embed version lines / `tomcat.version` in one commit.

## Done when

No versioned `tomcat-embed-*` pins (unless documented temporary Security exception); WAR uses `tomcat-runtime` when applicable; human confirms one Boot-managed Tomcat version on the runtime classpath.

## Handoff

`tomcatPins=removed|exception; packaging=jar|war; bootManagedVersion=<ver|unknown>`
