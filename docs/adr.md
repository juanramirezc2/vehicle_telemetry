1. What were the two or three most important decisions you made, and why?

- Fast API over any other, because of the async support and non blocking of workers for IO operations
- Websockets over pulling, the server can be under high amounts of traffic having a pulling frontend can increase the load, having an open socket is more efficient and helps for resource management

2. What constraints or requirements were **unclear** in this spec, and what did you assume? (Deliberately — the spec leaves things open.)

- what can be considered an anomaly, i assumed it was related to battery level and speed

3. What would need to change if scale grew significantly? You define "significantly.”

- pool size and max overflow
- we should probably consider a caching layer like redis
