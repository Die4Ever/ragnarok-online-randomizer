from os import stat
from ro_randomizer.base import *
from ro_randomizer.script import *
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
monsters_levels = {}
mob_scripts = {}
maps_mobs = {}

def mobs_rando():
    global monsters_levels, mob_scripts, maps_mobs
    monsters_levels.clear()
    seed = get_settings()['seed']
    monsters_files = get_settings()['inputs']['monsters']
    for filename in monsters_files:
        with open(filename, "r") as file:
            read_monsters_yml(file)

    for input in get_settings()['inputs']['mobs']:
        for file in insensitive_glob(input+'/*'):
            if file.endswith('.txt'):
                mob_scripts[file] = MobScript(file)

    for map in maps.values():
        rando_map_mobs(map)

    write_mobs(mob_scripts, get_settings()['outputs']['mobs'])


def rando_map_mobs(map):
    if map.name not in maps_mobs:
        return
    monsters = []
    danger = map.danger
    seed = get_settings()['seed']
    rng = random.Random( crc32('rando_map_mobs', seed, map.name ) )
    num = rng.randint(3, 6)
    while len(monsters) < num:
        add_monster(danger, rng, monsters)

    for mob in maps_mobs[map.name]:
        rando_mob(mob, rng, monsters)


def rando_mob(mob, rng, monsters):
    global maps
    map = maps.get(mob.map)
    if map is None:
        return
    danger = map.danger
    m = rng.choice(monsters)
    mob.monster_name = m['Name']
    mob.monster_id = m['Id']
    mob.update()


def add_monster(danger, rng, monsters, min=-5, max=5):
    global monsters_levels
    level = -1
    while level not in monsters_levels:
        level = danger + rng.randint(min, max)
        level = clamp(level, 1, 200)
        min = int(clamp(min*2, 0, 200))
        max = int(clamp(max*1.25, 0, 200))

    choices = list(monsters_levels[level].values())
    m = rng.choice(choices)
    if m and m not in monsters:
        monsters.append(m)
    else:
        m = add_monster(danger, rng, monsters, min, max)
    return m


def read_monsters_yml(file):
    global monsters_levels
    monsters = yaml.safe_load(file)['Body']
    for m in monsters:
        id = m['Id']
        level = m.get('Level')
        if not level:
            info(m['Name'] + " doesn't have a level")
            m['Level'] = 1
            level = 1
        if level not in monsters_levels:
            monsters_levels[level] = {id: m}
        else:
            monsters_levels[level][id] = m


def write_mobs(mob_scripts, out):
    success = write_scripts(mob_scripts, out)
    return success


class MobSpawn():
    def __init__(self, statement):
        self.statement = statement
        self.map = statement.args[0][0]
        self.monster_name = statement.args[2][0]
        self.monster_id = statement.args[3][0]

        # self.position = IntPoint(0, 0)
        # self.position.x = statement.args[0].get(1)
        # self.position.y = statement.args[0].get(2)

        # self.size = IntPoint(0, 0)
        # self.size.x = statement.args[0].get(3)
        # self.size.y = statement.args[0].get(4, 0)

        # self.amount = statement.args[3][1]
        # self.delay1 = statement.args[3].get(2)
        # self.delay2 = statement.args[3].get(3)

    def update(self):
        self.statement.args[2][0] = self.monster_name
        self.statement.args[3][0] = self.monster_id


class MobScript(ROScript):
    def __init__(self, file):
        global maps_mobs
        super().__init__(file)
        for s in self.root:
            if s.type == 'monster':
                mob = MobSpawn(s)
                if mob.map not in maps_mobs:
                    maps_mobs[mob.map] = []
                maps_mobs[mob.map].append(mob)


