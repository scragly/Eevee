from types import SimpleNamespace

from eevee.utils.fuzzymatch import FuzzyEnum, get_match
from eevee.cogs.pokemon import Pokemon

class Weather(FuzzyEnum):
    NONE = 'NO_WEATHER'
    EXTREME = 'NO_WEATHER'
    CLEAR = 'CLEAR'
    RAIN = 'RAINY'
    PARTLY_CLOUDY = 'PARTLY_CLOUDY'
    CLOUDY = 'OVERCAST'
    WINDY = 'WINDY'
    SNOW = 'SNOW'
    FOG = 'FOG'

    DEFAULT = NONE

class DodgeStrategy(FuzzyEnum):
    NONE = 'CINEMATIC_ATTACK_WHEN_POSSIBLE'
    SPECIALS = 'DODGE_SPECIALS'
    ALL = 'DODGE_WEAVE_CAUTIOUS'

    DEFAULT = NONE

class DodgeSkill(FuzzyEnum):
    PERFECT = 'DODGE_100'
    REALISTIC = 'DODGE_REACTION_TIME'
    REALISTIC_PRO = 'DODGE_REACTION_TIME2'
    POOR = 'DODGE_25'

    DEFAULT = REALISTIC

class Scoring(FuzzyEnum):
    OVERALL = 'OVERALL'
    POWER = 'POWER'
    WIN_PC = 'WIN'
    WIN_TIME = 'TIME'
    TIME = 'TIME'

    DEFAULT = OVERALL

class CounterPkmn(Pokemon):
    """Represents a Pokebattler Counter Pokemon"""

    __slots__ = ('name', 'id', 'types', 'bot', 'guild', 'pkmn_list',
                 'move1', 'move2', 'cp', 'win', 'combat_time', 'deaths',
                 'potions', 'power', 'rating', 'win_ratio')

    def __init__(self, bot, data):
        pkmn_list = list(bot.pkmn_info.keys())
        pkmn = data.pop('pokemonId').replace('_', ' ')
        pkmn = get_match(pkmn_list, pkmn, score_cutoff=80)[0]
        super().__init__(bot, pkmn)
        self.cp = data.pop('cp')
        self.move1 = self.clean_txt(data['byMove'][-1].pop('move1')[:-5])
        self.move2 = self.clean_txt(data['byMove'][-1].pop('move2'))
        result = data['byMove'][-1]['result']
        self.win = result.pop('win')
        self.win_ratio = round(result.pop('winRatio'), 2)
        self.combat_time = round(result.pop('effectiveCombatTime')/1000, 2)
        self.deaths = round(result.pop('deaths'), 2)
        self.potions = round(result.pop('potions'), 2)
        self.power = round(result.pop('power'), 2)
        self.rating = round(1/result.pop('overallRating'), 2)

    def clean_txt(self, txt: str):
        return txt.replace('_', ' ').title()

    @property
    def moveset(self):
        return (self.move1, self.move2)


