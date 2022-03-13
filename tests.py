from ro_randomizer.base import *
from ror_tests.entrance_rando import *
from ror_tests.script import *
import unittest

def run_tests():
    increase_loglevel(DebugLevels.DEBUG)
    unittest.main(verbosity=9, warnings="error")

if __name__ == '__main__':
    if do_profiling:
        profile("run_tests()")
    else:
        run_tests()
