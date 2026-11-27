#!/usr/bin/env python3
"""Map Afro's PC sampler CSV to every sampled generated guest function.

The sampler writes module-relative instruction addresses; llvm-symbolizer reads
the matching PDB beside the PC executable. No game data is included in output.
"""

import argparse
import collections
import pathlib
import re
import subprocess


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", type=pathlib.Path)
    ap.add_argument("exe", type=pathlib.Path)
    ap.add_argument("--symbolizer", default=r"C:\Program Files\LLVM\bin\llvm-symbolizer.exe")
    ap.add_argument("--out", type=pathlib.Path)
    ap.add_argument("--bulk-list", type=pathlib.Path,
                    help="merge all sampled generated functions into the machine-copy candidate list")
    ap.add_argument("--exclude", type=pathlib.Path,
                    default=pathlib.Path("app/src/cpu/hot/excluded_pc.txt"),
                    help="sampled functions excluded by the tiny-leaf or exactness checks")
    args = ap.parse_args()

    module = None
    addresses = collections.Counter()
    threads = collections.Counter()
    for line in args.csv.read_text(encoding="utf-8").splitlines():
        if line.startswith("#modulo;"):
            fields = line.split(";")
            if fields[2].lower() == args.exe.name.lower():
                module = fields[1]
        elif line and not line.startswith("#"):
            fields = line.split(";")
            threads[fields[0]] += 1
            if fields[1] == module:
                addresses[int(fields[2], 16)] += 1
    if module is None or not addresses:
        raise SystemExit("No samples from the matching executable")

    rvas = sorted(addresses)
    result = subprocess.run(
        [args.symbolizer, "--no-inlines", "--relative-address", f"--obj={args.exe}"],
        input="".join(f"0x{rva:X}\n" for rva in rvas),
        text=True, capture_output=True, check=True,
    )
    records = result.stdout.strip().split("\n\n")
    if len(records) != len(rvas):
        raise SystemExit(f"Expected {len(rvas)} symbol records, got {len(records)}")
    functions = collections.Counter()
    other = collections.Counter()
    for rva, record in zip(rvas, records):
        name = record.splitlines()[0].strip()
        if re.fullmatch(r"sub_[0-9A-Fa-f]{8}", name):
            functions[name.upper().replace("SUB_", "sub_")] += addresses[rva]
        else:
            other[name] += addresses[rva]

    rows = [f"# {sum(addresses.values())} executable samples from {sum(threads.values())} total; "
            f"{len(functions)} generated functions; {len(other)} other symbols"]
    rows += [f"{name} {count}" for name, count in functions.most_common()]
    report = "\n".join(rows) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(report, encoding="utf-8")
    if args.bulk_list:
        old = args.bulk_list.read_text(encoding="utf-8") if args.bulk_list.exists() else ""
        listed = set(re.findall(r"^sub_[0-9A-F]{8}", old, flags=re.M))
        excluded = set(re.findall(r"^sub_[0-9A-F]{8}", args.exclude.read_text(encoding="utf-8"),
                                  flags=re.M)) if args.exclude.exists() else set()
        additions = [name for name in functions if name not in listed and name not in excluded]
        with args.bulk_list.open("a", encoding="utf-8", newline="\n") as f:
            if additions and old and not old.endswith("\n"):
                f.write("\n")
            if additions:
                f.write(f"# PC profile {args.csv.name}: {len(additions)} newly sampled functions; "
                        "localize_native may refuse unsafe forms.\n")
                for name in additions:
                    f.write(f"{name}\n")
        print(f"Merged {len(additions)} new candidates into {args.bulk_list}")
    print("\n".join(rows[:42]))
    print(f"Other executable samples: {sum(other.values())}; top: {other.most_common(8)}")


if __name__ == "__main__":
    main()
