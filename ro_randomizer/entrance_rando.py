import ro_randomizer.base
from ro_randomizer.base import *
from ro_randomizer.script import *
from ro_randomizer.map import *
import ro_randomizer.world_map_grids

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
    ro_randomizer.base.maps.clear()
    ro_randomizer.base.map_sizes.clear()
    map_scripts = {}

    printHeader("ENTRANCE RANDO!")

    with open('gat_cache.json') as f:
        gat_cache = json.load(f)
        for m in gat_cache.keys():
            s = gat_cache[m]
            map_sizes[m] = IntPoint(s['x'], s['y'])

    for input in settings['inputs']['gat']:
        try:
            for file in insensitive_glob(input+'/*'):
                if file.endswith('.gat'):
                    read_gat_file(file)
        except Exception as e:
            printError(e)

    for input in settings['inputs']['warps']:
        for file in insensitive_glob(input+'/*'):
            if file.endswith('.txt'):
                map_scripts[file] = MapScript(file)

    with open('gat_cache.json', 'w') as f:
        json.dump(map_sizes, f, default=lambda x:x.__dict__)

    estimate_warp_offsets()
    estimate_positions(settings['location_anchors'])
    for m in maps.values():
        m.original_position = m.position
        if m.position is None and m.type == MapTypes.CITY and len(m.warps) > 0:
            notice("map missing position:", m.name, ',', m)
        #elif m.type == MapTypes.CITY:
        #    debug(m)

    assertWarps(maps)

    #notice(maps['morocc'])
    debug(world_to_string())

    # now mark each area with their closest city, to group them into biomes?
    set_closest_cities()

    shuffle_world(seed)
    info(world_to_string())
    for w in maps['prontera'].warps:
        if w.toMap is None:
            info(w.warpname, w)
    write_warps(maps, map_scripts, settings['outputs']['warps'])
    # TODO:
    # mark the desired danger ratings for the lowbie routes for travelling between cities
    rng = random.Random(crc32('random_danger', seed))
    for m in maps.values():
        m.danger = rng.randint(1, 100)
    #   these don't need to be optimal routes between cities
    #   lowbies don't really need to be able to reach every city easily
    #   maybe only need to test that every starting city has 1 reachable lowbie leveling zone?
    # mark higher danger ratings away from the lowbie routes and for dungeons


def shuffle_world(seed):
    i = 0
    while True:
        if i > 1000:
            raise Exception('shuffle_world('+str(seed)+') failed at '+str(i)+' attempts')
        printHeader('shuffle_world:', seed, ', attempt:', i)
        if try_shuffle_world(seed, i):
            break
        i += 1
    info('shuffle_world(', seed, ') took', i, 'attempts')

    # TODO: tie up one-way connections where the other side has toMap is None?
    assertWarps(maps)

    return i


def shuffle_biome(city, seed):
    # build the areas that make up this biome
    areas = []
    for m in maps.values():
        # what about areas that have 0 warps out, but 1 or more warps in?
        if m.type == MapTypes.IGNORE or m.type == MapTypes.INDOORS:
            continue
        if m.closest_city == city.name and len(m.warps) > 0 and m.original_position is not None:
            areas.append(m)

    info('starting shuffle_biome(', city, ',', seed, ') len(areas):', len(areas))
    if len(areas) == 0:
        printError('shuffle_biome found 0 areas!')
        return (None, 0)
    i = 0
    grid = None
    while not grid:
        if i > 1000:
            warning('shuffle_biome(', city, ',', seed, ') failed at', i, 'attempts, original_position:', city.original_position, areas)
            return (None, i)
        grid = try_shuffle_areas(random.Random(crc32('shuffle_biome', seed, i)), areas)
        i += 1

    # success!
    if i > 1000:
        warning('shuffle_biome(', city, ',', seed, ') took', i, 'attempts')
    else:
        debug('shuffle_biome(', city, ',', seed, ') took', i, 'attempts')
    return (grid, i)


