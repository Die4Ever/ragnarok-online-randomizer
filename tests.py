from ro_randomizer.base import *
from ror_tests.entrance_rando import *
from ror_tests.script import *
import unittest

if __name__ == '__main__':
    increase_loglevel(DebugLevels.DEBUG)
    unittest.main(verbosity=9, warnings="error")
