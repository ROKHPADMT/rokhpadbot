# RokhpadBot — Hands-off automation status (2026-11-17)

## Incident

- Bot appeared fully down (not merely inside a 5h50m session gap).
- D1/DSH free token exhaustion was concurrent noise; **not** the cause of bot downtime.
- Root cause: last scheduled session had finished; the next 6-hourly schedule did not start in time (GitHub schedule delay / sparse cron).

## Recovery (same day)

1. Confirmed Actions history: runs #11–#12 succeeded; no job in progress at check time.
2. First fix: cron `0 */6 * * *` → `0 */3 * * *` + push → run **#13** started and bot answered in Telegram.
3. Second fix (hands-off): cron → **`0 * * * *` (hourly)** so restart does not depend on F0 or any model clicking Run.

## Target operating mode

| Piece | Setting |
|-------|--------|
| Session length | ~5h50m (`timeout 21000` + job `timeout-minutes: 355`) |
| Schedule | every hour UTC |
| Concurrency | `rokhpadbot-poller`, `cancel-in-progress: false` |
| Normal restart | automatic (pending hourly run or next tick after session end) |
| Manual Run / model push | emergency only |

## What is automated now

- Start after deploy/push
- Restart after a session ends, without human/model intervention under normal GitHub schedule behavior
- Single poller only (no dual `getUpdates` fight)

## What is still not guaranteed

- Paid VPS-level 100% uptime
- Zero gap if GitHub delays all nearby schedule events
- Persistent DB across sessions (still ephemeral by design)
- DSH/D1 involvement (not required for this bot path)

## Authority

Founder (F0). Recorded by X1 on 2026-11-17.
