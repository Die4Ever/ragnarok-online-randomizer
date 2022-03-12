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

def entrance_rando():
    global maps
    global map_sizes
    settings = get_settings()
    seed = settings['seed']
    maps = {}
    map_sizes = {}

    printHeader("ENTRANCE RANDO!")

    for input in settings['inputs']['gat']:
        for file in insensitive_glob(input+'/*'):
            if file.endswith('.gat'):
                read_gat_file(file)

    for input in settings['inputs']['warps']:
        for file in insensitive_glob(input+'/*'):
            if file.endswith('.txt'):
                ms = MapScript(file)

    estimate_positions(settings['location_anchors'])
    for m in maps.values():
        if m.type == MapTypes.CITY:
            debug(m)

    notice(maps['morocc'])
    debug(world_to_string())

    # now mark each area with their closest city, to group them into biomes?
    set_closest_cities()

    shuffle_world(seed)

    # TODO:
    # mark the desired danger ratings for the lowbie routes for travelling between cities
    #   these don't need to be optimal routes between cities
    #   lowbies don't really need to be able to reach every city easily
    #   maybe only need to test that every starting city has 1 reachable lowbie leveling zone?
    # mark higher danger ratings away from the lowbie routes and for dungeons


class MapTypes(Enum):
    UNKNOWN = 0
    FIELD = 1
    CITY = 2
    DUNGEON = 3
    INDOORS = 4
    OTHER = 5


map_sizes = {}
maps = {}
class Warp():
    def __init__(self, s):
        self.statement = s
        self.map = s.args[0][0]
        self.fromPos = IntPoint(s.args[0][1], s.args[0][2])
        self.facing = int(s.args[0][3])
        self.warpname = s.args[2][0]
        self.span = IntPoint(s.args[3][0], s.args[3][1])
        self.toMap = s.args[3][2]
        self.toPos = IntPoint(s.args[3][3], s.args[3][4])

    def __repr__(self):
        return self.map + " -> " + self.toMap


class Map():
    def __init__(self, name, type):
        self.warps = []
        self.name = name
        self.type = type
        self.position = None
        self.conns_in = 0
        self.closest_city = None
        try:
            self.size = map_sizes[name]
        except Exception as e:
            warning('Map __init__ ' +repr(e)+' using default size of (64, 64)')
            self.size = IntPoint(64, 64)

    def append(self, warp):
        self.warps.append(warp)
        self.size.maximize(warp.fromPos)
        if warp.toMap not in maps:
            maps[warp.toMap] = Map(warp.toMap, MapTypes.UNKNOWN)

    def __repr__(self):
        return self.name + '('+self.type.name+') ' + repr(self.position) + ', ' + str(self.size) + ', ' + str(len(self.warps)) + ' warps out, ' + str(self.conns_in) + ' warps in'

    def estimate_position(self, fromWarp, fromMap):
        self.conns_in += 1
        self.size.maximize(fromWarp.toPos)
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

def estimate_positions(location_anchors):
    warps = {}
    for a in location_anchors:
        if a['map'] not in maps:
            warning('location_anchor '+a['map']+' not found')
            continue
        m = maps[a['map']]
        m.position = Point(a['x'], a['y'])
        # init the warps to crawl starting from our anchors
        for w in m.warps:
            if w not in warps:
                warps[w] = 1
                maps[w.toMap].estimate_position(w, maps[w.map])

    # crawl and build the tree of warps
    new_warps = {}
    while True:
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


def set_closest_cities():
    for m in maps.values():
        if m.type == MapTypes.CITY:
            m.closest_city = m.name
            continue
        if m.position is None:
            continue
        closest_city = None
        closest_dist = 999999
        for c in maps.values():
            if c.type != MapTypes.CITY or c.position is None:
                continue
            dist = m.position.dist(c.position)
            if dist < closest_dist:
                closest_dist = dist
                closest_city = c.name
        if closest_city is not None:
            m.closest_city = closest_city


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


def read_gat_file(name):
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
        warning(str(e))


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
        if y >= len(arr) or x >= len(arr[y]) or x < 0 or y < 0:
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
    minp = Point(0,0)
    maxp = Point(0,0)
    for m in maps.values():
        if m.position is not None:
            minp.minimize(m.position)
            maxp.maximize(m.position)
            for w in m.warps:
                p = Point(m.position.x + w.fromPos.x, m.position.y + w.fromPos.y)
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
                pos = Point(m.position.x+w.fromPos.x, m.position.y+w.fromPos.y)
                write_on_world_string(arr, '.', pos, off, scale)

    # then write city names (in all caps to differentiate?)
    for m in maps.values():
        if m.type == MapTypes.CITY and m.position is not None:
            write_on_world_string(arr, m.name.upper(), m.position, off, scale)

    ret = "minx: {}, miny: {}, maxx: {}, maxy: {}".format(minp.x, minp.y, maxp.x, maxp.y)
    # y axis is upside-down
    for i in reversed(range(height)):
        ret += '\n' + arr[i].decode('ascii')
    return ret


