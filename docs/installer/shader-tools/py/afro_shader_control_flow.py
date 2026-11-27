#!/usr/bin/env python3
"""Diagnostic only: lower Afro's linear Xenos shader switch to ordered guards.

The recompiler's case labels fall through and every explicit pc assignment is
followed by continue. An ``active`` flag starts execution at the selected case,
then remains true for fall-through cases. A continue restarts the loop and
recomputes the starting case from ``pc``. This preserves backward light loops
without keeping a giant switch live in the compiler. The result is diagnostic
only and must pass picture verification before it can replace the original.
"""

import argparse
import pathlib
import re


START = "\tuint pc = 0;\n\twhile (true)\n\t{\n\t\tswitch (pc)\n\t\t{\n"
END = "\t\t}\n\t\tbreak;\n\t}\n}"
CASE = re.compile(r"(?m)^\t\tcase (\d+):")
JUMP = re.compile(r"pc = (\d+);\s*continue;")


def lower(source: str, mode: str = "ordered") -> str:
    begin = source.index(START)
    end = source.index(END, begin + len(START))
    body = source[begin + len(START):end]
    labels = list(CASE.finditer(body))
    numbers = [int(m.group(1)) for m in labels]
    if numbers != list(range(len(numbers))) or len(numbers) < 2:
        raise ValueError(f"expected consecutive Afro shader cases, got {numbers}")
    targets = [int(v) for v in JUMP.findall(body)]
    if len(targets) != 9 or any(v not in numbers for v in targets):
        raise ValueError(f"expected nine in-range pc/continue jumps, got {targets}")
    if len(re.findall(r"\bpc\s*=", body)) != len(targets):
        raise ValueError("found a pc assignment without continue")
    if len(re.findall(r"\bpc\b", body)) != len(targets):
        raise ValueError("case body reads pc outside its continue jumps")
    if len(re.findall(r"(?m)^\s*break;", body)) != 2:
        raise ValueError("unexpected break in shader cases")
    if mode not in ("ordered", "threshold"):
        raise ValueError(f"unknown lowering mode: {mode}")
    out = ["\tuint pc = 0;\n\twhile (true)\n\t{\n"]
    if mode == "ordered":
        out.append("\t\tbool active = false;\n")
    for i, label in enumerate(labels):
        following = labels[i + 1].start() if i + 1 < len(labels) else len(body)
        statements = body[label.end():following]
        if mode == "ordered":
            out.append(f"\t\tactive = active || (pc == {numbers[i]}u);\n")
            out.append("\t\tif (active)\n\t\t{")
        else:
            # pc changes only immediately before continue, so on this pass it
            # is constant. Starting at case N executes every case i >= N.
            out.append(f"\t\tif (pc <= {numbers[i]}u)\n\t\t{{")
        out.append(statements)
        out.append("\t\t}\n")
    out.append("\t\tbreak;\n\t}\n}")
    return (source[:begin] + f"// Afro diagnostic: {mode} case guards; not visually approved.\n" +
            "".join(out) + source[end + len(END):])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=pathlib.Path)
    ap.add_argument("output", type=pathlib.Path)
    ap.add_argument("--mode", choices=("ordered", "threshold"), default="ordered")
    args = ap.parse_args()
    result = lower(args.source.read_text(encoding="utf-8"), args.mode)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(result, encoding="utf-8", newline="\n")
    print(f"wrote {args.output}: {len(result)} characters")


if __name__ == "__main__":
    main()
