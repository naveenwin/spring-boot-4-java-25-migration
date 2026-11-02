# 14 — jsonschema2pojo 1.2 → 1.3 (Jackson 3 annotations)

## Detect

Gradle/Maven plugin `org.jsonschema2pojo` (or `jsonschema2pojo`), a `jsonSchema2Pojo { }` / Mojo config block, and generated DTOs under a configured target package. Skip if the service does not generate from JSON Schema / example JSON.

Often paired with Jackson 3 ([04-jackson-3.md](04-jackson-3.md)): generated types use Jackson annotations for Feign/MVC payloads.

## Before → After

```gradle
// BEFORE (common Boot 3-era)
id "org.jsonschema2pojo" version "1.2.x"
jsonSchema2Pojo {
  source = files("${project.rootDir}/json")
  targetPackage = 'com.example.shared.module'
  sourceType = 'json'          // or jsonschema
  generateBuilders = true
  useInnerClassBuilders = true
  useBigDecimals = true
  // annotationStyle defaults to jackson / jackson2
}

// AFTER — 1.3.x (prefer latest patch, e.g. 1.3.3)
id "org.jsonschema2pojo" version "1.3.x"
jsonSchema2Pojo {
  source = files("${project.rootDir}/json")
  targetPackage = 'com.example.shared.module'
  sourceType = 'json'
  // When the app is on Jackson 3:
  annotationStyle = 'jackson3'
  // jackson3: databind annotations (e.g. @JsonDeserialize) use tools.jackson.databind.annotation
  // Field/property annotations remain com.fasterxml.jackson.annotation.*
  generateBuilders = true
  useInnerClassBuilders = true
  useBigDecimals = true
}
```

### What 1.3.x actually changes (agent expectations)

| Change | Impact |
|--------|--------|
| JDK 17+ for the plugin | Fine on JDK 25 |
| Ant task removed | Irrelevant for Gradle/Maven users |
| `annotationStyle = 'jackson3'` | Needed for Jackson 3 databind annotator; most generated files still import `com.fasterxml.jackson.annotation.*` |
| Common Gradle DSL (`source`, `targetPackage`, `sourceType`, builders, `useBigDecimals`) | Held stable 1.2 → 1.3 in practice — still smoke-generate |
| 1.3.2 Gradle apply fix | Prefer ≥ 1.3.2 / 1.3.3 if plugin apply failed on 1.3.1 |

## Steps

1. Run after [04-jackson-3.md](04-jackson-3.md); Boot 4 uses `annotationStyle = 'jackson3'` with no Jackson 2 intermediate state.
2. Bump plugin `1.2.x` → latest `1.3.x`.  
3. Set `annotationStyle = 'jackson3'`.
4. Smoke: `generateJsonSchema2Pojo` (or Maven equivalent) + `compileJava`.  
5. Spot-check one generated DTO: `com.fasterxml.jackson.annotation` present; `tools.jackson.databind.annotation` only if databind annotations were emitted.  
6. One commit for this bump (do not mix with protoc / Cucumber).

## Do not

- Assume a full DSL rewrite is required before trying generate — 1.3 kept common options.  
- Leave `annotationStyle` on jackson2 after the service is Jackson 3-only.  
- Mark done on version bump alone without a generate + compile smoke.

## Risk

`SAFE_AUTO` after generate smoke succeeds.  
`ASK_HUMAN` if the Gradle/Maven DSL fails to apply or generated types break Feign/MVC compile.

## Rollback

Revert plugin version and `annotationStyle`; regenerate.

## Done when

Plugin on 1.3.x; generation runs and the latest compile shows no errors owned by this phase; `annotationStyle=jackson3`.

## Handoff

`jsonschema2pojo=1.3.x; annotationStyle=jackson3; generate=ok|fail`
