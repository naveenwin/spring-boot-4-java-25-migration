# Stub — Task execution and scheduling

> **Status:** stub. Boot 4 changed the executor bean name and the scheduling default. Compile does not catch either one.

## Detect

`@Async`, `@Scheduled`, `AsyncConfigurer`, a bean named `taskExecutor`, or `spring.task.execution` / `spring.task.scheduling` keys.

## Skeleton notes

1. Boot 3.5 removed the bean name `taskExecutor`. The auto-configured executor is `applicationTaskExecutor`. Injection by the old name fails at startup.
2. The silent case: an `AsyncConfigurer` bean is present, nothing fails, and `@Async` runs on `SimpleAsyncTaskExecutor` (a new thread per call, no pool). Return the intended executor from `AsyncConfigurer.getAsyncExecutor()`, or register an alias only when a human has agreed the old name must survive.
3. `spring.task.scheduling.pool.size` defaults to **1**. Every `@Scheduled` method shares that thread. One slow job blocks the rest. Set the size only when the service already depends on concurrent schedules, and record the number the human chose. Do not invent a pool size.
4. A custom `Executor` bean that is not named `applicationTaskExecutor` is not the MVC async executor. Do not rename production beans to chase that default without a human decision.
5. Virtual threads discard these pool settings. See [virtual-threads.md](virtual-threads.md). Do not enable them here.

## Open questions for a future fill-in pass

- Boot 4.1 property names for the execution and scheduling pools, confirmed against that patch’s changelog
- Whether an alias for `taskExecutor` is still required by a library this catalog already pins

## Handoff

`taskExecutionStub=used|skipped; asyncExecutor=applicationTaskExecutor|alias|configurer|n/a; schedulingPool=default-1|explicit|n/a`
