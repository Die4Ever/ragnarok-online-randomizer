from ro_randomizer.base import *

class ScriptStatement():
    def __init__(self, content, sub, type, args, start_idx, end_idx):
        self.content = content
        self.sub = sub
        self.type = type
        self.args = args
        self.start_idx = start_idx
        self.end_idx = end_idx

    def __repr__(self):
        ret = ''
        for a in self.args:
            if a is None:
                ret = '//' + ret + 'None\t'
                continue

            for b in a:
                if b is None:
                    ret = '//' + ret + 'None,'
                    continue
                ret += str(b) + ','
            ret = ret[:-1] + '\t'
        return ret[:-1]


class CodeTree(listget):
    def __init__(self, content, start_idx):
        self.content = content
        self.type = 'tree'
        self.start_idx = start_idx

    def append(self, item):
        if item:
            super().append(item)

    def __str__(self):
        return type(self).__name__ + '(' + str(len(self)) + ')'

    def __repr__(self):
        ret = ''
        for s in self:
            ret += repr(s) + '\n'
        return ret


class ROScript():
    def __init__(self, file):
        info(file)
        self.file = file
        path = listget(Path(file).parts)
        self.name = path[-1]
        self.folder = path[-2]
        debug(self.__dict__)
        content = None
        with open(self.file) as f:
            content = f.read()
        self.root: CodeTree = parse_script(content)

    def __str__(self):
        return self.file + ' ' + str(self.root)

    def __repr__(self):
        return '/* randomized from ' + self.file + ' */\n' + repr(self.root)

    def write(self, output_path):
        path = output_path + self.folder + '/'
        if not exists_dir(path):
            os.makedirs(path, exist_ok=True)
        path += self.name
        info('writing to:', path)
        if exists(path):
            info("appending")
        with open(path, "a") as outfile:
            outfile.write( repr(self) )



def parse_script_line(content, sub, start_idx, end_idx):
    (line, separator, remaining) = content.partition('{')
    if not line:
        return None

    tabs = line.split('\t')
    args = listget()
    for t in tabs:
        args.append(listget(t.split(',')))

    type = None
    if len(args) > 1 and len(args[1]) > 0:
        type = args[1][0]
        if remaining:
            args[-1][-1] += separator+remaining

    if not type:
        return None
    return ScriptStatement(content, sub, type, args, start_idx, end_idx)



def parse_script(content, sub=False, idx=-1) -> CodeTree:
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
                buf += c
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
            continue

        if c == '{':
            in_curly_brace += 1
        elif c == '}':
            in_curly_brace -= 1
            if in_curly_brace == 0:
                buf += c
                buf = buf.strip()
                t = parse_script_line(buf, sub, start_idx, idx)
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


def write_scripts(scripts, output_path, description=''):
    if get_settings().get('dry_run'):
        warning('dry_run is enabled, not writing any files')
        return False

    if exists_dir(output_path):
        if not get_settings().get('unattended'):
            input("Press enter to delete old "+output_path+'\n(set unattended to true in your settings to skip this confirmation)')
        notice("Removing old "+output_path)
        shutil.rmtree(output_path)
    if not exists_dir(output_path):
        os.makedirs(output_path, exist_ok=True)

    notice('writing scripts to:', output_path)

    with open(output_path + ' randomizer_info.txt', "w") as outfile:
        out = '/*\n'
        out += datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + '\n'
        out += 'settings: ' + json.dumps(get_settings(), indent=4) + '\n\n'
        out += description
        out += '\n\n*/\n'
        outfile.write( out )

    for s in scripts.values():
        s.write(output_path)
    return True
