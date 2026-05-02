import discord
import qbreader.types as types
from enum import StrEnum, IntEnum


class GameState(StrEnum):
    IDLE = "idle"
    PAUSED = "paused"
    READ_TU = "reading tossup"
    WAIT_ANS_MID_TU = "waiting answer mid-tossup"
    WAIT_ANS_END_TU = "waiting answer end of tossup"
    WAIT_BUZZ_END_TU = "waiting buzz end of tossup"
    READ_BONUS = "reading bonus"
    WAIT_ANS_BONUS = "waiting answer bonus"
    BETWEEN_CYCLES = "between cycles"


class BonusState(IntEnum):
    PART_1 = 1
    PART_2 = 2
    PART_3 = 3


class CustomPacket:
    """
    A packet. Can be a packet of random tossups and bonuses or a specific packet.
    """
    def __init__(self, tossups: tuple[types.Tossup, ...], bonuses: tuple[types.Bonus, ...]):
        self.tossups = tossups # crazy
        self.bonuses = bonuses # double crazy


class Team:
    """
    Team that can be joined and left by Discord users.
    """
    def __init__(self):
        self.users: list[discord.User] = [] # can buzz in and direct bonus answers
        self.points = 0
        self.buzzed = False # whether the team has buzzed on the current tossup.

    def add_player(self, user: discord.User):
        self.users.append(user)

    def remove_player(self, user: discord.User):
        self.users.remove(user)