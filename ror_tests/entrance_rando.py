from ro_randomizer.entrance_rando import *
import unittest

class TestEntranceRando(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # lower numbers are SW for these tests
        # cities first so they get marked as cities
        set_settings({ 'location_anchors': [{'map': 'prontera', 'x': 0, 'y': 0}]})
        warps('prontera', 50, 100, 'north', 32, 0)
        warps('aldebaran', 32, 0, 'north', 32, 64)
        warps('payon', 0, 64, 'se', 64, 0)

        warps('prontera', 0, 100, 'nw', 64, 0)
        warps('prontera', 100, 100, 'ne', 0, 0)

        warps('nw', 64, 64, 'aldebaran', 0, 0)
        warps('ne', 0, 64, 'aldebaran', 64, 0)

        warps('prontera', 100, 0, 'se', 0, 64)

        estimate_positions([{'map': 'prontera', 'x': 0, 'y': 0}])
        for m in maps.values():
            m.original_position = m.position
        set_closest_cities()
        debug(world_to_string(16, 12))

    def test_closest_cities(self):
        self.assertEqual(maps['prontera'].closest_city, 'prontera')
        self.assertIsNotNone(maps['north'].closest_city)

    def test_estimate_positions(self):
        self.checkPos('prontera', 0, 0)
        self.checkPos('aldebaran', 22.5, 164)
        self.checkPos('payon', 164, -128)

    def test_maps_can_connect(self):
        m1 = maps['prontera']
        m2 = maps['aldebaran']
        m3 = maps['payon']
        self.assertTrue( maps_can_connect(m1, m2, Point(0, 100))[0] )
        self.assertFalse( maps_can_connect(m1, m3, Point(0, 100))[0] )
        self.assertTrue( maps_can_connect(m1, m3, Point(100, -100))[0] )

    def test_get_map_for_spot(self):
        m = Matrix(3,3)
        m[0][1] = maps['north']

        # aldebaran doesn't have teleporters at the north, only at the south
        map = get_map_for_spot([maps['prontera'], maps['aldebaran']], m, IntPoint(0,2))
        self.assertEqual(map, maps['prontera'])

        map = get_map_for_spot([maps['aldebaran']], m, IntPoint(0,0))
        self.assertEqual(map, maps['aldebaran'])

    def test_shuffle_biome(self):
        for m in maps.values():
            m.closest_city = 'prontera'
            m.position = None
        self.assertTrue( shuffle_biome(maps['prontera'], 1) < 10 )

        for m in maps.values():
            m.closest_city = 'prontera'
            m.position = None
        self.assertTrue( shuffle_biome(maps['prontera'], 999) < 10 )

    def test_shuffle_world(self):
        anchors = get_settings()['location_anchors']
        for m in maps.values():
            m.closest_city = 'prontera'
            m.position = None
        self.assertTrue( shuffle_world(1) < 100 )
        estimate_positions(anchors)
        debug(world_to_string(16, 12))

        for m in maps.values():
            m.closest_city = 'prontera'
            m.position = None
        self.assertTrue( shuffle_world(999) < 100 )
        estimate_positions(anchors)
        debug(world_to_string(16, 12))

    def test_matrix(self):
        m = Matrix(4, 3)
        debug("created matrix "+repr(m))
        self.assertTrue( m.ContainsPoint(Point(0,0)) )
        self.assertTrue( m.ContainsPoint(Point(3,2)) )
        self.assertFalse( m.ContainsPoint(Point(-1,0)) )
        self.assertFalse( m.ContainsPoint(Point(0,-1)) )
        self.assertFalse( m.ContainsPoint(Point(4,0)) )
        self.assertFalse( m.ContainsPoint(Point(0,3)) )
        m[3][2] = 1

    def checkPos(self, map, x, y):
        info('checkPos: '+ repr(maps[map]) + ' vs ' + repr((x, y)))
        self.assertEqual(maps[map].position.x, x)
        self.assertEqual(maps[map].position.y, y)



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
