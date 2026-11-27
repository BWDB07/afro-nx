#!/usr/bin/env python3
"""Find PPC integer instructions whose low half equals a selected immediate.

Useful for checking whether an address is formed in code when no literal
function pointer or direct branch names it. Hits need manual PPC inspection.
"""
import argparse
import struct
from pathlib import Path

BASE = 0x82000000


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('immediates', nargs='+', type=lambda s: int(s, 0))
    ap.add_argument('--image', default='out/renut_image.bin')
    ap.add_argument('--lo', type=lambda s: int(s, 0), default=0x82210000)
    ap.add_argument('--hi', type=lambda s: int(s, 0), default=0x82A05350)
    ap.add_argument('--memory', action='store_true',
                    help='also include load/store D-form offsets')
    args = ap.parse_args()
    wanted = {value & 0xffff for value in args.immediates}
    image = Path(args.image).read_bytes()
    for address in range(args.lo, min(args.hi, BASE + len(image) - 3), 4):
        word, = struct.unpack_from('>I', image, address - BASE)
        opcode = word >> 26
        if (opcode in (14, 15, 24, 25, 26, 27, 28, 29)
                or (args.memory and 32 <= opcode <= 55)) and (word & 0xffff) in wanted:
            print(f'0x{address:08X} 0x{word:08X}')


if __name__ == '__main__':
    main()
