"""Read the exception and candidate return addresses from a Windows minidump.

Uses only Python's standard library; addresses are printed as module offsets so
they can be resolved against the matching PDB. This is a stack scan, not an
unwinder: only the exception RIP is certain.
"""
import argparse
import pathlib
import struct


def u32(data, at):
    return struct.unpack_from('<I', data, at)[0]


def u64(data, at):
    return struct.unpack_from('<Q', data, at)[0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('dump', type=pathlib.Path)
    args = parser.parse_args()
    data = args.dump.read_bytes()
    if data[:4] != b'MDMP':
        raise ValueError('not a minidump')
    count, directory = u32(data, 8), u32(data, 12)
    streams = {u32(data, directory + 12*i): (u32(data, directory + 12*i + 4),
                                                 u32(data, directory + 12*i + 8))
               for i in range(count)}
    modules = []
    size, at = streams[4]
    for i in range(u32(data, at)):
        entry = at + 4 + i*108
        base, image_size, name_rva = u64(data, entry), u32(data, entry+8), u32(data, entry+20)
        name_size = u32(data, name_rva)
        name = data[name_rva+4:name_rva+4+name_size].decode('utf-16le', 'replace')
        modules.append((base, base+image_size, pathlib.PureWindowsPath(name).name))

    def fmt(addr):
        for base, end, name in modules:
            if base <= addr < end:
                return f'{name}+0x{addr-base:X}'
        return f'0x{addr:X}'

    size, at = streams[6]
    thread_id = u32(data, at)
    code, address = u32(data, at+8), u64(data, at+24)
    ctx_size, ctx_rva = u32(data, at+160), u32(data, at+164)
    rsp, rip = u64(data, ctx_rva+0x98), u64(data, ctx_rva+0xF8)
    print(f'exception thread={thread_id} code=0x{code:X} address={fmt(address)}')
    print(f'context size={ctx_size} RSP=0x{rsp:X} RIP={fmt(rip)}')

    size, at = streams[3]
    for i in range(u32(data, at)):
        entry = at + 4 + i*48
        if u32(data, entry) != thread_id:
            continue
        stack_start = u64(data, entry+24)
        stack_size, stack_rva = u32(data, entry+32), u32(data, entry+36)
        print(f'stack 0x{stack_start:X}..0x{stack_start+stack_size:X}')
        if not stack_start <= rsp < stack_start+stack_size:
            break
        first = rsp-stack_start
        for off in range(first, min(first+0x800, stack_size), 8):
            value = u64(data, stack_rva+off)
            label = fmt(value)
            if not label.startswith('0x') or 0x82000000 <= value < 0x83000000:
                print(f'RSP+0x{off-first:03X} {label}')
        break


if __name__ == '__main__':
    main()
