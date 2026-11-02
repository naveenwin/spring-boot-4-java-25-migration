# 06 — HTTP clients (MVC, Feign, WebFlux)

## Detect

Any of:

- OpenFeign clients, custom `ErrorDecoder` / `Decoder` / `SpringDecoder` configs
- `WebClient` / WebFlux, or imperative `RestClient` / `RestTemplate`
- `RetryableException(` constructor call sites
- Helpers that take `Map` / `MultiValueMap` fed by `response.getHeaders()` / `HttpHeaders`

## Before → After

### Prefer Boot’s Jackson 3 converters

Spring Cloud OpenFeign on Boot 4 typically encodes/decodes via Spring `HttpMessageConverter`s backed by Boot’s `JsonMapper`. Custom Feign configs that inject a mapper should take `JsonMapper`:

```java
// Before
private final ObjectMapper objectMapper; // com.fasterxml…

// After
private final JsonMapper jsonMapper; // tools.jackson.databind.json.JsonMapper
```

### Feign `SpringDecoder` / message converters (Cloud OpenFeign on Boot 4)

```java
// Before
ObjectFactory<HttpMessageConverters> messageConverters;
ObjectProvider<HttpMessageConverterCustomizer> customizers;
new SpringDecoder(messageConverters, customizers)

// After
ObjectProvider<FeignHttpMessageConverters> messageConverters;
new SpringDecoder(messageConverters)
```

Custom `ErrorDecoder` / body readers that used `ObjectMapper` should take `JsonMapper` the same way as phase 04.

### Feign Jackson codec modules

```text
Some Cloud trains manage Feign 13.6.x — that line has feign-jackson (Jackson 2)
but NOT feign-jackson3.

Do NOT add io.github.openfeign:feign-jackson3 without a managed version.
If the BOM does not manage it, resolution fails (empty version).
```

**Standard on those trains:** do not add or directly use `feign-jackson`; exclude it when it becomes an application codec/conflict, and rely on Spring converters + Boot Jackson 3.

If a newer Feign line (with `feign-jackson3`) is managed by the BOM, swapping codecs is optional and needs human approval.

### `RetryableException` overload ambiguity

```java
// Before — may fail to compile when null matches multiple overloads
throw new RetryableException(status, message, method, null, response);

// After — disambiguate retry-after
throw new RetryableException(status, message, method, (Long) null, response);
```

### HttpHeaders (Framework 7)

`HttpHeaders` is no longer a `MultiValueMap` / Map subtype in the same way.

```java
// Before — headers passed where Map / MultiValueMap was accepted
helper(response.headers()) // or headers treated as Map

// After (preferred) — overload helpers to accept HttpHeaders
helper(HttpHeaders headers) {
  if (headers.containsHeader("X")) { ... }
  headers.getFirst("X");
  // iterate headerNames / headerSet as needed
}

// After (compile bridge only — tech debt)
helper(headers.asMultiValueMap());
```

Prefer overloading the helper. Treat `asMultiValueMap()` as a short-lived bridge (`ASK_HUMAN` if left as the permanent API). See [99-anti-patterns.md](../references/99-anti-patterns.md).

### Which HTTP client Boot 4 actually uses

Boot 4 picks the imperative client in this order: Apache HttpClient 5, Jetty, Reactor Netty, the JDK client, then the simple JDK `HttpURLConnection` client. A Boot 2.6 `RestTemplate` that never named a factory was usually `SimpleClientHttpRequestFactory`.

- `httpclient5` on the classpath moves **every** `RestTemplate` and `RestClient` onto `HttpComponentsClientHttpRequestFactory`, including clients that never imported Apache types. Pool size, keep-alive, and redirect policy change together. Compile stays green.
- With no detected client library, Boot uses the JDK client. That client rejects the restricted headers `Connection`, `Host`, `Content-Length`, `Expect`, and `Upgrade` on a live call. `MockRestServiceServer` does not send those headers, so the suite stays green.
- HttpClient 5 follows a redirect for every method. A **301** or **302** turns POST into GET. **303** does too. **307** and **308** keep the method. The exception the caller logs still says POST. Nothing in the interceptor chain records the redirect.

