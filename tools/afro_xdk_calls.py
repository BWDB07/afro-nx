#!/usr/bin/env python3
"""Count direct PPC branches into Afro's D3D library from outside it.

This is a discovery aid only: tail calls and indirect calls need manual tracing.
The binary image stays in the ignored out/ directory.
"""
import argparse
import bisect
import collections
import re
import struct
from pathlib import Path

BASE = 0x82000000


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--image', default='out/renut_image.bin')
    ap.add_argument('--init', default='app/generated/renut_init.cpp')
    ap.add_argument('--library', default='82340000:82380000')
    ap.add_argument('--code', default='82210000:82A05350')
    ap.add_argument('--source', help='restrict caller addresses, as hex lo:hi')
    ap.add_argument('--limit', type=int, default=100)
    args = ap.parse_args()
    lib_lo, lib_hi = (int(v, 16) for v in args.library.split(':'))
    code_lo, code_hi = (int(v, 16) for v in args.code.split(':'))
    source_range = tuple(int(v, 16) for v in args.source.split(':')) if args.source else None
    image = Path(args.image).read_bytes()
    starts = sorted(int(v, 16) for v in re.findall(
        r'\{ 0x([0-9A-F]{8}), sub_[0-9A-F]{8} \}', Path(args.init).read_text()))
    hits = collections.defaultdict(list)
    for source in range(code_lo, min(code_hi, BASE + len(image) - 3), 4):
        if lib_lo <= source < lib_hi:
            continue
        if source_range and not source_range[0] <= source < source_range[1]:
            continue
        word, = struct.unpack_from('>I', image, source - BASE)
        if word >> 26 != 18:
            continue
        displacement = word & 0x03fffffc
        if displacement & 0x02000000:
            displacement -= 0x04000000
        target = (displacement if word & 2 else source + displacement) & 0xffffffff
        if not lib_lo <= target < lib_hi:
            continue
        idx = bisect.bisect_right(starts, source) - 1
        owner = starts[idx] if idx >= 0 else 0
        hits[target].append((source, owner, bool(word & 1)))
    for target, sources in sorted(hits.items(), key=lambda item: -len(item[1]))[:args.limit]:
        callers = ','.join(f'{owner:08X}' for owner in sorted({owner for _, owner, _ in sources})[:8])
        print(f'{target:08X} {len(sources):4d} callers={callers}')


if __name__ == '__main__':
    main()
