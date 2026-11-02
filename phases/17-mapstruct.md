# 17 — MapStruct (annotation processing)

## Detect

`mapstruct` / `mapstruct-processor` coordinates, `annotationProcessor` MapStruct entries, or an included/composite SPI build for MapStruct.

Skip if the service has no MapStruct.

## Before → After

### Versions

```gradle
// Before (common Boot 2/3 pin)
implementation 'org.mapstruct:mapstruct:1.5.5.Final'
annotationProcessor 'org.mapstruct:mapstruct-processor:1.5.5.Final'
// lombok-mapstruct-binding if Lombok is used — keep in sync

// After — 1.6.x line used successfully with JDK 25 / Boot 4 migrations
implementation 'org.mapstruct:mapstruct:1.6.3'
annotationProcessor 'org.mapstruct:mapstruct-processor:1.6.3'
```

> **Open / not fully analyzed** — confirm whether MapStruct 1.6 is *required* for JDK 25 vs merely the version validated on a sample migration. Prefer the latest 1.6.x patch the team approves.

### Included / composite SPI builds

```gradle
// Before — stale toolchain on the SPI module
java {
  toolchain { languageVersion = JavaLanguageVersion.of(11) }
}

// After — same Java 25 as the root project
sourceCompatibility = JavaVersion.VERSION_25
targetCompatibility = JavaVersion.VERSION_25
// or toolchain languageVersion = 25
```

Keep processor, API, and any SPI module versions aligned; bump `lombok-mapstruct-binding` when Lombok + MapStruct are both present.

## Steps

1. Detect MapStruct API + processor (+ SPI included build).  
2. Bump to a 1.6.x line (API and processor together).  
3. Align included builds to Java 25.  
4. `compileJava` smoke (and regenerate OpenAPI/MapStruct outputs if the build wires them).  
5. Further patch bumps can sit in [12-dependency-bump-queue.md](12-dependency-bump-queue.md) once on 1.6.x.

## Do not

- Bump only `mapstruct` and leave `mapstruct-processor` on 1.5.x.  
- Leave SPI / `includeBuild` modules on toolchain 11 while the root is 25.  
- Mix MapStruct majors with Spotless-only commits ([10-build-plugins.md](10-build-plugins.md)).

## Risk

`SAFE_AUTO` for coordinated 1.5 → 1.6 + Java 25 SPI alignment after compile succeeds.  
`ASK_HUMAN` if mapper regeneration changes public DTO mapping behavior unexpectedly.

## Rollback

Revert MapStruct coordinates and SPI Java level.

## Done when

`compileJava` succeeds with MapStruct on the classpath; included SPI builds (if any) target Java 25.

## Handoff

`mapstruct=<ver>|n/a; spiJava=25|n/a`