Record which implementation the classpath will select before adding `httpclient5`. A GET/HEAD-only redirect strategy restores the old POST behavior and is `ASK_HUMAN`. Do not invent `spring.http.clients` connect or read timeouts. The Boot 4.1 prefix is `spring.http.clients` (`spring.http.client` is the deprecated prefix); confirm the patch changelog before writing a key.

### HttpMessageConverters customizers (Boot 4 / Framework 7)

Boot’s older `HttpMessageConverters` bean style is deprecated in favor of Framework converters + customizers ([Framework message converters](https://docs.spring.io/spring-framework/reference/web/webmvc/message-converters.html)).

```java
// Before — contributing a raw HttpMessageConverter @Bean / mutating a shared list
@Bean
HttpMessageConverter<?> customConverter() { … }

// After — prefer client vs server customizers (names per Boot 4.x line)
@Bean
ClientHttpMessageConvertersCustomizer clientCustomizer() {
  return converters -> { /* add/replace */ };
}
@Bean
ServerHttpMessageConvertersCustomizer serverCustomizer() {
  return converters -> { /* add/replace */ };
}
```

Configure client and server separately when both exist. Cross-link Jackson 3 ([04-jackson-3.md](04-jackson-3.md)).

> **Open / not fully analyzed** — exact customizer type names if renamed on a given Boot patch. A Jersey integration that requires Jackson 2 blocks the direct cutover until upgraded or replaced.

### WebFlux

See [35-webflux.md](35-webflux.md) for focused WebClient starters, Jackson 3 codecs, WebTestClient, and Netty 4.2.

### HTTP Service Clients (opt-in)

`@HttpExchange` / `@ImportHttpServices` → [stubs/http-service-clients.md](../stubs/http-service-clients.md).

## Steps

1. Point Feign custom decoders/encoders / ErrorDecoders at `JsonMapper`.  
2. Update `SpringDecoder` construction to `FeignHttpMessageConverters` / single-arg form.  
3. Confirm JSON traffic uses Spring converters (default OpenFeign setup).  
4. Migrate custom `HttpMessageConverter` beans to client/server customizers when present.  
5. Remove broken `feign-jackson3` pins if the BOM cannot version them.  
6. Fix `RetryableException` ambiguous `null` args.  
7. Update `HttpHeaders` call sites (prefer overloads; bridge only if needed).  
8. For WebFlux services, follow phase 35.  
9. Name the imperative client Boot 4 will select from the classpath. If that adds `httpclient5` or drops the simple factory, record it. Do not add the Apache client only to quiet a restricted-header failure.  
10. If production calls follow redirects, ask the human before installing a GET/HEAD-only strategy. Leave timeouts unset unless the service already set them.

## Do not

- Add unversioned `feign-jackson3` “because Jackson 3.”  
- Keep `feign-jackson` as an application JSON codec on Boot 4.
- Force `preferred-json-mapper=jackson2`.  
- Treat Map-shaped `HttpHeaders` usage as the long-term Boot 4 API.
- Add `httpclient5` without recording that every `RestTemplate` and `RestClient` changes implementation.
- Install a redirect strategy, or write `spring.http.clients` timeouts, to recreate Boot 2 behavior without a human decision.

## Risk

`SAFE_AUTO` for JsonMapper injection, SpringDecoder constructor, and `(Long) null`.  
`ASK_HUMAN` if converter customizers change wire format; if keeping a permanent `asMultiValueMap()` bridge vs refactoring helpers; before Feign major upgrades or codec module swaps; before a redirect strategy or any new client timeout.

## Rollback

Restore previous Feign dependencies and mapper types.

## Done when

Feign/MVC compile; no hard dependency on unresolved `feign-jackson3`; header helpers compile on Framework 7. The imperative client Boot 4 will select is recorded. A redirect-strategy or timeout change is either absent or human-approved.

## Handoff

`feign=spring-converters|custom; httpHeaders=overloaded|bridge|n/a; springDecoder=updated|n/a; clientImpl=apache|jdk|simple|unchanged|n/a; redirectPolicy=unchanged|asked`
