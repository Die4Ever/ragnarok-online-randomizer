import re
import glob
import os.path
import traceback
from pathlib import Path
import random
import time
from timeit import default_timer as timer
from enum import Enum, IntEnum
import json

# shared code for all ro_randomizer modules
settings = None

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

loglevel = DebugLevels.NOTICE
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

def trace(str):
    global loglevel
    if loglevel >= DebugLevels.TRACE:
        print(str)

def debug(str):
    global loglevel
    if loglevel >= DebugLevels.DEBUG:
        print(str)

def info(str):
    global loglevel
    if loglevel >= DebugLevels.INFO:
        print(str)

def notice(str):
    # this might be useful if we do threading? so we can redirect to a file?
    global loglevel
    if loglevel >= DebugLevels.NOTICE:
        print(str)

def prependException(e, msg):
    if not e.args:
        e.args = ("",)
    e.args = (msg + " \n" + e.args[0],) + e.args[1:]

def appendException(e, msg):
    if not e.args:
        e.args = ("",)
    e.args = (e.args[0] + " \n" + msg,) + e.args[1:]

def printWarning(e):
    print(WARNING+e+ENDCOLOR)

def printError(e):
    print(WARNING+e+ENDCOLOR)

def printHeader(text):
    print("")
    print("=====================================================")
    print("            "+text)
    print("=====================================================")
    print("")


def insensitive_glob(pattern):
    return (
        glob.glob(pattern, recursive=True)
        + glob.glob(pattern+'/**', recursive=True)
        + glob.glob(pattern+'/*', recursive=True)
    )


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

    def __repr__(self):
        return "(" + str(self.x) + ", " + str(self.y) + ")"
