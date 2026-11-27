"""One-time removal of Katamari's custom frame limiter from Afro's key shim."""
from pathlib import Path
import re

p = Path(__file__).resolve().parents[1] / 'app/src/afro_keys.cpp'
s = p.read_text(encoding='utf-8')
s, n = re.subn(r'// AFRO-nx \(2026-11-02, the user\'s request:.*?\nvoid renutFrameLimit\(\) \{.*?\n\}\n',
               '// Afro has no port-specific frame limiter; preserve the game timing.\n'
               'void renutFrameLimit() {}\n', s, count=1, flags=re.S)
if n != 1:
    raise SystemExit('Katamari limiter block not found')
p.write_text(s, encoding='utf-8', newline='\n')
print('Removed inherited frame limiter.')
