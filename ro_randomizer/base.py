import re
import glob
import os.path
import traceback
from pathlib import Path
import random
import time
from timeit import default_timer as timer

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


# should make a class for CodeObject so we don't need to use awkward nested arrays
# need a way to differentiate the comma arguments and the tab arguments
def parse_script_line(line, sub):
    if not line:
        return None
    
    args = line.split('\t')
    ret = [line]
    type = None
    if len(args) > 1:
        type = args[1]
    if not args[0]:
        return ret
    if not type:
        return ret
    
    # make type be the first entry so it's easy to filter by?
    ret.append(type)
    for a in args:
        for b in a.split(','):
            ret.append(b)
    return ret


def parse_script(content, sub=False):
    # if sub is true then we're inside of the curly braces of a script
    # so we would need to look for : to start a new tree branch, and ; to end a line
    in_block_comment = False
    in_line_comment = False
    in_curly_brace = 0
    buf = ''
    prev = ''
    tree = []

    for c in content:
        if in_line_comment:
            if c == '\n':
                in_line_comment = False
            continue
        if in_block_comment:
            if prev == '*' and c == '/':
                in_block_comment = False
            prev = c
            continue
        
        if c == '/' and len(buf) and buf[-1] == '/':
            in_line_comment = True
            buf = buf[:-1]
            buf = buf.strip()
            t = parse_script_line(buf, sub)
            if t:
                tree.append(t)
            buf = ''
            continue
        
        if c == '{':
            in_curly_brace += 1
            if in_curly_brace == 1:
                buf = ''
                continue
        elif c == '}':
            in_curly_brace -= 1
            if in_curly_brace == 0:
                buf = buf.strip()
                t = parse_script(buf, True)
                if t:
                    tree.append(t)
                buf = ''
                continue
        elif c == '\n' and in_curly_brace == 0:
            buf = buf.strip()
            if len(buf):
                tree.append(parse_script_line(buf, sub))
            buf = ''
            continue

        buf += c
    
    buf = buf.strip()
    if len(buf):
        tree.append(parse_script_line(buf, sub))
    return tree
