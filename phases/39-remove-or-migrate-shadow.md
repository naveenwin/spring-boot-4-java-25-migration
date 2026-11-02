# 39 — Remove Shadow or migrate to GradleUp

`com.github.johnrengelman.shadow` is abandoned (tops at **8.1.1** — not a Java 25–safe long-term pin). Prefer **drop Shadow** when Boot `bootJar` / Jib / distroless already produce the runtime artifact. Otherwise **migrate plugin id** to `com.gradleup.shadow` **9.6.x**.

Always run [DEP-REMOVAL](../references/DEP-REMOVAL.md) analysis + risk score **for the drop path** before deleting Shadow tasks.

## Detect

Apply when:

- Plugin id `com.github.johnrengelman.shadow` or legacy `com.github.johnrengelman.shadow` classpath
- Already on `com.gradleup.shadow` but catalog wants alignment / drop reassessment
- Custom `shadowJar` / relocate / minimize / merge service files

Skip when neither johnrengelman nor gradleup Shadow is applied.

Catalog: johnrengelman → migrate; gradleup `9.6.1` approved for keep path. **Not** a silent [12](12-dependency-bump-queue.md) bump of 8.1.1.

## Before → After

### Path A — remove Shadow (preferred when score LOW)

```gradle
// BEFORE
plugins {
  id 'com.github.johnrengelman.shadow' version '8.1.1'
}
shadowJar { /* relocate / minimize */ }
// CI publishes shadowJar

// AFTER — Boot / Jib owns the artifact
plugins {
  id 'org.springframework.boot'
  // id 'com.google.cloud.tools.jib' when already used
}
// tasks.named('jar') { enabled = false } // only if Boot convention already does this
// CI publishes bootJar or Jib image — update job artifact names
```

### Path B — migrate plugin id (keep fat/relocated JAR)

```gradle
// BEFORE
id 'com.github.johnrengelman.shadow' version '8.1.1'

// AFTER
id 'com.gradleup.shadow' version '9.6.1'
// Audit DSL: enableAutoRelocation (not isEnableRelocation), lazy properties, duplicatesStrategy
```

## Steps

1. **Inventory** — plugin id/version; `shadowJar` / `ShadowJar` tasks; relocate/minimize/mergeServiceFiles; CI jobs that publish/consume the shaded artifact; overlap with `bootJar` / Jib.  
2. **Decide path intent** — if CI only needs an executable Spring jar/image and relocate is empty → prefer Path A. If relocate/minimize is load-bearing → Path B.  
3. **Score the drop path** (DEP-REMOVAL) even if Path B looks likely — record why drop was rejected.  
4. **Gate for Path A (remove)**  
   - **LOW:** `SAFE_AUTO` drop plugin + point CI at `bootJar`/Jib.  
   - **MED:** `ASK_HUMAN` with CI impact list.  
   - **HIGH:** do not drop; take Path B or park.  
5. **Path A execute:** remove plugin; delete Shadow-only config; update CI artifact task names; confirm no remaining `shadowJar` references.  
6. **Path B execute:** switch to `com.gradleup.shadow` **9.6.1** (catalog); fix DSL breaks; ask human to validate shaded JAR contents (Diffuse / smoke) — agent does not invent checksums.  
7. Record evidence labels after human verify.

## Do not

- Bump johnrengelman past **8.1.1** or treat 8.1.1 as Boot 4–complete.  
- Drop Shadow while CI still publishes `shadowJar` without updating the pipeline.  
- Silent phase-12 version bump instead of this phase.  
- Relocate Spring Boot loader classes “for fun.”  
- Claim remove when gradleup was added without deleting unused Shadow behavior you meant to drop.

## Risk

- **Path A (remove):** band-driven via DEP-REMOVAL.  
- **Path B (gradleup):** `ASK_HUMAN` when relocate/minimize/duplicatesStrategy present; `SAFE_AUTO` only for trivial `shadowJar` with no relocate and tests already green on Boot packaging.  
- Packaging/CI contract change ⇒ at least MED.

## Rollback

Restore previous plugin id/version and CI artifact wiring in one revert set.

## Done when

Shadow either **removed** (Boot/Jib path) or **on gradleup 9.6.x** with DSL adjusted; johnrengelman id gone; CI contract updated or explicitly deferred in `findings.md`.

## Handoff

`shadow=removed|gradleup-9.6.x|parked|n/a; removalRisk=<0-100>; band=LOW|MED|HIGH; path=A|B; ciArtifact=bootJar|jib|shadowJar|deferred; next=12|37|none`
