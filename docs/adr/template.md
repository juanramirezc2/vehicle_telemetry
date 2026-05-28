# ADR-000: Title

## Status

Proposed

## Context

50 vehicles telemetry at 1hz

## Decision

Connection pool sized at pool_size=20, max_overflow=10 (ceiling of 30). At 50 vehicles × 1 Hz, sustained load is ~50 writes/sec averaging ~5ms each, so steady-state utilization is well under 1 connection

## Consequences

The headroom absorbs synchronized bursts where all 50 vehicles emit within the same millisecond. At 10× scale (500 vehicles), this approaches Postgres’s default max_connections=100, at which point the answer is PgBouncer in transaction pooling mode rather than larger app-side pool
