import discord
from discord.ext import commands
from discord import app_commands
from datetime import timedelta

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ================= KICK =================
    @app_commands.command(name="kick", description="Kick a member")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str | None = None
    ):
        await member.kick(reason=reason)
        await interaction.response.send_message(
            f"✅ {member.mention} has been kicked.",
            ephemeral=True
        )

    # ================= BAN =================
    @app_commands.command(name="ban", description="Ban a member")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str | None = None
    ):
        await member.ban(reason=reason)
        await interaction.response.send_message(
            f"🔨 {member.mention} has been banned.",
            ephemeral=True
        )

    # ================= TIMEOUT =================
    @app_commands.command(name="timeout", description="Timeout a member (minutes)")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        minutes: int,
        reason: str | None = None
    ):
        until = discord.utils.utcnow() + timedelta(minutes=minutes)
        await member.timeout(until, reason=reason)

        await interaction.response.send_message(
            f"⏳ {member.mention} timed out for {minutes} minutes.",
            ephemeral=True
        )

    # ================= PURGE =================
    @app_commands.command(name="purge", description="Delete messages in this channel")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def purge(
        self,
        interaction: discord.Interaction,
        amount: int
    ):
        if amount < 1 or amount > 100:
            return await interaction.response.send_message(
                "❌ Amount must be between 1 and 100",
                ephemeral=True
            )

        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=amount)

        await interaction.followup.send(
            f"🧹 Deleted {len(deleted)} messages.",
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(Moderation(bot))
