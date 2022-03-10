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
    OTHER = 5


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
    def __init__(self, name, type):
        self.warps = []
        self.name = name
        self.type = type
        self.x = None
        self.y = None
        self.conns_in = 0

    def append(self, warp):
        self.warps.append(warp)
        if warp.toMap not in maps:
            maps[warp.toMap] = Map(warp.toMap, MapTypes.UNKNOWN)

    def __repr__(self):
        return repr((self.name, self.type, self.x, self.y, len(self.warps), self.conns_in))

    def estimate_position(self, fromWarp, fromMap):
        if fromMap.x is None:
            return
        if fromMap.type == MapTypes.DUNGEON and self.type != MapTypes.DUNGEON:
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
        self.conns_in += 1

def estimate_positions(location_anchors):
    warps = {}
    for a in location_anchors:
        m = maps[a['map']]
        m.x = a['x']
        m.y = a['y']
        # init the warps to crawl starting from our anchors
        for w in m.warps:
            if w not in warps:
                warps[w] = 1
                maps[w.toMap].estimate_position(w, maps[w.map])

    # crawl and build the tree of warps
    new_warps = {}
    while 1:
        num_warps = len(warps)
        for f in warps.keys():
            for w in maps[f.toMap].warps:
                if w not in warps and w not in new_warps:
                    new_warps[w] = 1
                    maps[w.toMap].estimate_position(w, maps[w.map])
        if len(new_warps) == 0:
            break
        warps.update(new_warps)
        new_warps = {}

    for map in maps:
            m = maps[map]
            if m.x is None and m.type == MapTypes.CITY and len(m.warps) > 0:
                notice("map missing position:" + map)


def add_warp(w, type):
    m = None
    if w.map not in maps:
        m = maps[w.map] = Map(w.map, type)
    elif maps[w.map].type != type and type != MapTypes.OTHER:
        m = maps[w.map]
        oldtype = m
        if m.type == MapTypes.OTHER:
            m.type = type
    else:
        m = maps[w.map]

    m.append(w)
    debug(w)

def new_warp(statement, folder):
    type = MapTypes.UNKNOWN
    if folder == 'cities':
        type = MapTypes.CITY
    elif folder == 'fields':
        type = MapTypes.FIELD
    elif folder == 'dungeons':
        type = MapTypes.DUNGEON
    elif folder == 'other' or folder == 'warps':
        type = MapTypes.OTHER
    else:
        notice("unknown map type: "+folder)

    w = Warp(statement)
    add_warp(w, type)

class MapScript():
    # approximate location? list of the warps in this map? a desired danger rating?
    def __init__(self, file):
        notice(file)
        self.file = file
        path = list(Path(file).parts)
        self.name = path[-1]
        self.folder = path[-2]
        debug(self.__dict__)
        if self.folder == 'other' or self.folder == 'warps':
            return
        self.script = ROScript(file)
        for s in self.script.root:
            if s.type in ['warp','warp2']:
                new_warp(s, self.folder)

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

    estimate_positions(settings['location_anchors'])
    for m in maps.values():
        if m.type == MapTypes.CITY:
            debug(m)

    notice(world_to_string())

    # now mark each area with their closest city, to group them into biomes?
    # shuffle the areas of each biome slightly, mostly just to change the location of the city
    # or shuffle them completely by detaching everything and attaching everything starting with the city
    # then connect the biomes to each other randomly
    # then mark the desired danger ratings for the lowbie routes for travelling between cities
    # mark higher danger ratings away from the lowbie routes and for dungeons


def write_on_world_string(arr, str, pos, off, scale):
    x = (pos[0] + off[0]) * scale[0]
    x = int(x)
    y = (pos[1] + off[1]) * scale[1]
    y = int(y)
    s = str[0:4]
    if len(str) > len(s):
        notice(s+' == '+str)
    if len(s) >= 3:
        x -= 1

    for c in s:
        if y >= len(arr) or x >= len(arr[y]):
            printError('{}: {}, {}'.format(s, y, x))
        else:
            arr[y][x] = ord(c)
        x += 1
    return (x, y)


def world_to_string():
    # make a 2D array of characters
    # settings for width and height scaling
    width = 80
    height = 70
    tarr = bytearray(width)
    for i in range(width):
        tarr[i] = ord(' ')
    arr = []
    for i in range(height):
        arr.append(tarr.copy())

    (minx, miny, maxx, maxy) = (0,0,0,0)
    for m in maps.values():
        if m.x is not None:
            minx = min(m.x, minx)
            miny = min(m.y, miny)
            maxx = max(m.x, maxx)
            maxy = max(m.y, maxy)
            for w in m.warps:
                x = m.x + w.fromX
                y = m.y + w.fromY
                minx = min(x, minx)
                miny = min(y, miny)
                maxx = max(x, maxx)
                maxy = max(y, maxy)

    # width-3 because we want to show city names
    scalex = (width-3) / (maxx - minx)
    scaley = (height-1) / (maxy - miny)
    # y axis is upside-down
    scaley *= -1
    scale = (scalex, scaley)
    off = (-minx, miny)

    # first write a character to each spot where an area is, indicating danger rating
    # then write . for each teleporter
    for m in maps.values():
        if m.x is not None:
            for w in m.warps:
                write_on_world_string(arr, '.', (m.x+w.fromX, m.y+w.fromY), off, scale)

    # then write city names (in all caps to differentiate?)
    for m in maps.values():
        if m.type == MapTypes.CITY and m.x is not None:
            write_on_world_string(arr, m.name.upper(), (m.x, m.y), off, scale)

    ret = "minx: {}, miny: {}, maxx: {}, maxy: {}".format(minx, miny, maxx, maxy)
    for i in range(height):
        ret += '\n' + arr[i].decode('ascii')
    return ret


def get_num_warps_on_side(m, offset):
    cmpX = clamp(offset[0], -1, 1)
    cmpY = clamp(offset[1], -1, 1)
    num = 0
    for w in m.warps:
        if w.fromX * cmpX >= 0 and w.fromY * cmpY >= 0:
            num += 1
    debug("get_num_warps_on_side(" + m.name + ", " + repr(offset) + "): "+str(num)+" / "+str(len(m.warps)))
    return num


def maps_can_connect(m1, m2, offset):
    if len(m1.warps) < 1 or len(m2.warps) < 1:
        return False

    num1 = get_num_warps_on_side(m1, offset)
    num2 = get_num_warps_on_side(m2, tuple(i * -1 for i in offset))

    if num1 > 0 and num2 > 0:
        return True

    return False
