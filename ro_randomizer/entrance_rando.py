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
        self.fromPos = Point(int(s.args[0][1]), int(s.args[0][2]))
        self.facing = int(s.args[0][3])
        self.warpname = s.args[2][0]
        self.span = Point(int(s.args[3][0]), int(s.args[3][1]))
        self.toMap = s.args[3][2]
        self.toPos = Point(int(s.args[3][3]), int(s.args[3][4]))

    def __repr__(self):
        return self.map + " -> " + self.toMap


class Map():
    def __init__(self, name, type):
        self.warps = []
        self.name = name
        self.type = type
        self.position = None
        self.conns_in = 0

    def append(self, warp):
        self.warps.append(warp)
        if warp.toMap not in maps:
            maps[warp.toMap] = Map(warp.toMap, MapTypes.UNKNOWN)

    def __repr__(self):
        return self.name + "("+self.type.name+") " + repr(self.position) + ", " + str(len(self.warps)) + " warps out, " + str(self.conns_in) + " warps in"

    def estimate_position(self, fromWarp, fromMap):
        if fromMap.position is None:
            return
        if fromMap.type == MapTypes.DUNGEON and self.type != MapTypes.DUNGEON:
            return
        x = fromMap.position.x + fromWarp.fromPos.x
        x -= fromWarp.toPos.x
        y = fromMap.position.y + fromWarp.fromPos.y
        y -= fromWarp.toPos.y
        if self.position is None:
            self.position = Point(x, y)
        else:
            self.position.x = (self.position.x + x) / 2
            self.position.y = (self.position.y + y) / 2
        self.conns_in += 1

def estimate_positions(location_anchors):
    warps = {}
    for a in location_anchors:
        m = maps[a['map']]
        m.position = Point(a['x'], a['y'])
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
            if m.position is None and m.type == MapTypes.CITY and len(m.warps) > 0:
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
    debug('added warp: ' + repr(w))

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
        info(file)
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
        trace(json.dumps(code, indent=1))
        for t in code:
            if len(t) > 1 and type(t[1]) == str:
                if t[1] in ['warp', 'warp2']:
                    self.warps.append(t)
                    debug(t[2])
        debug(self.warps)
        info(self.name + " warps: " + str(len(self.warps)))


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

    debug(world_to_string())

    # TODO:
    # now mark each area with their closest city, to group them into biomes? how will I keep the deserts of ex-morroc together?
    #   I can just do a hardcoded maps['morroc'].position = ...
    # shuffle the areas of each biome slightly, mostly just to change the location of the city
    # or shuffle them completely by detaching everything and attaching everything starting with the city
    # then connect the biomes to each other randomly
    # then mark the desired danger ratings for the lowbie routes for travelling between cities
    # mark higher danger ratings away from the lowbie routes and for dungeons


def write_on_world_string(arr, str, pos, off, scale):
    x = (pos.x + off.x) * scale.x
    x = int(x)
    y = (pos.y + off.y) * scale.y
    y = int(y)
    s = str[0:4]
    if len(str) > len(s):
        debug(s+' == '+str)
    if len(s) >= 3:
        x -= 1

    for c in s:
        if y >= len(arr) or x >= len(arr[y]):
            printError('{}: {}, {}'.format(s, y, x))
        else:
            arr[y][x] = ord(c)
        x += 1
    return (x, y)


def world_to_string(width=80, height=70):
    # make a 2D array of characters
    # settings for width and height scaling
    tarr = bytearray(width)
    for i in range(width):
        tarr[i] = ord(' ')
    arr = []
    for i in range(height):
        arr.append(tarr.copy())

    (minx, miny, maxx, maxy) = (0,0,0,0)
    for m in maps.values():
        if m.position is not None:
            minx = min(m.position.x, minx)
            miny = min(m.position.y, miny)
            maxx = max(m.position.x, maxx)
            maxy = max(m.position.y, maxy)
            for w in m.warps:
                x = m.position.x + w.fromPos.x
                y = m.position.y + w.fromPos.y
                minx = min(x, minx)
                miny = min(y, miny)
                maxx = max(x, maxx)
                maxy = max(y, maxy)

    # width-3 because we want to show city names
    scalex = (width-3) / (maxx - minx)
    scaley = (height-1) / (maxy - miny)
    # y axis is upside-down
    scaley *= -1
    scale = Point(scalex, scaley)
    off = Point(-minx, miny)

    # first write a character to each spot where an area is, indicating danger rating
    # then write . for each teleporter
    for m in maps.values():
        if m.position is not None:
            for w in m.warps:
                pos = Point(m.position.x+w.fromPos.x, m.position.y+w.fromPos.y)
                write_on_world_string(arr, '.', pos, off, scale)

    # then write city names (in all caps to differentiate?)
    for m in maps.values():
        if m.type == MapTypes.CITY and m.position is not None:
            write_on_world_string(arr, m.name.upper(), m.position, off, scale)

    ret = "minx: {}, miny: {}, maxx: {}, maxy: {}".format(minx, miny, maxx, maxy)
    for i in range(height):
        ret += '\n' + arr[i].decode('ascii')
    return ret


def get_num_warps_on_side(m, offset):
    cmpX = clamp(offset.x, -1, 1)
    cmpY = clamp(offset.y, -1, 1)
    num = 0
    for w in m.warps:
        if w.fromPos.x * cmpX >= 0 and w.fromPos.y * cmpY >= 0:
            num += 1
    debug("get_num_warps_on_side(" + m.name + ", " + repr(offset) + "): "+str(num)+" / "+str(len(m.warps)))
    return num


def maps_can_connect(m1, m2, offset):
    if len(m1.warps) < 1 or len(m2.warps) < 1:
        info('maps_can_connect failed, len(m1.warps): ' + str(len(m1.warps)) + ', len(m2.warps): ' + str(len(m2.warps)) )
        return False

    num1 = get_num_warps_on_side(m1, offset)
    offset2 = Point(-offset.x, -offset.y)
    num2 = get_num_warps_on_side(m2, offset2)

    if num1 > 0 and num2 > 0:
        return True

    return False
