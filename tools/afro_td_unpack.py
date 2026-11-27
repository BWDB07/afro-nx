"""Unpack Afro's Xbox XMem TD files with the local libmspack LZX test tool.

The 0FF512ED wrapper holds fixed-pitch compressed segments. Each segment has
big-endian 16-bit lengths before its LZX frames. Output is game data: keep it
under ignored out/ or outside this repository.
"""
import argparse
import pathlib
import subprocess
import tempfile


def unpack(source: pathlib.Path, target: pathlib.Path, decoder: pathlib.Path):
    data = source.read_bytes()
    if len(data) < 16 or data[:4] != bytes.fromhex('0ff512ed'):
        raise ValueError('not an Xbox XMem TD file')
    flags = int.from_bytes(data[12:16], 'big')
    count = (flags >> 6) & 0xFFFF
    size_bits = (20, 32, 0, 0)[(flags >> 22) & 3]
    pitch = 0x8000 << ((flags >> 4) & 3)
    window_bits = (flags & 15) + 15
    if not count or not size_bits or not 15 <= window_bits <= 21:
        raise ValueError('unsupported XMem TD flags')
    table_bytes = ((count * size_bits + 31) // 32) * 4
    payload = 16 + table_bytes
    if payload > len(data):
        raise ValueError('truncated segment table')
    table = int.from_bytes(data[16:payload], 'big')
    sizes = [(table >> (table_bytes * 8 - (i + 1) * size_bits)) & ((1 << size_bits) - 1)
             for i in range(count)]
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('wb') as output, tempfile.TemporaryDirectory() as temporary:
        segment_input = pathlib.Path(temporary) / 'segment.lzx'
        segment_output = pathlib.Path(temporary) / 'segment.raw'
        for index, size in enumerate(sizes):
            start = payload if index == 0 else index * pitch
            end = min((index + 1) * pitch, len(data))
            if start > end:
                raise ValueError(f'segment {index} outside file')
            cursor = start
            remaining = size
            frames = bytearray()
            while remaining:
                if cursor + 2 > end:
                    raise ValueError(f'segment {index} truncated frame header')
                packed = int.from_bytes(data[cursor:cursor + 2], 'big')
                cursor += 2
                if not packed or cursor + packed > end:
                    raise ValueError(f'segment {index} truncated frame')
                frames.extend(data[cursor:cursor + packed])
                cursor += packed
                remaining -= min(remaining, 0x8000)
            segment_input.write_bytes(frames)
            subprocess.run([str(decoder), str(segment_input), str(segment_output), str(size),
                            str(window_bits)], check=True)
            decoded = segment_output.read_bytes()
            if len(decoded) != size:
                raise ValueError(f'segment {index} decoded {len(decoded)}, expected {size}')
            output.write(decoded)
            if index % 32 == 0 or index + 1 == count:
                print(f'{index + 1}/{count} segments, {output.tell()} bytes', flush=True)
    return sum(sizes)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=pathlib.Path)
    parser.add_argument('target', type=pathlib.Path)
    parser.add_argument('--decoder', type=pathlib.Path, default=pathlib.Path('out/tools/lzx_tool.exe'))
    args = parser.parse_args()
    print(f'unpacked {unpack(args.source, args.target, args.decoder)} bytes')
