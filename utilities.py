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

def strings_approximately_match(search, set_name):
    # the list comprehension means if some moron hits space four times, nothing insane happens
    search_tokens = search.split()

    for search_token in search_tokens:
        if search_token not in set_name: # we want all the words in the search to be found at some point in the set name
            # if a token wasn't found, well, maybe they misspelled it.
            try:
                _ = int(search_token) # first we'll make sure the token isn't a year because we don't want to match 2025 and 2024.
            except ValueError:
                pass # an error, so the token isn't a number and can't be a year
            else:
                # if there's a non-year number in the string, we're fucked, but i figure that's not a big problem
                return False

            # now let's see if maybe one of the words in the set name approximately match
            set_tokens = set_name.split()
            match = False
            for set_token in set_tokens:
                if levenshtein_distance(search_token, set_token) < 3:
                    match = True
                    break
            if match:
                continue # great, let's check the other tokens
            print(f"no match found for '{search_token}'")
            return False # no match, the token can't be found so user probably searched some bullshit like "some bullshit"
    # yippee!
    return True