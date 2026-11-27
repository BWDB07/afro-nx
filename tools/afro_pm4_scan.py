#!/usr/bin/env python3
"""Locate PPC immediates that may form Xenos PM4 packet headers.

This is a shortlist for manual disassembly, not a declaration that each hit
issues a packet. The opcode byte sits in bits 8..15 of a type-3 PM4 header.
"""
import argparse
import bisect
import re
import struct
from pathlib import Path

BASE = 0x82000000


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('opcodes', nargs='+', help='PM4 opcode bytes, e.g. 0x22 0x36')
    ap.add_argument('--image', default='out/renut_image.bin')
    ap.add_argument('--init', default='app/generated/renut_init.cpp')
    ap.add_argument('--lo', type=lambda x: int(x, 0), default=0x82300000)
    ap.add_argument('--hi', type=lambda x: int(x, 0), default=0x82380000)
    ap.add_argument('--literal', action='store_true',
                    help='also report big-endian PM4 packet words in the image')
    a = ap.parse_args()
    wanted = {int(x, 0) for x in a.opcodes}
    image = Path(a.image).read_bytes()
    starts = sorted(int(x, 16) for x in re.findall(
        r'\{ 0x([0-9A-F]{8}), sub_[0-9A-F]{8} \}', Path(a.init).read_text()))
    for addr in range(a.lo, min(a.hi, BASE + len(image)), 4):
        word, = struct.unpack_from('>I', image, addr - BASE)
        if (a.literal and (word & 0xff000000) == 0xC0000000
                and ((word >> 8) & 0xff) in wanted and (word & 0xff) <= 7):
            idx = bisect.bisect_right(starts, addr) - 1
            owner = starts[idx] if idx >= 0 else 0
            print(f'0x{addr:08X}  owner=0x{owner:08X}  literal=0x{word:08X}')
        # ori/oris/addi often finish a type-3 packet constant (0xC...OOOO).
        if word >> 26 not in (14, 24, 25):
            continue
        imm = word & 0xFFFF
        if (imm >> 8) not in wanted:
            continue
        idx = bisect.bisect_right(starts, addr) - 1
        owner = starts[idx] if idx >= 0 else 0
        print(f'0x{addr:08X}  owner=0x{owner:08X}  word=0x{word:08X}  imm=0x{imm:04X}')


if __name__ == '__main__':
    main()
