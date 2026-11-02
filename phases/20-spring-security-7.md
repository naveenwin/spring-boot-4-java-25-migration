# 20 — Spring Security 7

## Detect

`spring-boot-starter-security`, OAuth2 client/resource/authorization server, `@EnableMethodSecurity`, `HttpSecurity` / `SecurityFilterChain`, reactive security, security tests without `spring-boot-starter-security-test`.

Skip if the service has no Spring Security.

## Before → After

### Prep

Prefer being current on Security **6.5** behaviors before jumping with Boot 4 / Security **7**. Follow the official [Security migration index](https://docs.spring.io/spring-security/reference/migration/index.html).

### DSL

```java
// Before — .and() chaining (removed)
http.authorizeRequests()… .and().csrf()…

// After — lambda DSL + authorizeHttpRequests
http.authorizeHttpRequests(auth -> auth.anyRequest().authenticated())
    .csrf(csrf -> { /* … */ });
```

### Request matching

- Default moves toward `PathPatternRequestMatcher`  
- Watch absolute URIs and servlet-path prefix rules  

### CSRF and access APIs

CSRF protection is **not** a new Boot 4 behavior. Do **not** disable CSRF merely to make tests pass — decide from the client model (browser/SPA vs pure API) and add tests for allowed and rejected requests.

Access-decision APIs may need the separate `spring-security-access` module or migration to `AuthorizationManager`. Verify against the selected Security release.

> **Open / not fully analyzed** — MFA, modular `HttpSecurity`, SPA CSRF details, full Access API module matrix: spike per service; link Security “what’s new.”

### Jackson 3

Security’s Jackson support modules target Jackson 3 / `JsonMapper.Builder` on Boot 4 — coordinate with [04-jackson-3.md](04-jackson-3.md) (`SecurityJacksonModules` where used).

### Starters / tests

```gradle
implementation 'org.springframework.boot:spring-boot-starter-security'
// OAuth2 starter coordinates per Boot 4 BOM
testImplementation 'org.springframework.boot:spring-boot-starter-security-test'
```

## Steps

1. Confirm Security is in use; note servlet vs reactive.  
2. Align security / OAuth2 starters to Boot 4 names ([19-modular-starters.md](19-modular-starters.md)).  
3. Rewrite `HttpSecurity` to lambda DSL; replace removed `.and()` / deprecated authorize APIs.  
4. Fix request matchers / path patterns that fail authorization tests.  
5. Align Jackson security modules with Jackson 3.  
6. Add `security-test`; replace inert annotations; avoid blanket `addFilters = false` unless the test is non-security ([09-testing.md](09-testing.md)).  
7. Smoke authenticated and anonymous paths the service cares about (human-requested tests).

## Do not

- Change authorization rules “to make tests pass” without approval.  
- Disable CSRF as a generic Boot 4 fix.  
- Leave Security on Jackson 2 modules after phase 04.  
- Skip `security-test` when method/web security tests exist.

## Risk

`SPIKE_FIRST` for custom DSL, matchers, or multi-filter-chain setups.  
`ASK_HUMAN` before any authn/authz behavior change.  
Mechanical starter + test annotation fixes: `SAFE_AUTO` after compile.

## Rollback

Revert Security config commit; keep Boot 4 only if security compiles in isolation.

## Done when

Security config compiles on Security 7; security tests use Boot 4 test starter; no `.and()` DSL left in first-party config.

## Handoff

`security7=ok|spike|n/a; oauth2=yes|no; askedHuman=yes|no`
