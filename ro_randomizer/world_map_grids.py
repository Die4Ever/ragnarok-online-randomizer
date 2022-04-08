import ro_randomizer.base
from ro_randomizer.base import *
from ro_randomizer.map import *

class MapsGrid(ShuffledGrid):
    def items_can_connect(self, m1, m2, move):
        # TODO: how to handle corner teleporters? we can check the num1 and num2 returned from maps_can_connect and score them up?
        if len(m1.warps) < 1 or len(m2.warps) < 1:
            warning('maps_can_connect failed, len('+m1.name+'.warps):', len(m1.warps), ', len('+m2.name+'.warps):', len(m2.warps) )

        num1 = len(m1.get_warps_on_side(move))
        num2 = len(m2.get_warps_on_side(move.negative()))

        # do we want to also return num1 and num2?
        if num1 > 0 and num2 > 0:
            return True
        return False

    def clear_connections(self):
        for map in self.items:
            map.position = None
            if map.type == MapTypes.INDOORS or map.type == MapTypes.IGNORE or map.conns_in == 0:
                continue
            for w in map.warps:
                to = maps.get(w.toMap)
                if w.toMap != w.map and to and to.type != MapTypes.INDOORS and to.type != MapTypes.IGNORE:
                    w.toMap = None

    def connect_warps(self, warps1, warps2, move, map1size):
        offset = move.multiply(map1size)
        linked = 0
        # for each warps1, find the nearest available warps2 and link them
        trace('connect_warps(', move, ') warps1: ', len(warps1), ', warps2: ', len(warps2))
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
                w1.toPos = w2.inPos
                w2.toMap = w1.map
                w2.toPos = w1.inPos
                linked += 1
                trace('connect_warps linked', w1, ',', w2)
        return linked


    def connect_items(self, map1, map2, move, spot):
        warps1 = map1.get_warps_on_side(move)
        warps2 = map2.get_warps_on_side(move.negative())
        return self.connect_warps(warps1, warps2, move, map1.size)


class WorldGrid(ShuffledGrid):
    def __init__(self, rand, items):
        ShuffledGrid.__init__(self, rand, items)
        # build a list of warps that we control
        # these are the ones we clear in clear_connections
        self.warps = []
        for biome in items:
            for map in biome.items:
                map.position = None
                if map.type != MapTypes.INDOORS and map.type != MapTypes.IGNORE and map.conns_in > 0:
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
        for m1 in edge1:
            for m2 in edge2:
                linked += biome1.connect_items(m1, m2, move, spot)

        #for m1 in edge1:
        #    for m2 in edge2:
        #        linked += biome1.connect_warps(m1.warps, m2.warps, move, m1.size)

        # desperately link anything? or maybe I should link within the biome more?
        for x1 in biome1.grid:
            for m1 in x1:
                if m1 is None:
                    continue
                for x2 in biome2.grid:
                    for m2 in x2:
                        if m2 is None:
                            continue
                        linked += biome1.connect_items(m1, m2, move, spot)
        return linked

    def get_finalize_connections_moves(self):
        # we also want double steps and knight's moves at the end of the list, just to fill in any unlinked warps
        return (moves + corners + knights)


