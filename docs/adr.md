1. What were the two or three most important decisions you made, and why?

**FastAPI with an async stack.** The workload is I/O-bound, so async lets one process handle the 50-vehicles-at-1-Hz burst without thread pools. Pydantic validation, dependency injection, and OpenAPI docs come for free. Connection pool sized at 20 + 10 overflow — well above steady-state demand, with headroom for shift-change bursts.

**WebSockets over polling.** Multiple dashboards polling four endpoints per second would multiply read load linearly with viewers and produce mostly-empty responses. Socket.IO pushes only on change; idle connections are cheap. REST endpoints still serve the initial snapshot on connect, so a dropped connection self-heals on reconnect.

2. What constraints or requirements were **unclear** in this spec, and what did you assume? (Deliberately — the spec leaves things open.)

- **Status updates are derived from telemetry**, not a separate operation. Telemetry events carry status; the ingest path detects transitions. The PATCH endpoint is a manual override sharing the same service logic.
- **Anomalies** are single events violating an operational invariant (battery, speed, status/motion mismatch). Stateless rules, inline during ingest. Thresholds are placeholders.
- **The fleet is fixed and seeded at startup**, like zones. Unknown `vehicle_id` is a 400, not an auto-register.

3. What would need to change if scale grew significantly? You define "significantly.”

- pool size and max overflow
- we should probably consider a caching layer if read traffic becomes a bottleneck

4. What did you deliberately leave out, and why?

- authentication was left out for simplicity
- i thought about adding a caching layer with redis but i think it would be an overkill for the current requirements.

5. **An AI Interaction Log** — a plain markdown file containing:
   - [opencode_session_history.md](../opencode_session_history.md)

6. Corrections or redirections you made when the AI got it wrong
   - after editing services the agent, ran the stale tests and tried to edit the services back to pass the tests
   - the agent was defining every time async_sessionmaker inside routes affecting performance , this is a factory and was moved outside
   - the agent was not using a MVC pattern, enforced this pattern for consistency

7. A 3-5 bullet reflection at the end: what the AI was good at, where it failed you, what you had to double-check manually
   - the agent was good at writing code and following instructions, it was able to write a lot of code in a short amount of time
   - the agent was using uv run fastapi and this was not working with the socket io server, i manually changed it to uv run uvicorn
