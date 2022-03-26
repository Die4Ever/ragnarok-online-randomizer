import ro_randomizer.base
from ro_randomizer.base import *
from ro_randomizer.map import *

class MapsGrid(ShuffledGrid):
    def items_can_connect(self, m1, m2, move):
        # TODO: how to handle corner teleporters? we can check the num1 and num2 returned from maps_can_connect and score them up?
        if len(m1.warps) < 1 or len(m2.warps) < 1:
            warning('maps_can_connect failed, len('+m1.name+'.warps): ' + str(len(m1.warps)) + ', len('+m2.name+'.warps): ' + str(len(m2.warps)) )

        num1 = len(m1.get_warps_on_side(move.negative()))
        num2 = len(m2.get_warps_on_side(move))

        # do we want to also return num1 and num2?
        if num1 > 0 and num2 > 0:
            return True
        return False

    def clear_connections(self):
        for map in self.items:
            map.position = None
            if map.type != MapTypes.INDOORS and map.conns_in > 0:
                for w in map.warps:
                    to = maps.get(w.toMap)
                    if to and to.type != MapTypes.INDOORS:
                        w.toMap = None

    def connect_items(self, map1, map2, move, spot):
        warps1 = map1.get_warps_on_side(move.negative())
        warps2 = map2.get_warps_on_side(move)
        offset = move.multiply(map1.size)
        linked = 0
        # for each warps1, find the nearest available warps2 and link them
        trace('connect_items('+repr(map1)+', '+repr(map2)+') warps1: '+str(len(warps1))+', warps2: '+str(len(warps2)))
        for w1 in warps1:
            if w1.toMap is not None:
                continue
            closest = None
            for w2 in warps2:
                if w2.toMap is not None:
                    continue
                # adjust w2pos by move or spot, and compare it to w1.fromPos
                w2pos = w2.fromPos.add(offset)
                closest = w1.fromPos.closest(w2pos, w2, closest)
            # make the link
            if closest:
                w2 = closest[0]
                w1.toMap = w2.map
                w1.toPos = w2.fromPos
                w2.toMap = w1.map
                w2.toPos = w1.fromPos
                linked += 1
                trace('connect_items linked '+repr(w1)+', '+repr(w2))
        return linked


class WorldGrid(ShuffledGrid):
    def __init__(self, rand, items):
        ShuffledGrid.__init__(self, rand, items)
        # build a list of warps that we control
        # these are the ones we clear in clear_connections
        self.warps = []
        for biome in items:
            for map in biome.items:
                map.position = None
                if map.type != MapTypes.INDOORS and map.conns_in > 0:
                    for w in map.warps:
                        if w.toMap is None:
                            self.warps.append(w)

    def items_can_connect(self, biome1, biome2, move):
        edge1 = biome1.get_items_on_edge(move)
        edge2 = biome2.get_items_on_edge(move.negative())
        for e1 in edge1:
            for e2 in edge2:
                if biome1.items_can_connect(e1, e2, move):
                    return True
        return False

    def clear_connections(self):
        for biome in self.items:
            for map in biome.items:
                map.position = None
        for w in self.warps:
            w.toMap = None
        pass

    def connect_items(self, biome1, biome2, move, spot):
        edge1 = biome1.get_items_on_edge(move)
        edge2 = biome2.get_items_on_edge(move.negative())
        linked = 0
        for e1 in edge1:
            for e2 in edge2:
                linked += biome1.connect_items(e1, e2, move, spot)
        return linked

