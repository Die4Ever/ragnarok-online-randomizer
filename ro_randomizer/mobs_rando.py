from ro_randomizer.base import *
import yaml

# https://github.com/rathena/rathena/blob/master/doc/script_commands.txt#L133-L135
# <map name>{,<x>{,<y>{,<xs>{,<ys>}}}}%TAB%monster%TAB%<monster name>{,<monster level>}%TAB%<mob id>,<amount>{,<delay1>{,<delay2>{,<event>{,<mob size>{,<mob ai>}}}}}
# I think if I want to set an AI mode then I need to set event to 0?
# <mob ai> can be:
# 	AI_NONE		(0)		(default)
# 	AI_ATTACK	(1)		(attack/friendly)
# 	AI_SPHERE	(2)		(Alchemist skill)
# 	AI_FLORA	(3)		(Alchemist skill)
# 	AI_ZANZOU	(4)		(Kagerou/Oboro skill)
# 	AI_LEGION	(5)		(Sera skill)
# 	AI_FAW		(6)		(Mechanic skill)
# 	AI_WAVEMODE	(7)		Normal monsters will ignore attack from AI_WAVEMODE monsters

# should it figure out the default levels for each monster? or just always specify them?
monsters = {}
monsters_levels = {}

def mobs_rando():
    global monsters, monsters_levels
    monsters.clear()
    monsters_levels.clear()
    monsters_files = get_settings()['inputs']['monsters']
    mobs_files = get_settings()['inputs']['mobs'] # do I even need to read the original mobs scripts? I can just create new ones from scratch
    for filename in monsters_files:
        with open(filename, "r") as file:
            read_monsters_yml(file)


def read_monsters_yml(file):
    global monsters, monsters_levels
    tmonsters = yaml.safe_load(file)['Body']
    for m in tmonsters:
        id = m['Id']
        level = m.get('Level')
        if not level:
            m['Level'] = 1
            level = 1
        monsters[id] = m
        if level not in monsters_levels:
            monsters_levels[level] = {id: m}
        else:
            monsters_levels[level][id] = m
