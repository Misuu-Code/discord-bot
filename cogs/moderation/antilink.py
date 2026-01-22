import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone, timedelta
import re

# ================= STORAGE =================
ANTILINK_CFG = {}
WARN_COUNT = {}

# ================= UTILS =================
def get_cfg(guild_id: int):
    if guild_id not in ANTILINK_CFG:
        ANTILINK_CFG[guild_id] = {
            "enabled": False,
            "channels": [],
            "anti_image": False,
            "blacklist": ["http://", "https://", "www."],
            "punishment": {
                "type": "timeout",   # warn | timeout | kick | ban
                "timeout": 10,
                "max_warn": 3
            }
        }
    return ANTILINK_CFG[guild_id]

def is_admin(member: discord.Member):
    return member.guild_permissions.administrator or member.guild_permissions.manage_messages

# ================= COG =================
class AntiLink(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ================= COMMAND =================
    @app_commands.command(name="antilink", description="AntiLink control panel")
    async def antilink_panel(self, interaction: discord.Interaction):
        if not is_admin(interaction.user):
            return await interaction.response.send_message(
                "❌ Admin only", ephemeral=True
            )

        cfg = get_cfg(interaction.guild.id)

        color = discord.Color.green() if cfg["enabled"] else discord.Color.red()
        status = "🟢 ENABLED" if cfg["enabled"] else "🔴 DISABLED"

        embed = discord.Embed(
            title="🛡️ AntiLink Control Panel",
            description=status,
            color=color
        )

        embed.add_field(
            name="Channels",
            value=", ".join(f"<#{c}>" for c in cfg["channels"]) if cfg["channels"] else "Not set",
            inline=False
        )

        embed.add_field(
            name="Punishment",
            value=f"{cfg['punishment']['type'].upper()}",
            inline=True
        )

        embed.add_field(
            name="Max Warn",
            value=str(cfg["punishment"]["max_warn"]),
            inline=True
        )

        embed.add_field(
            name="Anti Image",
            value="Enabled" if cfg["anti_image"] else "Disabled",
            inline=True
        )

        await interaction.response.send_message(
            embed=embed,
            view=AntiLinkMainPanel(self),
            ephemeral=True
        )

    # ================= MESSAGE LISTENER =================
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return

        cfg = get_cfg(message.guild.id)

        if not cfg["enabled"]:
            return

        if message.channel.id not in cfg["channels"]:
            return

        if is_admin(message.author):
            return

        violated = False

        # LINK CHECK
        for bad in cfg["blacklist"]:
            if bad in message.content.lower():
                violated = True
                break

        # IMAGE CHECK
        if cfg["anti_image"] and message.attachments:
            violated = True

        if not violated:
            return

        try:
            await message.delete()
        except:
            pass

        await self.apply_punishment(message.author, message.channel)

    # ================= PUNISH =================
    async def apply_punishment(self, member: discord.Member, channel: discord.TextChannel):
        cfg = get_cfg(member.guild.id)
        gid = member.guild.id
        uid = member.id

        WARN_COUNT.setdefault(gid, {})
        WARN_COUNT[gid].setdefault(uid, 0)

        ptype = cfg["punishment"]["type"]

        if ptype == "timeout":
            minutes = cfg["punishment"]["timeout"]
            until = datetime.now(timezone.utc) + timedelta(minutes=minutes)
            await member.timeout(until)
            await channel.send(
                f"⏱️ {member.mention} timed out for **{minutes} minutes**"
            )

        elif ptype == "kick":
            await channel.send(f"👢 {member.mention} kicked.")
            await member.kick(reason="AntiLink")

        elif ptype == "ban":
            await channel.send(f"⛔ {member.mention} banned.")
            await member.ban(reason="AntiLink")

# ================= MAIN PANEL =================
class AntiLinkMainPanel(discord.ui.View):
    def __init__(self, cog: AntiLink):
        super().__init__(timeout=900)
        self.cog = cog

    @discord.ui.button(label="Enable / Disable", style=discord.ButtonStyle.success)
    async def toggle(self, interaction: discord.Interaction, _):
        cfg = get_cfg(interaction.guild.id)
        cfg["enabled"] = not cfg["enabled"]
        await interaction.response.send_message(
            f"✅ AntiLink {'enabled' if cfg['enabled'] else 'disabled'}",
            ephemeral=True
        )

    @discord.ui.button(label="Set Channels", style=discord.ButtonStyle.primary)
    async def channels(self, interaction: discord.Interaction, _):
        options = [
            discord.SelectOption(label=ch.name, value=str(ch.id))
            for ch in interaction.guild.text_channels[:25]
        ]

        await interaction.response.send_message(
            "📌 Select channels:",
            view=ChannelSelectView(options),
            ephemeral=True
        )

    @discord.ui.button(label="Set Punishment", style=discord.ButtonStyle.secondary)
    async def punish(self, interaction: discord.Interaction, _):
        await interaction.response.send_message(
            "⚠️ Select punishment:",
            view=PunishmentSelectView(),
            ephemeral=True
        )

    @discord.ui.button(label="Toggle Anti Image", style=discord.ButtonStyle.danger)
    async def antiimg(self, interaction: discord.Interaction, _):
        cfg = get_cfg(interaction.guild.id)
        cfg["anti_image"] = not cfg["anti_image"]
        await interaction.response.send_message(
            f"🖼️ Anti Image {'enabled' if cfg['anti_image'] else 'disabled'}",
            ephemeral=True
        )

# ================= CHANNEL SELECT =================
class ChannelSelectView(discord.ui.View):
    def __init__(self, options):
        super().__init__(timeout=120)
        self.add_item(ChannelSelect(options))

class ChannelSelect(discord.ui.Select):
    def __init__(self, options):
        super().__init__(
            placeholder="Select channels",
            options=options,
            min_values=1,
            max_values=len(options)
        )

    async def callback(self, interaction: discord.Interaction):
        cfg = get_cfg(interaction.guild.id)
        cfg["channels"] = [int(v) for v in self.values]
        await interaction.response.send_message(
            "✅ Channels updated",
            ephemeral=True
        )

# ================= PUNISHMENT =================
class PunishmentSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)
        self.add_item(PunishmentSelect())

