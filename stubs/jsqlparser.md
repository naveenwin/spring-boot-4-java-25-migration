# Stub — JSqlParser 4.x → 5.x

> **Status:** stub. Only when the application **directly** imports JSqlParser or owns SQL rewriting. Prefer upgrading the owning library (MyBatis/Hibernate extension) over forking parser internals.

## Detect

`net.sf.jsqlparser`, `SelectBody`, `SubSelect`, `ItemsList`, custom pagination/SQL interceptors; linkage errors after Spring Data / persistence bumps.

Also Detect when Boot 4 removes `spring.data.jpa.query.native.parser` and the service still **owns** JSqlParser rewrite logic — configure `QueryEnhancerSelector` via [33-jpa-spring-data.md](../phases/33-jpa-spring-data.md) first; only deepen this stub if first-party parser code remains.

## Skeleton notes

1. Prove the resolved JAR version; use `javap` on `Select`, `PlainSelect`, `ParenthesedSelect`, `Insert`, `InExpression` — do not migrate from memory.  
2. Common direction signals (confirm in the JAR): `SelectBody`→`Select` hierarchy; `SubSelect`→`ParenthesedSelect`; `SelectExpressionItem`→`SelectItem<?>`; `ItemsList`→`ExpressionList`/`Values`; `Insert.getItemsList()`→`getSelect()`/`getValues()`; `InExpression.getRightItemsList()`→`getRightExpression()`.  
3. Avoid raw casts; handle `PlainSelect`, parenthesized selects, set ops, and `Values` explicitly.  
4. Verify with a SQL corpus (joins, CTEs, INSERT VALUES/SELECT, vendor syntax), then the real persistence path.  
5. Cross-link [dependency-diagnosis.md](dependency-diagnosis.md).

## Open questions for a future fill-in pass

- Promote to phase when a fleet service owns SQL rewrite  
- MyBatis pagination adapter examples  

## Handoff

`jsqlparserStub=used|skipped`
