from ro_randomizer.base import *

class Map():
    # approximate location? list of the warps in this map? a desired danger rating?
    def __init__(self, file):
        self.file = file

def entrance_rando():
    settings = get_settings()
    seed = settings['seed']
    print("ENTRANCE RANDO!")
    for file in insensitive_glob(settings['paths']['warps']+'/*'):
        notice(file)