class PunishmentSelect(discord.ui.Select):
    def __init__(self):
        super().__init__(
            placeholder="Select punishment",
            options=[
                discord.SelectOption(label="Timeout", value="timeout"),
                discord.SelectOption(label="Kick", value="kick"),
                discord.SelectOption(label="Ban", value="ban")
            ]
        )

    async def callback(self, interaction: discord.Interaction):
        cfg = get_cfg(interaction.guild.id)
        p = self.values[0]
        cfg["punishment"]["type"] = p

        if p == "timeout":
            await interaction.response.send_modal(TimeoutModal())
            return

        await interaction.response.send_message(
            f"✅ Punishment set to {p.upper()}",
            ephemeral=True
        )

# ================= TIMEOUT MODAL =================
class TimeoutModal(discord.ui.Modal, title="⏱️ Timeout Duration"):
    minutes = discord.ui.TextInput(
        label="Minutes",
        placeholder="Example: 10",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        cfg = get_cfg(interaction.guild.id)

        try:
            minutes = int(self.minutes.value)
            if minutes <= 0:
                raise ValueError
        except:
            return await interaction.response.send_message(
                "❌ Invalid number",
                ephemeral=True
            )

        cfg["punishment"]["timeout"] = minutes
        await interaction.response.send_message(
            f"✅ Timeout set to {minutes} minutes",
            ephemeral=True
        )

# ================= SETUP =================
async def setup(bot: commands.Bot):
    await bot.add_cog(AntiLink(bot))
