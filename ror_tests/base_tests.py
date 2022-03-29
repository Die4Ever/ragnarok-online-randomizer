from ro_randomizer.base import *
import unittest

class BaseTestCase(unittest.TestCase):
    def setUp(self):
        info(GREENCOLOR+'----'+ENDCOLOR)
        pass

    def tearDown(self):
        info('\n'+GREENCOLOR+ str(self).partition(' (')[0] +' result: '+ENDCOLOR, sep='')
        pass


class TestBaseModule(BaseTestCase):
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

