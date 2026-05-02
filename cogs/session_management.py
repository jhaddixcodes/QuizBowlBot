# my name is retep and i am evil
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from main import QuizBowlBot

import asyncio

import discord
from discord.ext import commands
from discord import app_commands

from game_session import QuizBowlGameSession

class SessionManagement(commands.Cog):
    def __init__(self, bot: QuizBowlBot):
        self.bot = bot
        super().__init__()

    @app_commands.command(name="create_game", description="Create a game session.")
    async def create_game(self, interaction: discord.Interaction):
        if self.bot.session_exists(interaction.channel):
            await interaction.response.send_message("nice try buddy, there's a game here already", ephemeral=True)
            return

        packet = await self.bot.collect_random_packet(difficulties = ["3"], categories=["Literature", "Social Science", "Fine Arts", "Science"], subcategories=["Other Science"])
        self.bot.game_sessions[interaction.channel.id] = QuizBowlGameSession(interaction.user, packet, self.bot, interaction.channel)
        await interaction.response.send_message("ok made your game session :)")


    @app_commands.command(name="end_game", description="End a game session.")
    async def end_game(self, interaction: discord.Interaction):
        if not self.bot.session_exists(interaction.channel):
            await interaction.response.send_message("no such game", ephemeral=True)
            return

        session = self.bot.get_session(interaction.channel)
        if session.current_task:
            session.current_task.cancel()
            try:
                await session.current_task
            except asyncio.CancelledError:
                pass

        del self.bot.game_sessions[interaction.channel.id]
        await interaction.response.send_message("ok then")

    @app_commands.command(name="join_game", description="Join the specified team in the current game session.")
    async def join_game(self, interaction: discord.Interaction, team: int):
        if not self.bot.session_exists(interaction.channel):
            await interaction.response.send_message("what game???", ephemeral=True)
            return
        await self.bot.get_session(interaction.channel).join_team(interaction, team)

    @app_commands.command(name="leave_game", description="Leave the game.")
    async def leave_game(self, interaction: discord.Interaction):
        if not self.bot.session_exists(interaction.channel):
            await interaction.response.send_message("what game???", ephemeral=True)
            return
        await self.bot.get_session(interaction.channel).leave_team(interaction)