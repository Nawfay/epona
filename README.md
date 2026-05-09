# Epona

A personal Discord and Slack bot that tells you the next GO train on the Stouffville line between Markham GO and Union Station.

Named after Link's horse in The Legend of Zelda 

## Commands

- `/work` — next train from Markham GO to Union Station
- `/home` — next train from Union Station to Markham GO
- `/help` (Discord) / `/gohelp` (Slack) — explains the output

## Setup

1. Copy `.env.example` to `.env` and fill in your tokens
2. Install dependencies and run:

```bash
uv run python -m src.main
```

To run Discord only while Slack is not yet configured:

```bash
ENABLE_SLACK=false uv run python -m src.main
```

## Requirements

- GO Transit API key from Metrolinx Open Data
- Discord bot token (discord.com/developers)
- Slack bot + app-level tokens (api.slack.com/apps) — optional
