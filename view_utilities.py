import discord

# retep...
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from main import QuizBowlBot

from game_session import QuizBowlGameSession

from utilities import strings_approximately_match

DIFFICULTY_OPTIONS = [
    "0: Pop Culture",
    "1: Middle School",
    "2: Easy High School",
    "3: Regular High School",
    "4: Hard High School",
    "5: National High School",
    "6: Easy College",
    "7: Medium College",
    "8: Regionals College",
    "9: Nationals College",
    "10: Open",
]

CATEGORY_OPTIONS = [
    "Literature",
    "History",
    "Science",
    "Fine Arts",
    "Religion",
    "Mythology",
    "Philosophy",
    "Social Science",
    "Current Events",
    "Geography",
    "Other Academic",
    "Pop Culture",
]

SUBCATEGORY_OPTIONS = {
    "Literature" : [
        "American Literature",
        "British Literature",
        "Classical Literature",
        "European Literature",
        "World Literature",
        "Other Literature",
    ],
    "History" : [
        "American History",
        "Ancient History",
        "European History",
        "World History",
        "Other History",
    ],
    "Science" : [
        "Biology",
        "Chemistry",
        "Physics",
        "Other Science",
    ],
    "Fine Arts" : [
        "Visual Fine Arts",
        "Auditory Fine Arts",
        "Other Fine Arts",
    ],
    "Pop Culture" : [
        "Movies",
        "Music",
        "Sports",
        "Television",
        "Video Games",
        "Other Pop Culture",
    ],
}

ALTERNATE_SUBCATEGORY_OPTIONS = {
    "Literature" : [
        "Drama",
        "Long Fiction",
        "Poetry",
        "Short Fiction",
        "Misc Literature",
    ],
    "Science" : [
        "Math",
        "Astronomy",
        "Computer Science",
        "Earth Science",
        "Engineering",
        "Misc Science",
    ],
    "Fine Arts" : [
        "Architecture",
        "Dance",
        "Film",
        "Jazz",
        "Musicals",
        "Opera",
        "Photography",
        "Misc Arts",
    ],
    "Social Science" : [
        "Anthropology",
        "Economics",
        "Linguistics",
        "Psychology",
        "Sociology",
        "Other Social Science",
    ],
}

class Settings:
    def __init__(self):
        self.message: discord.InteractionMessage | None = None
        self.owner_id: int = 0

        # random questions or specific set
        self.mode: str | None = None

        # only if random question mode
        self.difficulties = []
        self.categories = []
        self.subcategories = []
        self.alt_subcats = []
        self.min_year = 2000
        self.max_year = 2026

        # only if specific packet mode
        self.set_search_results = []
        self.selected_set = None
        self.selected_packet = 0

    def __str__(self):
        return f"Mode: {self.mode}\nDifficulties: {self.difficulties}\nCategories: {self.categories}\nSubcategories: {self.subcategories}\nAlt Subcategories: {self.alt_subcats}\nMin Year: {self.min_year}\nMax Year: {self.max_year}"


