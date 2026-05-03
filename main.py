# for asynchronous stuff
import asyncio

# discord py
import discord
from discord.ext import commands

import logging

from cogs.session_management import SessionManagement
from cogs.game_flow import GameFlow
from cogs.miscellaneous import Miscellaneous

# for env variables
from dotenv import load_dotenv
from os import getenv

# qbreader api
from qbreader.asynchronous import Async as QBReaderAsync

from game_objects import GameState
from game_session import CustomPacket, QuizBowlGameSession

class QuizBowlBot(commands.Bot):

    def __init__(self, qbreader_client: QBReaderAsync):
        intents = discord.Intents.default() # some bullshit i don't know
        intents.message_content = True
        intents.presences = False
        intents.typing = False

        super().__init__(command_prefix=";", intents=intents)

        self.qbreader_client = qbreader_client # where the packets come from. i know nothing more
        self.game_sessions: dict[int, QuizBowlGameSession] = {} # dictionary mapping channel IDs to active game sessions

    @classmethod
    async def create(cls):
        qbreader_client = await QBReaderAsync.create()
        return cls(qbreader_client)

    def session_exists(self, channel: discord.TextChannel):
        return channel.id in self.game_sessions

    def get_session(self, channel: discord.TextChannel):
        return self.game_sessions[channel.id]

    async def collect_random_packet(self, difficulties=None, categories=None, subcategories=None):
        """
        :return: Packet with 20 tossups and 20 bonuses based on the given filters
        """
        tossups = await self.qbreader_client.random_tossup(difficulties=difficulties, categories=categories, subcategories=subcategories, number=20)
        bonuses = await self.qbreader_client.random_bonus(difficulties=difficulties, categories=categories, subcategories=subcategories, number=20, three_part_bonuses=True)

        return CustomPacket(tossups, bonuses)

    async def collect_specific_packet(self, set_name, packet_number):
        """
        Get a specific packet from set name and packet number
        :param set_name: The name of the set. Must be exact.
        :param packet_number: Number of the packet within the set. Must be a valid number (1-n where n is number of packets in set)
        :return: Packet containing all tossups and bonuses in the set.
        """
        packet = await self.qbreader_client.packet(set_name, packet_number)
        return CustomPacket(packet.tossups, packet.bonuses)


    async def setup_hook(self):

        await self.add_cog(SessionManagement(self))
        await self.add_cog(GameFlow(self))
        await self.add_cog(Miscellaneous(self))

        synced = await self.tree.sync()
        print(f"Synced {len(synced)} commands:")
        for command in synced:
            print(f"{command.name}")

    async def on_ready(self):
        print(f"{self.user} is online!")

    async def on_message(self, message: discord.Message):
        if self.session_exists(message.channel):
            session = self.get_session(message.channel)

            # on_message handles spontaneous directs and buzzes, not when the bot is actively waiting for them
            if session.is_valid_buzz(message) and session.game_state == GameState.READ_TU:
                await session.buzz(message)

            elif session.is_valid_direct(message):
                if session.game_state == GameState.READ_BONUS:
                    await session.evaluate_bonus_answer(message)

            elif session.is_valid_score_check(message):
                await session.score_check(message)

    async def end(self):
        await self.qbreader_client.close()
        await self.close()


async def main():
    # load environment variables
    load_dotenv(".env")
    token = getenv("DISCORD_TOKEN")

    # set up discord client
    discord_client = None

    logger = logging.getLogger('discord')
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
    handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
    logger.addHandler(handler)

    try:
        discord_client = await QuizBowlBot.create()
        await discord_client.start(token)
    finally:
        if discord_client is not None:
            await discord_client.end()

asyncio.run(main())