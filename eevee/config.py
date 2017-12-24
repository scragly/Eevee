'''Configuration values for Eevee'''

# bot token from discord developers
bot_token = 'Mzk0NTI5MDg1OTIzMjYyNDY0.DSFpXA.vX1wnEwFEtFpWPuXoPVaKPyFah4'

# default bot settings
bot_prefix = ['!']
bot_master = 174764205927432192
bot_coowners = [132314336914833409,263607303096369152]
preload_extensions = ['tests']

# minimum required permissions for bot user
bot_permissions = 268822608

# postgresql database credentials
db_user = 'test'
db_pass = 'password'
db_host = 'localhost'
db_name = 'test'

# default language
lang_bot = 'en'
lang_pkmn = 'en'

# team settings
team_list = ['mystic','valor','instinct']
team_colours = {
    "mystic"   : "0x3498db",
    "valor"    : "0xe74c3c",
    "instinct" : "0xf1c40f"
}
team_emoji = {
    "mystic"   : "<:mystic:350686962388303873>",
    "valor"    : "<:valor:350686957820706816>",
    "instinct" : "<:instinct:350686957703135232>"
}

# raid settings
allow_assume = {
    "5" : "False",
    "4" : "False",
    "3" : "False",
    "2" : "False",
    "1" : "False"
}
status_emoji = {
    "omw"     : ":omw:",
    "here_id" : ":here:"
}
type_emoji = {
    "normal"   : "<:normal:350686939965554689>",
    "fire"     : "<:fire1:350686939378221057>",
    "water"    : "<:water:350686939571290112>",
    "electric" : "<:electric:350686938178650113>",
    "grass"    : "<:grass:350686939504050180>",
    "ice"      : "<:ice:350686939667496961>",
    "fighting" : "<:fighting:350686939466432523>",
    "poison"   : "<:poison:350686939449393180>",
    "ground"   : "<:ground:350686938983956480>",
    "flying"   : "<:flying:350686937050513418>",
    "psychic"  : "<:psychic:350686937754894347>",
    "bug"      : "<:bug1:350686933732687872>",
    "rock"     : "<:rock:350686939520696321>",
    "ghost"    : "<:ghost1:350686939462107146>",
    "dragon"   : "<:dragon:350686936949587978>",
    "dark"     : "<:dark:350686934881927169>",
    "steel"    : "<:steel:350686939919155201>",
    "fairy"    : "<:fairy:350686936698060812>"
}

# help command categories
command_categories = {
    "Owner" : {
        "index"       : "1",
        "description" : "Owner-only commands for bot config or info."
    },
    "Server Config" : {
        "index"       : "2",
        "description" : "Server configuration commands."
    },
    "Bot Info" : {
        "index"       : "3",
        "description" : "Commands for finding out information on the bot."
    },
}
