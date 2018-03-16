import nuke
import os
import re
import functools


def normpath(path):
    return os.path.normpath(
            os.path.normcase(
                os.path.realpath(path)))


def path_equals(path1, path2):
    return normpath(path1) == normpath(path2)


def split_path_until(path, level=3):
    main_dir = path
    comps = []
    comp = None

    for idx in range(level):
        main_dir, basename = os.path.split(main_dir)
        if comp is not None:
            comps.insert(0, comp)
        comp = basename

    return main_dir, basename, comps


def _select_iter_func(mode, nodes):

    if mode == 'all':
        func = functools.partial(nuke.allNodes, 'Read')
    elif mode == 'provided':
        func = functools.partial(iter, nodes)
    elif mode == 'selected':
        func = functools.partial(nuke.selectedNodes, 'Read')
    else:
        raise ValueError('mode=%s is not valid' % mode)

    return func


def get_render_layers_from_comp(mode='selected', nodes=None):
    all_layers = dict()

    for node in _select_iter_func(mode, nodes)():

        path = node.knob('file').getValue()
        main_dir, rl, children = split_path_until(path, level=3)

        if main_dir and rl:

            _dir = normpath(main_dir)
            _rl = os.path.normcase(rl)

            rls = all_layers.get(_dir, dict())
            dirs = rls.get(_rl, [])
            dirs.append(path)

            rls[_rl] = dirs
            all_layers[_dir] = rls

    return all_layers


def get_render_layers_in_path(path):
    layers = []
    main_dir, rl, children = split_path_until(path)
    if main_dir and rl and os.path.isdir(main_dir):
        for name in os.listdir(main_dir):
            if os.path.isdir(os.path.join(main_dir, name)):
                layers.append(name)
    return layers


def range_exists(path, start, end, by=1, match_pattern=re.compile('#+'),
                 criterion=all):
    start = int(start)
    end = int(end)
    path = match_pattern.sub(lambda match: '%%0%dd' % len(match.group()), path)
    existence = [os.path.exists(path % num) for num in xrange(start, end, by)]
    return criterion(existence)


def replace_render_layers(
        maps, main_dir=None, mode='selected', nodes=None):
    nodes, bad_nodes = [], []

    maps = {k.lower(): v for k, v in maps.items()}

    for node in _select_iter_func(mode, nodes)():
        path = node.knob('file').getValue()

        try:
            _dir, rl, (passname, filename) = split_path_until(path)
        except ValueError:
            continue

        if rl.lower() in maps and (
                not main_dir or path_equals(main_dir, _dir)):

            rl2 = maps[rl.lower()]

            filename_new = filename.replace(rl, rl2)
            passname_new = passname.replace(rl, rl2)
            new_rl_dir = os.path.join(main_dir, rl2)

            new_path = os.path.join(new_rl_dir, passname_new, filename_new)
            new_path = new_path.replace('\\', '/')

            if range_exists(new_path, node.knob('first').getValue(),
                            node.knob('last').getValue()):
                node.knob('file').setValue(new_path)
                nodes.append(nodes)

            else:
                node.knob('tile_color').setValue(0xff000000)
                bad_nodes.append(node)

    return nodes, bad_nodes


if __name__ == "__main__":
    pass
