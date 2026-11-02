# 44 — Spring Kafka 4

Boot 4 manages Spring for Apache Kafka 4. The client is Apache Kafka 4, which is KRaft only. This phase changes the test starter, the embedded-broker test API, Kafka's own back-off types, and Jackson serializers that Kafka constructs. It does not turn on a new consumer protocol.

**Not this phase:** application `@Retryable` / `@EnableRetry` / `maxAttempts` → `maxRetries` → [41-spring-retry-framework.md](41-spring-retry-framework.md). Jackson cutover for HTTP and messages that are not Kafka serializers → [04-jackson-3.md](04-jackson-3.md). GCP Pub/Sub → [43-pubsub.md](43-pubsub.md).

## Detect

Apply when any of:

- `spring-boot-starter-kafka` or `org.springframework.kafka:spring-kafka`
- `org.springframework.kafka:spring-kafka-test`
- `@KafkaListener`, `@RetryableTopic`, `KafkaTemplate`, or `@EmbeddedKafka`
- `EmbeddedKafkaZKBroker` or `StreamsBuilderFactoryBeanCustomizer`

Skip when none of those are present. A transitive Kafka type inside a starter the service does not configure is not a hit.

Catalog: `spring-kafka` stays on the Boot BOM. `spring-kafka-test` is a coordinate change, not a version bump ([DEPENDENCY-CATALOG.md](../references/DEPENDENCY-CATALOG.md)).

## Before → After

### Test starter

`spring-boot-starter-kafka` stays. The test jar moves.

```gradle
// BEFORE
testImplementation 'org.springframework.kafka:spring-kafka-test'

// AFTER — version from the Boot BOM, do not pin one
testImplementation 'org.springframework.boot:spring-boot-starter-kafka-test'
```

### Embedded broker

ZooKeeper support is gone. Delete the attributes that only existed for it. KRaft is the only mode, so delete `kraft` as well.

| Remove from `@EmbeddedKafka` | Why |
|-------------------------------|-----|
| `zookeeperPort` | ZooKeeper is gone |
| `zkConnectionTimeout` | ZooKeeper is gone |
| `zkSessionTimeout` | ZooKeeper is gone |
| `kraft` | KRaft is the only mode |

```java
// BEFORE
@EmbeddedKafka(
    partitions = 1,
    topics = {"orders"},
    kraft = true,
    zookeeperPort = 2181)

// AFTER
@EmbeddedKafka(partitions = 1, topics = {"orders"})
```

Inject `EmbeddedKafkaBroker`, not `EmbeddedKafkaZKBroker`. The runtime broker the service already uses must already be KRaft. Do not add a Compose stack in this phase.

### Back-off on Kafka types

Spring Kafka 4 no longer depends on Spring Retry. `@RetryableTopic` stays in Spring Kafka. A custom back-off passed into Kafka (`BackOffValuesGenerator`, a Kafka Streams retry template) uses Framework `BackOff`.

```java
// BEFORE
BackOffPolicy backOff = new ExponentialBackOffPolicy();
backOff.setInitialInterval(1_000);

// AFTER
ExponentialBackOff backOff = new ExponentialBackOff();
backOff.setInitialInterval(1_000);
```

| Kafka still imports | Replace with |
|---------------------|----------------|
| `org.springframework.retry.backoff.BackOffPolicy` on a Kafka type | `org.springframework.util.backoff.BackOff` |
| `ExponentialBackOffPolicy` / `FixedBackOffPolicy` on a Kafka type | `org.springframework.util.backoff.ExponentialBackOff` / `FixedBackOff` |

Listener methods annotated `@Retryable` from `org.springframework.retry` are phase 41, including the `maxAttempts` / `maxRetries` check. Do not rewrite those counts here.

### Serializers

Kafka's `JsonSerializer` / `JsonDeserializer` take a Jackson 3 mapper. Build it with `tools.jackson`, in the same cutover as phase 04. Do not add `spring-boot-jackson2` so the old constructor compiles.