def get_num_warps_on_side(m, offset):
    cmpX = clamp(offset.x, -1, 1)
    cmpY = clamp(offset.y, -1, 1)
    center = IntPoint(m.size.x / 2, m.size.y / 2)
    num = 0
    for w in m.warps:
        if (w.fromPos.x - center.x) * cmpX >= 0 and (w.fromPos.y - center.y) * cmpY >= 0:
            num += 1
    if num == 0:
        trace("get_num_warps_on_side(" + m.name + ", " + repr(offset) + "): "+str(num)+" / "+str(len(m.warps)))
    return num


def maps_can_connect(m1, m2, offset):
    if len(m1.warps) < 1 or len(m2.warps) < 1:
        warning('maps_can_connect failed, len('+m1.name+'.warps): ' + str(len(m1.warps)) + ', len('+m2.name+'.warps): ' + str(len(m2.warps)) )

    num1 = get_num_warps_on_side(m1, offset)
    offset2 = Point(-offset.x, -offset.y)
    num2 = get_num_warps_on_side(m2, offset2)

    if num1 > 0 and num2 > 0:
        return (True, num1, num2)

    return (False, num1, num2)


def shuffle_world(seed):
    i = 0
    good = False
    while not good:
        printHeader('shuffle_world: ' + str(seed) + ', attempt: ' + str(i) + '...')
        good = try_shuffle_world(seed, i)
        i += 1
        if i > 1000:
            raise Exception('shuffle_world('+str(seed)+') failed at '+str(i)+' attempts')
    debug('shuffle_world('+str(seed)+') took '+str(i)+' attempts')
    return i


def shuffle_biome(city, seed):
    areas = []
    for m in maps.values():
        # what about areas that have 0 warps out, but 1 or more warps in?
        if m.closest_city == city.name and len(m.warps) > 0:
            areas.append(m)
    info('starting shuffle_biome('+repr(city)+', '+str(seed)+') len(areas): '+str(len(areas)) + '...')
    i = 0
    good = False
    while not good:
        good = try_shuffle_areas(random.Random(seed + i), areas)
        i += 1
        if i > 100000:
            warning('shuffle_biome('+repr(city)+', '+str(seed)+') failed at '+str(i)+' attempts')
            return False

    if i > 1000:
        warning('shuffle_biome('+repr(city)+', '+str(seed)+') took '+str(i)+' attempts')
    else:
        debug('shuffle_biome('+repr(city)+', '+str(seed)+') took '+str(i)+' attempts')
    return i


moves = (IntPoint(-1,0), IntPoint(0,-1), IntPoint(1,0), IntPoint(0,1))
corners = (IntPoint(-1,-1), IntPoint(-1,1), IntPoint(1,-1), IntPoint(1,1))
def get_map_for_spot(areas, m, spot):
    # TODO: how to handle corner teleporters? we can check the num1 and num2 returned from maps_can_connect and score them up?
    for map in areas:
        good = True
        for move in moves:
            tspot = IntPoint(spot.x + move.x, spot.y + move.y)
            if not m.ContainsPoint(tspot):
                continue

            other = m[tspot.x][tspot.y]
            if other is None:
                continue

            (can_connect, num1, num2) = maps_can_connect(other, map, move)
            if not can_connect:
                good = False
                break
        if good:
            return map
    return None


def try_shuffle_areas(rand, areas):
    # we shuffle the array and put it into a 2D array
    shuffled_areas = rand.sample(areas, k=len(areas))
    width = len(shuffled_areas)
    height = len(shuffled_areas)
    m = Matrix(width, height)

    center = IntPoint(width/2, height/2)
    m[center.x][center.y] = shuffled_areas.pop(0)
    attempts = 0

    while len(shuffled_areas):
        # find a spot to place the next piece
        attempts += 1
        if attempts > 1000:
            warning('try_shuffle_areas failed at '+str(attempts)+' attempts, '+str(len(shuffled_areas)) + '/' + str(len(areas)))
            return False
        spot = center.copy()
        while True:
            move = rand.choice(moves)
            spot.x += move.x
            spot.y += move.y
            if not m.ContainsPoint(spot):
                spot = center.copy()
                continue
            if m[spot.x][spot.y] is None:
                break

        # find a map to put in the spot
        map = get_map_for_spot(shuffled_areas, m, spot)
        if map is None:
            trace('try_shuffle_areas failed, '+str(len(shuffled_areas)) + '/' + str(len(areas)) )
            continue
        shuffled_areas.remove(map)
        m[spot.x][spot.y] = map

    # TODO:
    # ensure can navigate from all/most areas to the city?
    # write the warps
    return True


def try_shuffle_world(seed, attempt):
    for c in maps.values():
        if c.type != MapTypes.CITY:
            continue
        if not shuffle_biome(c, seed + attempt * 10000):
            return False

    # ensure all (or most?) cities can be reached from any other city
    return True
