from ro_randomizer.entrance_rando import *
import unittest

class TestEntranceRando(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # lower numbers are SW for these tests
        # cities first so they get marked as cities
        set_settings({ 'location_anchors': [{'map': 'prontera', 'x': 0, 'y': 0}], 'ignore_maps': []})
        warps('prontera', 50, 100, 'north', 32, 0)
        warps('aldebaran', 32, 0, 'north', 32, 64)
        warps('payon', 0, 64, 'se', 64, 0)

        warps('prontera', 0, 100, 'nw', 64, 0)
        warps('prontera', 100, 100, 'ne', 0, 0)

        warps('nw', 64, 64, 'aldebaran', 0, 0)
        warps('ne', 0, 64, 'aldebaran', 64, 0)

        warps('prontera', 100, 0, 'se', 0, 64)

        estimate_warp_offsets()
        estimate_positions([{'map': 'prontera', 'x': 0, 'y': 0}])
        for m in maps.values():
            m.original_position = m.position
        set_closest_cities()
        debug(world_to_string(16, 12))

    def setUp(self):
        print('----')
        pass

    def tearDown(self):
        print('\n===================\n'+ str(self).partition(' (')[0] +' result: ', sep='')
        pass

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
        self.assertTrue( grid.items_can_connect(m1, m2, Point(0, -100)) )
        self.assertFalse( grid.items_can_connect(m1, m3, Point(0, -100)) )
        self.assertTrue( grid.items_can_connect(m1, m3, Point(-100, 100)) )

        m = grid.grid[1][1]
        self.assertEqual(m, maps['prontera'])
        m = grid.put_random_item_in_spot(IntPoint(1, 2))
        self.assertEqual(m, maps['payon'])
        m = grid.put_random_item_in_spot(IntPoint(1, 0))
        self.assertEqual(m, maps['aldebaran'])

        m4 = maps['nw']
        m5 = maps['ne']
        m6 = maps['se']
        grid.shuffled_items.append(m4)
        grid.shuffled_items.append(m5)
        grid.shuffled_items.append(m6)
        self.assertCountEqual(grid.shuffled_items, [m5, m4, m6])
        grid.put_random_item_in_spot(IntPoint(2, 0))
        grid.put_random_item_in_spot(IntPoint(2, 1))
        grid.put_random_item_in_spot(IntPoint(2, 2))
        self.assertCountEqual(grid.shuffled_items, [m5])

        right_edge = grid.get_items_on_edge(Point(1, 0))
        self.assertCountEqual(right_edge, [m4, m6])

        bottom_edge = grid.get_items_on_edge(Point(0, -1))
        self.assertCountEqual(bottom_edge, [m2, m4])

        top_edge = grid.get_items_on_edge(Point(0, 1))
        self.assertCountEqual(top_edge, [m3])

    def test_shuffle_biome(self):
        for m in maps.values():
            m.closest_city = 'prontera'
            m.position = None
        (grid, attempts) = shuffle_biome(maps['prontera'], 1)
        self.assertIsNotNone(grid)
        self.assertTrue( attempts < 10 )
        self.verifyGrid(grid)

        for m in maps.values():
            m.closest_city = 'prontera'
            m.position = None
        (grid, attempts) = shuffle_biome(maps['prontera'], 999)
        self.assertIsNotNone(grid)
        self.assertTrue( attempts < 10 )
        self.verifyGrid(grid)

    def test_shuffle_world(self):
        anchors = get_settings()['location_anchors']
        for m in maps.values():
            m.closest_city = 'prontera'
            m.position = None
        self.assertTrue( shuffle_world(1) < 100 )
        estimate_positions(anchors)
        debug(world_to_string(16, 12))
        self.printWorld(maps)
        assertWarps(maps, True)

        for m in maps.values():
            m.closest_city = 'prontera'
            m.position = None
        self.assertTrue( shuffle_world(999) < 100 )
        estimate_positions(anchors)
        debug(world_to_string(16, 12))
        self.printWorld(maps)
        assertWarps(maps, True)

    def test_matrix(self):
        m = Matrix(4, 3)
        debug("created matrix")
        self.assertTrue( m.ContainsPoint(Point(0,0)) )
        self.assertTrue( m.ContainsPoint(Point(3,2)) )
        self.assertFalse( m.ContainsPoint(Point(-1,0)) )
        self.assertFalse( m.ContainsPoint(Point(0,-1)) )
        self.assertFalse( m.ContainsPoint(Point(4,0)) )
        self.assertFalse( m.ContainsPoint(Point(0,3)) )
        m[0][0] = 'L'
        m[0][1] = 'L'
        m[0][2] = 'L'
        m[3][0] = 'R'
        m[3][1] = 'R'
        m[3][2] = 'R'
        debug(repr(m))

    def test_shuffled_grid(self):
        grid = ShuffledGrid(random.Random(1), ['C', 'C', 'C'])
        grid.grid[0][0] = 'L'
        grid.grid[0][1] = 'L'
        grid.grid[0][2] = 'L'
        grid.grid[2][0] = 'R'
        grid.grid[2][1] = 'R'
        grid.grid[2][2] = 'R'
        debug(repr(grid))
        left = grid.get_items_on_edge(IntPoint(-1, 0))
        right = grid.get_items_on_edge(IntPoint(1, 0))
        self.assertEqual(left, ['L', 'L', 'L'])
        self.assertEqual(right, ['R', 'R', 'R'])
        top = grid.get_items_on_edge(IntPoint(0, -1))
        self.assertCountEqual(top, ['L', 'R'])

    def checkPos(self, map, x, y):
        info('checkPos:', maps[map], 'vs', (x, y))
        self.assertEqual(maps[map].position.x, x)
        self.assertEqual(maps[map].position.y, y)

    def printWorld(self, maps):
        for m in maps.values():
            print(m)
            for w in m.warps:
                print('\t', w)
            self.assertIsNotNone(m.position)
        print('')

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
    warp(map, fromX, fromY, toMap, toX, toY)
    warp(toMap, toX, toY, map, fromX, fromY)
