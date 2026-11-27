#!/usr/bin/env python3
"""Pair the big-endian GPR loads and stores in generated Xbox ABI helpers."""
import argparse
from pathlib import Path
import re


HELPER = re.compile(
    r'(DEFINE_REX_FUNC\(__(save|rest)gprlr_(\d+)\) \{\n'
    r'\tREX_FUNC_PROLOGUE\(\);\n)([^}]*)(\})'
)
START = '#if defined(__SWITCH__) && defined(__aarch64__) && !defined(REX_GPR_STACK_PAIRS_OFF)'
FALLBACK = '#else // REX_GPR_STACK_PAIRS'
END = '#endif // REX_GPR_STACK_PAIRS'
PAIRED = re.compile(rf'{re.escape(START)}\n.*?{re.escape(FALLBACK)}\n(.*?){re.escape(END)}\n', re.S)


def pair_helper(match):
    prologue, operation, first, body, close = match.groups()
    first = int(first)
    if not 14 <= first <= 30:
        return match.group()

    saving = operation == 'save'
    transfers = []
    for reg in range(first, 32):
        disp = (reg - 33) * 8
        if saving:
            transfers.append(f'\t// std r{reg},{disp}(r1)\n'
                             f'\tREX_STORE_D_U64(ctx.r1.u32, {disp}, ctx.r{reg}.u64);\n')
        else:
            transfers.append(f'\t// ld r{reg},{disp}(r1)\n'
                             f'\tctx.r{reg}.u64 = REX_LOAD_D_U64(ctx.r1.u32, {disp});\n')
    if saving:
        tail = '\t// stw r12,-8(r1)\n\tREX_STORE_D_U32(ctx.r1.u32, -8, ctx.r12.u32);\n'
    else:
        tail = ('\t// lwz r12,-8(r1)\n\tctx.r12.u64 = REX_LOAD_D_U32(ctx.r1.u32, -8);\n'
                '\t// mtlr r12\n\tREX_LR_WRITE(ctx.r12);\n')
    if body != ''.join(transfers) + tail + '\t// blr \n\treturn;\n':
        return match.group()

    paired_count = len(transfers) & ~1
    displacement = (first - 33) * 8
    lines = [START, '\tstatic_assert(sizeof(PPCRegister) == 8);']
    for index in range(1, paired_count):
        lines.append(f'\tstatic_assert(offsetof(PPCContext, r{first + index}) == '
                     f'offsetof(PPCContext, r{first}) + {index * 8});')
    lines.extend([
        f'\tauto* regs = reinterpret_cast<unsigned char*>(&ctx) + offsetof(PPCContext, r{first});',
        f'\tauto* stack = REX_ADDR_D(ctx.r1.u32, {displacement});',
    ])
    source, destination = ('regs', 'stack') if saving else ('stack', 'regs')
    for offset in range(0, paired_count * 8, 16):
        lines.append(f'\tvst1q_u8({destination} + {offset}, vrev64q_u8(vld1q_u8({source} + {offset})));')
    lines.append(FALLBACK)
    scalar = ''.join(transfers[:paired_count])
    return prologue + '\n'.join(lines) + '\n' + scalar + END + '\n' + body[len(scalar):] + close


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gen', type=Path, required=True)
    parser.add_argument('--restore', action='store_true')
    options = parser.parse_args()
    count = 0
    for path in sorted(options.gen.glob('renut_recomp.*.cpp')):
        original = path.read_bytes()
        text = original.decode('utf-8')
        normalized = text.replace('\r\n', '\n')
        restored = PAIRED.sub(r'\1', normalized)
        updated = restored if options.restore else HELPER.sub(pair_helper, restored)
        count += updated.count(START)
        if original.find(b'\r\n') != -1:
            updated = updated.replace('\n', '\r\n')
        if updated != text:
            path.write_bytes(updated.encode('utf-8'))
    print(f'gpr_stack_pairs: {count} paired helpers')


if __name__ == '__main__':
    main()