def try_shuffle_areas(rand, areas):
    # we shuffle the array and put it into a 2D array
    grid = ro_randomizer.world_map_grids.MapsGrid(rand, areas)
    if not grid.fill(rand):
        return None

    trace('try_shuffle_areas matrix:')
    trace(grid.grid)

    if not grid.finalize_connections():
        return None

    # ensure can navigate from all/most areas to the city
    estimate_positions([{'map': grid.grid[grid.center.x][grid.center.y].name, 'x': 0, 'y': 0}])
    for map in areas:
        #if map.type == MapTypes.CITY and map.position is None:
        if map.position is None and map.original_position is not None:
            return None
        map.position = None

    return grid


def try_connect_world(rand, biomes):
    grid = ro_randomizer.world_map_grids.WorldGrid(rand, biomes)
    if not grid.fill(rand):
        return None

    trace('try_connect_world matrix:')
    trace(grid.grid)

    if not grid.finalize_connections():
        return None

    # TODO: ensure can navigate from all/most areas to the city
    goods = 0
    bads = 0
    for m in maps.values():
        m.position = None
        for w in m.warps:
            if w.toMap is None:
                bads += 1
            else:
                goods += 1
    info('try_connect_world check warps goods:', goods, 'bads:', bads)
    if bads*10 > goods:
        return None

    # TODO: should try to fill in more warps here? or before the check?

    estimate_positions(get_settings()['location_anchors'])
    goods = 0
    bads = 0
    for m in maps.values():
        if m.original_position is None:
            continue
        if m.position is None:
            bads += 1
        else:
            goods += 1
    info('try_connect_world check map positions goods:', goods, 'bads:', bads)
    if bads*10 > goods:
        return None
    # for b in biomes:
    #     if map.type == MapTypes.CITY and map.position is None:
    #         grid.clear_connections()
    #         return None
    #     map.position = None

    return grid


def try_shuffle_world(seed, attempt):
    biomes = []
    for c in maps.values():
        if c.type != MapTypes.CITY or c.closest_city != c.name or c.original_position is None:
            continue
        (biome, attempts) = shuffle_biome(c, crc32('try_shuffle_world', seed, attempt))
        if not biome:
            return None
        biomes.append(biome)

    # now connect the biomes together
    info('connecting world together, biomes:', len(biomes))
    world = None
    for i in range(100):
        world = try_connect_world(random.Random(crc32('try_connect_world', seed, attempt, i)), biomes)
        if world:
            break

    if not world:
        printError('failed to connect world')
        return None
    return world


def write_warps(maps, map_scripts, output_path):
    for m in maps.values():
        for w in m.warps:
            statement = w.statements[0]
            oldTo = statement.args[3][2]
            oldToMap = maps.get(oldTo)
            if oldToMap and oldToMap.type in [MapTypes.IGNORE, MapTypes.INDOORS]:
                w.toMap = oldTo
                w.toPos = IntPoint(statement.args[3][3], statement.args[3][4])
            for statement in w.statements:
                statement.args[3][2] = w.toMap
                statement.args[3][3] = w.toPos.x
                statement.args[3][4] = w.toPos.y

    success = write_scripts(map_scripts, output_path, world_to_string(120, 50))
    return success


def assertWarps(maps, error=False):
    for m in maps.values():
        if m.type == MapTypes.INDOORS or m.conns_in == 0:
            continue
        good = False
        for w in m.warps:
            if not w.toMap and not w.statements[0].args[3][2]:
                if error:
                    raise Exception('assertWarps with error enabled, found warp to None: '+str(m)+' '+str(w)+', '+repr(w.statements[0]))
                continue
            if w.inPos == w.fromPos:
                warning('\nassertWarps found w.inPos == w.fromPos:', m, w)
            m2 = maps.get(w.toMap)
            if not m2 or len(m2.warps) == 0:
                continue
            for w2 in m2.warps:
                if w.toMap == w2.map and w.map == w2.toMap:
                    good = True
        if not good:
            warning('\nassertWarps warning in map:', m, '\n\twarps:', m.warps)
            if error:
                raise Exception('assertWarps with error enabled: '+str(m)+'\n\t'+str(m.warps))
    #
