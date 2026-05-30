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
