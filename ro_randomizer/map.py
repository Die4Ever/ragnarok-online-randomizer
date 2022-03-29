from ro_randomizer.base import *
from ro_randomizer.script import *

class MapTypes(Enum):
    UNKNOWN = 0
    FIELD = 1
    CITY = 2
    DUNGEON = 3
    INDOORS = 4
    OTHER = 5
    IGNORE = 6


class Warp():
    def __init__(self, s):
        self.statements = [s]
        self.map = s.args[0][0]
        self.fromPos = IntPoint(s.args[0][1], s.args[0][2])
        self.facing = int(s.args[0][3])
        self.warpname = s.args[2][0]
        self.span = IntPoint(s.args[3][0], s.args[3][1])
        self.toMap = s.args[3][2]
        self.toPos = IntPoint(s.args[3][3], s.args[3][4])
        self.inPos = None

    def setDefaultInPos(self, map):
        center = map.size.multiply_scalar(0.5)
        offset = self.fromPos.subtract(center).multiply_scalar(10)
        offset.clamp(IntPoint(-4, -4), IntPoint(4, 4))
        self.inPos = self.fromPos.subtract(offset)
        info('setDefaultInPos', self, self.inPos)

    def __repr__(self):
        to = self.toMap
        if not to:
            to = 'None'
        else:
            to += ' ' + str(self.toPos)
        return self.map + ' ' + str(self.fromPos) + ' -> ' + to + ' ('+self.statements[0].args[3][2]+')'


class Map():
    def __init__(self, name, type):
        global map_sizes
        self.warps = []
        self.name = name
        self.type = type
        if name.endswith('_in'):
            self.type = MapTypes.INDOORS

        ignore_maps = get_settings()['ignore_maps']
        if name in ignore_maps:
            self.type = MapTypes.IGNORE

        self.position = None
        self.conns_in = 0
        self.closest_city = None
        try:
            self.size = map_sizes[name]
        except Exception as e:
            self.size = IntPoint(64, 64)
            warning('Map __init__', e, 'using default size of', self.size)

    def append(self, warp):
        global maps
        for w in self.warps:
            if w.fromPos == warp.fromPos:
                if w.toMap != warp.toMap:
                    printError(w, '\nfalse dupe\n', warp)
                    raise Exception('false dupe')
                w.statements.extend(warp.statements)
                return
        self.warps.append(warp)
        self.size.maximize(warp.fromPos)
        if warp.toMap not in maps:
            maps[warp.toMap] = Map(warp.toMap, MapTypes.UNKNOWN)

    def __repr__(self):
        return self.name + '('+self.type.name+') ' + repr(self.position) + ', ' + str(self.size) + ', ' + str(len(self.warps)) + ' warps out, ' + str(self.conns_in) + ' warps in'

    def __str__(self):
        return self.name

    def get_warps_on_side(self, offset):
        # TODO: exclude warps to maps that don't have any warps of their own? but how will that work when I've set toMap to None?
        cmpX = clamp(offset.x, -1, 1)
        cmpY = clamp(offset.y, -1, 1)
        center = IntPoint(self.size.x / 2, self.size.y / 2)
        warps = []
        for w in self.warps:
            if (w.fromPos.x - center.x - cmpX) * cmpX >= 0 and (w.fromPos.y - center.y - cmpY) * cmpY >= 0:
                warps.append(w)
        if len(warps) == 0:
            trace("get_num_warps_on_side(", self.name, ", ", offset, "): 0 / ", len(self.warps))
        return warps

    def estimate_position(self, fromWarp, fromMap):
        self.conns_in += 1
        self.size.maximize(fromWarp.toPos)
        if fromMap.position is None:
            return
        if fromMap.type == MapTypes.DUNGEON and self.type != MapTypes.DUNGEON:
            return

        position = fromMap.position.add(fromWarp.fromPos).subtract(fromWarp.toPos)
        assert type(position) != IntPoint

        if self.position is None:
            self.position = position
        else:
            self.position = self.position.add(position).multiply_scalar(0.5)

    def estimate_warp_offsets(self, fromWarp):
        for w in self.warps:
            if w.toMap != fromWarp.map:
                continue
            if w.fromPos.dist(fromWarp.toPos) > 12:
                continue
            offset = w.fromPos.subtract(fromWarp.toPos)
            newInPos = w.fromPos.subtract(offset)
            if w.inPos is None:
                w.inPos = newInPos
            else:
                w.inPos = w.inPos.add(newInPos).multiply_scalar(0.5)



