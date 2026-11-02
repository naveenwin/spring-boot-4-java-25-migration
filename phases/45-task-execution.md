# 45 — Task execution and scheduling

Boot **3.5** stopped registering the auto-configured executor under the name `taskExecutor`. Boot **4.0** and **4.1** keep that arrangement: the auto-configured bean name is `applicationTaskExecutor` (`TaskExecutionAutoConfiguration.APPLICATION_TASK_EXECUTOR_BEAN_NAME`). Compile does not see a missing bean name. This phase is Stage B only (source and configuration). There is no Stage A build edit.

## Detect

Apply when any of:

- `@Async`, `@EnableAsync`, `@Scheduled`, `@EnableScheduling`
- `AsyncConfigurer` (`org.springframework.scheduling.annotation.AsyncConfigurer`)
- `@Qualifier("taskExecutor")`, `@Resource(name = "taskExecutor")`, or `getBean("taskExecutor", …)` aimed at the auto-configured executor
- A `@Bean` whose name is `taskExecutor` or `applicationTaskExecutor`
- `spring.task.execution.*` or `spring.task.scheduling.*`
- A custom `Executor` / `AsyncTaskExecutor` bean while the service uses Spring MVC, WebFlux, or GraphQL async request handling

Skip when none of those signals exist. A user bean that is already named `taskExecutor` on purpose is not the removed alias; leave that bean and the injections that target it.

## Before → After

### Auto-configured bean name (since Boot 3.5)

Code that asks for the auto-configured executor by the name `taskExecutor` no longer finds it. Retarget that lookup to `applicationTaskExecutor`.

```java
// Before — name removed from the auto-configured bean in Boot 3.5
@Autowired
@Qualifier("taskExecutor")
Executor executor;

// After
@Autowired
@Qualifier("applicationTaskExecutor")
Executor executor;
```

`@Resource(name = "taskExecutor")` and `BeanFactory` lookups of that name follow the same retarget. Do this only when no application `@Bean` is declared under the name `taskExecutor`.

An alias is a separate decision. Register one only when the plan already records that the name `taskExecutor` must survive:

```java
@Bean
static BeanFactoryPostProcessor taskExecutorAliasBeanFactoryPostProcessor() {
    return beanFactory -> beanFactory.registerAlias("applicationTaskExecutor", "taskExecutor");
}
```

### `AsyncConfigurer`

A user `AsyncConfigurer` replaces Boot's configurer, which is what selects `applicationTaskExecutor` for `@EnableAsync`. Framework 7 then uses `getAsyncExecutor()`. A `null` return keeps Framework's default: the unique `TaskExecutor` bean, otherwise an `Executor` bean named `taskExecutor`, otherwise a local `SimpleAsyncTaskExecutor` (a new thread per call, no pool). The missing `taskExecutor` name means that second step does not see Boot's executor. When the unique-`TaskExecutor` lookup also fails, `@Async` uses `SimpleAsyncTaskExecutor` and startup still succeeds.

When `getAsyncExecutor()` already returns an executor, leave it. When it returns null and the auto-configured `applicationTaskExecutor` bean is still present, return that bean:

```java
@Bean
AsyncConfigurer asyncConfigurer(BeanFactory beanFactory) {
    return new AsyncConfigurer() {
        @Override
        public Executor getAsyncExecutor() {
            return beanFactory.getBean(
                    TaskExecutionAutoConfiguration.APPLICATION_TASK_EXECUTOR_BEAN_NAME,
                    Executor.class);
        }

        @Override
        public AsyncUncaughtExceptionHandler getAsyncUncaughtExceptionHandler() {
            // existing handler
        }
    };
}
```

`AsyncConfigurer` beans initialize early. Take the executor from the `BeanFactory` argument (or a lazy `ObjectProvider`). Do not field-inject it. The same bean name and constant apply in Kotlin.

### Scheduling pool and execution pool keys (Boot 4.1)

Boot 4.0 and 4.1 configuration changelogs do not rename these keys. `ThreadPoolTaskScheduler` uses one thread unless `spring.task.scheduling.pool.size` is set. Every `@Scheduled` method shares that thread until the service sets a size.

| Key | Boot 4.1.2 default |
|-----|--------------------|
| `spring.task.scheduling.pool.size` | `1` |
| `spring.task.scheduling.thread-name-prefix` | `scheduling-` |
| `spring.task.scheduling.shutdown.await-termination` | `false` |
| `spring.task.scheduling.shutdown.await-termination-period` | unset |
| `spring.task.scheduling.simple.concurrency-limit` | unset |
| `spring.task.execution.pool.core-size` | `8` |
| `spring.task.execution.pool.max-size` | unbounded (`Integer.MAX_VALUE`) |
| `spring.task.execution.pool.queue-capacity` | unbounded (`Integer.MAX_VALUE`) |
| `spring.task.execution.pool.keep-alive` | `60s` |
| `spring.task.execution.pool.allow-core-thread-timeout` | `true` |
| `spring.task.execution.pool.shutdown.accept-tasks-after-context-close` | `false` |
| `spring.task.execution.thread-name-prefix` | `task-` |
| `spring.task.execution.shutdown.await-termination` | `false` |
| `spring.task.execution.shutdown.await-termination-period` | unset |
| `spring.task.execution.mode` | `auto` |
| `spring.task.execution.propagate-context` | `false` (added in 4.1) |

Leave a key that the service already sets. Do not add a pool size. `spring.task.execution.simple.*` (`cancel-remaining-tasks-on-close`, `reject-tasks-when-limit-reached`, `concurrency-limit`) applies to the simple executor, including when virtual threads are on. Do not set those keys here.

