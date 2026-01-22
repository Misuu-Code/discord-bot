import discord
from discord.ext import commands
from discord import app_commands

class Welcome(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.welcome_channel = {}
        self.goodbye_channel = {}
        self.dm_welcome = {}

    # ================= SETUP =================
    @app_commands.command(name="welcome", description="Setup welcome / goodbye system")
    @app_commands.choices(action=[
        app_commands.Choice(name="Set Welcome Channel", value="welcome"),
        app_commands.Choice(name="Set Goodbye Channel", value="goodbye"),
        app_commands.Choice(name="Toggle DM Welcome", value="dm"),
        app_commands.Choice(name="Reset", value="reset")
    ])
    async def welcome(
        self,
        interaction: discord.Interaction,
        action: app_commands.Choice[str],
        channel: discord.TextChannel | None = None
    ):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(
                "❌ Admin only",
                ephemeral=True
            )

        gid = interaction.guild.id

        # ===== SET WELCOME =====
        if action.value == "welcome":
            if not channel:
                return await interaction.response.send_message(
                    "❌ Please provide a channel.",
                    ephemeral=True
                )
            self.welcome_channel[gid] = channel.id
            await interaction.response.send_message(
                f"✅ Welcome channel set to {channel.mention}",
                ephemeral=True
            )

        # ===== SET GOODBYE =====
        elif action.value == "goodbye":
            if not channel:
                return await interaction.response.send_message(
                    "❌ Please provide a channel.",
                    ephemeral=True
                )
            self.goodbye_channel[gid] = channel.id
            await interaction.response.send_message(
                f"✅ Goodbye channel set to {channel.mention}",
                ephemeral=True
            )

        # ===== DM WELCOME =====
        elif action.value == "dm":
            current = self.dm_welcome.get(gid, False)
            self.dm_welcome[gid] = not current
            await interaction.response.send_message(
                f"📩 DM Welcome: **{'ON' if not current else 'OFF'}**",
                ephemeral=True
            )

        # ===== RESET =====
        elif action.value == "reset":
            self.welcome_channel.pop(gid, None)
            self.goodbye_channel.pop(gid, None)
            self.dm_welcome.pop(gid, None)
            await interaction.response.send_message(
                "♻️ Welcome & Goodbye reset.",
                ephemeral=True
            )

    # ================= MEMBER JOIN =================
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        gid = member.guild.id

        # CHANNEL WELCOME
        if gid in self.welcome_channel:
            channel = member.guild.get_channel(self.welcome_channel[gid])
            if channel:
                embed = discord.Embed(
                    title="👋 Welcome!",
                    description=(
                        f"Welcome {member.mention} to **{member.guild.name}**!\n"
                        f"Member count: **{member.guild.member_count}**"
                    ),
                    color=discord.Color.green()
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                await channel.send(embed=embed)

        # DM WELCOME
        if self.dm_welcome.get(gid):
            try:
                await member.send(
                    f"👋 Welcome to **{member.guild.name}**!\n"
                    "Enjoy your stay 💙"
                )
            except discord.Forbidden:
                pass

    # ================= MEMBER LEAVE =================
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        gid = member.guild.id

        if gid in self.goodbye_channel:
            channel = member.guild.get_channel(self.goodbye_channel[gid])
            if channel:
                embed = discord.Embed(
                    title="👋 Goodbye!",
                    description=(
                        f"**{member}** has left the server.\n"
                        f"Members now: **{member.guild.member_count}**"
                    ),
                    color=discord.Color.red()
                )
                await channel.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Welcome(bot))
