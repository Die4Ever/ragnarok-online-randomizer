import argparse
from ro_randomizer.base import *
import ro_randomizer.core

parser = argparse.ArgumentParser(description='Randomizer for Ragnarok Online private server.')
parser.add_argument('--seed', help='What seed number to use.')
args = vars(parser.parse_args())
notice('args: ')
notice(repr(args))

default_settings = {}
with open('settings.default.json') as f:
    default_settings = json.load(f)

settings = args.copy()
try:
    with open('settings.json') as f:
        settings = json.load(f)
except FileNotFoundError as e:
    e2 = Exception('ERROR: You need to copy settings.example.json to settings.json and adjust the paths.')
    raise e2 from e

merged = default_settings
for p in settings:
    if p not in merged:
        merged[p] = {}
    merged[p] = {**merged[p], **settings[p]}

set_settings(merged)
ro_randomizer.core.randomize(merged)
