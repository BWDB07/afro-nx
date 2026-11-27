"""Locate visible Xenos shader containers in Afro files without copying game bytes.

The output contains counts and offsets only. Package compression may hide
containers, so a zero count is a storage-format finding, not a shader absence.
"""
import argparse
import json
import mmap
import pathlib
import struct

MAGIC = b'\x10\x2a\x11'


def scan(path):
    found = []
    with path.open('rb') as file:
        if not file.seek(0, 2):
            return found
        file.seek(0)
        with mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as data:
            at = 0
            while (at := data.find(MAGIC, at)) >= 0:
                at += 1
                start = at - 1
                if start + 0x24 > len(data):
                    continue
                virt, phys = struct.unpack_from('>II', data, start + 4)
                ct, dt, so = struct.unpack_from('>III', data, start + 0x10)
                if not (0x24 <= virt < 0x10000 and 0 < phys < 0x100000 and start + virt + phys <= len(data)):
                    continue
                if ct >= virt or dt >= virt or not (0x24 <= so < virt - 8):
                    continue
                poff, psize = struct.unpack_from('>II', data, start + so)
                if poff + psize != phys:
                    continue
                kind = 'vs' if struct.unpack_from('>I', data, start)[0] & 1 else 'ps'
                found.append({'offset': start, 'bytes': virt + phys, 'kind': kind})
    return found


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--image', type=pathlib.Path, required=True)
    parser.add_argument('--game', type=pathlib.Path, required=True)
    parser.add_argument('--out', type=pathlib.Path, required=True)
    args = parser.parse_args()
    rows = []
    for path in [args.image, *args.game.rglob('*.bin')]:
        containers = scan(path)
        if containers:
            rows.append({'file': str(path.relative_to(args.game)) if path.is_relative_to(args.game) else '<decoded image>',
                         'containers': containers})
            print(f'{rows[-1]["file"]}: {len(containers)} containers')
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(rows, indent=1) + '\n', encoding='utf-8')
    print(f'{sum(len(row["containers"]) for row in rows)} containers in {len(rows)} files -> {args.out}')


if __name__ == '__main__':
    main()