class PBRaid:
    """Represents a Pokebattler Raid

    Parameters
    -----------
    pokemon
    """

    __slots__ = ('bot', 'tracker', 'pokemon', 'settings', 'counters',
                 'raid_cp', 'raid_tier', 'atk_lvl', 'userid', 'stats',
                 'movesets_list', '_movesets_data', '_moveset',
                 '_no_moveset_data', 'url', 'public_url', 'def_cp',
                 'atk_strat', 'dodge', 'weather', 'sort')

    base_url_api = "https://fight.pokebattler.com/"
    base_url_web = "https://www.pokebattler.com/"

    def __init__(self, bot, pokemon, **settings):
        self.bot = bot
        self.tracker = bot.config.pokebattler_tracker
        if not isinstance(pokemon, Pokemon):
            pkmn_list = list(bot.pkmn_info.keys())
            pkmn_match = get_match(pkmn_list, pokemon, score_cutoff=80)[0]
            pokemon = Pokemon(bot, pkmn_match)
        self.pokemon = pokemon
        self.counters = []
        self.settings = settings
        self.raid_tier = settings.get('raid_tier', None)
        self.def_cp = settings.get('def_cp', None)
        self.atk_strat = settings.get('atk_strat', DodgeStrategy.DEFAULT)
        self.dodge = settings.get('dodge', DodgeSkill.DEFAULT)
        self.atk_lvl = settings.get('atk_lvl', 30)
        self.weather = settings.get('weather', Weather.DEFAULT)
        self.userid = settings.get('userid', None)
        self.sort = settings.get('sort', Scoring.DEFAULT)
        self.raid_cp = None
        self.stats = None
        self.movesets_list = []
        self._movesets_data = {}
        self._no_moveset_data = None
        self._moveset = None
        self.url = None
        self.public_url = None

    @classmethod
    async def get(cls, bot, pokemon, **settings):
        instance = cls(bot, pokemon, **settings)
        await instance.get_data()
        instance.set_moveset()
        return instance

    async def get_data(self):
        """Gets the json data for a Pokebattler Raid"""
        url = self.raid_url()
        async with self.bot.session.get(url) as resp:
            if resp.status != 200:
                raise RuntimeError('Pokebattler failed to repond.')
            json_data = await resp.json()
            print(resp.headers)
            return self._parse_data(json_data['attackers'][0])

    def _parse_data(self, data):
        self.raid_cp = data.pop('cp')
        self.stats = SimpleNamespace(**(data.pop('stats')))

        # get moveset specific defenders
        for moveset in data['byMove']:
            moves = (moveset['move1'][:-5], moveset['move2'])
            self.movesets_list.append(moves)
            self._movesets_data[''.join(moves)] = moveset['defenders']

        # get non-specified moveset defenders
        self._no_moveset_data = data['randomMove']['defenders']

    def set_moveset(self, moveset: list = None):
        if not moveset:
            self._moveset = None
        else:
            fast_moves, charge_moves = zip(*self.movesets_list)
            mv1 = get_match(fast_moves, moveset[0])[0]
            mv2 = get_match(charge_moves, moveset[1])[0]
            if not mv1 or not mv2:
                raise RuntimeError('Invalid moveset.')
            self._moveset = (mv1, mv2)
        return self.set_counters()

    def clean_txt(self, txt: str):
        return txt.replace('_', ' ').title()

    def set_counters(self):
        if self._moveset:
            moves = ''.join(self._moveset)
            counters = self._movesets_data[moves][-6:]
        else:
            counters = self._no_moveset_data[-6:]
        self.counters = []
        for counter in reversed(counters):
            self.counters.append(CounterPkmn(self.bot, counter))

    @property
    def moveset(self):
        return list(map(self.clean_txt, self._moveset)) if self._moveset else None

    @property
    def fast_moves(self):
        fast_moves, _ = zip(*self.movesets_list)
        return set(map(self.clean_txt, fast_moves))

    @property
    def charge_moves(self):
        _, charge_moves = zip(*self.movesets_list)
        return set(map(self.clean_txt, charge_moves))

    def raid_url(self):
        """Generates a Pokebattler Raid URL"""
        pkmn = self.pokemon
        raid_tier = self.raid_tier
        def_cp = self.def_cp
        atk_strat = self.atk_strat
        dodge = self.dodge
        atk_lvl = self.atk_lvl
        weather = self.weather
        userid = self.userid
        sort = self.sort

        # determine defender stats
        if raid_tier:
            defender = f"levels/RAID_LEVEL_{raid_tier}"
        elif def_cp:
            defender = f"cp/{def_cp}"
        else:
            if isinstance(pkmn, Pokemon):
                raid_tier = pkmn.raid_level
                if not raid_tier:
                    return None
                defender = f"levels/RAID_LEVEL_{raid_tier}"
            else:
                return None
        # ensure pkmn name is caps and str
        if isinstance(pkmn, Pokemon):
            pkmn = pkmn.name.replace(" ", "_").upper()
        else:
            pkmn = pkmn.replace(" ", "_").upper()

        # determine attacker stats
        if userid:
            attacker = f"attackers/users/{userid}"
        else:
            attacker = f"attackers/levels/{atk_lvl}"

        strategies = f"strategies/{atk_strat.value}/DEFENSE_RANDOM_MC"
        full_url = f"raids/defenders/{pkmn}/{defender}/{attacker}/{strategies}"

        sort_url = f"sort={sort.value}"
        weather_url = f"weatherCondition={weather.value}"
        dodge_url = f"dodgeStrategy={dodge.value}"
        aggregation = f"aggregation=AVERAGE"

        param_url = "&".join((sort_url, weather_url, dodge_url, aggregation))

        if self.tracker:
            param_url += f"&source={self.tracker}"

        self.url = f"{self.base_url_api}{full_url}?{param_url}"
        self.public_url = f"{self.base_url_web}{full_url}?{param_url}"

        return self.url
