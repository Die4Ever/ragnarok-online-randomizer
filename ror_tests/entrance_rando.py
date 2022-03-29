from ro_randomizer.entrance_rando import *
from ror_tests.base_tests import *
import unittest

class TestEntranceRando(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.data_set1()

    def lock_in_data_set(self):
        estimate_warp_offsets()
        estimate_positions(get_settings()['location_anchors'])
        for m in maps.values():
            m.original_position = m.position
            for w in m.warps:
                w.setDefaultInPos(m)

        set_closest_cities()


    def data_set1(self):
        # lower numbers are SW for these tests
        # cities first so they get marked as cities
        ro_randomizer.base.maps.clear()
        old_loglevel = get_loglevel()
        set_loglevel(DebugLevels.SILENT)
        set_settings({ 'location_anchors': [{'map': 'prontera', 'x': 0, 'y': 0}], 'ignore_maps': []})
        warps('prontera', 50, 100, 'north', 32, 0)
        warps('aldebaran', 32, 0, 'north', 32, 64)
        warps('aldebaran', 32, 64, 'morenorth', 32, 0)
        warps('payon', 0, 64, 'se', 64, 0)

        warps('prontera', 0, 100, 'nw', 64, 0)
        warps('prontera', 100, 100, 'ne', 0, 0)

        warps('nw', 64, 64, 'aldebaran', 0, 0)
        warps('ne', 0, 64, 'aldebaran', 64, 0)

        warps('prontera', 100, 0, 'se', 0, 64)
        warps('prontera', 50, 0, 'south', 32, 64)
        self.lock_in_data_set()
        set_loglevel(old_loglevel)

    def data_set2(self):
        ro_randomizer.base.maps.clear()
        old_loglevel = get_loglevel()
        set_loglevel(DebugLevels.SILENT)
        warps('prontera', 0, 32, 'w', 64, 32)
        warps('prontera', 64, 32, 'e', 0, 32)
        self.lock_in_data_set()
        set_loglevel(old_loglevel)

    def data_set3(self):
        ro_randomizer.base.maps.clear()
        old_loglevel = get_loglevel()
        set_loglevel(DebugLevels.SILENT)
        warps('prontera', 32, 64, 'n', 32, 0)
        warps('prontera', 32, 0, 's', 32, 64)
        self.lock_in_data_set()
        set_loglevel(old_loglevel)


    def test_closest_cities(self):
        self.assertEqual(maps['prontera'].closest_city, 'prontera')
        self.assertIsNotNone(maps['north'].closest_city)

    def test_estimate_positions(self):
        self.checkPos('prontera', 0, 0)
        self.checkPos('aldebaran', 22.5, 164)
        self.checkPos('payon', 164, -128)

    def test_MapsGrid(self):
        m1 = maps['prontera']
        m2 = maps['aldebaran']
        m3 = maps['payon']

        grid = ro_randomizer.world_map_grids.MapsGrid(random.Random(1), [m1, m2, m3])
        self.assertTrue( grid.items_can_connect(m1, m2, Point(0, 1)) )
        self.assertFalse( grid.items_can_connect(m1, m3, Point(0, 1)) )
        self.assertTrue( grid.items_can_connect(m1, m3, Point(1, -1)) )

        m = grid.grid[1][1]
        self.assertEqual(m, maps['prontera'])
        m = grid.put_random_item_in_spot(IntPoint(1, 0))
        self.assertEqual(m, maps['payon'])
        m = grid.put_random_item_in_spot(IntPoint(1, 2))
        self.assertEqual(m, maps['aldebaran'])

        m4 = maps['nw']
        m5 = maps['ne']
        m6 = maps['se']
        grid.shuffled_items.append(m4)
        grid.shuffled_items.append(m5)
        grid.shuffled_items.append(m6)
        self.assertCountEqual(grid.shuffled_items, [m5, m4, m6])
        grid.put_random_item_in_spot(IntPoint(0, 2))
        grid.put_random_item_in_spot(IntPoint(0, 1))
        grid.put_random_item_in_spot(IntPoint(0, 0))
        self.assertCountEqual(grid.shuffled_items, [m5])

        right_edge = grid.get_items_on_edge(Point(-1, 0))
        self.assertCountEqual(right_edge, [m4, m6])

        bottom_edge = grid.get_items_on_edge(Point(0, 1))
        self.assertCountEqual(bottom_edge, [m2, m4])

        top_edge = grid.get_items_on_edge(Point(0, -1))
        self.assertCountEqual(top_edge, [m3])

    def test_shuffle_biome1(self):
        anchors = get_settings()['location_anchors']

        small_biome = [maps['prontera'], maps['north']]
        small_biome_d = dict(map(lambda x: (x.name,x), small_biome))
        grid = self.shuffle_biome('prontera', small_biome, 1)
        estimate_positions(anchors)
        debug(world_to_string(16, 12))
        self.printWorld(small_biome, grid)
        assertWarps(small_biome_d, True)

        grid = self.shuffle_biome('prontera', maps.values(), 1)
        estimate_positions(anchors)
        debug(world_to_string(16, 12))
        self.printWorld(maps.values(), grid)
        assertWarps(maps, True)

        self.shuffle_biome('prontera', maps.values(), 999)
        estimate_positions(anchors)
        debug(world_to_string(16, 12))
        self.printWorld(maps.values(), grid)
        assertWarps(maps, True)


    def test_shuffle_biome2(self):
        self.data_set2()
        biome = self.shuffle_biome('prontera', maps.values(), 1)
        self.assertEqual(biome.grid[1][1].name, 'prontera')
        self.assertEqual(biome.grid[0][1].name, 'w')
        self.assertEqual(biome.grid[2][1].name, 'e')


    def test_shuffle_biome3(self):
        self.data_set3()
        biome = self.shuffle_biome('prontera', maps.values(), 1)
        self.assertEqual(biome.grid[1][1].name, 'prontera')
        self.assertEqual(biome.grid[1][2].name, 'n')
        self.assertEqual(biome.grid[1][0].name, 's')


    def test_Aget_warps_on_side(self):
        self.data_set2()
        w = maps['w'].get_warps_on_side(IntPoint(1,0))
        self.assertEqual(str(w[0].toMap), 'prontera')
        w = maps['w'].get_warps_on_side(IntPoint(-1,0))
        self.assertEqual(len(w), 0)
        w = maps['w'].get_warps_on_side(IntPoint(0,-1))
        self.assertEqual(len(w), 0)
        w = maps['w'].get_warps_on_side(IntPoint(0,1))
        self.assertEqual(len(w), 0)


    def shuffle_biome(self, city, biome_maps, seed):
        info('testing shuffle_biome '+city+' with '+str(len(biome_maps))+' maps')
        city_map = None
        for m in maps.values():
            m.closest_city = ''
            m.position = None
            for w in m.warps:
                w.toMap = None
        for m in biome_maps:
            if m.name == city:
                city_map = m
            m.closest_city = 'prontera'
        (grid, attempts) = shuffle_biome(city_map, seed)
        self.assertIsNotNone(grid)
        self.assertTrue( attempts < 100 )
        self.verifyGrid(grid)
        return grid

    def test_shuffle_world(self):
        self.shuffle_world(2)
        self.shuffle_world(999)

    def shuffle_world(self, seed):
        anchors = get_settings()['location_anchors']
        for m in maps.values():
            m.position = None
        world = None
        for i in range(1000):
            world = try_shuffle_world(seed, i)
            if world:
                break
        self.assertIsNotNone(world)
        estimate_positions(anchors)
        debug(world_to_string(16, 12))
        self.printWorld(maps.values(), world)
        assertWarps(maps, True)

    def checkPos(self, map, x, y):
        info('checkPos:', maps[map], 'vs', (x, y))
        self.assertAlmostEqual(maps[map].position.x, x)
        self.assertAlmostEqual(maps[map].position.y, y)

    def printWorld(self, maps, world):
        if len(world.grid) == 1:
            debug(repr(world.grid[0][0]))
        for m in maps:
            debug(m, m.position, 'closest_city:', m.closest_city)
            for w in m.warps:
                debug('\t', w)
                # TODO: I'm not sure there are non-vanilla arrangements of the test data that pass this check
                #self.assertIsNotNone(w.toMap)
            self.assertIsNotNone(m.position)
        debug('')

    def verifyGrid(self, grid):
        info('verifying grid...')
        info(repr(grid))
        self.assertEqual(grid.shuffled_items, [])



def warp(map, fromX, fromY, toMap, toX, toY):
    args = [
        [map, fromX, fromY, 0],
        ['warp'],
        ['testwarp'],
        [0, 0, toMap, toX, toY]
    ]
    s = ScriptStatement('', False, 'warp', args, 0, 0)
    return new_warp(s, 'cities')


def warps(map, fromX, fromY, toMap, toX, toY):
    global map_sizes
    map_sizes[map] = IntPoint(64, 64)
    map_sizes[toMap] = IntPoint(64, 64)
    warp(map, fromX, fromY, toMap, toX, toY)
    warp(toMap, toX, toY, map, fromX, fromY)
