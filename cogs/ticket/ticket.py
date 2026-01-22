import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone
import asyncio

class Ticket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ticket_category = {}
        self.open_users = {}

    @app_commands.command(name="ticket", description="Send ticket panel")
    @app_commands.describe(category="Ticket category")
    async def ticket(self, interaction: discord.Interaction, category: discord.CategoryChannel):

        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("Admin only", ephemeral=True)

        self.ticket_category[interaction.guild.id] = category.id

        embed = discord.Embed(
            title="🎫 Support Ticket",
            description="Click button to open ticket",
            color=discord.Color.blurple()
        )

        await interaction.channel.send(embed=embed, view=TicketPanel(self))
        await interaction.response.send_message("✅ Ticket panel sent", ephemeral=True)

class TicketPanel(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(label="Open Ticket", emoji="🎫", style=discord.ButtonStyle.green)
    async def open(self, interaction: discord.Interaction, _):

        guild = interaction.guild
        user = interaction.user

        if user.id in self.cog.open_users.setdefault(guild.id, set()):
            return await interaction.response.send_message("You already have a ticket", ephemeral=True)

        await interaction.response.send_modal(TicketModal(self.cog, guild, user))

class TicketModal(discord.ui.Modal, title="📝 Ticket Form"):

    issue = discord.ui.TextInput(label="Issue", required=True)
    detail = discord.ui.TextInput(label="Details", style=discord.TextStyle.paragraph)

    def __init__(self, cog, guild, user):
        super().__init__()
        self.cog = cog
        self.guild = guild
        self.user = user

    async def on_submit(self, interaction: discord.Interaction):
        cat = self.guild.get_channel(self.cog.ticket_category[self.guild.id])
        channel = await cat.create_text_channel(f"ticket-{self.user.id}")

        await channel.set_permissions(self.user, read_messages=True, send_messages=True)
        await channel.send(
            embed=discord.Embed(
                title="Ticket Opened",
                description=f"{self.issue.value}\n\n{self.detail.value}",
                color=discord.Color.green()
            )
        )

        self.cog.open_users[self.guild.id].add(self.user.id)
        await interaction.response.send_message(f"Ticket created: {channel.mention}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Ticket(bot))
