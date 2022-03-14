import ro_randomizer.base
from ro_randomizer.base import *
from ro_randomizer.script import *
from ro_randomizer.map import *

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
    ro_randomizer.base.maps = {}
    ro_randomizer.base.map_sizes = {}

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
        m.original_position = m.position
        if m.position is None and m.type == MapTypes.CITY and len(m.warps) > 0:
            notice("map missing position:" + m.name + ', ' + repr(m))
        elif m.type == MapTypes.CITY:
            debug(m)

    notice(maps['morocc'])
    debug(world_to_string())

    # now mark each area with their closest city, to group them into biomes?
    set_closest_cities()

    shuffle_world(seed)
    info(world_to_string())
    # TODO:
    # mark the desired danger ratings for the lowbie routes for travelling between cities
    #   these don't need to be optimal routes between cities
    #   lowbies don't really need to be able to reach every city easily
    #   maybe only need to test that every starting city has 1 reachable lowbie leveling zone?
    # mark higher danger ratings away from the lowbie routes and for dungeons


def shuffle_world(seed):
    i = 0
    good = False
    while not good:
        if i > 1000:
            raise Exception('shuffle_world('+str(seed)+') failed at '+str(i)+' attempts')
        printHeader('shuffle_world: ' + str(seed) + ', attempt: ' + str(i) + '...')
        good = try_shuffle_world(seed, i)
        i += 1
    info('shuffle_world('+str(seed)+') took '+str(i)+' attempts')

    return i


def shuffle_biome(city, seed):
    areas = []
    for m in maps.values():
        # what about areas that have 0 warps out, but 1 or more warps in?
        if m.closest_city == city.name and len(m.warps) > 0 and m.original_position is not None:
            areas.append(m)
    info('starting shuffle_biome('+repr(city)+', '+str(seed)+') len(areas): '+str(len(areas)) + '...')
    if len(areas) == 0:
        printError('shuffle_biome found 0 areas!')
        return 1
    i = 0
    good = False
    while not good:
        if i > 100000:
            warning('shuffle_biome('+repr(city)+', '+str(seed)+') failed at '+str(i)+' attempts')
            return None
        good = try_shuffle_areas(random.Random(seed + i), areas)
        i += 1

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
        good = 0
        for move in moves:
            tspot = spot.add(move)
            if not m.ContainsPoint(tspot):
                continue

            other = m[tspot.x][tspot.y]
            if other is None:
                continue

            (can_connect, num1, num2) = maps_can_connect(other, map, move)
            if not can_connect:
                good = 0
                break
            good += 1
        if good > 0:
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

    # erase the warps (excluding warps to areas that have no warps of their own?)
    for map in areas:
        map.position = None
        for w in map.warps:
            if maps[w.map].conns_in > 0:
                w.toMap = None

    trace('try_shuffle_areas matrix:')
    trace(m)
    # write the warps
    for x in range(width):
        for y in range(height):
            map1 = m[x][y]
            if map1 is None:
                continue
            # loop through cardinal moves first and then the corners
            for move in (moves + corners):
                spot = IntPoint(x + move.x, y + move.y)
                if not m.ContainsPoint(spot):
                    continue
                map2 = m[spot.x][spot.y]
                if map2 is None:
                    continue
                # If I want to make it more lenient, I can make it do a single connection for each pair of maps before going back and doing the rest
                # so call connect_maps_single (or a parameter of 1 for max connections)
                # then do the loop again with regular connect_maps to fill in the rest
                # maybe the lists of warps should be shuffled too?
                linked = connect_maps(m, map1, map2, move, spot)
            linked = 0
            for w in map1.warps:
                if w.toMap is not None:
                    linked += 1
            if linked == 0:
                return False

    # ensure can navigate from all/most areas to the city
    estimate_positions([{'map': m[center.x][center.y].name, 'x': 0, 'y': 0}])
    for map in areas:
        if map.type == MapTypes.CITY and map.position is None:
            return False
        map.position = None
    return True


def connect_maps(m, map1, map2, move, spot):
    warps1 = map1.get_warps_on_side(move.negative())
    warps2 = map2.get_warps_on_side(move)
    offset = move.multiply(map1.size)
    linked = 0
    # for each warps1, find the nearest available warps2 and link them
    trace('connect_maps('+repr(map1)+', '+repr(map2)+') warps1: '+str(len(warps1))+', warps2: '+str(len(warps2)))
    for w1 in warps1:
        if w1.toMap is not None:
            continue
        closest = None
        for w2 in warps2:
            if w2.toMap is not None:
                continue
            # adjust w2pos by move or spot, and compare it to w1.fromPos
            w2pos = w2.fromPos.add(offset)
            closest = w1.fromPos.closest(w2pos, w2, closest)
        # make the link
        if closest:
            w2 = closest[0]
            w1.toMap = w2.map
            w1.toPos = w2.fromPos
            w2.toMap = w1.map
            w2.toPos = w1.fromPos
            linked += 1
            trace('connect_maps linked '+repr(w1)+', '+repr(w2))
    return linked


def try_shuffle_world(seed, attempt):
    for c in maps.values():
        if c.type != MapTypes.CITY or c.closest_city != c.name or c.original_position is None:
            continue
        if not shuffle_biome(c, seed + attempt * 1000007):
            return False

    # now connect the biomes together
    # ensure all (or most?) cities can be reached from any other city
    # probably just estimate_positions and then ensure their position is not None unless their original_position is None
    for m in maps.values():
        m.position = None
    estimate_positions(get_settings()['location_anchors'])
    #for map in maps.values():
    #    if map.type == MapTypes.CITY and map.position is None and map.original_position is not None:
    #        return False
    return True
