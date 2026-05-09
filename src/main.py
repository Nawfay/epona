import asyncio
from src.config import ENABLE_DISCORD, ENABLE_SLACK, DISCORD_TOKEN, SLACK_BOT_TOKEN, SLACK_APP_TOKEN


async def main():
    tasks = []

    if ENABLE_DISCORD:
        if not DISCORD_TOKEN:
            print("Warning: ENABLE_DISCORD=true but DISCORD_TOKEN is not set — skipping")
        else:
            from src.adapters.discord_bot import run as discord_run
            print("Starting Discord adapter...")
            tasks.append(asyncio.create_task(discord_run()))

    if ENABLE_SLACK:
        if not SLACK_BOT_TOKEN or not SLACK_APP_TOKEN:
            print("Warning: ENABLE_SLACK=true but SLACK_BOT_TOKEN or SLACK_APP_TOKEN is not set — skipping")
        else:
            from src.adapters.slack_bot import run as slack_run
            print("Starting Slack adapter...")
            tasks.append(asyncio.create_task(slack_run()))

    if not tasks:
        print("No adapters enabled. Set ENABLE_DISCORD=true or ENABLE_SLACK=true in .env")
        return

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
