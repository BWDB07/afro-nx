"""One-time removal of inherited hand-native registrations; keep the generic guard."""
from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
path = root / 'app/src/cpu/banjo_hot_guest.cpp'
s = path.read_text(encoding='utf-8')

def once(pattern, replacement):
    global s
    s, n = re.subn(pattern, replacement, s, count=1, flags=re.S)
    if n != 1:
        raise SystemExit(f'expected one match: {pattern[:65]}')

once(r'// The hand-written natives\' own keys.*?\nnamespace banjo::hand \{.*?\n\}  // namespace banjo::hand',
     '// Afro: no hand-written native may be enabled without a qualifying console profile.\n'
     'namespace banjo::hand { void Count(uint32_t, uint32_t) {} }')
once(r'  for \(uint32_t k = 0; k < ::banjo::hand::kNatives; \+\+k\) row\(user, ::banjo::hand::kKeys\[k\], ::banjo::hand::Own\(k\)\);\n', '')
once(r'    // The hand-written natives\' calls by size.*?    \}\n    return;', '    return;')
path.write_text(s, encoding='utf-8', newline='\n')

path = root / 'app/src/cpu/banjo_enhancements.cpp'
s = path.read_text(encoding='utf-8')
s, n1 = re.subn(r'^REXCVAR_DECLARE\(bool, banjo_hand_.*\n', '', s, flags=re.M)
s, n2 = re.subn(r'^      \{"banjo_hand_.*\n', '', s, flags=re.M)
if (n1, n2) != (4, 4):
    raise SystemExit(f'expected four declarations and rows, got {n1}, {n2}')
path.write_text(s, encoding='utf-8', newline='\n')
print('Removed inherited hand-native keys and counters; machine-copy guard remains.')
