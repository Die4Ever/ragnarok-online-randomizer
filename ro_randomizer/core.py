from ro_randomizer.base import *
from ro_randomizer.entrance_rando import *

def randomize(local_settings):
    settings = local_settings
    seed = settings.get('seed')
    if not seed:
        seed = random.randrange(1,999999)
    else:
        seed = int(seed)
    print("randomizing with seed: "+str(seed))
    settings['seed'] = seed
    print("settings: ")
    print(repr(settings))
    entrance_rando()
    #randomize_spawns
    #randomize_sql
