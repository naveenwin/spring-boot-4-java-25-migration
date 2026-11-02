# 10 — Build plugins (Spotless / formatting)

## Detect

Spotless, google-java-format, or other format plugins that break on JDK 25.

For **jsonschema2pojo** → [14-jsonschema2pojo.md](14-jsonschema2pojo.md).  
For **protobuf / protoc** → [15-protobuf-protoc.md](15-protobuf-protoc.md).  
For **Shadow** (johnrengelman / gradleup / drop) → [39-remove-or-migrate-shadow.md](39-remove-or-migrate-shadow.md).

## Before → After

### Spotless / google-java-format

```gradle
// JDK 25 needs google-java-format ≥ 1.28; Spotless 7.x often pins ≥ 1.30
googleJavaFormat('1.30.0')
```

## Steps

1. Upgrade Spotless + GJF for JDK 25.  
2. Confirm format check runs on JDK 25.  
3. If jsonschema2pojo or protobuf are present, run phases **14** / **15** as separate commits (do not bury them only in this file).

## Do not

- Ignore Spotless failures on JDK 25 by disabling formatting.  
- Bump `protoc` or jsonschema2pojo majors inside the Spotless-only commit.

## Risk

`SAFE_AUTO` for Spotless / GJF.

## Rollback

Revert plugin / GJF pin.

## Done when

Formatting tasks run on JDK 25.

## Handoff

`spotless=ok; next=14-jsonschema2pojo|15-protobuf|none`
