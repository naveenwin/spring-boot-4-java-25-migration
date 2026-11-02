# 43 — Pub/Sub on Spring Cloud GCP 8

## Detect

Apply when any of these are present:

- `spring-cloud-gcp-starter-pubsub` or `spring-cloud-gcp-pubsub-stream-binder`
- `PubSubTemplate`, `PubSubPublisherTemplate`, `PubSubSubscriberTemplate`, `PubSubAdmin`
- `PubSubInboundChannelAdapter`, `PubSubMessageHandler`, `PubSubMessageSource`
- `JacksonPubSubMessageConverter`, `PubSubMessageConverter`, `GcpPubSubHeaders`
- `spring.cloud.gcp.pubsub.*` or `management.health.pubsub.enabled`

Skip when Pub/Sub is absent. Secret Manager, trace, logging, and the GCP BOM stay in [34-spring-cloud-gcp.md](34-spring-cloud-gcp.md). Protobuf pins stay in [15-protobuf-protoc.md](15-protobuf-protoc.md).

Catalog target: `spring-cloud-gcp-dependencies` **8.2.4** (or the approved 8.x patch). That patch is past **8.0.4**, which removed the Jackson 2 BOM import that breaks `tools.jackson` on Boot 4. Do not run this phase against **8.0.0–8.0.3**.

Stage B runs after phase 34 has aligned the BOM and after phase 04 has a Boot `JsonMapper`. When phase 15 is `must`, its Stage A pin is in the same wave as the GCP 8 BOM, before this phase's source edits.

Read the **pre-migration** GCP version from intake (the versions seen on Boot 3: 4.x, 5.x, 6.x, 7.x). The post-34 BOM line is always 8.x and cannot tell you which defaults changed.

## Before → After

### What Boot 4 actually changes

`PubSubTemplate.publish` already returns `CompletableFuture` on Spring Cloud GCP **4.8.4**. The 8.2.4 javadoc still says "listenable future"; the signature does not. The delivery breaks below remain after that return type is already in place.

| Source train | Unset `max-ack-extension-period` | JSON converter ctor | Health bean |
|--------------|----------------------------------|---------------------|-------------|
| GCP **≤ 5.x** (Boot 3.2 / 3.3, including **5.12.3**) | Spring passes **0 seconds**, which disables ack-deadline extension | `com.fasterxml.jackson.databind.ObjectMapper` | `PubSubHealthIndicator` bean |
| GCP **6.x / 7.x** | Client default, **60 minutes** (property left unset) | Jackson 2 `ObjectMapper` | `PubSubHealthIndicator` bean |
| GCP **8.2.4** (Boot 4) | Client default, **60 minutes** | `tools.jackson.databind.ObjectMapper` | `pubSubHealthContributor` (`HealthContributor`, always a composite) |

GCP **8.2.4** `computeMaxAckExtensionPeriod` returns the configured `Long` or null. `DefaultSubscriberFactory` calls `setMaxAckExtensionPeriod` only when that value is non-null. The client default, used when the setter is skipped, is 60 minutes. The method javadoc on 8.2.4 still says "the default (0) is returned." That sentence is stale. Follow the code and the 8.x property table.

An explicit `0` still disables extension on 8.2.4, because `0` is non-null and is passed through as `Duration.ofSeconds(0)`.

### Ack lease (the silent one)

```yaml
# BEFORE — GCP 5.x with the key absent.
# Effective behavior: ack deadline is not extended.
# A handler slower than the subscription ack deadline (often 10s, set in GCP) is redelivered.
spring:
  cloud:
    gcp:
      pubsub:
        subscriber: {}

# AFTER — preserve that behavior on GCP 8. Record the human choice.
# Adopt the 6+/8 default only when the human accepts 60 minutes of lease extension.
spring:
  cloud:
    gcp:
      pubsub:
        subscriber:
          max-ack-extension-period: 0
```

Leaving the key absent on a service that came from GCP **< 6** switches extension from 0 seconds to 60 minutes. In-flight messages are held much longer; a stuck callback blocks redelivery for up to an hour; duplicate processing from short ack deadlines drops. Both outcomes are production behavior. The human picks one. This phase does not.

Per-subscription keys win over the global key. An unset global key still moves every subscription that has no `spring.cloud.gcp.pubsub.subscription.<name>.max-ack-extension-period`. A `setMaxAckExtensionPeriod` call on `DefaultSubscriberFactory` (or a replaced `SubscriberFactory`) overrides the property for every subscription that factory builds. Record that as `code-override` and do not set a conflicting property.

