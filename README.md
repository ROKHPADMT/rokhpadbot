# RokhpadBot

**[▶ Open the bot in Telegram → @ROKHPADbot](https://t.me/ROKHPADbot)**

A Telegram **service-request bot**: a user picks a service, describes the problem, gives their
area, location and phone number, and the request is stored and forwarded to the operator.

It runs **serverless on GitHub Actions** — a deliberate architectural decision, explained below.

---

## Live status

| | |
|---|---|
| Bot | [`@ROKHPADbot`](https://t.me/ROKHPADbot) — verified with `getMe` (`id 7173035688`, `is_bot true`) |
| Runtime | [GitHub Actions workflow](../../actions/workflows/bot.yml) |
| Session length | ~5 h 50 m of long-polling, restarted by cron every 6 hours |
| Cost | **zero** — a public repository gets unlimited Actions minutes |

---

## Why this runs on GitHub Actions instead of a server

The project originally ran on a Windows 10 machine (Pentium E5200, 4 GB RAM) behind a home router
in Iran, managed by NSSM as a Windows service.

Two measured facts made that unreliable:

1. **Telegram's Bot API is unreachable from Iran.** Not slow — actively refused. Every resolver,
   including `8.8.8.8`, `1.1.1.1` and `9.9.9.9`, is transparently rewritten to the same private
   black-hole address, and DNS-over-HTTPS is blocked:
   ```
   api.telegram.org          -> 10.10.34.36      (RFC1918 — impossible)
   TCP api.telegram.org:443  -> refused          (WinError 10061)
   TCP www.python.org:443    -> OK
   ```
2. **Free tunnels are unstable.** A Proton WireGuard config was blocked at the protocol level
   (handshake `0 B received` on five different ports while ICMP/TCP to the same endpoint and
   generic UDP egress all worked). A working free VLESS+REALITY config measured over three
   consecutive probes: `Timeout / Timeout / HTTP 200` — alive but saturated. That is exactly what
   produces `Telegram API TimedOut` in production.

**So execution was moved outside the filtered network.** GitHub's runners reach
`api.telegram.org` natively, cost nothing, and remove the entire class of problems — proxies,
VPNs, kill switches, DNS poisoning, protocol-level DPI.

### Architecture

```
   Telegram users
        │  MTProto (their app)
        ▼
  ┌───────────────┐      HTTPS Bot API      ┌──────────────────────────┐
  │   Telegram    │ ◄─────────────────────► │  GitHub Actions runner   │
  │  Bot Server   │   api.telegram.org      │  (outside Iran, no proxy)│
  └───────────────┘                         │                          │
                                            │  python-telegram-bot 21.6│
                                            │  ConversationHandler     │
                                            │  SQLite (ephemeral)      │
                                            └──────────┬───────────────┘
                                                       ▼
                                              operator notification
                                              (ADMIN_CHAT_ID)
```

---

## Features (all currently implemented)

- `/start` — entry point and service menu
- `/menu` — return to the service menu
- `/myid` — print your chat id (useful for configuring `ADMIN_CHAT_ID`)
- Guided conversation: **service → problem description → area → location → phone number**
- Requests persisted to SQLite (`requests` table, created automatically on first run)
- New requests forwarded to the operator chat
- Graceful session shutdown via `SIGINT` so the poller stops cleanly

---

## Configuration

All configuration is supplied as **GitHub Actions secrets** — nothing sensitive is in the repo.

| Secret | Purpose |
|---|---|
| `BOT_TOKEN` | token from [@BotFather](https://t.me/BotFather) |
| `ADMIN_CHAT_ID` | where incoming requests are forwarded (send `/myid` to the bot to get it) |

### Local development vs production

| | Local | Production |
|---|---|---|
| Where | your machine | GitHub Actions |
| Configuration | `.env` file (git-ignored) | repository secrets |
| Telegram reachability | **requires a working network path to `api.telegram.org`** | native, no proxy |
| Database | persists on disk | **ephemeral — recreated each session** |

```bash
pip install -r requirements.txt
python test_bot.py     # prints the getMe result, proving the token works
python rokbot.py
```

Copy `.env.example` to `.env` first. Never commit `.env`.

> **Note:** if you are inside a network where `api.telegram.org` is blocked, `python test_bot.py`
> will fail locally even with a perfectly valid token. That is a network condition, not a code
> defect — it is precisely why production does not run locally.

---

## Privacy

The database is **ephemeral by design**: it lives for the duration of a workflow run and is never
committed, uploaded as an artifact, or published. `.gitignore` excludes `*.db` and `.env`.
No visitor's name, phone number or location is ever exposed by this repository.

---

## Operational notes

- `concurrency: rokhpadbot-poller` with `cancel-in-progress: false` prevents two pollers racing
  for the same `getUpdates` queue.
- `timeout --signal=INT 21000` (5 h 50 m) stays inside the 6-hour job limit and gives the library
  a clean shutdown.
- GitHub disables *scheduled* workflows after 60 days without repository activity; any real
  commit re-enables them.
- Secrets are never available to workflows triggered from fork pull requests.

---

## License

Personal project — shared as a working reference. Please ask before commercial reuse.
