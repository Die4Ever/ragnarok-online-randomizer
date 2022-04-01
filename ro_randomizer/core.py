from ro_randomizer.base import *
from ro_randomizer.entrance_rando import *
from ro_randomizer.mobs_rando import *

def randomize(local_settings):
    settings = local_settings
    seed = settings.get('seed')
    if not seed:
        seed = random.randrange(1,999999)
    else:
        seed = int(seed)
    settings['seed'] = seed
    set_settings(settings)
    check_settings_config(settings)

    printHeader("randomizing with seed: "+str(seed))
    notice("settings:", settings)

    if do_profiling:
        profile("ro_randomizer.core.do_rando()")
    else:
        do_rando()


def do_rando():
    entrance_rando()
    #randomize_mobs for mob spawns according to the desired danger level of each map
    mobs_rando()
    #randomize skills...


def check_settings_config(settings):
    assert 'seed' in settings
    assert 'inputs' in settings
    assert 'outputs' in settings
    for type in settings['inputs']:
        if type not in settings['outputs']:
            continue
        for i in settings['inputs'][type]:
            if i == settings['outputs'][type]:
                raise Exception("bad config: can't use the same path for input and output of "+type+': '+i)

