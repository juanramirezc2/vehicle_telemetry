# ADR-000: Title

- Connection pool sized at pool_size=20, max_overflow=10 (ceiling of 30). At 50 vehicles × 1 Hz, sustained load is ~50 writes/sec averaging ~5ms each, so steady-state utilization is well under 1 connection

- Telemetry events are stored in telemetry_events, append-only, with a synthetic integer primary key. Native Postgres types for error_codes (array) and timezone-aware timestamp, plus a separate received_at populated by Postgres to track ingest latency. Two indexes: a composite (vehicle_id, timestamp DESC) covering all per-vehicle queries, and a partial index on zone_entered for zone-entry analytics that only includes transition rows (<1% of the table). CHECK constraints enforce status enum and value ranges at the DB layer. At significantly higher volume (>1M rows/day) this would be partitioned by timestamp and likely moved to TimescaleDB; both are deliberately out of scope here.
