# 05 — OpenAPI Generator (Spring)

## Detect

Gradle plugin `org.openapi.generator` or Maven `openapi-generator-maven-plugin`, and/or generated sources under `build/generated*`.

For **runtime** OpenAPI docs (springdoc / Swagger UI / Knife4j failures), use [32-springdoc-openapi.md](32-springdoc-openapi.md) — that is a different stack from this generator phase.

## Before → After

### Plugin version

```text
Before: 7.14.x (or older) — may lack useSpringBoot4 / useJackson3
After:  ≥ 7.16 (prefer current stable 7.26+ when available)
```

### Config flags

```gradle
// Before
configOptions.set([
  useJakartaEe: 'true',
  useSpringBoot3: 'true',
])

// After
configOptions.set([
  useSpringBoot4: 'true',  // implies Jakarta
  useJackson3: 'true',     // requires useSpringBoot4
])
```

`useSpringBoot3` means “Boot 3+/Jakarta era templates,” **not** “this app runs Boot 3.” On Boot 4, prefer `useSpringBoot4`.

### Gradle 7.26+ `outputDir` typing

`srcDir(...outputDir.dir("<folder>"))` **must** match `configOptions.sourceFolder` (often `openapi`). Prefer DirectoryProperty wiring so `:openApiGenerate` → `compileJava` stays task-tracked (avoid string path `.get()`).

```gradle
// Before (String path) — breaks when outputDir is DirectoryProperty
outputDir.set(layout.buildDirectory.dir("generated-sources").map { it.asFile.path })
srcDir(files("${tasks.openApiGenerate.outputDir.get()}/openapi"))

// After — folder name == configOptions.sourceFolder
configOptions.set([
  // ...
  sourceFolder: 'openapi',
])
outputDir.set(layout.buildDirectory.dir("generated-sources"))
srcDir(tasks.openApiGenerate.outputDir.dir("openapi"))
```

### Coverage / JaCoCo

Generator may emit `org.openapitools.**` helpers (e.g. enum converter configuration). If coverage gates fail on those classes, exclude `org.openapitools.**` from JaCoCo / verification (see light notes in [13-verification.md](13-verification.md)).

## Steps

1. Bump generator plugin to a version that supports `useSpringBoot4` + `useJackson3`.  
2. Replace Boot 3 flags with Boot 4 + Jackson 3 flags.  
3. Fix `outputDir` / sourceSet wiring for DirectoryProperty; keep `sourceFolder` aligned with `dir(...)`.  
4. Regenerate and fix first-party code that depended on old generated signatures.  
5. Align `jackson-databind-nullable` if nullable models are enabled (≥ 0.2.10).  
6. If coverage fails on generated OpenAPI support classes, add excludes.

## Do not

- Set `useJackson3` without `useSpringBoot4` (generator will reject).  
- Jump generator majors without fixing DirectoryProperty / config API.  
- Point `srcDir` at a folder that does not match `sourceFolder`.  
- Commit generated sources unless the repo already does.

## Risk

`SAFE_AUTO` for flag + DirectoryProperty fixes.  
`ASK_HUMAN` if regeneration changes public API DTOs unexpectedly.

## Rollback

Pin previous generator version + flags; delete regenerated tree and rebuild.

## Done when

`openApiGenerate` evaluates and runs; generated code compiles with Jackson 3 packages where expected.

## Handoff

`openapiPlugin=<ver>; useSpringBoot4=true; useJackson3=true; jacocoOpenApiExclude=yes|n/a`
