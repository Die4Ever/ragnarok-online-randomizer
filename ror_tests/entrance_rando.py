from ro_randomizer.entrance_rando import *
import unittest

class TestEntranceRando(unittest.TestCase):
    def test(self):
        warp('prontera', 0, 100, 'north', 0, -100)
        warp('north', 0, 100, 'aldebaran', 0, -100)
        warp('prontera', 100, -100, 'se', -100, 100)
        warp('se', 100, -100, 'payon', -100, 100)
        estimate_positions()
        self.checkPos('prontera', 0, 0)
        self.checkPos('aldebaran', 0, 400)
        self.checkPos('payon', 400, -400)
    
    
    def checkPos(self, map, x, y):
        notice(maps[map])
        self.assertEquals(maps[map].x, x)
        self.assertEquals(maps[map].y, y)



def warp(map, fromX, fromY, toMap, toX, toY):
    args = []
    args.append([map, fromX, fromY, 0])
    args.append(['warp'])
    args.append(['testwarp'])
    args.append([0, 0, toMap, toX, toY])
    s = ScriptStatement('', False, 'warp', args, 0, 0)
    return new_warp(s)
