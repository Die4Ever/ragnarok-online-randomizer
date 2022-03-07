from ro_randomizer.base import *

class ScriptStatement():
    def __init__(self, content, sub, type, args, start_idx, end_idx):
        self.content = content
        self.sub = sub
        self.type = type
        self.args = args
        self.start_idx = start_idx
        self.end_idx = end_idx


class CodeTree(list):
    def __init__(self, content, start_idx):
        self.content = content
        self.type = 'tree'
        self.start_idx = start_idx
    
    def append(self, item):
        if item:
            super().append(item)

class ROScript():
    def __init__(self, file):
        self.file = file
        content = None
        with open(self.file) as f:
            content = f.read()
        self.root = parse_script(content)



def parse_script_line(content, sub, start_idx, end_idx):
    (line, separator, remaining) = content.partition('{')
    if not line:
        return None

    tabs = line.split('\t')
    args = []
    for t in tabs:
        args.append(t.split(','))
    
    type = None
    if len(args) > 1 and len(args[1]) > 0:
        type = args[1][0]
        if remaining:
            args.append([separator+remaining])

    if not type:
        return None
    return ScriptStatement(content, sub, type, args, start_idx, end_idx)



def parse_script(content, sub=False, idx=-1):
    # if sub is true then we're inside of the curly braces of a script
    # so we would need to look for : to start a new tree branch, and ; to end a line
    in_block_comment = False
    in_line_comment = False
    in_curly_brace = 0
    buf = ''
    start_idx = 0
    prev = ''
    tree = CodeTree(content, idx)

    for c in content:
        idx+=1
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
            t = parse_script_line(buf, sub, start_idx, idx-2)
            tree.append(t)
            buf = ''
            start_idx = idx+1
            continue
        
        if c == '{':
            in_curly_brace += 1
            if in_curly_brace == 1:
                buf = ''
                start_idx = idx+1
                continue
        elif c == '}':
            in_curly_brace -= 1
            if in_curly_brace == 0:
                buf = buf.strip()
                t = parse_script(buf, True, start_idx)
                tree.append(t)
                buf = ''
                start_idx = idx+1
                continue
        elif c == '\n' and in_curly_brace == 0:
            buf = buf.strip()
            if len(buf):
                t = parse_script_line(buf, sub, start_idx, idx)
                tree.append(t)
            buf = ''
            start_idx = idx+1
            continue

        buf += c
    
    buf = buf.strip()
    if len(buf):
        t = parse_script_line(buf, sub, start_idx, idx)
        tree.append(t)
    return tree

