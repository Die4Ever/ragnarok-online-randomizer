import re
import glob
import os.path
import traceback
from pathlib import Path
import random
import time
from timeit import default_timer as timer
from enum import Enum

# shared code for all ro_randomizer modules
settings = None

def get_settings():
    global settings
    return settings

def set_settings(new_settings):
    global settings
    settings = new_settings


loglevel = 'info'

# text colors
WARNING = '\033[91m'
ENDCOLOR = '\033[0m'

def trace(str):
    # lower than debug
    pass


def debug(str):
    global loglevel
    if loglevel == 'debug':
        print(str)

def info(str):
    global loglevel
    # later we should make this actually separate
    if loglevel == 'debug':
        print(str)

def notice(str):
    # this might be useful if we do threading? so we can redirect to a file?
    print(str)

def prependException(e, msg):
    if not e.args:
        e.args = ("",)
    e.args = (msg + " \n" + e.args[0],) + e.args[1:]

def appendException(e, msg):
    if not e.args:
        e.args = ("",)
    e.args = (e.args[0] + " \n" + msg,) + e.args[1:]

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

