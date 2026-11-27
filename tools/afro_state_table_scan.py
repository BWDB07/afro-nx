#!/usr/bin/env python3
"""Find candidate XDK D3D state tables in Afro's decoded image.

Each record is three big-endian words: getter code pointer, setter code pointer,
and the default value. A long uninterrupted run is a candidate; this does not
assert state identity or authorize hooks. Game bytes stay outside Git.
"""
import argparse
import struct

BASE = 0x82000000


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--image', default='out/renut_image.bin')
    ap.add_argument('--code-lo', type=lambda x: int(x, 0), default=0x82150000)
    ap.add_argument('--code-hi', type=lambda x: int(x, 0), default=0x828419F4)
    ap.add_argument('--min-run', type=int, default=12)
    a = ap.parse_args()
    image = open(a.image, 'rb').read()

    def record(off):
        getter, setter, default = struct.unpack_from('>III', image, off)
        if (a.code_lo <= getter < a.code_hi and not getter & 3 and
                a.code_lo <= setter < a.code_hi and not setter & 3 and
                not a.code_lo <= default < a.code_hi):
            return getter, setter, default
        return None

    runs = []
    for phase in (0, 4, 8):
        off = phase
        while off + 12 <= len(image):
            if record(off) is None:
                off += 12
                continue
            start = off
            entries = []
            while off + 12 <= len(image) and (value := record(off)) is not None:
                entries.append(value)
                off += 12
            if len(entries) >= a.min_run:
                runs.append((start, entries))
    for off, entries in sorted(runs, key=lambda x: len(x[1]), reverse=True)[:25]:
        print(f'0x{BASE + off:08X}  {len(entries)} records')
        for i, (getter, setter, default) in enumerate(entries[:4]):
            print(f'  {i:3d}  get=0x{getter:08X}  set=0x{setter:08X}  default=0x{default:08X}')


if __name__ == '__main__':
    main()