class ModeSelectView(discord.ui.View):
    def __init__(self, settings: Settings = Settings()):
        self.settings = settings
        super().__init__(timeout=20)

        mode_select = discord.ui.Select(
            placeholder="Select where questions should come from...",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(label="Random questions", description="Select custom difficulties and categories and get 20 random tossups and bonuses.", default=(self.settings.mode == "Random")),
                discord.SelectOption(label="Search for a packet", description="Search for a specific packet from the database.", default=(self.settings.mode == "Search")),
            ],
            row=0,
        )

        async def mode_callback(interaction: discord.Interaction):
            await interaction.response.defer()
            if mode_select.values[0] == "Random questions":
                self.settings.mode = "Random"
            elif mode_select.values[0] == "Search for a packet":
                self.settings.mode = "Search"
            else:
                self.settings.mode = None

        mode_select.callback = mode_callback

        self.add_item(mode_select)

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id == self.settings.owner_id:
            return True

        await interaction.response.send_message("erm, you aren't the owner of this game", ephemeral=True)
        return False

    async def on_timeout(self):
        await self.settings.message.edit(content="you took too long, try again.", view=None)

    @discord.ui.button(
        label="Cancel",
        style=discord.ButtonStyle.danger,
        row=1,
    )
    async def cancel_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()
        await interaction.response.edit_message(content="Game creation canceled.", view=None)

    @discord.ui.button(
        label="Continue",
        style=discord.ButtonStyle.success,
        row=1,
    )
    async def continue_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.settings.mode is None:
            await interaction.response.send_message("No mode selected!", ephemeral=True)
        else:
            self.stop()
            if self.settings.mode == "Random":
                await interaction.response.edit_message(content="Select difficulties and categories.", view=DiffCatSelectView(self.settings))
            elif self.settings.mode == "Search":
                await interaction.response.edit_message(content="Search for set.", view=SetSearchView(self.settings))

class DiffCatSelectView(discord.ui.View):
    def __init__(self, settings: Settings):
        self.settings = settings
        super().__init__(timeout=60)

        difficulty_select = discord.ui.Select(
            placeholder="Select difficulties...",
            min_values=0,
            max_values=11,
            options=[
                discord.SelectOption(label=difficulty, default=(difficulty in self.settings.difficulties))
                for difficulty in DIFFICULTY_OPTIONS
            ],
            row=0,
        )
        async def difficulty_callback(interaction: discord.Interaction):
            await interaction.response.defer()
            self.settings.difficulties = [value[0] for value in difficulty_select.values]

        difficulty_select.callback = difficulty_callback

        category_select = discord.ui.Select(
            placeholder="Select categories...",
            min_values=0,
            max_values=12,
            options=[
                discord.SelectOption(label=category, default=(category in self.settings.categories))
                for category in CATEGORY_OPTIONS
            ],
            row=1,
        )

        async def category_callback(interaction: discord.Interaction):
            await interaction.response.defer()
            self.settings.categories = category_select.values

        category_select.callback = category_callback

        self.add_item(difficulty_select)
        self.add_item(category_select)

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id == self.settings.owner_id:
            return True

        await interaction.response.send_message("erm, you aren't the owner of this game", ephemeral=True)
        return False

    async def on_timeout(self):
        await self.settings.message.edit(content="you took too long, try again.", view=None)

    @discord.ui.button(
        label="Cancel",
        style=discord.ButtonStyle.danger,
        row=2,
    )
    async def cancel_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()
        await interaction.response.edit_message(content="Game creation canceled.", view=None)

    @discord.ui.button(
        label="Back",
        style=discord.ButtonStyle.secondary,
        row=2,
    )
    async def back_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()
        await interaction.response.edit_message(content="Select game mode.", view=ModeSelectView(self.settings))

    @discord.ui.button(
        label="Continue",
        style=discord.ButtonStyle.success,
        row=2,
    )
    async def continue_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if len(self.settings.difficulties) == 0:
            self.settings.difficulties = DIFFICULTY_OPTIONS
        if len(self.settings.categories) == 0:
            self.settings.categories = CATEGORY_OPTIONS
        self.stop()
        await interaction.response.edit_message(content="Select subcategories.", view=SubcatSelectView(self.settings))


