# 21 — Null-safety (JSpecify)

## Detect

Any of:

- Kotlin sources / `kotlin("jvm")` (Kotlin level is [31-kotlin.md](31-kotlin.md): **2.2.x** on Boot 4.0, **2.3.x** on Boot 4.1 + JDK 25)
- NullAway or strict null checking (`-Xjsr305`, etc.)
- `org.springframework.lang.Nullable` / `@NonNull` in first-party or Actuator custom endpoints
- Spring Cloud 2025.1 + Kotlin nullness compile breaks

### Explicit no-op

When `rg 'org\.springframework\.lang' src/main src/test` is empty:

- Complete the phase with `filesTouched=[]` and handoff `jspecify=n/a`.
- Write the phase note anyway, so a later agent does not “fix” annotations that were intentionally left.
- `-Xjsr305=strict` by itself is not a source edit.
- Do not mass-convert non-Spring annotations: `jakarta.annotation.Nullable`, `jakarta.annotation.Nonnull`, `org.jetbrains.annotations.Nullable` / `NotNull`, or other checker annotations in tests.

Skip the rewrite (still record the no-op) when the service has no `org.springframework.lang` usage. Skip the phase entirely only when there is also no null-checker, no Kotlin, and no custom Actuator endpoint nullability issue — and say so in the note.

### Boot 4.1 Kotlin

This phase does not bump Kotlin. On Boot **4.1** + JDK **25**, nullness failures on Kotlin **2.2.x** are a [31-kotlin.md](31-kotlin.md) problem (need **2.3.x**, Boot-managed **2.3.21**) before they are a JSpecify rewrite. Boot **4.0** stays on the **2.2** line. Do not downgrade Kotlin, and do not cap bytecode at 24, to avoid annotations.

## Before → After

```java
// Before (Spring’s older nullability annotations)
import org.springframework.lang.Nullable;

// After (JSpecify — Framework 7 / Boot 4 direction)
import org.jspecify.annotations.Nullable;
```

Framework overview: [Null-safety](https://docs.spring.io/spring-framework/reference/core/null-safety.html).

Actuator optional parameters and custom endpoints should follow JSpecify when touching Boot 4 Actuator APIs — see [22-actuator.md](22-actuator.md).

> **Open / not fully analyzed** — enabling NullAway fleet-wide is a policy decision, not a default migration step. Kotlin multiplatform nullness not covered here.

## Steps

1. Detect Kotlin version (against [31](31-kotlin.md)), NullAway/compiler flags, and `org.springframework.lang.*` usage.  
2. If that import search is empty, stop: `filesTouched=[]`, `jspecify=n/a`. Do not convert `jakarta.annotation` or JetBrains nullness annotations.  
3. On Boot 4.1 + JDK 25, if Kotlin is still 2.2.x, send the bump to phase 31 before editing nullness annotations here.  
4. Replace Actuator / Framework boundary `org.springframework.lang` annotations that fail compile with `org.jspecify.annotations.*`.  
5. Fix first-party APIs only where the compiler or checker fails — do not boil the ocean.  
6. Recompile; record remaining checker debt if any.

## Do not

- Rewrite the entire codebase to JSpecify in the Boot bump without a null-safety initiative.  
- Mass-convert `jakarta.annotation.Nullable` / `Nonnull` or JetBrains test nullness annotations when `org.springframework.lang` is absent.  
- Downgrade Kotlin, or stay on 2.2 for a Boot 4.1 + JDK 25 contract, to “avoid” JSpecify. Bump Kotlin in [31-kotlin.md](31-kotlin.md).

## Risk

`SAFE_AUTO` for the explicit no-op (`filesTouched=[]`) and for Actuator `org.springframework.lang` `@Nullable` swaps that unblock compile.  
`ASK_HUMAN` if NullAway/Kotlin failures cascade across modules. Kotlin **2.2** on Boot **4.1** is phase 31, not a JSpecify debate.

## Rollback

Revert annotation import commits.

## Done when

Either `filesTouched=[]` and `jspecify=n/a` (no `org.springframework.lang` in first-party sources; non-Spring nullness annotations unchanged), or compile (and the existing null-checker, if any) is green for the migrated Boot 4 line. Kotlin matches [31](31-kotlin.md): **2.3.x** on Boot 4.1 + JDK 25, **2.2.x** only on Boot 4.0.

## Handoff

`jspecify=migrated|partial|n/a; filesTouched=<n>|[]; kotlin=2.2|2.3+|n/a; nullAway=ok|debt|n/a`
