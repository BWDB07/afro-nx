#!/usr/bin/env python3
"""Disable inherited Katamari hooks without an Afro address census.

The 222 state-table functions are separately validated by afro_state_map.py.
All other active declarations need an explicit Afro address in ANCHORS.
"""
import argparse
import re
from pathlib import Path

from afro_hook_anchors import ANCHORS, ROOT

HOOKS = ROOT / 'app/src/renut_engine/gpu/d3d/hooks'
STATE_NAME = re.compile(r'(?:Set|Get)(?:Render|Sampler)StateHook<\d+>')
DECL = re.compile(r'BANJO_RENUT_HOOK\(sub_([0-9A-F]{8}),\s*([^);]+)\);')
RAW = re.compile(r'BANJO_RENUT_HOOK_RAW\(sub_([0-9A-F]{8})\)')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    args = ap.parse_args()
    disabled = []
    for path in sorted(HOOKS.glob('*.cpp')):
        source = path.read_bytes().decode('utf-8')

        def ordinary(match):
            address, name = match.groups()
            name = name.strip()
            if name in ANCHORS or STATE_NAME.fullmatch(name):
                return match.group(0)
            disabled.append((path.name, address, name))
            return match.group(0).replace('BANJO_RENUT_HOOK(', 'BANJO_RENUT_UNHOOKED_HOOK(', 1)

        rewritten = DECL.sub(ordinary, source)

        def raw(match):
            disabled.append((path.name, match.group(1), 'raw'))
            return match.group(0).replace('BANJO_RENUT_HOOK_RAW(', 'BANJO_RENUT_UNHOOKED_HOOK_RAW(', 1)

        rewritten = RAW.sub(raw, rewritten)
        if args.apply and rewritten != source:
            path.write_bytes(rewritten.encode('utf-8'))
    for path, address, name in disabled:
        print(f'{path} sub_{address} {name}')
    print(f'{len(disabled)} inherited hooks need Afro identities'
          + (' (disabled)' if args.apply else ' (dry run)'))


if __name__ == '__main__':
    main()