class SubcatSelectView(discord.ui.View):
    def __init__(self, settings: Settings):
        self.settings = settings
        super().__init__(timeout=60)

        # literature, history, and science options
        self.lhs_options = []
        for cat in ("Literature", "History", "Science"):
            if cat in self.settings.categories:
                self.lhs_options.extend(SUBCATEGORY_OPTIONS[cat])

        # fine arts and pop culture options
        self.fap_options = []
        for cat in ("Fine Arts", "Pop Culture"):
            if cat in self.settings.categories:
                self.fap_options.extend(SUBCATEGORY_OPTIONS[cat])

        # if there's subcategories not covered by our options, the user probably changed categories, so we're good to wipe the settings anyway
        # not exactly the user-friendly option, but they shouldn't have changed categories hehehehe
        if not all(selection in self.lhs_options or selection in self.fap_options for selection in self.settings.subcategories):
            self.settings.subcategories = []

        row = 0
        if len(self.lhs_options) > 0:
            lhs_subcat_select = discord.ui.Select(
                placeholder="Select subcategories (lit, hist, sci)...",
                min_values=0,
                max_values=len(self.lhs_options),
                options=[
                    discord.SelectOption(label=subcat, default=(subcat in self.settings.subcategories))
                    for subcat in self.lhs_options
                ],
                row=row
            )

            async def lhs_callback(interaction: discord.Interaction):
                await interaction.response.defer()
                for option in lhs_subcat_select.options:
                    if option.value in lhs_subcat_select.values and option.value not in self.settings.subcategories:
                        self.settings.subcategories.append(option.value)
                    elif option.value not in lhs_subcat_select.values and option.value in self.settings.subcategories:
                        self.settings.subcategories.remove(option.value)

            lhs_subcat_select.callback = lhs_callback

            self.add_item(lhs_subcat_select)

            row += 1

        if len(self.fap_options) > 0:
            fap_subcat_select = discord.ui.Select(
                placeholder="Select subcategories (fine arts, pop culture)...",
                min_values=0,
                max_values=len(self.fap_options),
                options=[
                    discord.SelectOption(label=subcat, default=(subcat in self.settings.subcategories))
                    for subcat in self.fap_options
                ],
                row=row
            )

            async def fap_callback(interaction: discord.Interaction):
                await interaction.response.defer()
                for option in fap_subcat_select.options:
                    if option.value in fap_subcat_select.values and option.value not in self.settings.subcategories:
                        self.settings.subcategories.append(option.value)
                    elif option.value not in fap_subcat_select.values and option.value in self.settings.subcategories:
                        self.settings.subcategories.remove(option.value)

            fap_subcat_select.callback = fap_callback

            self.add_item(fap_subcat_select)

            row += 1

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id == self.settings.owner_id:
            return True

        await interaction.response.send_message("erm, you aren't the owner of this game", ephemeral=True)
        return False

    async def on_timeout(self):
        await self.settings.message.edit(content="you took too long, try again.", view=None)

    @discord.ui.button(
        label="Cancel",
        style=discord.ButtonStyle.danger,
        row=2,
    )
    async def cancel_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()
        await interaction.response.edit_message(content="Game creation canceled.", view=None)

    @discord.ui.button(
        label="Back",
        style=discord.ButtonStyle.secondary,
        row=2,
    )
    async def back_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()
        await interaction.response.edit_message(content="Select difficulties and categories.", view=DiffCatSelectView(self.settings))

    @discord.ui.button(
        label="Continue",
        style=discord.ButtonStyle.success,
        row=2,
    )
    async def continue_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if len(self.settings.subcategories) == 0:
            self.settings.subcategories = self.lhs_options + self.fap_options
        self.stop()
        await interaction.response.edit_message(content="Select alternate subcategories.", view=AltSubcatSelectView(self.settings))


