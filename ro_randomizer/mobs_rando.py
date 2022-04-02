from os import stat
from ro_randomizer.base import *
from ro_randomizer.script import *
from ro_randomizer.map import *
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
    info('starting mobs_rando()')
    set_danger_ratings()
    monsters_levels.clear()
    monsters_files = get_settings()['inputs']['monsters']
    for filename in monsters_files:
        info('reading monsters file:', filename)
        with open(filename, "r") as file:
            read_monsters_yml(file)

    for input in get_settings()['inputs']['mobs']:
        info('reading mobs from: ' + input+'/*')
        for file in insensitive_glob(input+'/*'):
            if file.endswith('.txt'):
                mob_scripts[file] = MobScript(file)

    info('randomizing mobs')
    for map in maps.values():
        rando_map_mobs(map)

    write_mobs(mob_scripts, get_settings()['outputs']['mobs'])


def set_danger_ratings():
    # TODO: pathfinding?
    seed = get_settings()['seed']
    danger_settings = get_settings()['danger']
    mult = danger_settings['max_city_mult']
    lowbie_city_distance = danger_settings['city_distance']
    dungeon_mult = danger_settings['dungeon_mult']

    for m in maps.values():
        if m.type == MapTypes.CITY:
            rng = random.Random(crc32('set_danger_ratings city', m.name, seed))
            m.danger = rng.uniform(0.1, 1)

    for m in maps.values():
        if m.type == MapTypes.CITY or not m.closest_city in maps:
            continue
        city = maps[m.closest_city]
        rng = random.Random(crc32('set_danger_ratings', m.name, seed))
        dist = 10000
        if m.position is not None and city.position is not None:
            dist = m.position.dist(city.position)
        if dist <= lowbie_city_distance:
            m.danger = int(rng.uniform(1, mult) * city.danger * clamp(dist/300, 0.25, mult))
        else:
            m.danger = rng.randint(10, 100)
        if m.type == MapTypes.DUNGEON:
            m.danger *= dungeon_mult
        m.danger = clamp(m.danger, 1, 200)


def rando_map_mobs(map):
    if map.name not in maps_mobs:
        return
    monsters = []
    danger = map.danger
    seed = get_settings()['seed']
    rng = random.Random( crc32('rando_map_mobs', seed, map.name ) )
    num = rng.randint(4, 7)
    while len(monsters) < num:
        add_monster(danger, rng, monsters)

    shuffled = []
    for mob in maps_mobs[map.name]:
        if len(shuffled) == 0:
            shuffled = rng.sample(monsters, k=len(monsters))
        m = shuffled.pop()
        mob.monster_name = 'Lvl ' + str(m['Level']) + ' ' + m['Name']
        mob.monster_id = m['Id']
        mob.update()


def add_monster(danger, rng, monsters, min=-10, max=5):
    global monsters_levels
    level = -1
    while level not in monsters_levels:
        min = clamp(min*1.5, -danger, -1)
        max = clamp(max*1.5, 1, 200)
        level = danger + rng.randint(int(min), int(max))
        level = clamp(level, 1, 200)

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
        if m['AegisName'].startswith('E_') or m['AegisName'].startswith('G_'):
            continue
        id = m['Id']
        level = m.get('Level')
        if not level:
            warning(m['Name'] + ' ('+str(id)+") doesn't have a level")
            m['Level'] = 1
            level = 1
        elif level == 1:
            info(m['Name'] + ' ('+str(id)+") is level 1")
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
        self.level = None #statement.args[2].get(1, None)
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
        if self.level:
            self.statement.args[2] = [self.monster_name, self.level]
        else:
            self.statement.args[2] = [self.monster_name]
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


