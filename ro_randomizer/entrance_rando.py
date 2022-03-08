from ro_randomizer.base import *
from ro_randomizer.script import *

# https://github.com/rathena/rathena/blob/master/doc/script_commands.txt#L210-L229
# <from mapname>,<fromX>,<fromY>,<facing>%TAB%warp%TAB%<warp name>%TAB%<spanx>,<spany>,<to mapname>,<toX>,<toY>
# <from mapname>,<fromX>,<fromY>,<facing>%TAB%warp2%TAB%<warp name>%TAB%<spanx>,<spany>,<to mapname>,<toX>,<toY>
# Unlike 'warp', 'warp2' will also be triggered by hidden player.

# randomize the world layout, ensure the paths make some sense
# then choose the expected routes for lowbies to take between cities, and set their desired danger ratings accordingly
# then for the other areas that aren't needed for the lowbie paths, we can give them higher danger ratings

# for cities we'll probably want to remember which warps go to outdoor areas and which go to indoor areas

class MapTypes(Enum):
    UNKNOWN = 0
    FIELD = 1
    CITY = 2
    DUNGEON = 3
    INDOORS = 4


maps = {}
class Warp():
    def __init__(self, s):
        self.statement = s
        self.map = s.args[0][0]
        self.fromX = int(s.args[0][1])
        self.fromY = int(s.args[0][2])
        self.facing = int(s.args[0][3])
        self.warpname = s.args[2][0]
        self.spanX = int(s.args[3][0])
        self.spanY = int(s.args[3][1])
        self.toMap = s.args[3][2]
        self.toX = int(s.args[3][3])
        self.toY = int(s.args[3][4])
    
    def __repr__(self):
        return self.map + " -> " + self.toMap


class Map():
    def __init__(self, name):
        self.warps = []
        self.name = name
        self.type = MapTypes.UNKNOWN
        self.x = None
        self.y = None
    
    def append(self, warp):
        self.warps.append(warp)
        if warp.toMap not in maps:
            maps[warp.toMap] = Map(warp.toMap)

    def __repr__(self):
        return repr((self.name, self.type, self.x, self.y, len(self.warps)))
    
    def estimate_position(self, fromWarp, fromMap):
        if fromMap.x is None:
            return
        x = fromMap.x + fromWarp.fromX
        x -= fromWarp.toX
        y = fromMap.y + fromWarp.fromY
        y -= fromWarp.toY
        if self.x is None:
            self.x = x
            self.y = y
        else:
            self.x = (self.x + x) / 2
            self.y = (self.y + y) / 2

def estimate_positions():
    num_none = len(maps)
    # init the first map to position 0
    maps['prontera'].x = 0
    maps['prontera'].y = 0
    
    # crawl the list
    for i in range(1,100):
        num_none = 0
        maps['prontera'].x = 0
        maps['prontera'].y = 0
        for map in maps:
            m = maps[map]
            if m.x is None:
                num_none += 1
                continue
            for w in m.warps:
                maps[w.toMap].estimate_position(w, m)
    
    for map in maps:
            m = maps[map]
            if m.x is None:
                notice("map missing position:" + map)

class MapScript():
    # approximate location? list of the warps in this map? a desired danger rating?
    def __init__(self, file):
        notice(file)
        self.file = file
        path = list(Path(file).parts)
        self.name = path[-1]
        self.folder = path[-2]
        debug(self.__dict__)
        self.script = ROScript(file)
        for s in self.script.root:
            if s.type in ['warp','warp2']:
                w = Warp(s)
                if w.map not in maps:
                    maps[w.map] = Map(w.map)
                maps[w.map].append(w)
                debug(s)
    
    def read_file(self):
        self.content = None
        with open(self.file) as f:
            self.content = f.read()
        self.warps = []
        code = parse_script(self.content)
        # warps from script triggers will be changed along with the normal teleporters to the same map
        # need to identify which maps are only reachable from script triggers
        #debug(json.dumps(code, indent=1))
        for t in code:
            if len(t) > 1 and type(t[1]) == str:
                if t[1] in ['warp', 'warp2']:
                    self.warps.append(t)
                    notice(t[2])
        debug(self.warps)
        notice(self.name + " warps: " + str(len(self.warps)))


def entrance_rando():
    settings = get_settings()
    seed = settings['seed']
    printHeader("ENTRANCE RANDO!")
    for input in settings['inputs']['warps']:
        for file in insensitive_glob(input+'/*'):
            if file.endswith('.txt'):
                ms = MapScript(file)
    
    estimate_positions()
    notice(maps['prontera']) # center
    notice(maps['payon']) # SE
    notice(maps['alberta']) # more SE
    notice(maps['morocc']) # SW
    notice(maps['geffen']) # W and slightly N
    notice(maps['aldebaran']) # N