class YearRangeModal(discord.ui.Modal):
    def __init__(self, settings: Settings):
        self.settings = settings
        super().__init__(title="Choose Minimum and Maximum Year")

        self.min_year_input = discord.ui.TextInput(
            label="Minimum year",
            placeholder="Must be less than max year",
            required=True,
            max_length=4,
        )

        self.max_year_input = discord.ui.TextInput(
            label="Maximum year",
            placeholder="Must be greater than min year",
            required=True,
            max_length=4,
        )

        self.add_item(self.min_year_input)
        self.add_item(self.max_year_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            min_year = int(self.min_year_input.value)
            max_year = int(self.max_year_input.value)
        except ValueError:
            await interaction.response.send_message("Error parsing year input", ephemeral=True)
            return

        if min_year > max_year:
            await interaction.response.send_message("Min year must be less than max year", ephemeral=True)
            return

        self.settings.min_year = min_year
        self.settings.max_year = max_year

        await interaction.response.edit_message(content="Select alternate categories.", view=AltSubcatSelectView(self.settings))

class AltSubcatSelectView(discord.ui.View):
    def __init__(self, settings: Settings):
        self.settings = settings
        super().__init__(timeout=60)

        # literature and science options
        self.ls_options = []
        for cat in ("Literature", "Science"):
            if cat in self.settings.categories:
                self.ls_options.extend(ALTERNATE_SUBCATEGORY_OPTIONS[cat])

        # fine arts and social science options
        self.fass_options = []
        for cat in ("Fine Arts", "Social Science"):
            if cat in self.settings.categories:
                self.fass_options.extend(ALTERNATE_SUBCATEGORY_OPTIONS[cat])

        # if there's alternate subcategories not covered by our options, the user probably changed categories, so we're good to wipe the settings anyway
        # not exactly the user-friendly option, but they shouldn't have changed categories hehehehe
        if not all(selection in self.ls_options or selection in self.fass_options for selection in self.settings.alt_subcats):
            self.settings.alt_subcats = []

        row = 0
        if len(self.ls_options) > 0:
            ls_subcat_select = discord.ui.Select(
                placeholder="Select alternate subcategories (lit and sci)...",
                min_values=0,
                max_values=len(self.ls_options),
                options=[
                    discord.SelectOption(label=alt_subcat, default=(alt_subcat in self.settings.alt_subcats))
                    for alt_subcat in self.ls_options
                ],
                row=row
            )

            async def ls_callback(interaction: discord.Interaction):
                await interaction.response.defer()
                for option in ls_subcat_select.options:
                    if option.value in ls_subcat_select.values and option.value not in self.settings.alt_subcats:
                        self.settings.alt_subcats.append(option.value)
                    elif option.value not in ls_subcat_select.values and option.value in self.settings.alt_subcats:
                        self.settings.alt_subcats.remove(option.value)

            ls_subcat_select.callback = ls_callback

            self.add_item(ls_subcat_select)

            row += 1

        if len(self.fass_options) > 0:
            fass_subcat_select = discord.ui.Select(
                placeholder="Select alternate subcategories (fine arts and social science)...",
                min_values=0,
                max_values=len(self.fass_options),
                options=[
                    discord.SelectOption(label=alt_subcat, default=(alt_subcat in self.settings.alt_subcats))
                    for alt_subcat in self.fass_options
                ],
                row=row
            )

            async def fass_callback(interaction: discord.Interaction):
                await interaction.response.defer()
                for option in fass_subcat_select.options:
                    if option.value in fass_subcat_select.values and option.value not in self.settings.alt_subcats:
                        self.settings.alt_subcats.append(option.value)
                    elif option.value not in fass_subcat_select.values and option.value in self.settings.alt_subcats:
                        self.settings.alt_subcats.remove(option.value)

            fass_subcat_select.callback = fass_callback

            self.add_item(fass_subcat_select)

            row += 1

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id == self.settings.owner_id:
            return True

        await interaction.response.send_message("erm, you aren't the owner of this game", ephemeral=True)
        return False

    async def on_timeout(self):
        await self.settings.message.edit(content="you took too long, try again.", view=None)

    @discord.ui.button(
        label="Set Year Range",
        style=discord.ButtonStyle.primary,
        row=2,
    )
    async def year_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(YearRangeModal(self.settings))

    @discord.ui.button(
        label="Cancel",
        style=discord.ButtonStyle.danger,
        row=3,
    )
    async def cancel_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()
        await interaction.response.edit_message(content="Game creation canceled.", view=None)

    @discord.ui.button(
        label="Back",
        style=discord.ButtonStyle.secondary,
        row=3,
    )
    async def back_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()
        await interaction.response.edit_message(content="Select subcategories.", view=SubcatSelectView(self.settings))

    @discord.ui.button(
        label="Confirm Choices",
        style=discord.ButtonStyle.success,
        row=3,
    )
    async def confirm_callback(self, interaction: discord.Interaction[QuizBowlBot], button: discord.ui.Button):
        self.stop()
        packet = await interaction.client.collect_random_packet(
            difficulties=self.settings.difficulties,
            categories=self.settings.categories,
            subcategories=self.settings.subcategories,
            alternate_subcategories=self.settings.alt_subcats,
            min_year=self.settings.min_year,
            max_year=self.settings.max_year,
        )
        interaction.client.game_sessions[interaction.channel.id] = QuizBowlGameSession(interaction.user, packet, interaction.client, interaction.channel)
        await interaction.response.edit_message(content="ok made your game session :)", view=None)


class SetSearchModal(discord.ui.Modal):
    def __init__(self, settings: Settings):
        self.settings = settings
        super().__init__(title="Search for Set Name")

        self.set_name_input = discord.ui.TextInput(
            label="Set Name",
            placeholder="Only the most recent 25 results will show up!",
            required=True
        )

        self.add_item(self.set_name_input)

    async def on_submit(self, interaction: discord.Interaction[QuizBowlBot]):
        search = self.set_name_input.value

        # this is probably an expensive line but i don't care, it'll get much worse
        set_list = await interaction.client.get_set_list() # yknow, it's actually a set tuple

        # up to 25 results
        search_results = []

        for set_name in set_list:
            # first we check if the search is contained within the set name (e.g. "ACF" returns "2025 ACF Regionals")
            if search in set_name:
                search_results.append(set_name)
                if len(search_results) >= 25:
                    break
                continue

            # well, fuck. that didn't work, did it? let's try this
            if strings_approximately_match(search, set_name):
                search_results.append(set_name)
                if len(search_results) >= 25:
                    break
                continue

        # wow, somebody here is an idiot.
        if len(search_results) == 0:
            await interaction.response.send_message(content="No results found, try again.", ephemeral=True)
        else:
            self.settings.set_search_results = search_results
            await interaction.response.send_message(content=f"Found {len(search_results)} results.", ephemeral=True)
        await interaction.response.edit_message(content="Search for set.", view=SetSearchView(self.settings))


class SetSearchView(discord.ui.View):
    def __init__(self, settings: Settings):
        self.settings = settings
        super().__init__(timeout=60)

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id == self.settings.owner_id:
            return True

        await interaction.response.send_message("erm, you aren't the owner of this game", ephemeral=True)
        return False

    async def on_timeout(self):
        await self.settings.message.edit(content="you took too long, try again.", view=None)

    @discord.ui.button(
        label="Set Search",
        style=discord.ButtonStyle.primary,
        row=0,
    )
    async def search_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SetSearchModal(self.settings))

    @discord.ui.button(
        label="Cancel",
        style=discord.ButtonStyle.danger,
        row=2,
    )
    async def cancel_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()
        await interaction.response.edit_message(content="Game creation canceled.", view=None)

    @discord.ui.button(
        label="Back",
        style=discord.ButtonStyle.secondary,
        row=2,
    )
    async def back_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()
        await interaction.response.edit_message(content="Select game mode.", view=ModeSelectView(self.settings))

    @discord.ui.button(
        label="Continue",
        style=discord.ButtonStyle.success,
        row=2,
    )
    async def continue_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if len(self.settings.set_search_results) == 0:
            await interaction.response.send_message(content="No results loaded!", ephemeral=True)
            return
        self.stop()
        await interaction.response.edit_message(content="Select a set.", view=SetSelectView(self.settings))


