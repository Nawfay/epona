from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

from src import commute, formatting
from src.commute import NoTrainsError
from src.config import SLACK_BOT_TOKEN, SLACK_APP_TOKEN

app = AsyncApp(token=SLACK_BOT_TOKEN)


@app.command("/work")
async def work_command(ack, respond):
    await ack()
    try:
        trip = await commute.next_to_work()
        reply = formatting.render(trip, flavor="slack")
    except NoTrainsError as e:
        reply = str(e)
    except Exception as e:
        print(f"Slack /work error: {e}")
        reply = "Could not reach GO Transit API. Try again in a moment."
    await respond(reply)


@app.command("/home")
async def home_command(ack, respond):
    await ack()
    try:
        trip = await commute.next_to_home()
        reply = formatting.render(trip, flavor="slack")
    except NoTrainsError as e:
        reply = str(e)
    except Exception as e:
        print(f"Slack /home error: {e}")
        reply = "Could not reach GO Transit API. Try again in a moment."
    await respond(reply)


@app.command("/gohelp")
async def help_command(ack, respond):
    await ack()
    reply = (
        "*GO Train Bot*\n"
        "\n"
        "*/work* — next Stouffville line train from Markham GO → Union Station\n"
        "*/home* — next Stouffville line train from Union Station → Markham GO\n"
        "*/gohelp* — this message\n"
        "\n"
        "*Reading the output:*\n"
        "```\n"
        "🚆 Next to Union Station\n"
        "Departs Markham GO at 5:12 PM (in 14 min)\n"
        "Arrives Union Station at 5:51 PM\n"
        "Trip 7421 · on time\n"
        "```\n"
        "*Departs* — when the train leaves your origin stop\n"
        "*in X min* — countdown from right now\n"
        "*Arrives* — estimated arrival at your destination\n"
        "*Trip XXXX* — GO train number\n"
        "*Status* — `on time` · `delayed N min` · `early N min` · `scheduled` (no real-time data yet)"
    )
    await respond(reply)


async def run():
    handler = AsyncSocketModeHandler(app, SLACK_APP_TOKEN)
    await handler.start_async()
