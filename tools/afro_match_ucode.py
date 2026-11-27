"""Locate SDK-dumped Xenos microcode in decoded Afro packages (offsets only)."""
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ucode', type=Path, required=True)
    parser.add_argument('--packages', type=Path, required=True)
    args = parser.parse_args()
    packages = [(path, path.read_bytes()) for path in args.packages.glob('*.bin')]
    files = list(args.ucode.glob('*.bin.*'))
    hits = []
    for path in files:
        data = path.read_bytes()
        # The SDK's dump is a native little-endian array of 32-bit Xenos words;
        # Xbox package contents are big-endian.
        signature = b''.join(data[i:i + 4][::-1] for i in range(0, min(len(data), 32), 4))
        found = [(package.name, raw.find(signature)) for package, raw in packages
                 if raw.find(signature) >= 0]
        if found:
            hits.append((path.name, found))
    print(f'{len(files)} microcodes, {len(hits)} matched in {len(packages)} decoded packages')
    for name, found in hits[:40]:
        print(name, found)


if __name__ == '__main__':
    main()