### MVC, WebFlux, and GraphQL

With no custom `Executor`, Boot's `applicationTaskExecutor` serves `@EnableAsync` (unless an `AsyncConfigurer` is present), MVC async request handling, WebFlux blocking execution, and GraphQL `Callable` handling.

A custom `Executor` bean makes that auto-configuration back off. The custom bean is then the regular `@EnableAsync` executor. MVC, WebFlux, and GraphQL still require a bean named `applicationTaskExecutor`. MVC and WebFlux also require type `AsyncTaskExecutor`. A custom `Executor` under another name is not that bean.

Leave the custom bean's name. Do not set `spring.task.execution.mode=force` and do not rename it to `applicationTaskExecutor` unless the plan records that decision. `force` keeps the auto-configured executor for those integrations, and for `@EnableAsync`, even when another `Executor` is `@Primary` or named `taskExecutor`. An `AsyncConfigurer` still overrides `@EnableAsync` in that mode.

`@Bean(defaultCandidate = false)` on a custom `Executor` that must stay injectable without suppressing `applicationTaskExecutor` is the reference pattern. Use it only when the plan already says the auto-configured executor must remain.

### Several `TaskDecorator` beans (Boot 4.0)

Boot 4.0 applies every `TaskDecorator` bean to the auto-configured executor and scheduler. More than one becomes a `CompositeTaskDecorator` in `@Order` / `Ordered` order. Leave the beans. Set `@Order` when the service has more than one and the order is already known. Do not drop a decorator to force a single bean.

## Steps

1. **Stage B.** Inventory `@Async`, `@Scheduled`, `AsyncConfigurer`, executor `@Bean` names, `@Qualifier("taskExecutor")`, `@Resource(name = "taskExecutor")`, and `spring.task.execution` / `spring.task.scheduling` keys. If a `@Bean` is named `taskExecutor`, record it as an application bean and do not retarget injections that select it.
2. **Stage B.** For lookups of the removed auto-config name, switch the qualifier, `@Resource` name, or `getBean` name to `applicationTaskExecutor`. Register the alias in the Before → After block only when the plan records that the old name must survive.
3. **Stage B.** For each `AsyncConfigurer`, if `getAsyncExecutor()` returns null and `applicationTaskExecutor` is still auto-configured, return that bean using the `BeanFactory` lookup above. If it already returns an executor, leave the method. If a custom `Executor` has suppressed the auto-configured bean, do not look up a missing `applicationTaskExecutor`.
4. **Stage B.** Read `spring.task.scheduling.pool.size` and `spring.task.execution.pool.*`. If a key is absent, leave it absent. If it is present, keep the service's value. Write a new size only when the plan records the number a human chose.
5. **Stage B.** If a custom `Executor` is not named `applicationTaskExecutor`, leave the name and leave `spring.task.execution.mode` unset (default `auto`). Record `mvcExecutor=custom-unnamed`. Rename or set `mode=force` only when the plan records that decision.
6. **Stage B.** If more than one `TaskDecorator` bean exists, leave each bean and keep or add `@Order` when the existing code already defines an order.
7. Do not set `spring.threads.virtual.enabled` or `spring.task.execution.propagate-context`. Virtual threads are [virtual-threads.md](../stubs/virtual-threads.md). Sleuth executor wrapping is [07-observability.md](07-observability.md).

## Do not

- Register a `taskExecutor` alias, or raise `spring.task.scheduling.pool.size` or any `spring.task.execution.pool.*` value, without a number or alias decision already recorded in the plan ([99-anti-patterns.md](../references/99-anti-patterns.md) item 44).
- Invent a pool size. The scheduling default of 1 stays until a human records a different size.
- Turn on `spring.threads.virtual.enabled` so the pool properties "take effect." With virtual threads, `spring.task.execution.pool.*` and `spring.task.scheduling.pool.*` have no effect. `spring.task.execution.thread-name-prefix` and `spring.task.scheduling.thread-name-prefix` still apply.
- Rename a production `Executor` to `applicationTaskExecutor`, or set `spring.task.execution.mode=force`, without a recorded decision.
- Set `spring.task.execution.propagate-context`. It defaults to `false` on Boot 4.1. This phase does not opt in.
- Field-inject collaborators into an `AsyncConfigurer` configuration class.

## Risk

`SAFE_AUTO` for retargeting lookups of the removed auto-config name to `applicationTaskExecutor`, and for returning that existing bean from a null `getAsyncExecutor()`, when the auto-configured bean is still present.

`ASK_HUMAN` when the plan must decide an alias, a pool size the service did not already set, `spring.task.execution.mode=force`, or renaming a custom `Executor` to `applicationTaskExecutor`. Virtual threads stay out of this phase.

## Rollback

Restore the previous qualifier and resource names, remove an alias this phase added, and restore the previous `getAsyncExecutor()` body. Pool keys this phase must not have changed; if a recorded human value was written, restore the prior file.

## Done when

The latest compile shows no errors owned by this phase. Lookups of the auto-configured executor use `applicationTaskExecutor` unless a recorded alias is in place. An `AsyncConfigurer` that previously returned null now returns that bean when the auto-configured executor still exists. Pool keys match what the service already had, or a size the plan recorded. This phase did not enable virtual threads. Which thread actually runs `@Async` and `@Scheduled` is Stage C.

## Handoff

`taskExecution=used|skipped; asyncExecutor=applicationTaskExecutor|alias|configurer|n/a; schedulingPool=default-1|explicit|n/a; mvcExecutor=auto|custom-unnamed|n/a`
