# retep, evil, etc.
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from main import QuizBowlBot

import discord
from discord.ext import commands
from discord import app_commands

class Miscellaneous(commands.Cog):
    def __init__(self, bot: QuizBowlBot):
        self.bot = bot
        super().__init__()

    @app_commands.command(name="help", description="Send message explaining how to use the bot.")
    async def help(self, interaction: discord.Interaction):
        await interaction.response.send_message(
"""r
```
* Use /create_game to create a new game session.
* Use /end_game to delete a game session.
* Use /start_game to start the game.
* Use /next_cycle to go to the next tossup/bonus cycle.
* Use /join_game \[team_number] to join a game.
* Use /leave_game to leave a game.
* During a tossup, buzz by entering either 'buzz' or 'b' in the chat.
* During a bonus, direct an answer by entering either 'direct', 'answer', 'd', or 'a' followed by your answer in the chat.
* To get a score check at any time, type 'score check' or 'sc'. There will also be a final score at the end of the packet.
```
"""
        )