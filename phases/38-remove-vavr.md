# 38 — Remove Vavr (replace with JDK / Kotlin)

Prefer **deleting** `io.vavr:vavr` over bumping to 1.x. Run deep analysis + [DEP-REMOVAL](../references/DEP-REMOVAL.md) risk score before any delete. If band is HIGH, park removal and optionally interim-bump to `1.0.1` only when the human accepts keeping Vavr.

## Detect

Apply when any of:

- Gradle/Maven pin `io.vavr:vavr` (any version, including 0.10.x / 1.x)
- Imports `io.vavr.` / `javaslang.` (legacy)
- `io.vavr:vavr-jackson` or Jackson modules registering Vavr types

Skip when inventory finds **zero** declarations and **zero** imports.

Catalog: `drop (prefer)` / `status=migrate` → this phase (not [12](12-dependency-bump-queue.md)).

## Before → After

```gradle
// BEFORE
implementation 'io.vavr:vavr:0.10.4'
// optional
implementation 'io.vavr:vavr-jackson:0.10.4'

// AFTER — dependency gone; use JDK / Kotlin
```

```java
// BEFORE
import io.vavr.control.Option;
import io.vavr.control.Either;
import io.vavr.control.Try;
import io.vavr.collection.List;

Option<String> name = Option.of(raw);
Either<Err, Ok> r = Either.right(ok);
Try<Foo> t = Try.of(this::load);
List<String> xs = List.of("a", "b");

// AFTER (Java)
import java.util.Optional;
import java.util.List;

Optional<String> name = Optional.ofNullable(raw);
// Either → sealed interface / record pair, or domain-specific result type
// Try → try/catch, or a small Result type — do not add another FP lib
List<String> xs = List.of("a", "b");
```

```kotlin
// AFTER (Kotlin) — prefer language features
val name: String? = raw
val xs = listOf("a", "b")
runCatching { load() }.getOrElse { fallback }
// Either-like → sealed class Result { data class Ok(...); data class Err(...) }
```

**Jackson:** drop `vavr-jackson`. Re-model payloads with JDK/Kotlin types so Jackson 3 needs no Vavr module. Do not add `vavr-jackson:1.x` as the “Boot 4 fix.”

## Steps

1. **Inventory** (DEP-REMOVAL § Deep analysis) — grep `io.vavr` / `javaslang` in main + test; list Gradle pins; note `vavr-jackson`.  
2. **Surface map** — tally Option / Either / Try / Validation / Tuple / Vavr collections / Lazy / API usage.  
3. **Score** — write `removalRisk` + band into `phase-notes/38-remove-vavr.md`.  
4. **Gate**  
   - **LOW (0–29):** proceed to replace + delete deps (`SAFE_AUTO`).  
   - **MED (30–59):** `ASK_HUMAN` with inventory summary + proposed replacements; wait for OK.  
   - **HIGH (60–100):** `SPIKE_FIRST` — do **not** mass-rewrite; handoff `action=parked` or human-approved interim `1.0.1` only.  
5. **Replace** clusters (one slice per cluster; a cluster whose mapping is unclear becomes a blocker, not a guess):  
   - `Option` → `Optional` / Kotlin nullable  
   - Vavr `List`/`Map`/`Set` → `java.util` / Kotlin collections  
   - `Try` → `try/catch` or `runCatching`  
   - `Either` / `Validation` → sealed types or existing domain errors  
6. Stage A slice: remove `io.vavr:*` from the build. Stage B: purge unused imports.  
7. Done when the orchestrator's compile shows no errors owned by this phase; record evidence labels per CONTEXT-CONTROL.

## Do not

- Silent phase-12 bump to `1.0.1` without this analysis.  
- Add `vavr-jackson` 1.x to “fix” Jackson 3 while keeping Vavr.  
- Replace Vavr with Arrow / another FP stack.  
- Change REST wire shapes without `ASK_HUMAN`.  
- Claim `removed` while imports or transitive Vavr remain on the compile classpath intentionally.

## Risk

Band-driven (see DEP-REMOVAL). Default after scoring: LOW → `SAFE_AUTO`; MED → `ASK_HUMAN`; HIGH → `SPIKE_FIRST`. Public DTO leak or prod Jackson module ⇒ at least MED.

## Rollback

Restore previous `io.vavr` pins and revert replacement commits together. Do not leave half-migrated Option/Either mixes.

## Done when

- Score + band recorded; and  
- **removed:** no `io.vavr` pins/imports, replacements use JDK/Kotlin; or  
- **parked / deferred-bump:** human accepted keep + optional `1.0.1`, with follow-up noted in `findings.md`.

## Handoff

`vavr=removed|deferred-bump|parked|n/a; removalRisk=<0-100>; band=LOW|MED|HIGH; vavrJackson=removed|n/a|kept; replacedWith=jdk|kotlin|mixed; next=12|none`
