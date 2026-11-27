#!/usr/bin/env python3
"""Report Afro's XDK state getter/setter candidates for inherited Renut hooks.

The two 101/20-record tables were found by afro_state_table_scan.py. A matching
index is strong structural evidence, but device field offsets still need an
Afro audit before any native state hook is enabled. The report is not source.
"""
import argparse
import re
import struct
from pathlib import Path

BASE = 0x82000000
TABLES = {'Render': (0x82865180, 101), 'Sampler': (0x82865640, 20)}
HOOK = re.compile(
    r'BANJO_RENUT_(?:HOOK|UNHOOKED_HOOK)\((sub_[0-9A-F]{8}),\s*'
    r'(Set|Get)(Render|Sampler)StateHook<(\d+)>\);')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--image', default='out/renut_image.bin')
    ap.add_argument('--hooks', default='app/src/renut_engine/gpu/d3d/hooks/state.cpp')
    ap.add_argument('--init', default='app/generated/renut_init.cpp')
    ap.add_argument('--out', default='out/afro_state_map.txt')
    ap.add_argument('--apply', action='store_true',
                    help='rewrite only the 222 state hook declaration addresses; AFRO_RENUT_HOOKS stays off')
    a = ap.parse_args()
    image = Path(a.image).read_bytes()
    hooks = Path(a.hooks).read_bytes().decode('utf-8')  # keep the source's exact line endings
    generated = set(re.findall(r'\{ 0x([0-9A-F]{8}), sub_[0-9A-F]{8} \}',
                               Path(a.init).read_text(encoding='utf-8')))
    rows = []
    missing = []
    for old, verb, kind, idx in HOOK.findall(hooks):
        start, count = TABLES[kind]
        idx = int(idx)
        if idx >= count:
            missing.append((old, verb, kind, idx))
            continue
        getter, setter, default = struct.unpack_from('>III', image, start - BASE + 12 * idx)
        new = getter if verb == 'Get' else setter
        rows.append((kind, idx, verb, old, f'sub_{new:08X}', default))
    rows.sort(key=lambda r: (r[0], r[1], r[2]))
    unresolved = sorted({new for _, _, _, _, new, _ in rows if new[4:] not in generated})
    duplicate = len(rows) - len({new for _, _, _, _, new, _ in rows})
    lines = [f'# Afro state table candidates: render 0x{TABLES["Render"][0]:08X} x101, '
             f'sampler 0x{TABLES["Sampler"][0]:08X} x20',
             '# kind index get/set inherited_address Afro_address default; mapping alone does not enable hooks']
    for kind, idx, verb, old, new, default in rows:
        lines.append(f'{kind.lower():7} {idx:3d} {verb.lower():3} {old} {new} 0x{default:08X}')
    lines += [f'# {len(rows)} declared hooks matched, {len(missing)} out-of-range, '
              f'{len(unresolved)} missing generated starts, {duplicate} duplicate targets']
    if missing:
        lines += [f'# missing {item}' for item in missing]
    if unresolved:
        lines += [f'# unresolved {item}' for item in unresolved]
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('\n'.join(lines[:20] + lines[-1:]))
    if missing or unresolved or duplicate:
        raise SystemExit(1)
    if a.apply:
        if len(rows) != 222:
            raise SystemExit(f'expected 222 inherited state declarations, got {len(rows)}')
        replacements = {(kind, idx, verb): new for kind, idx, verb, _, new, _ in rows}
        changed = 0

        def remap(match):
            nonlocal changed
            old, verb, kind, index = match.groups()
            new = replacements[(kind, int(index), verb)]
            if old != new:
                changed += 1
            return match.group(0).replace(old, new, 1)

        rewritten, matched = HOOK.subn(remap, hooks)
        if matched != 222:
            raise SystemExit(f'expected 222 replacements, got {matched}')
        Path(a.hooks).write_bytes(rewritten.encode('utf-8'))
        print(f'afro_state_map: {changed} state declarations moved to Afro addresses')


if __name__ == '__main__':
    main()