def estimate_positions(location_anchors):
    global maps
    warps = {}
    for a in location_anchors:
        if a['map'] not in maps:
            warning('location_anchor', a['map'], 'not found')
            continue
        m = maps[a['map']]
        m.position = Point(a['x'], a['y'])
        # init the warps to crawl starting from our anchors
        for w in m.warps:
            if w not in warps and w.toMap is not None:
                warps[w] = 1
                maps[w.toMap].estimate_position(w, maps[w.map])

    # crawl and build the tree of warps
    new_warps = {}
    while True:
        num_warps = len(warps)
        for f in warps.keys():
            for w in maps[f.toMap].warps:
                if w not in warps and w not in new_warps and w.toMap is not None:
                    new_warps[w] = 1
                    maps[w.toMap].estimate_position(w, maps[w.map])
        if len(new_warps) == 0:
            break
        warps.update(new_warps)
        new_warps = {}


def estimate_warp_offsets():
    global maps
    for m in maps.values():
        for w in m.warps:
            to = maps.get(w.toMap)
            if to:
                to.estimate_warp_offsets(w)
    for m in maps.values():
        for w in m.warps:
            if w.inPos is None:
                w.setDefaultInPos(m)


def set_closest_cities():
    global maps
    for m in maps.values():
        if m.type == MapTypes.CITY:
            m.closest_city = m.name
            continue
        if m.position is None:
            continue
        closest = None
        for c in maps.values():
            if c.type != MapTypes.CITY or c.position is None:
                continue
            closest = m.position.closest(c.position, c.name, closest)
        if closest is not None:
            m.closest_city = closest[0]


def add_warp(w, type):
    global maps
    m = None
    if w.map not in maps:
        m = maps[w.map] = Map(w.map, type)
    else:
        m = maps[w.map]
        if m.type == MapTypes.OTHER and type != MapTypes.OTHER:
            m.type = type

    m.append(w)
    debug('added warp:', w)


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
        self.script = ROScript(file)
        if self.folder == 'other' or self.folder == 'warps':
            return
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
        info(self.name, "warps:", len(self.warps))


def read_gat_file(name):
    global map_sizes
    try:
        with open(name, mode='rb') as file:
            data = file.read(14)
            (GRAT, version, width, height) = struct.unpack("<4sHII", data)
            assert GRAT == b"GRAT"
        assert width <= 512
        assert height <= 512
        path = list(Path(name).parts)
        mapname = path[-1].replace('.gat', '')
        size = IntPoint(width, height)
        map_sizes[mapname] = size
    except Exception as e:
        warning(e)


def write_on_world_string(arr, str, pos, off, scale):
    t = pos.add(off).multiply(scale)
    x = int(t.x)
    y = int(t.y)
    s = str[0:4]
    if len(str) > len(s):
        debug(s+' == '+str)
    if len(s) >= 3 and x > 0:
        x -= 1

    for c in s:
        if y >= len(arr) or x >= len(arr[y]) or x < 0 or y < 0:
            printError('{}: {}, {}'.format(s, y, x))
        else:
            arr[y][x] = ord(c)
        x += 1
    return (x, y)


def world_to_string(width=80, height=50):
    global maps
    # make a 2D array of characters
    # settings for width and height scaling
    tarr = bytearray(width)
    for i in range(width):
        tarr[i] = ord(' ')
    arr = []
    for i in range(height):
        arr.append(tarr.copy())

    (minx, miny, maxx, maxy) = (0,0,0,0)
    minp = Point(0,0)
    maxp = Point(0,0)
    for m in maps.values():
        if m.position is not None:
            minp.minimize(m.position)
            maxp.maximize(m.position.add(m.size))
            for w in m.warps:
                p = m.position.add(w.fromPos)
                minp.minimize(p)
                maxp.maximize(p)

    # width-3 because we want to show city names
    scalex = (width-3) / (maxp.x - minp.x)
    scaley = (height-1) / (maxp.y - minp.y)
    scale = Point(scalex, scaley)
    off = Point(-minp.x, -minp.y)

    # first write a character to each spot where an area is, indicating danger rating
    # then write . for each teleporter
    for m in maps.values():
        if m.position is not None:
            for w in m.warps:
                if w.toMap is not None:
                    pos = m.position.add(w.fromPos)
                    write_on_world_string(arr, '.', pos, off, scale)

    # then write city names (in all caps to differentiate?)
    for m in maps.values():
        if m.type == MapTypes.CITY and m.position is not None:
            center = m.position.add(m.size.multiply_scalar(0.5))
            write_on_world_string(arr, m.name.upper(), center, off, scale)

    ret = "minx: {}, miny: {}, maxx: {}, maxy: {}".format(minp.x, minp.y, maxp.x, maxp.y)
    # y axis is upside-down
    for i in reversed(range(height)):
        ret += '\n' + arr[i].decode('ascii')
    return ret
