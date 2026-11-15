# RokhpadBot

A Telegram **service-request bot**: users pick a service, describe the problem, give their
area, location and phone number, and the request is stored and forwarded to the operator.

It runs **serverless on GitHub Actions** — a deliberate architectural decision explained below.

---

## Why the bot runs on GitHub Actions and not on a server

The project originally ran on a Windows 10 machine (Pentium E5200, 4 GB RAM) behind a home
router in Iran, as an NSSM-managed Windows service.

Two hard facts made that impossible to keep reliable:

1. **Telegram's Bot API is unreachable from Iran.** Not slow — actively refused. Every DNS
   resolver (including `8.8.8.8`, `1.1.1.1`, `9.9.9.9`) is transparently rewritten to the same
   private black-hole address, and DoH is blocked:
   ```
   api.telegram.org -> 10.10.34.36      (RFC1918, impossible)
   TCP api.telegram.org:443 -> refused  (WinError 10061)
   TCP www.python.org:443   -> OK
   ```
2. **A tunnel is the only workaround, and free tunnels are unstable.** A Proton WireGuard config
   was blocked at the protocol level (handshake: `0 B received` on five different ports, while
   ICMP/TCP to the same endpoint and generic UDP egress both worked). A working free
   VLESS+REALITY config was measured over three consecutive probes as
   `Timeout / Timeout / HTTP 200` — alive but saturated. That is exactly the pattern that
   produces `Telegram API TimedOut` in production.

**So the execution was moved outside the filtered network.** GitHub's runners are in the cloud,
reach `api.telegram.org` natively, and cost nothing. The whole class of problems — proxies, VPNs,
kill switches, DNS poisoning, DPI — disappears.

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
                                            └──────────────────────────┘
                                                       │
                                                       ▼
                                              operator notification
                                              (ADMIN_CHAT_ID)
```

**Each run** is a ~5 h 50 m long-polling session. A cron schedule starts a new one every 6
hours, so the bot is effectively always on without ever needing a persistent VM.

---

## Bot flow

```
/start
  └─ choose a service        (ReplyKeyboardMarkup)
       └─ describe the problem
            └─ choose the area
                 └─ share the location
                      └─ share the phone number
                           └─ saved to SQLite + forwarded to the operator
```

Commands: `/start`, `/menu`, `/myid` (handy for finding your chat id, e.g. for `ADMIN_CHAT_ID`).

---

## Configuration

All configuration is supplied as **GitHub Actions secrets** — nothing sensitive is in the repo.

| Secret | Purpose |
|---|---|
| `BOT_TOKEN` | token from [@BotFather](https://t.me/BotFather) |
| `ADMIN_CHAT_ID` | where incoming requests are forwarded (send `/myid` to the bot to get it) |

For local development, copy `.env.example` to `.env` and fill it in. `.env` is git-ignored.

```bash
pip install -r requirements.txt
python test_bot.py     # prints the getMe result, proves the token works
python rokbot.py
```

---

## Privacy

The database is **ephemeral by design**: it lives only for the duration of a workflow run and is
never committed, uploaded as an artifact, or shared. `.gitignore` excludes `*.db` and `.env`.
No visitor's name, phone number or location is ever published in this repository.

---

## Operational notes

- `concurrency` prevents two pollers racing for the same `getUpdates` queue.
- `timeout --signal=INT` gives the library a clean shutdown instead of a hard kill.
- GitHub disables *scheduled* workflows after 60 days without repository activity; any commit
  re-enables them.
- Job time limit is 6 h, hence the 5 h 50 m session length and the 6-hourly schedule.

---

## License

Personal project — shared as a working reference. Please ask before commercial reuse.
