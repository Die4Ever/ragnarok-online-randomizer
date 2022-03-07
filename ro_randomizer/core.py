from ro_randomizer.base import *
from ro_randomizer.entrance_rando import *

def randomize(local_settings):
    settings = local_settings
    seed = settings.get('seed')
    if not seed:
        seed = random.randrange(1,999999)
    else:
        seed = int(seed)
    printHeader("randomizing with seed: "+str(seed))
    settings['seed'] = seed
    notice("settings: ")
    notice(repr(settings))
    entrance_rando()
    #randomize_mobs for mob spawns according to the desired danger level of each map
    #randomize_sql for skills/classes...
    #randomize_config for leveling rates, item rates...
