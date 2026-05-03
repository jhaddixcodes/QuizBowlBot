from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from main import QuizBowlBot

import asyncio
from asyncio import Task

from qbreader.types import Directive

import discord
from game_objects import GameState, BonusState, CustomPacket, Team


class QuizBowlGameSession:
    """
    da meat
    """
    def __init__(self, owner: discord.User, packet: CustomPacket, bot: QuizBowlBot, channel: discord.TextChannel):
        self.owner: discord.User = owner # the "owner" of the session can start and end it

        self.last_state: GameState | None = None # for keeping track of game state while paused
        self.game_state: GameState = GameState.IDLE
        self.cycle_number: int = 1 # the cycle the game is on (e.g. TU and bonus 1)
        self.bonus_state: BonusState = BonusState.PART_1
        self.bonus_owner: Team | None = None # which team owns the bonus

        self.packet: CustomPacket = packet
        self.teams: list[Team] = [Team(), Team()]

        # the bot (so we can wait for responses)
        # chat is this cursed
        self.bot: QuizBowlBot = bot

        # the channel the session is in (so it's not just getting passed around arbitrarily)
        self.channel = channel

        # the message the session wants the bot to edit
        self.current_message: discord.Message | None = None

        self.current_task: Task[None] | None = None

        # current index of what the bot is reading (in case of interrupt)
        self.current_index: int = 0
        self.power_mark_index: int | None = None # index of power mark


    def get_team_from_user(self, user: discord.User):
        for team in self.teams:
            if user in team.users:
                return team
        return None

    async def join_team(self, interaction: discord.Interaction, team: int):
        # make sure user isn't already on a team
        user = interaction.user

        if self.get_team_from_user(user):
            await interaction.response.send_message("the real team was the team you were already on...", ephemeral=True)
            return

        if team < 1 or team > len(self.teams):
            await interaction.response.send_message("this is not the team you are looking for", ephemeral=True)
            return

        self.teams[team - 1].add_player(user)
        await interaction.response.send_message(f"added {user.display_name} to team {team}.")

    async def leave_team(self, interaction: discord.Interaction):
        user = interaction.user

        team = self.get_team_from_user(user)
        if not team:
            await interaction.response.send_message("bro is not on a team", ephemeral=True)
            return

        team.remove_player(user)
        await interaction.response.send_message(f"removed {user.display_name} from team.")

    async def start_game(self, interaction: discord.Interaction):
        if self.game_state != GameState.IDLE:
            await interaction.response.send_message("LOOK WITH YOUR EYES, GAME STARTED ALREADY", ephemeral=True)
            return

        if interaction.user != self.owner:
            await interaction.response.send_message("bro thinks they're the owner", ephemeral=True)
            return

        await interaction.response.send_message("starting game!!!")
        await self.next_cycle(interaction)


    async def next_cycle(self, interaction: discord.Interaction):

        if not self.game_state in (GameState.IDLE, GameState.BETWEEN_CYCLES):
            await interaction.response.send_message("no skipping cycles!", ephemeral=True)
            return

        if not self.get_team_from_user(interaction.user) and not interaction.user == self.owner:
            await interaction.response.send_message("who are you???", ephemeral=True)
            return

        self.game_state = GameState.READ_TU

        self.current_task = asyncio.create_task(self.read_tossup())

    def get_power_mark_index(self, chunks: list[str]) -> int | None:
        for index, chunk in enumerate(chunks):
            if "(*)" in chunk:
                return index

        return None

    async def read_tossup(self):

        # if there's not a current message, we're on a new tossup
        if not self.current_message:
            self.current_message = await self.channel.send(content=f"Tossup {self.cycle_number}")
            self.current_index = 0

        # split tossup into individual words
        current_tossup = f"{self.cycle_number}. " + self.packet.tossups[self.cycle_number - 1].question_sanitized
        words = current_tossup.split(" ")

        # next join groups of 4 words (4 words per second)
        # no error because splicing out of index just returns nothing
        tossup_chunks = [" ".join(words[i:i + 4]) for i in range(0, len(words), 4)]

        # update power mark if it's None
        # (questions that aren't power marked will have this happen every time they're reread but that's not too bad i don't think)
        if not self.power_mark_index:
            self.power_mark_index = self.get_power_mark_index(tossup_chunks)

        # remove any power marks
        for index, chunk in enumerate(tossup_chunks):
            tossup_chunks[index] = chunk.replace("(*)", "")

        start_index = self.current_index
        for i in range(start_index, len(tossup_chunks)):
            await self.current_message.edit(content=" ".join(tossup_chunks[0:i + 1]))
            self.current_index = i
            await asyncio.sleep(1)

        self.game_state = GameState.WAIT_BUZZ_END_TU
        await self.wait_for_buzz(self.current_message)


    async def read_bonus(self):
        # get the current bonus part we're on
        current_bonus = self.packet.bonuses[self.cycle_number - 1]
        response = f"{self.cycle_number}. " + current_bonus.leadin_sanitized + "\n" if self.bonus_state == BonusState.PART_1 else ""
        response += current_bonus.parts[self.bonus_state - 1]

        # split into words
        words = response.split(" ")

        # join groups of 4 words
        bonus_chunks = [" ".join(words[i:i+4]) for i in range(0, len(words), 4)]

        bonus_message = await self.channel.send("Bonus")

        for i in range(0, len(bonus_chunks)):
            await bonus_message.edit(content=" ".join(bonus_chunks[0:i+1]))
            await asyncio.sleep(1)

        self.game_state = GameState.WAIT_ANS_BONUS
        await self.wait_for_direct(bonus_message)

    async def wait_for_buzz(self, tossup_message: discord.Message):
        try:
            buzz_message = await self.bot.wait_for("message", check=lambda m: self.is_valid_buzz(m), timeout=5)
            await self.buzz(buzz_message)
        except asyncio.TimeoutError:
            await tossup_message.reply(f"time, tossup goes dead. answer: {self.packet.tossups[self.cycle_number - 1].answer_sanitized}")
            await self.wrong_or_timeout()


    async def wait_for_direct(self, bonus_message: discord.Message):
        try:
            directed_message = await self.bot.wait_for("message", check=lambda m: self.is_valid_direct(m), timeout=6)
            await self.evaluate_bonus_answer(directed_message)
        except asyncio.TimeoutError:
            try:
                await bonus_message.reply("answer?")
                directed_message = await self.bot.wait_for("message", check=lambda m: self.is_valid_direct(m), timeout=4)
                await self.evaluate_bonus_answer(directed_message)
            except asyncio.TimeoutError:
                await bonus_message.reply(f"time. twas: {self.packet.bonuses[self.cycle_number - 1].answers_sanitized[self.bonus_state - 1]}")
                await self.wrong_or_timeout()


    async def score_check(self, message: discord.Message):
        response = ""
        for index, team in enumerate(self.teams):
            response += f"Team {index + 1}: {team.points}\n"

        await message.reply(response)

    async def advance_bonus(self):
        if self.bonus_state < 3:
            # still bonus parts
            self.bonus_state += 1
            self.game_state = GameState.READ_BONUS
            self.current_task = asyncio.create_task(self.read_bonus())

        else:
            # out of parts
            self.bonus_state = 1
            self.cycle_number += 1
            self.power_mark_index = None
            self.game_state = GameState.BETWEEN_CYCLES
            self.current_message = None

            for team in self.teams:
                team.buzzed = False

            if self.cycle_number > len(self.packet.tossups):
                # game is over
                await self.end_round()



    async def wrong_or_timeout(self):
        if self.game_state == GameState.WAIT_ANS_MID_TU:
            # check that there exist teams to buzz lol
            for team in self.teams:
                if not team.buzzed:
                    self.game_state = GameState.READ_TU
                    self.current_task = asyncio.create_task(self.read_tossup())
                    return

            self.cycle_number += 1
            self.power_mark_index = None
            self.game_state = GameState.BETWEEN_CYCLES
            self.current_message = None
            for team in self.teams:
                team.buzzed = False

            if self.cycle_number > len(self.packet.tossups):
                # game is over
                await self.end_round()

        # time
        elif self.game_state == GameState.WAIT_BUZZ_END_TU:
            self.cycle_number += 1
            self.power_mark_index = None
            self.game_state = GameState.BETWEEN_CYCLES
            self.current_message = None
            for team in self.teams:
                team.buzzed = False

            if self.cycle_number > len(self.packet.tossups):
                # game is over
                await self.end_round()

        # time or wrong answer
        elif self.game_state == GameState.WAIT_ANS_END_TU:
            for team in self.teams:
                if not team.buzzed:
                    self.game_state = GameState.WAIT_BUZZ_END_TU
                    await self.wait_for_buzz(self.current_message)
                    return

            self.cycle_number += 1
            self.power_mark_index = None
            self.game_state = GameState.BETWEEN_CYCLES
            self.current_message = None
            for team in self.teams:
                team.buzzed = False

            if self.cycle_number > len(self.packet.tossups):
                # game is over
                await self.end_round()

        # bonus
        elif self.game_state in (GameState.READ_BONUS, GameState.WAIT_ANS_BONUS):
            await self.advance_bonus()

    async def right(self):
        # answer tossup
        if self.game_state in (GameState.WAIT_ANS_MID_TU, GameState.WAIT_ANS_END_TU):
            self.current_message = None
            self.game_state = GameState.READ_BONUS
            self.current_task = asyncio.create_task(self.read_bonus())

        # bonus
        elif self.game_state in (GameState.READ_BONUS, GameState.WAIT_ANS_BONUS):
            await self.advance_bonus()

    def is_valid_buzz(self, message: discord.Message):
        if message.author == self.bot.user:
            return False

        if message.channel != self.channel:
            return False

        if not self.game_state in (GameState.READ_TU, GameState.WAIT_BUZZ_END_TU):
            return False

        user = message.author

        # user isn't part of the game, do nothing
        if not (team := self.get_team_from_user(user)):
            return False

        # team already buzzed
        if team.buzzed:
            return False

        # check that they actually said buzz lmao
        if message.content.lower() not in ("b", "buzz"):
            return False

        team.buzzed = True
        return True

    def is_valid_direct(self, message: discord.Message):
        if message.author == self.bot.user:
            return False

        if message.channel != self.channel:
            return False

        if not self.game_state in (GameState.READ_BONUS, GameState.WAIT_ANS_BONUS):
            return False

        user = message.author

        # user isn't part of the game, do nothing
        if not (team := self.get_team_from_user(user)):
            return False

        # doesn't own the bonus
        if team != self.bonus_owner:
            return False

        # check that the first part of the answer indicates directing
        parts = message.content.split(" ", maxsplit=1)
        if parts[0] not in ("direct", "answer", "d", "a"):
            return False

        # there should be a part after the direct bit
        if len(parts) != 2:
            return False

        return True

    def is_valid_score_check(self, message: discord.Message):
        if message.author == self.bot.user:
            return False

        if message.channel != self.channel:
            return False

        if not "score check" in message.content.lower() and not "sc" in message.content.lower():
            return False

        return True

    async def buzz(self, message: discord.Message):

        if self.current_task:
            self.current_task.cancel()

            try:
                await self.current_task
            except asyncio.CancelledError:
                pass

        self.current_task = None

        if self.game_state == GameState.READ_TU:
            self.game_state = GameState.WAIT_ANS_MID_TU
        else:
            self.game_state = GameState.WAIT_ANS_END_TU

        await self.get_tossup_answer(message)

    async def get_tossup_answer(self, message: discord.Message):
        await message.reply(f"i have {message.author}. answer?")
        try:
            user_answer = await self.bot.wait_for("message", check=lambda m: m.author == message.author and m.channel == message.channel, timeout=8)
            answerline = self.packet.tossups[self.cycle_number - 1].answer
            judgement = await self.bot.qbreader_client.check_answer(answerline, user_answer.content)
            while judgement.directive == Directive.PROMPT:
                await user_answer.reply(judgement.directed_prompt or "prompt")
                user_answer = await self.bot.wait_for("message", check=lambda m: m.author == message.author and m.channel == message.channel, timeout=5)
                judgement = await self.bot.qbreader_client.check_answer(answerline, user_answer.content)

            if judgement.directive == Directive.ACCEPT:
                team = self.get_team_from_user(message.author)
                if self.power_mark_index and self.current_index <= self.power_mark_index:
                    await user_answer.reply("15")
                    team.points += 15
                else:
                    await user_answer.reply("10")
                    team.points += 10

                self.bonus_owner = team
                await self.right()

            elif judgement.directive == Directive.REJECT:

                # has another team buzzed?
                first_interrupt = True
                for team in self.teams:
                    if team.buzzed and team != self.get_team_from_user(message.author):
                        first_interrupt = False

                # is it the end of the tossup?
                if self.game_state == GameState.WAIT_ANS_END_TU or not first_interrupt:
                    await user_answer.reply("incorrect, no penalty")
                else:
                    await user_answer.reply("neg 5")
                    self.get_team_from_user(message.author).points -= 5

                await self.wrong_or_timeout()

        except asyncio.TimeoutError:
            await message.channel.send("timeout, neg 5")
            self.get_team_from_user(message.author).points -= 5
            await self.wrong_or_timeout()


    async def evaluate_bonus_answer(self, directed_message: discord.Message):

        if self.current_task:
            self.current_task.cancel()

            try:
                await self.current_task
            except asyncio.CancelledError:
                pass

        self.current_task = None

        try:
            answerline = self.packet.bonuses[self.cycle_number - 1].answers[self.bonus_state - 1]
            judgement = await self.bot.qbreader_client.check_answer(answerline, directed_message.content.split(" ", maxsplit=1)[1])
            while judgement.directive == Directive.PROMPT:
                await directed_message.reply(judgement.directed_prompt or "prompt")
                directed_message = await self.bot.wait_for("message", check=lambda m: self.is_valid_direct(m), timeout=10)
                judgement = await self.bot.qbreader_client.check_answer(answerline, directed_message.content.split(" ", maxsplit=1)[1])

            if judgement.directive == Directive.ACCEPT:
                await directed_message.reply("10")
                self.bonus_owner.points += 10
                await self.right()

            elif judgement.directive == Directive.REJECT:
                await directed_message.reply(f"no: {self.packet.bonuses[self.cycle_number - 1].answers_sanitized[self.bonus_state - 1]}")
                await self.wrong_or_timeout()

        except asyncio.TimeoutError:
            await directed_message.channel.send(f"timeout: {self.packet.bonuses[self.cycle_number - 1].answers_sanitized[self.bonus_state - 1]}")
            await self.wrong_or_timeout()


    async def end_round(self):
        if self.current_task:
            self.current_task.cancel()

        try:
            await self.current_task
        except asyncio.CancelledError:
            pass

        message = await self.channel.send("Round over - Final score:")
        await self.score_check(message)
        del self.bot.game_sessions[self.channel.id]