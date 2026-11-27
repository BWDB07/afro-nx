#!/usr/bin/env python3
"""Find big-endian pointer words that name selected Afro guest functions.

Reports only direct 32-bit words in the decoded image. Relocations, computed
pointers and immediate pairs need separate analysis. Image bytes stay ignored.
"""
import argparse
import struct
from pathlib import Path

BASE = 0x82000000


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('targets', nargs='+', type=lambda s: int(s, 0))
    ap.add_argument('--image', default='out/renut_image.bin')
    ap.add_argument('--lo', type=lambda s: int(s, 0), default=BASE)
    ap.add_argument('--hi', type=lambda s: int(s, 0), default=0x83000000)
    ap.add_argument('--context', type=int, default=0, help='adjacent 32-bit words on each side')
    a = ap.parse_args()
    image = Path(a.image).read_bytes()
    targets = set(a.targets)
    lo = max(0, a.lo - BASE)
    hi = min(len(image), a.hi - BASE)
    for off in range((lo + 3) & ~3, hi - 3, 4):
        value, = struct.unpack_from('>I', image, off)
        if value in targets:
            print(f'0x{BASE + off:08X} -> 0x{value:08X}')
            if a.context:
                for delta in range(-a.context, a.context + 1):
                    if delta == 0 or off + delta * 4 < 0 or off + delta * 4 + 4 > len(image):
                        continue
                    near, = struct.unpack_from('>I', image, off + delta * 4)
                    print(f'  {delta:+d}: 0x{near:08X}')


if __name__ == '__main__':
    main()
