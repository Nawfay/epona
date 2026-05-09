import os
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

load_dotenv()

GO_API_KEY: str = os.environ["GO_API_KEY"]
HOME_STATION: str = os.getenv("HOME_STATION", "MR")
WORK_STATION: str = os.getenv("WORK_STATION", "UN")
LINE: str = os.getenv("LINE", "ST")
TIMEZONE = ZoneInfo(os.getenv("TIMEZONE", "America/Toronto"))
MIN_DEPARTURE_BUFFER_MINUTES: int = int(os.getenv("MIN_DEPARTURE_BUFFER_MINUTES", "2"))

DISCORD_TOKEN: str | None = os.getenv("DISCORD_TOKEN")
DISCORD_APP_ID: str | None = os.getenv("DISCORD_APP_ID")
DISCORD_GUILD_ID: str | None = os.getenv("DISCORD_GUILD_ID")

SLACK_BOT_TOKEN: str | None = os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN: str | None = os.getenv("SLACK_APP_TOKEN")

ENABLE_DISCORD: bool = os.getenv("ENABLE_DISCORD", "true").lower() == "true"
ENABLE_SLACK: bool = os.getenv("ENABLE_SLACK", "true").lower() == "true"