class SetSelectView(discord.ui.View):
    def __init__(self, settings: Settings):
        self.settings = settings
        super().__init__(timeout=60)

        set_select = discord.ui.Select(
            placeholder="Select a set...",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(label=set_name, default=(set_name == self.settings.selected_set))
                for set_name in self.settings.set_search_results
            ],
            row=0,
        )

        async def set_callback(interaction: discord.Interaction):
            await interaction.response.defer()
            self.settings.selected_set = set_select.values[0]

        set_select.callback = set_callback

        self.add_item(set_select)

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id == self.settings.owner_id:
            return True

        await interaction.response.send_message("erm, you aren't the owner of this game", ephemeral=True)
        return False

    async def on_timeout(self):
        await self.settings.message.edit(content="you took too long, try again.", view=None)

    @discord.ui.button(
        label="Cancel",
        style=discord.ButtonStyle.danger,
        row=1,
    )
    async def cancel_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()
        await interaction.response.edit_message(content="Game creation canceled.", view=None)

    @discord.ui.button(
        label="Back",
        style=discord.ButtonStyle.secondary,
        row=1,
    )
    async def back_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()
        await interaction.response.edit_message(content="Search for set.", view=SetSearchView(self.settings))

    @discord.ui.button(
        label="Continue",
        style=discord.ButtonStyle.success,
        row=1,
    )
    async def continue_callback(self, interaction: discord.Interaction[QuizBowlBot], button: discord.ui.Button):
        if self.settings.selected_set is None:
            await interaction.response.send_message(content="Select a set first!", ephemeral=True)
            return
        self.stop()
        self.settings.set_num_packets = await interaction.client.get_num_packets(self.settings.selected_set)
        await interaction.response.edit_message(content="Select a packet.", view=PacketSelectView(self.settings))


