from ro_randomizer.base import *

# https://github.com/rathena/rathena/blob/master/doc/script_commands.txt#L133-L135
# <map name>{,<x>{,<y>{,<xs>{,<ys>}}}}%TAB%monster%TAB%<monster name>{,<monster level>}%TAB%<mob id>,<amount>{,<delay1>{,<delay2>{,<event>{,<mob size>{,<mob ai>}}}}}
# so many optional arguments will complicate this, need a way to differentiate the comma arguments and the tab arguments