GCP **≥ 6.0.0** already had the 60-minute default. Do not add the property on that path.

`min-duration-per-ack-extension` and `max-duration-per-ack-extension` are unchanged in effect: unset still means the client default of 0. `executor-threads` stays 4. `parallel-pull-count` stays 1. Flow-control limits stay unlimited. Do not retune them here.

`spring.threads.virtual.enabled` does not replace the Pub/Sub executor. Subscriber callbacks run on the GCP pool (`gcp-pubsub-*` threads).

### JSON converter

Boot 4 application JSON is Jackson 3 ([04-jackson-3.md](04-jackson-3.md)). On GCP **8.2.4** the converter is:

```java
// com.google.cloud.spring.pubsub.support.converter.JacksonPubSubMessageConverter
public JacksonPubSubMessageConverter(tools.jackson.databind.ObjectMapper objectMapper)
```

`tools.jackson.databind.json.JsonMapper` extends that `ObjectMapper`. Pass Boot's `JsonMapper` bean.

```java
// BEFORE — Jackson 2, or a raw mapper the GCP sample still shows
@Bean
PubSubMessageConverter pubSubMessageConverter(com.fasterxml.jackson.databind.ObjectMapper mapper) {
  return new JacksonPubSubMessageConverter(mapper);
}

// AFTER — Boot's JsonMapper, so spring.jackson.* and phase 04 customizers apply
@Bean
PubSubMessageConverter pubSubMessageConverter(JsonMapper jsonMapper) {
  return new JacksonPubSubMessageConverter(jsonMapper);
}
```

`new ObjectMapper()` and `JsonMapper.builder().build()` do not see Boot's modules, date features, or enum config. A payload that matches HTTP JSON on Boot's mapper can diverge on the bus. Run the phase 04 fixtures through the converter that publish and subscribe actually use.

Auto-config calls `ObjectProvider<PubSubMessageConverter>.ifUnique`. Zero beans keeps `SimplePubSubMessageConverter` (`String`, `byte[]`, `ByteString`, `ByteBuffer` only). Two beans wire **neither**, and POJO publish fails at runtime with `PubSubMessageConversionException`. Keep one converter bean.

`PubSubMessageConversionException` extends `NestedRuntimeException`. On Framework 7, `getMessage()` is only the wrapper sentence ("JSON deserialization of an object of type … failed."). The Jackson detail is on `getCause()` (`tools.jackson.core.JacksonException`, unchecked). Assertions and handlers that looked for Jackson text inside `getMessage()`, or caught `JsonProcessingException` as the cause, miss the failure.

`SimplePubSubMessageConverter` for `String` / `byte[]` / protobuf `PubsubMessage` needs no Jackson change. Do not add a Jackson converter that the service did not have.

### Health contributor

GCP 8 registers Pub/Sub health as a `HealthContributor` named `pubSubHealthContributor`. Boot wraps it in a `CompositeHealthContributor` even for one `PubSubTemplate`. Injecting `PubSubHealthIndicator` or `HealthIndicator` (including the old `org.springframework.boot.actuate.health` type) does not see that bean.

```java
// AFTER — only when application code injected the indicator
HealthContributor pubsub = context.getBean("pubSubHealthContributor", HealthContributor.class);
```

`management.health.pubsub.enabled` is still the switch (default true when Actuator is on the classpath). The indicator pulls a subscription: with no `spring.cloud.gcp.pubsub.health.subscription`, a random missing subscription, and `NOT_FOUND` or `PERMISSION_DENIED` means UP. A configured subscription is pulled and **not** acked unless `spring.cloud.gcp.pubsub.health.acknowledge-messages` is true. Do not point that property at a business subscription.

Timeout default has been **5000** ms since GCP **5.10** (`spring.cloud.gcp.pubsub.health.timeout-millis`). Services older than 5.10 had 2000 ms. Record the source version; do not change the key unless a probe budget requires the old timeout, and then set it explicitly.

### Futures that are actually left

Framework 7 removed `org.springframework.util.concurrent.ListenableFuture` and `SettableListenableFuture`. GCP 4.8+ Pub/Sub methods already return `CompletableFuture`, so `.completable()` is not a method on `publish` / `ack` / `nack` for a Boot 3 service. Rewrite only the application and test sites that still name the Spring type.

