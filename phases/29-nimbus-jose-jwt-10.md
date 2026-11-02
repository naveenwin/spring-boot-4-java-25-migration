# 29 — Nimbus JOSE JWT 9.x → 10.x

## Detect

Apply when:

- Direct `com.nimbusds:nimbus-jose-jwt:9.37*` (or older 9.x)
- Dual versions: app pins 9.x while Spring Security 7 `oauth2-jose` brings 10.x
- Direct use of `SignedJWT` / `JWTClaimsSet` / `DefaultJWTProcessor` / `JWKSource` alongside `NimbusJwtDecoder` / `NimbusJwtEncoder`

Skip when already on a single **10.3+** (prefer Security-aligned or **10.10**) with no 9.x left.

Boot 4 does **not** manage Nimbus — Spring Security (or an explicit force) owns the version.  
Catalog target: **10.10** (or match `spring-security-oauth2-jose`: ~10.4 on SS 7.0 / ~10.9 on SS 7.1).

## Before → After

```gradle
// BEFORE — fights SS7
implementation 'com.nimbusds:nimbus-jose-jwt:9.37.4'

// AFTER — one version on the classpath
implementation 'com.nimbusds:nimbus-jose-jwt:10.10'
// Or omit direct pin and let spring-security-oauth2-jose manage, then force only if needed:
// configurations.all { resolutionStrategy.force 'com.nimbusds:nimbus-jose-jwt:10.10' }
```

Parse / sign / verify call shapes stay the same:

```java
SignedJWT jwt = SignedJWT.parse(token);
jwt.verify(verifier);
JWTClaimsSet claims = jwt.getJWTClaimsSet();
```

## What breaks / how to fix

| Symptom | Cause | Fix |
|---------|--------|-----|
| Auth fails on nested/weird claim JSON | Nesting / invalid JSON rejected (CVE fixes) | Keep rejection; fix issuers — do not raise nesting limits |
| Missing `"claim": null` on the wire | Null claims omitted by default (post-9.40) | `serializeNullClaims(true)` where required |
| `JOSEException` on HS384/HS512 | Min HMAC key lengths | Lengthen secrets |
| Gson / module errors | Pinned 10.1–10.2 | Jump to **≥10.3** (prefer 10.10) |
| Two Nimbus versions | Direct 9.x + SS7 10.x | Unify stale pin; single force |
| JWE decrypt fails after 10.10 | Zip decompress default max 1 MiB | Raise only if legitimate via decrypt options |
| FIPS BC deps missing | FIPS profile removed in 10.0 | Use platform JCA FIPS, not Nimbus optional deps |

**Never pin 10.0 / 10.0.1** (CVE) or **10.1 / 10.2** (Gson churn).

## Steps

1. Inventory direct + transitive Nimbus; note Spring Security 7.0 vs 7.1.  
2. Choose target: match `oauth2-jose` **or** force **10.10** fleet-wide.  
3. Remove 9.x forces; unify resolution. Align `oauth2-oidc-sdk` if present (must not reintroduce 9.x).  
4. Compile; run JWT issue/verify / resource-server tests.  
5. Contract-check null claims, HMAC algs, JWE+`zip` if used.  
6. Ask human to smoke login / token / JwtDecoder paths.  
7. Confirm `dependencyInsight` shows **one** `nimbus-jose-jwt` version.

## Do not

- Keep `9.37*` forced beside Spring Security 7.  
- Land on 10.0–10.2.  
- Disable JSON nesting limits to green tests.  
- Jump to Nimbus **11** in the same change set.  
- Treat “force 10.x on Security 6” as supported — SS6 CVE path is **9.37.4**; move to SS7 for supported 10.x ([20-spring-security-7.md](20-spring-security-7.md)).

## Risk

`ASK_HUMAN` default (auth blast radius). `SPIKE_FIRST` if heavy JWE+zip, FIPS, or custom `JWTProcessor` claim rules.

## Rollback

Revert force/direct pin to previous single version; redeploy. No data migration. If rolling back on SS6, land on **9.37.4**.

## Done when

Single Nimbus **10.3+** (prefer catalog **10.10** or SS-aligned); human confirms JWT paths green or deferred.

## Handoff

`nimbus=10.10|ss-aligned; singleVersion=yes|no; jwtSmoke=green|deferred`
