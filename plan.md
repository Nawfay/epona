# Commute Bot — Plan

A small Python bot you DM with `/work` or `/home` to get the next GO train between Markham GO and Union Station (Stouffville line), with countdowns and arrival times. Runs on **both Discord and Slack** from one shared codebase.

## Goals

- `/work` — next train from **Markham GO → Union**. Reply with: next departure time, minutes until departure, ETA at Union.
- `/home` — next train from **Union → Markham GO**. Reply with: next departure time, minutes until departure, ETA at Markham.
- Works in DMs on Discord and in the Foratus Slack workspace.
- Uses real-time GO Transit data when available, falling back to scheduled times.
- One core, two thin platform adapters — adding a third platform later (SMS, iMessage, etc.) should be trivial.

## Architecture

```
        ┌────────────────┐        ┌────────────────┐
        │ Discord adapter │       │  Slack adapter │
        │  (discord.py)   │       │   (slack-bolt) │
        └────────┬────────┘       └────────┬───────┘
                 │                          │
                 └──────────┬───────────────┘
                            ▼
                 ┌──────────────────────┐
                 │  Shared core (pure)  │
                 │  commute.next_trip() │
                 │  go_api wrapper      │
                 │  formatting          │
                 └──────────┬───────────┘
                            ▼
                 ┌──────────────────────┐
                 │  Metrolinx GO API    │
                 └──────────────────────┘
```

The two adapters are ~50 lines each. They register slash commands, call into the shared core, and format the reply for that platform. All logic, data fetching, and trip-picking lives in the shared core.

## Tech stack

- **Python 3.11+**
- **discord.py 2.x** — Discord adapter, slash commands via `app_commands`.
- **slack-bolt** (Python, async) — Slack adapter. Use **Socket Mode** so we don't need a public HTTPS endpoint.
- **httpx** (async) — GO Transit API calls.
- **python-dotenv** — local secrets.
- **zoneinfo** (stdlib) — `America/Toronto` timezone handling.
- `pip` + `requirements.txt` (or `uv` if you prefer).

## Project layout

```
commute/
├── plan.md
├── .env                    # all secrets (gitignored)
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
└── src/
    ├── __init__.py
    ├── main.py             # entrypoint: starts both adapters as async tasks
    ├── config.py           # loads env, station codes, line config
    ├── go_api.py           # Metrolinx API wrapper (platform-agnostic)
    ├── commute.py          # next_trip() core logic (platform-agnostic)
    ├── formatting.py       # render reply for "discord" or "slack" flavor
    └── adapters/
        ├── __init__.py
        ├── discord_bot.py  # discord.py client + /work, /home
        └── slack_bot.py    # slack-bolt app + /work, /home
```

`main.py` runs both adapters concurrently with `asyncio.gather`. You can disable either one with an env flag (`ENABLE_DISCORD=false`, `ENABLE_SLACK=false`) for local testing.

## Configuration

`.env`:

```
# --- GO Transit ---
GO_API_KEY=...
HOME_STATION=MA             # Markham GO stop code (to verify)
WORK_STATION=UN             # Union stop code (to verify)
LINE=ST                     # Stouffville line code (to verify)
TIMEZONE=America/Toronto

# --- Discord ---
ENABLE_DISCORD=true
DISCORD_TOKEN=...
DISCORD_APP_ID=...
DISCORD_GUILD_ID=...        # optional dev guild for instant command sync

# --- Slack ---
ENABLE_SLACK=true
SLACK_BOT_TOKEN=xoxb-...    # Bot User OAuth Token
SLACK_APP_TOKEN=xapp-...    # App-Level Token (for Socket Mode, starts with xapp-)
SLACK_SIGNING_SECRET=...    # only needed if you switch off Socket Mode later
```

Stop and line codes are placeholders — confirmed during step 3 by hitting the API's stops/lines endpoints.

## GO Transit / Metrolinx API

Reference: https://api.openmetrolinx.com (Metrolinx Open Data API). Auth via `?key=<GO_API_KEY>` query param.

Endpoints we'll likely use (confirmed in step 3):

- **Stops list** — look up exact codes for Markham GO and Union.
- **Lines list** — confirm Stouffville line code.
- **Next service / departures at stop** — primary endpoint for "next train from X".
- **Schedule for a trip / line** — fallback when real-time data is missing.
- **Service updates / alerts** — surface delays in the reply if any are active.

Each endpoint we use is wrapped as one async function in `go_api.py` returning small dataclasses (`Departure`, `TripStop`).

## Shared core

### `commute.next_trip(origin, destination, line) -> Trip`

```python
@dataclass
class Trip:
    departure_at: datetime      # tz-aware
    arrival_at: datetime        # tz-aware
    trip_id: str
    status: str                 # "on time" | "delayed 5 min" | "scheduled" | "cancelled"
    origin_name: str
    destination_name: str
```

