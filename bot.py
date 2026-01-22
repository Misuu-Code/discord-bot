import discord
from discord.ext import commands
from core.config import TOKEN, MODE

intents = discord.Intents.default()
intents.guilds = True
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

INITIAL_EXTENSIONS = [
    "cogs.ticket.ticket",
    "cogs.moderation.moderation",
    "cogs.moderation.antilink",
    "cogs.welcome.welcome"
]

@bot.event
async def on_ready():
    print(f"🔌 Logged in as {bot.user}")
    print(f"⚙️ MODE = {MODE}")

@bot.event
async def setup_hook():
    for ext in INITIAL_EXTENSIONS:
        await bot.load_extension(ext)

    if MODE == "dev":
        for guild in bot.guilds:
            bot.tree.copy_global_to(guild=discord.Object(id=guild.id))
            await bot.tree.sync(guild=discord.Object(id=guild.id))
        print("⚡ DEV MODE: guild commands synced")

    else:
        await bot.tree.sync()
        print("🌍 PROD MODE: global commands synced")

bot.setup_hook = setup_hook
bot.run(TOKEN)