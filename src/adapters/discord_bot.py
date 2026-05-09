import discord
from discord import app_commands

from src import commute, formatting
from src.commute import NoTrainsError
from src.config import DISCORD_TOKEN, DISCORD_GUILD_ID


class CommuteClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        if DISCORD_GUILD_ID:
            guild = discord.Object(id=int(DISCORD_GUILD_ID))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()

    async def on_ready(self):
        print(f"Discord: logged in as {self.user}")


client = CommuteClient()


@client.tree.command(name="work", description="Next GO train from Markham GO to Union Station")
async def work_command(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    try:
        trip = await commute.next_to_work()
        reply = formatting.render(trip, flavor="discord")
    except NoTrainsError as e:
        reply = str(e)
    except Exception as e:
        print(f"Discord /work error: {e}")
        reply = "Could not reach GO Transit API. Try again in a moment."
    await interaction.followup.send(reply, ephemeral=True)


@client.tree.command(name="home", description="Next GO train from Union Station to Markham GO")
async def home_command(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    try:
        trip = await commute.next_to_home()
        reply = formatting.render(trip, flavor="discord")
    except NoTrainsError as e:
        reply = str(e)
    except Exception as e:
        print(f"Discord /home error: {e}")
        reply = "Could not reach GO Transit API. Try again in a moment."
    await interaction.followup.send(reply, ephemeral=True)


@client.tree.command(name="help", description="How to use this bot and what the output means")
async def help_command(interaction: discord.Interaction):
    reply = (
        "**GO Train Bot**\n"
        "\n"
        "**/work** — next Stouffville line train from Markham GO → Union Station\n"
        "**/home** — next Stouffville line train from Union Station → Markham GO\n"
        "**/help** — this message\n"
        "\n"
        "**Reading the output:**\n"
        "> 🚆 **Next to Union Station**\n"
        "> Departs Markham GO at 5:12 PM (in 14 min)\n"
        "> Arrives Union Station at 5:51 PM\n"
        "> Trip 7421 · on time\n"
        "\n"
        "**Departs** — when the train leaves your origin stop\n"
        "**in X min** — countdown from right now\n"
        "**Arrives** — estimated arrival at your destination\n"
        "**Trip XXXX** — GO train number\n"
        "**Status** — `on time` · `delayed N min` · `early N min` · `scheduled` (no real-time data yet)"
    )
    await interaction.response.send_message(reply, ephemeral=True)


async def run():
    await client.start(DISCORD_TOKEN)
