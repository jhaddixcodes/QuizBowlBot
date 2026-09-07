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


def html_to_markdown(text: str):
    return (text
            .replace("<b>", "**")
            .replace("</b>", "**")
            .replace("<i>", "*")
            .replace("</i>", "*")
            .replace("<em>", "*")
            .replace("</em>", "*")
            .replace("<u>", "__")
            .replace("</u>", "__")
            )

def levenshtein_distance(a: str, b: str):
    """
    python is an incredible language because for anything you can think of, you can import a module to do it for you.
    anyway disregard that here's an algorithm calculating levenshtein distance so i can do fuzzy search
    """
    # first we create a table that represents our subproblems. i don't have enough space google it
    table = [[-1] * (len(b) + 1) for _ in range(len(a) + 1)]

    # next we fill in our base cases (i.e. transforming from empty string to string B or string A to empty string)
    # empty string to string B
    table[0] = [i for i in range(len(b) + 1)]
    # string A to empty string
    for row in range(len(a) + 1):
        table[row][0] = row

    # next we can go through "recursively" (not exactly but whatever) and figure out the minimum steps for each subproblem
    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            # we don't do anything if characters already match
            if a[i - 1] == b[j - 1]:
                table[i][j] = table[i - 1][j - 1]
            else:
                table[i][j] = min(table[i - 1][j - 1], table[i - 1][j], table[i][j - 1]) + 1

    return table[len(a)][len(b)]