class PacketSelectView(discord.ui.View):
    def __init__(self, settings: Settings):
        self.settings = settings
        super().__init__(timeout=60)

        packet_select = discord.ui.Select(
            placeholder="Select a packet...",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(label=f"Packet {i + 1}", default=(i + 1 == self.settings.selected_packet))
                for i in range(self.settings.set_num_packets)
            ],
            row=0,
        )

        async def packet_callback(interaction: discord.Interaction):
            await interaction.response.defer()
            self.settings.selected_packet = int(packet_select.values[0].lstrip("Packet "))

        packet_select.callback = packet_callback

        self.add_item(packet_select)

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id == self.settings.owner_id:
            return True

        await interaction.response.send_message("erm, you aren't the owner of this game", ephemeral=True)
        return False

    async def on_timeout(self):
        await self.settings.message.edit(content="you took too long, try again.", view=None)

    @discord.ui.button(
        label="Cancel",
        style=discord.ButtonStyle.danger,
        row=1,
    )
    async def cancel_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()
        await interaction.response.edit_message(content="Game creation canceled.", view=None)

    @discord.ui.button(
        label="Back",
        style=discord.ButtonStyle.secondary,
        row=1,
    )
    async def back_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()
        await interaction.response.edit_message(content="Select a set.", view=SetSelectView(self.settings))

    @discord.ui.button(
        label="Confirm Choices",
        style=discord.ButtonStyle.success,
        row=1,
    )
    async def confirm_callback(self, interaction: discord.Interaction[QuizBowlBot], button: discord.ui.Button):
        if self.settings.selected_packet == 0:
            await interaction.response.send_message("Select a packet first!", ephemeral=True)
            return
        self.stop()
        packet = await interaction.client.collect_specific_packet(self.settings.selected_set, self.settings.selected_packet)
        interaction.client.game_sessions[interaction.channel.id] = QuizBowlGameSession(interaction.user, packet, interaction.client, interaction.channel)
        await interaction.response.edit_message(content="ok made your game session :)", view=None)
