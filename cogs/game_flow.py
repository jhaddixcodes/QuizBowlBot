# retep, evil, etc.
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from main import QuizBowlBot

import discord
from discord.ext import commands
from discord import app_commands


class GameFlow(commands.Cog):
    def __init__(self, bot: QuizBowlBot):
        self.bot = bot
        super().__init__()

    @app_commands.command(name="start_game", description="Start the game with the first TU. Can only be called by session owner.")
    async def start_game(self, interaction: discord.Interaction):
        if not self.bot.session_exists(interaction.channel):
            await interaction.response.send_message("what game?", ephemeral=True)
            return

        await self.bot.get_session(interaction.channel).start_game(interaction)

    @app_commands.command(name="next_cycle", description="Go to the next TU/bonus cycle. Can only be called by player in game or owner.")
    async def next_cycle(self, interaction: discord.Interaction):
        if not self.bot.session_exists(interaction.channel):
            await interaction.response.send_message("try starting a game first brochacho", ephemeral=True)
            return

        await interaction.response.send_message("starting next cycle", ephemeral=True)
        await self.bot.get_session(interaction.channel).next_cycle(interaction)