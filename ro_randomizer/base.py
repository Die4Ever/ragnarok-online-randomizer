import re
import glob
import os
import os.path
import shutil
import datetime
import traceback
from pathlib import Path
import random
import math
import time
from timeit import default_timer as timer
from enum import Enum, IntEnum
import json
import struct
import cProfile, pstats

version = '0.01'
# shared code for all ro_randomizer modules
settings = None
map_sizes = {}
maps = {}
do_profiling = False

def get_settings():
    global settings
    return settings

def set_settings(new_settings):
    global settings
    settings = new_settings

class DebugLevels(IntEnum):
    SILENT = 0
    NOTICE = 1
    INFO = 2
    DEBUG = 3
    TRACE = 4

loglevel = DebugLevels.INFO
def set_loglevel(new_loglevel):
    global loglevel
    assert isinstance(new_loglevel, DebugLevels), 'loglevel must be of type DebugLevels'
    loglevel = new_loglevel

def increase_loglevel(new_loglevel):
    if new_loglevel > loglevel:
        set_loglevel(new_loglevel)

# text colors
WARNING = '\033[91m'
ENDCOLOR = '\033[0m'

def trace(*args, **kargs):
    global loglevel
    if loglevel >= DebugLevels.TRACE:
        print(*args, **kargs)

def debug(*args, **kargs):
    global loglevel
    if loglevel >= DebugLevels.DEBUG:
        print(*args, **kargs)

def info(*args, **kargs):
    global loglevel
    if loglevel >= DebugLevels.INFO:
        print(*args, **kargs)

def notice(*args, **kargs):
    # this might be useful if we do threading? so we can redirect to a file?
    global loglevel
    if loglevel >= DebugLevels.NOTICE:
        print(*args, **kargs)

def prependException(e, msg):
    if not e.args:
        e.args = ("",)
    e.args = (msg + " \n" + e.args[0],) + e.args[1:]

def appendException(e, msg):
    if not e.args:
        e.args = ("",)
    e.args = (e.args[0] + " \n" + msg,) + e.args[1:]

def warning(*args, **kargs):
    print(WARNING + ' '.join(map(str, args)) + ENDCOLOR, **kargs)

def printError(*args, **kargs):
    print(WARNING + ' '.join(map(str, args)) + ENDCOLOR, **kargs)

def printHeader(*args):
    print(
          "\n====================================================="
        + "\n            " + ' '.join(map(str, args))
        + "\n====================================================="
        + "\n")


def insensitive_glob(pattern):
    return (
        glob.glob(pattern, recursive=True)
        + glob.glob(pattern+'/**', recursive=True)
        + glob.glob(pattern+'/*', recursive=True)
    )


def profile(function):
    cProfile.run(function, "{}.profile".format(__file__))
    s = pstats.Stats("{}.profile".format(__file__))
    keys = list(s.stats.keys())
    for f in keys:
        if 'ragnarok-online-randomizer' not in f[0]:
            del s.stats[f]
    s.strip_dirs()
    s.sort_stats('cumulative').print_stats(15)


def exists(file):
    exists = os.path.isfile(file)
    # if exists:
    #     print("file already exists: " + file)
    return exists

def exists_dir(path):
    exists = os.path.isdir(path)
    # if exists:
    #     print("dir already exists: " + path)
    return exists


# regex convenience
def rg(name, pattern='[^,\t]+'):
    return r'(?P<'+name+'>'+pattern+')'

def clamp(num, min_value, max_value):
   return max(min(num, max_value), min_value)

class Point():
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)

    def copy(self):
        return type(self)(self.x, self.y)

    def maximize(self, p):
        self.x = max(self.x, p.x)
        self.y = max(self.y, p.y)

    def minimize(self, p):
        self.x = min(self.x, p.x)
        self.y = min(self.y, p.y)

    def clamp(self, min, max):
        self.x = clamp(self.x, min.x, max.x)
        self.y = clamp(self.y, min.y, max.y)

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    @classmethod
    def from_point(cls, other):
        return cls(other.x, other.y)

    def negative(self):
        return type(self)(-self.x, -self.y)

    def flip(self):
        return type(self)(self.y, self.x)

    def multiply(self, other):
        return type(self)(self.x * other.x, self.y * other.y)

    def multiply_scalar(self, scalar):
        return type(self)(self.x * scalar, self.y * scalar)

    def add(self, other):
        return type(self)(self.x + other.x, self.y + other.y)

    def subtract(self, other):
        return type(self)(self.x - other.x, self.y - other.y)

    def __repr__(self):
        return "(" + str(self.x) + ", " + str(self.y) + ")"

    def dist(self, other):
        return ((self.x - other.x)**2 + (self.y - other.y)**2)**0.5

    def closest(self, other_point, object, closest):
        dist = self.dist(other_point)
        if closest is None or dist < closest[1]:
            closest = (object, dist)
        return closest


class IntPoint(Point):
    def __init__(self, x, y):
        self.x = int(x)
        self.y = int(y)


