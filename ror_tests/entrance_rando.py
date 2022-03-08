from ro_randomizer.entrance_rando import *
import unittest

class TestEntranceRando(unittest.TestCase):
    def test(self):
        # lower numbers are SW for these tests
        warp('prontera', 0, 100, 'north', 0, -100)

        warp('prontera', -100, 100, 'nw', 100, -100)
        warp('prontera', 100, 100, 'ne', -100, -100)

        warp('north', 0, 100, 'aldebaran', 0, -100)
        warp('nw', 100, 100, 'aldebaran', -100, -100)
        warp('ne', -100, 100, 'aldebaran', 100, -100)

        warp('prontera', 100, -100, 'se', -100, 100)
        warp('se', 100, -100, 'payon', -100, 100)

        estimate_positions([{'map': 'prontera', 'x': 0, 'y': 0}])
        self.checkPos('prontera', 0, 0)
        self.checkPos('aldebaran', 0, 400)
        self.checkPos('payon', 400, -400)
    
    
    def checkPos(self, map, x, y):
        notice(maps[map])
        self.assertEqual(maps[map].x, x)
        self.assertEqual(maps[map].y, y)



def warp(map, fromX, fromY, toMap, toX, toY):
    args = [
        [map, fromX, fromY, 0],
        ['warp'],
        ['testwarp'],
        [0, 0, toMap, toX, toY]
    ]
    s = ScriptStatement('', False, 'warp', args, 0, 0)
    return new_warp(s, 'cities')