| Before | After |
|--------|-------|
| `ListenableFuture<String>` holding a publish result | `CompletableFuture<String>` |
| `future.addCallback(ok, err)` | `whenComplete`, preserving swallow vs propagate |
| `SettableListenableFuture` + `set` / `setException` in a stub | `CompletableFuture.completedFuture` / `failedFuture` |
| Kotlin `future.completable().await()` | `future.await()` (`kotlinx.coroutines.future.await`) |

`whenComplete` must not change whether the failure callback swallowed or rethrew. It is not a stand-in for a blocking `.get()` the caller depended on.

GCP **3.x** (Boot 2.7) really did return Spring `ListenableFuture` from publish. That path uses the same table. Boot 3 → 4 does not.

### Unchanged on 8.2.4 (do not rewrite)

Confirmed against GCP **7.3.1** and **8.2.4** sources and the 8.x Pub/Sub reference:

- Property names under `spring.cloud.gcp.pubsub.*`, including `emulator-host`, retry, flow control, ordering, and publisher endpoint.
- `AckMode` (`AUTO`, `AUTO_ACK`, `MANUAL`) and `GcpPubSubHeaders.ORIGINAL_MESSAGE` / `ORDERING_KEY`.
- `PubSubInboundChannelAdapter` consume/ack behavior. `AUTO` nacks when the Spring handler throws. JSON conversion runs inside `subscribeAndConvert`, **before** the Integration error channel, and a conversion failure nacks. Same as 7.3.1.
- Auto-config class names: `GcpPubSubAutoConfiguration`, `PubSubHealthIndicatorAutoConfiguration`.
- `spring-cloud-gcp-pubsub-stream-binder` is still a module. Binder consumers share the subscriber factory and the converter. Do not replace a binder with `PubSubTemplate`.
- `PublisherCustomizer` exists. `SubscriberCustomizer` does **not** — it arrived in **8.3.0**, which is not the catalog target.
- Publisher scheduler: `executor-wait-for-tasks-to-complete-on-shutdown` default **false**, `executor-await-termination-millis` default **0**. Boot's `spring.lifecycle.timeout-per-shutdown-phase` does not wait for `pubsubPublisherThreadPool`. On Boot **≥ 3.2** (Spring 6.1+) this default is already the one GCP 8 uses. On Boot **< 3.2**, queued publishes can be dropped on shutdown unless the human sets `executor-wait-for-tasks-to-complete-on-shutdown: true`.

## Steps

Stage B (source and `application*` / test properties). The BOM edit is phase 34.

1. Record the pre-migration GCP version and every Pub/Sub module (`starter-pubsub`, stream binder, or a direct `spring-cloud-gcp-pubsub`).
2. Inventory subscriber entry points: `subscribe` / `subscribeAndConvert`, inbound adapters, `@ServiceActivator` consumers, stream bindings, `PubSubReactiveFactory` / `Flux` polls, and synchronous `pull`.
3. Resolve the lease. If the source train is **≥ 6.0.0**, leave an absent `max-ack-extension-period` absent (`leaseDecision=already-6plus`). If it is **< 6** and every live subscription is covered by an explicit global or per-subscription value, keep those numbers. If it is **< 6** and any live subscription has no value and no factory-level `setMaxAckExtensionPeriod`, stop for the human: preserve with `0`, or adopt 60 minutes by leaving the key absent. A code-level setter is `code-override`; do not add a conflicting property.
4. Apply the converter decision: no bean for `String` / `byte[]` / `ByteString` / `ByteBuffer` / raw `PubsubMessage`; otherwise one `PubSubMessageConverter` bean that receives Boot's `JsonMapper`. Delete Jackson 2 imports in that bean. Point phase 04's payload fixtures at this converter.
5. Replace Spring `ListenableFuture` / `addCallback` / `SettableListenableFuture` / `.completable()` at Pub/Sub call sites in main and test. Leave non-Pub/Sub GCP futures to phase 34.
6. If application code injects `PubSubHealthIndicator`, switch it to the `pubSubHealthContributor` bean (`org.springframework.boot.health.contributor.HealthContributor`). In tests that must not call Pub/Sub, set `management.health.pubsub.enabled=false` rather than mocking the old indicator type. Do not retarget `spring.cloud.gcp.pubsub.health.subscription` onto a business subscription.
7. Update tests that assert `PubSubMessageConversionException.getMessage()` contains the Jackson cause. Assert `getMostSpecificCause()` (or `getCause()`).
8. On a Boot **< 3.2** source only, ask the human before turning publisher wait-for-tasks on. Otherwise leave the shutdown properties untouched.
9. Residual grep, main and test. Pub/Sub sites must be clean:

