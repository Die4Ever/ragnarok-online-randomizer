from ro_randomizer.entrance_rando import *
import unittest

class TestEntranceRando(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # lower numbers are SW for these tests
        # cities first so they get marked as cities
        warp('prontera', 0, 100, 'north', 0, -100)
        warp('aldebaran', 0, -100, 'north', 0, 100)
        warp('payon', -100, 100, 'se', 100, -100)

        warp('prontera', -100, 100, 'nw', 100, -100)
        warp('prontera', 100, 100, 'ne', -100, -100)

        warp('north', 0, 100, 'aldebaran', 0, -100)
        warp('nw', 100, 100, 'aldebaran', -100, -100)
        warp('ne', -100, 100, 'aldebaran', 100, -100)

        warp('prontera', 100, -100, 'se', -100, 100)
        warp('se', 100, -100, 'payon', -100, 100)

        estimate_positions([{'map': 'prontera', 'x': 0, 'y': 0}])
        debug(world_to_string(15, 10))

    def test_estimate_positions(self):
        self.checkPos('prontera', 0, 0)
        self.checkPos('aldebaran', 0, 400)
        self.checkPos('payon', 400, -400)

    def test_set_closest_cities(self):
        set_closest_cities()
        self.assertEqual(maps['prontera'].closest_city, 'prontera')
        self.assertIsNotNone(maps['north'].closest_city)

    def test_maps_can_connect(self):
        m1 = maps['prontera']
        m2 = maps['aldebaran']
        m3 = maps['payon']
        self.assertTrue( maps_can_connect(m1, m2, Point(0, 100)) )
        self.assertFalse( maps_can_connect(m1, m3, Point(0, 100)) )
        self.assertTrue( maps_can_connect(m1, m3, Point(100, -100)) )

    def test_shuffle_biome(self):
        self.assertTrue( shuffle_biome(maps['prontera'], 1) < 100 )
        self.assertTrue( shuffle_biome(maps['prontera'], 999) < 100 )

    def test_shuffle_world(self):
        self.assertTrue( shuffle_world(1) < 100 )
        self.assertTrue( shuffle_world(999) < 100 )

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