Pure function — takes stop/line codes, returns a `Trip`. No Discord, no Slack, no I/O beyond the API call. Easy to unit test against captured sample JSON.

### `formatting.render(trip, flavor)` 

Returns a string for the given platform.

- `flavor="discord"` → standard markdown (`**Next to Union**`).
- `flavor="slack"` → `mrkdwn` (`*Next to Union*`).

Both produce the same content:

```
🚆 Next to Union
Departs Markham GO at 5:12 PM (in 14 min)
Arrives Union at 5:51 PM
Trip 1234 · on time
```

## Command behavior

### `/work`
1. Query upcoming southbound departures at `HOME_STATION` on `LINE`.
2. Filter to trips that stop at `WORK_STATION` (Union).
3. Pick the soonest departure ≥ now + a 2 min buffer (so we don't suggest a train you can't physically catch).
4. Compute arrival at Union from the trip's stop times.
5. Reply with the rendered string (ephemeral on Discord, default on Slack DMs).

### `/home`
Reversed: `WORK_STATION` → `HOME_STATION`.

### Edge cases
- No upcoming trains today → show next scheduled service tomorrow.
- API error / timeout → friendly fallback, log full error.
- Trip cancelled or delayed → show the delay and pick the next viable train.
- Trip has no real-time update → show scheduled time, labelled "scheduled".

## Discord setup

1. Create app at https://discord.com/developers/applications → add a **Bot** user, copy token.
2. Generate an install URL with scopes `bot` + `applications.commands`.
3. For DM-friendly slash commands without a shared server: enable **User Install** on the app and register commands with `dm_permission=True` and `integration_types=[USER_INSTALL]`.

## Slack setup

1. Create app at https://api.slack.com/apps → "From scratch" → name it, pick the Foratus workspace.
2. **OAuth & Permissions** → add Bot Token Scopes: `commands`, `chat:write`, `im:write`, `im:history`.
3. **Socket Mode** → enable; create an App-Level Token with `connections:write` scope (this is the `xapp-` token).
4. **Slash Commands** → create `/work` and `/home`. With Socket Mode you don't need a Request URL.
5. **Install to Workspace** — *this likely needs Foratus admin approval*. If it does, ask first; otherwise install and copy the Bot Token (`xoxb-`).
6. DM the bot in Slack to test.

> ⚠️ Foratus is a work Slack — even though the bot is for personal use, it'll be visible to admins. Worth a quick check that this is OK before installing.

## Implementation steps

1. **Scaffold** — `requirements.txt`, `.env.example`, `.gitignore`, empty `src/` modules. `python -m src.main` should start, log "ready" for whichever adapter(s) are enabled.
2. **Discord wiring** — `/work` and `/home` echo "ok" in DMs.
3. **GO API exploration** — `scripts/probe_go.py` hits stops, lines, next-service endpoints with the real key. Save sample JSON to `samples/`. Confirm real codes for Markham GO, Union, Stouffville.
4. **`go_api.py`** — implement only the endpoints we need. Typed dataclasses.
5. **`commute.py`** — `next_trip()` core logic. Pure, unit-tested against `samples/`.
6. **`formatting.py`** — `render(trip, flavor)` for both flavors.
7. **Wire Discord adapter** — `/work` and `/home` call `commute.next_trip` → `formatting.render(..., "discord")`.
8. **Slack adapter** — same, but with slack-bolt and `flavor="slack"`. Verify in Foratus DM (after admin sign-off if needed).
9. **Polish** — countdown formatting, timezone correctness, friendly errors, alerts surfaced.

Doing Discord first end-to-end (steps 2, 7) is intentional — gets the whole flow working on the easier platform before adding Slack's setup overhead.

## Testing

- Unit tests for `commute.next_trip` and `formatting.render` against captured sample JSON in `samples/` (no network).
- Manual end-to-end on each platform: DM at peak, off-peak, late evening to verify edge cases.

## Hosting (later)

Cheap always-on options:
- **Local + launchd** on your Mac (free, but laptop must be awake).
- **Fly.io** free-tier VM or **Railway** — ~$0–5/month, set-and-forget. Good fit since Socket Mode means no inbound HTTP needed.
- **Raspberry Pi** if one's lying around.

Both adapters in one process means one deployment.

## Open questions

- Confirm Metrolinx API base URL and endpoint shapes once you share the docs link (some endpoints differ between the legacy GO API and the newer Metrolinx Open Data API).
- Foratus Slack admin approval — needed? Worth checking before step 8.
- Push alerts for delays vs. pull-only? Plan is pull-only for now.
- Should `/work` and `/home` also show the train *after* the next one, in case you'd miss the first?
