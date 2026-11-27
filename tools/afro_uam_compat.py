#!/usr/bin/env python3
"""Prepare Afro GLSL with the smallest known desktop-uam compiler fix.

Two unusually large pixel shaders crash the installed uam on the raw
SPIRV-Cross text. The existing `sel` pass changes their OpSelect-style `?:`
expressions to boolean `mix` selects. It compiles both default and alpha-test
variants. All other shader text is copied byte-for-byte. Output is game data
under ignored out/; no shader source is committed.
"""
import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGETS = ('ps_069459B4C78435DC.glsl', 'ps_3AA213F4F5CAB0A0.glsl')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--in', dest='src', type=Path,
                    default=ROOT / 'out/deko3d_shaders/glsl')
    ap.add_argument('--out', type=Path,
                    default=ROOT / 'out/deko3d_shaders/glsl_compat')
    a = ap.parse_args()
    src = a.src.resolve()
    dst = a.out.resolve()
    if src == dst or not all((src / name).is_file() for name in TARGETS):
        raise SystemExit('input/output overlap or missing Afro pixel shader')
    shaders = sorted(src.glob('*.glsl'))
    with tempfile.TemporaryDirectory(prefix='afro_uam_', dir=ROOT / 'out') as tmp:
        subset = Path(tmp) / 'input'
        fixed = Path(tmp) / 'fixed'
        subset.mkdir()
        for name in TARGETS:
            shutil.copy2(src / name, subset / name)
        subprocess.run([sys.executable, str(ROOT / 'tools/deko3d_glsl_opt.py'),
                        '--in', str(subset), '--out', str(fixed), '--passes', 'sel',
                        '--check', '--jobs', '1'], cwd=ROOT, check=True)
        dst.mkdir(parents=True, exist_ok=True)
        for shader in shaders:
            replacement = fixed / shader.name
            shutil.copy2(replacement if replacement.exists() else shader,
                         dst / shader.name)
    print(f'afro_uam_compat: {len(shaders)} GLSL shaders; sel applied only to '
          f'{len(TARGETS)} uam crash cases -> {dst}')


if __name__ == '__main__':
    main()
