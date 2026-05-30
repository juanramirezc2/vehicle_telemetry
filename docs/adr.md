1. What were the two or three most important decisions you made, and why?

- Fast API over any other, because of the async support and non blocking of workers for IO operations
- Websockets over pulling, the server can be under high amounts of traffic having a pulling frontend can increase the load, having an open socket is more efficient and helps for resource management

2. What constraints or requirements were **unclear** in this spec, and what did you assume? (Deliberately — the spec leaves things open.)

- what can be considered an anomaly, i assumed it was related to battery level and speed

3. What would need to change if scale grew significantly? You define "significantly.”

- pool size and max overflow
- we should probably consider a caching layer if read traffic becomes a bottleneck

4. What did you deliberately leave out, and why?

- i thought about adding a caching layer with redis but i think it would be an overkill for the current requirements.

5. **An AI Interaction Log** — a plain markdown file containing:
   - [opencode_session_history.md](../opencode_session_history.md)
     5.1 Corrections or redirections you made when the AI got it wrong
   - after editing services the agent, ran the stale tests and tried to edit the services back to pass the tests
   - the agent was defining every time async_sessionmaker inside routes affecting performance , this is a factory and was moved outside
   - the agent was not using a MVC pattern, enforced this pattern for consistency
     5.2 A 3-5 bullet reflection at the end: what the AI was good at, where it failed you, what you had to double-check manually
   - the agent was good at writing code and following instructions, it was able to write a lot of code in a short amount of time
   - the agent was using uv run fastapi and this was not working with the socket io server, i manually changed it to uv run uvicorn

## Notes

- Connection pool sized at pool_size=20, max_overflow=10 (ceiling of 30). At 50 vehicles × 1 Hz, sustained load is ~50 writes/sec averaging ~5ms each, so steady-state utilization is well under 1 connection

- Telemetry events are stored in telemetry_events, append-only, with a synthetic integer primary key. Native Postgres types for error_codes (array) and timezone-aware timestamp, plus a separate received_at populated by Postgres to track ingest latency. Two indexes: a composite (vehicle_id, timestamp DESC) covering all per-vehicle queries, and a partial index on zone_entered for zone-entry analytics that only includes transition rows (<1% of the table). CHECK constraints enforce status enum and value ranges at the DB layer. At significantly higher volume (>1M rows/day) this would be partitioned by timestamp and likely moved to TimescaleDB; both are deliberately out of scope here.

- zone_counter concurrency

```sql
UPDATE zone_counters
SET entry_count = entry_count + 1, updated_at = NOW()
WHERE zone_id = 'charging_bay_1';

```

will help with concurrency in this way

1. T1 begins the UPDATE, acquires a row-level exclusive lock on the charging_bay_1 row.
2. T2's identical UPDATE arrives; Postgres sees the lock and T2 waits (it doesn't fail, doesn't see stale data, just blocks).
3. T1's transaction commits. The lock releases. T2 unblocks.
4. T2's UPDATE now reads the post-T1 value of entry_count (this is the key MVCC behavior for UPDATE: it re-reads the row at lock acquisition time, sees the latest committed value, computes latest + 1).
5. T2 commits.