class Matrix(list):
    def __init__(self, width, height):
        list.__init__(self, [[None for y in range(height)] for x in range(width)])

    def ContainsPoint(self, p):
        return p.x >= 0 and p.y >= 0 and p.x < len(self) and p.y < len(self[0])

    def __repr__(self):
        ret = type(self).__name__ + ' [\n'
        for y in range(len(self[0])):
            for x in range(len(self)):
                i = self[x][y]
                s = str(i)
                if i is None:
                    s = ''
                s = s[:7].center(7, ' ')
                ret += s +','
            ret += '\n'
        return ret + ']'

    def __str__(self):
        ret = type(self).__name__ + ' ['
        for y in range(len(self[0])):
            ret += '['
            for x in range(len(self)):
                i = self[x][y]
                s = str(i)
                if i is None:
                    s = ''
                s = s[:5].center(5, ' ')
                ret += s +','
            ret += ']'
        return ret + ']'


moves = (IntPoint(-1,0), IntPoint(0,-1), IntPoint(1,0), IntPoint(0,1))
corners = (IntPoint(-1,-1), IntPoint(-1,1), IntPoint(1,-1), IntPoint(1,1))


class ShuffledGrid:
    def __init__(self, rand, items):
        # we shuffle the array and put it into a 2D array, pops the first item from shuffled_items
        self.items = items
        self.shuffled_items = rand.sample(items, k=len(items))

        size = len(self.shuffled_items)
        # ensure we have a proper center point
        if size % 2 == 0:
            size += 1
        width = size
        height = size
        self.grid = Matrix(width, height)

        self.center = IntPoint(width/2, height/2)
        self.grid[self.center.x][self.center.y] = self.shuffled_items.pop(0)
        attempts = 0

    def items_can_connect(self, item, other, move):
        # base class placeholder
        return True

    def clear_connections(self):
        # base class placeholder
        pass

    def connect_items(self, item1, item2, move, spot):
        # base class placeholder
        return 1

    def __str__(self):
        return type(self).__name__ + ', ' + str(len(self.items)) + ' items, ' + str(self.grid)

    def __repr__(self):
        return type(self).__name__ + ', ' + str(len(self.items)) + ' items, ' + repr(self.grid)

    def _get_items_on_line(self, offset, start, slope):
        items = []
        line_center = start.add( slope.multiply_scalar(len(self.grid)/2) )
        if not self.grid.ContainsPoint( line_center ):
            return items

        p = start.copy()
        while not self.grid.ContainsPoint(p):
            p = p.add(slope)

        while self.grid.ContainsPoint(p):
            if self.grid[p.x][p.y]:
                items.append(self.grid[p.x][p.y])
            p = p.add(slope)

        if len(items) == 0:
            # don't go past the center point
            if line_center == self.center:
                return items
            # otherwise recurse
            start = start.subtract(offset)
            return self._get_items_on_line(offset, start, slope)
        return items

    def get_items_on_edge(self, offset):
        # recursively walk back the line until we find something or we hit the center
        size = len(self.grid)
        if size == 1:
            return [ self.grid[0][0] ]

        p = offset.add(Point(1,1)).multiply_scalar((size - 1)*0.5)
        slope = offset.flip()
        start = p.subtract(self.center.multiply(slope))
        start = IntPoint.from_point(start)

        trace('get_items_on_edge center:', self.center, ', size:', size, ', offset:', offset, ', p:', p, ', start:', start, ', slope:', slope)
        return self._get_items_on_line(offset, start, slope)

    def get_empty_spot(self, rand):
        spot = self.center.copy()
        while True:
            move = rand.choice(moves)
            spot.x += move.x
            spot.y += move.y
            if not self.grid.ContainsPoint(spot):
                spot = self.center.copy()
                continue
            if self.grid[spot.x][spot.y] is None:
                return spot

    def put_random_item_in_spot(self, spot):
        for item in self.shuffled_items:
            good = 0
            for move in moves:
                tspot = spot.add(move)
                if not self.grid.ContainsPoint(tspot):
                    continue

                other = self.grid[tspot.x][tspot.y]
                if other is None:
                    continue

                can_connect = self.items_can_connect(item, other, move)
                if not can_connect:
                    good = 0
                    break
                good += 1
            if good > 0:
                self.shuffled_items.remove(item)
                self.grid[spot.x][spot.y] = item
                return item
        trace(type(self).__name__, '.put_random_item_in_spot failed,', len(self.shuffled_items), '/', len(self.grid) )
        return None

    def fill(self, rand):
        attempts = 0
        while len(self.shuffled_items):
            # find a spot to place the next piece
            attempts += 1
            if attempts > 1000:
                warning(type(self).__name__ + '.fill failed at '+str(attempts)+' attempts, '+str(len(self.shuffled_items)) + '/' + str(len(self.grid)))
                return None
            spot = self.get_empty_spot(rand)
            # find an item to put in the spot
            self.put_random_item_in_spot(spot)
        return True

    def finalize_connections(self):
        self.clear_connections()
        size = len(self.grid)
        if size == 1:
            return True
        linked = 0
        for x in range(size):
            for y in range(size):
                item1 = self.grid[x][y]
                if item1 is None:
                    continue
                # loop through cardinal moves first and then the corners
                for move in (moves + corners):
                    spot = IntPoint(x + move.x, y + move.y)
                    if not self.grid.ContainsPoint(spot):
                        continue
                    item2 = self.grid[spot.x][spot.y]
                    if item2 is None:
                        continue
                    # If I want to make it more lenient, I can make it do a single connection for each pair of maps before going back and doing the rest
                    # so call connect_items_single (or a parameter of 1 for max connections)
                    # then do the loop again with regular connect_maps to fill in the rest
                    # maybe the lists of warps should be shuffled too?
                    linked += self.connect_items(item1, item2, move, spot)
        return linked > 0