```bash
rg -n 'ListenableFuture|ListenableFutureCallback|SettableListenableFuture|\.completable\(\)|addCallback\(|com\.fasterxml\.jackson\.databind\.ObjectMapper|new ObjectMapper\(' \
  --glob '*.java' --glob '*.kt' --glob '*.groovy' src
```

Hits that are not Pub/Sub belong to phase 04 or 34. Record them; do not rewrite them here.

## Do not

- Treat a green compile, or a deleted `.completable()`, as proof the subscriber lease is unchanged.
- Leave `max-ack-extension-period` unset when the source GCP is **< 6** and the human has not chosen 60 minutes.
- Set that property to `0` without the same recorded choice.
- Trust the 8.2.4 javadoc sentence that says the max ack extension default is 0.
- Construct `JacksonPubSubMessageConverter` with `new ObjectMapper()`, a Jackson 2 type, or a second converter bean.
- Add `spring-boot-jackson2` so the old converter constructor compiles.
- Exclude `jackson-bom` to paper over GCP **8.0.0–8.0.3**. Move to the catalog 8.x patch (phase 34).
- Inject `PubSubHealthIndicator` and expect the auto-config bean.
- Point the health subscription at a business subscription, or enable `acknowledge-messages` to make a probe green.
- Change `AckMode`, ordering, flow control, or `executor-threads` while fixing the lease or the converter.
- Bump to GCP **8.3** for `SubscriberCustomizer`. It is not the catalog target.
- Replace `spring-cloud-gcp-pubsub-stream-binder` with a hand-rolled template.
- Assume `spring.threads.virtual.enabled` or `spring.lifecycle.timeout-per-shutdown-phase` covers Pub/Sub callbacks or the publisher scheduler.
- Treat the Pub/Sub emulator as proof of ADC, Workload Identity, TLS, or IAM ([34-spring-cloud-gcp.md](34-spring-cloud-gcp.md)).
- Bump `protoc` or `protobuf-java` here.
- Put project ids, credentials, or message payloads that contain secrets into the pack or phase notes.

## Risk

`SPIKE_FIRST` when the source GCP is **< 6** and `max-ack-extension-period` is unset for any live subscription, when a custom `SubscriberFactory` / `PublisherFactory` exists, or when a JSON converter carries a wire contract.

`ASK_HUMAN` for the 0-vs-60-minute choice, for enabling publisher wait-for-tasks on a Boot < 3.2 source, and for exactly-once subscriptions whose `ack()` future is currently ignored (a failed ack then looks local-success).

`SAFE_AUTO` only when the source GCP is **≥ 6**, payloads are `String` / `byte[]` / `ByteString` / `ByteBuffer` / raw protobuf with no converter bean, nothing injects `PubSubHealthIndicator`, and the future grep is already empty.

## Rollback

Revert this phase's commit. Restoring Boot 3 also restores the GCP 5.x BOM; do not leave Boot 4 on a Boot 3 GCP train, and do not leave an explicit `max-ack-extension-period: 0` in place if the human had chosen the 60-minute default.

## Done when

- The handoff names the pre-migration GCP version and a lease decision for every live subscription.
- At most one `PubSubMessageConverter` bean exists, and a Jackson one takes Boot's `JsonMapper`.
- Phase 04 fixtures have been run through that converter when JSON payloads exist (claim stays `unverified` until Stage C).
- The residual grep is empty for Pub/Sub sites in main and test.
- Health injection, if any, uses `pubSubHealthContributor`.
- The latest compile shows no errors owned by this phase.

## Handoff

`pubsub=migrated|n/a; sourceGcp=<version>; lease=explicit-0|explicit-seconds|library-60m|code-override|n/a; leaseDecision=preserve-0|adopt-60m|already-6plus|n/a; converter=none|boot-jsonmapper|first-party-jsonmapper|blocked; futures=direct-completablefuture|n/a; futureResidual=<n>; healthBean=untouched|contributor|disabled; shutdownWait=untouched|preserved|n/a`
