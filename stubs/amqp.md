# Stub — Spring AMQP / Rabbit

> **Status:** stub.

## Detect

`spring-boot-starter-amqp`, `RabbitTemplate`, listener containers.

## Skeleton notes

1. Align starter with Boot 4.  
2. `Rabbit*RetrySettingsCustomizer` replaces older `RabbitRetryTemplateCustomizer` patterns — confirm names for the Boot line.  
3. Risk: `ASK_HUMAN` for retry/DLQ behavior changes.

## Open questions for a future fill-in pass

- Concrete customizer Before→After snippets  
- Observability instrumentation with Micrometer  

## Handoff

`amqpStub=used|skipped`