```java
// AFTER
JsonMapper mapper = JsonMapper.builder().build();
JsonDeserializer<Order> deserializer = new JsonDeserializer<>(Order.class, mapper);
deserializer.addTrustedPackages("com.example.orders");
```

`trusted.packages=*` stays forbidden. Name the packages the service already trusted.

### Streams customizer

`StreamBuilderFactoryBeanCustomizer` (Boot) is removed. Use Spring Kafka's `StreamsBuilderFactoryBeanConfigurer`.

### Leave off unless the human asks

| Opt-in | Default in this phase |
|--------|------------------------|
| `spring.kafka.consumer.properties.group.protocol=consumer` (KIP-848) | Leave unset (`classic`). Setting it disables `partition.assignment.strategy`, `heartbeat.interval.ms`, `session.timeout.ms`, and a custom `ConsumerPartitionAssignor`. |
| Share consumers / `ShareConsumerFactory` (KIP-932, early access) | Do not add. |

## Steps

1. Inventory starter, `spring-kafka-test`, `@EmbeddedKafka`, `EmbeddedKafkaZKBroker`, `BackOffPolicy` on Kafka types, `JsonSerializer` / `JsonDeserializer`, and `StreamsBuilderFactoryBeanCustomizer`.
2. Stage A: replace `spring-kafka-test` with `spring-boot-starter-kafka-test`. Leave `spring-kafka` on the Boot BOM. Do not pin either.
3. Stage B: apply the tables above. Optional accelerator, only when step 1 found source hits: OpenRewrite `org.openrewrite.java.spring.kafka.UpgradeSpringKafka_4_0`. The greps below are still the exit gate. The recipe does not decide `group.protocol`.
4. Grep. Zero hits required:

```text
rg -n 'spring-kafka-test|EmbeddedKafkaZKBroker|zookeeperPort|zkConnectionTimeout|zkSessionTimeout|StreamsBuilderFactoryBeanCustomizer' .
rg -n 'kraft\s*=' -g '*EmbeddedKafka*' .
```

5. A remaining `org.springframework.retry` import on a Kafka back-off type is this phase. The same import on a listener `@Retryable` is phase 41.
6. Compile via the orchestrator. Consumer-protocol and share-consumer adoption stay `ASK_HUMAN` and default to not adopted.

## Do not

- Add `spring-boot-jackson2` so a Kafka serializer keeps a Jackson 2 `ObjectMapper`.
- Pin `spring-kafka` or `spring-kafka-test` ahead of the Boot BOM.
- Set `group.protocol=consumer` or add a share consumer because the client is Kafka 4.
- Rewrite `@Retryable` attempt counts. That is phase 41.
- Add a Docker Compose broker file to the service.

## Risk

`SAFE_AUTO` for the test-starter rename, deleted ZooKeeper attributes, and `BackOff` on Kafka types when the intervals stay the same.

`ASK_HUMAN` before `group.protocol=consumer` or any share-consumer bean. `SPIKE_FIRST` when `@EmbeddedKafka` tests need a broker this environment cannot start; record them `unverified` for Stage C.

## Rollback

Revert this phase's commit. A group that was already switched to `group.protocol=consumer` in a deployed environment is not reverted by that commit.

## Done when

`spring-kafka-test`, `EmbeddedKafkaZKBroker`, and the four `@EmbeddedKafka` attributes above are gone. Kafka serializers construct a Jackson 3 mapper. Kafka back-off types use Framework `BackOff` with the same intervals. `group.protocol` and share consumers are unchanged unless the human asked. Compile is green.

## Handoff

`kafka=starter-renamed|source-migrated|n/a; embedded=kraft-only|n/a; backoff=framework|n/a; jackson=tools.jackson|n/a; groupProtocol=unchanged|human-opt-in; shareConsumer=unchanged|human-opt-in`
