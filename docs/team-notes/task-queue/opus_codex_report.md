# Opus Report
Status: ACK
Last Updated: 2026-01-10T22:40:00+07:00
Current Task: Debugging Host WS Upgrade Failure (P0 / Device Y05zj)
Notes:
- Confirmed Host usage of relative URL likely cause of upgrade failure.
- Backend returns `/sessions/{id}/ws`. Client must start with `ws://`.
