#!/usr/bin/env python3
"""List PPC D-form memory references to selected device field displacements.

Candidates only: the base register must still be checked in disassembly to
prove it points at D3DDevice. Dynamic indexed accesses are not included.
"""
import argparse
import bisect
import re
import struct
from collections import defaultdict
from pathlib import Path

BASE = 0x82000000
OPS = {32: 'lwz', 33: 'lwzu', 34: 'lbz', 35: 'lbzu', 36: 'stw', 37: 'stwu',
       38: 'stb', 39: 'stbu', 40: 'lhz', 41: 'lhzu', 42: 'lha', 43: 'lhau',
       44: 'sth', 45: 'sthu', 48: 'lfs', 49: 'lfsu', 50: 'lfd', 51: 'lfdu',
       52: 'stfs', 53: 'stfsu', 54: 'stfd', 55: 'stfdu'}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('offsets', nargs='+', type=lambda s: int(s, 0))
    ap.add_argument('--image', default='out/renut_image.bin')
    ap.add_argument('--init', default='app/generated/renut_init.cpp')
    ap.add_argument('--lo', type=lambda s: int(s, 0), default=0x82340000)
    ap.add_argument('--hi', type=lambda s: int(s, 0), default=0x82380000)
    ap.add_argument('--any-immediate', action='store_true',
                    help='include every instruction with the 16-bit immediate (for indexed base calculations)')
    a = ap.parse_args()
    image = Path(a.image).read_bytes()
    starts = sorted(int(x, 16) for x in re.findall(
        r'\{ 0x([0-9A-F]{8}), sub_[0-9A-F]{8} \}',
        Path(a.init).read_text(encoding='utf-8')))
    wanted = {n & 0xffff for n in a.offsets}
    hits = defaultdict(list)
    for addr in range(a.lo, min(a.hi, BASE + len(image)), 4):
        word, = struct.unpack_from('>I', image, addr - BASE)
        op = OPS.get(word >> 26)
        if (op is None and not a.any_immediate) or (word & 0xffff) not in wanted:
            continue
        owner = starts[bisect.bisect_right(starts, addr) - 1]
        reg = (word >> 16) & 31
        hits[word & 0xffff].append((owner, addr, op or f'op{word >> 26}', reg))
    for offset in a.offsets:
        records = hits[offset & 0xffff]
        print(f'+0x{offset:04X}: {len(records)} references')
        for owner, addr, op, reg in records[:60]:
            print(f'  sub_{owner:08X}  0x{addr:08X}  {op} (r{reg})')
        if len(records) > 60:
            print(f'  ... {len(records) - 60} more')


if __name__ == '__main__':
    main()
