import re, sys
from pathlib import Path
ids = [f"ORACLE-{n:03d}" for n in list(range(1, 21)) + list(range(27, 34)) + [42, 45]]
text = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in Path("astra/tests/academic_radar").glob("*.py"))
gaps = Path("ops/evidence/oracle_gaps_real.md")
declared = gaps.read_text(encoding="utf-8") if gaps.exists() else ""
missing = [i for i in ids if i not in text and i not in declared]
if missing:
    sys.exit("untagged Tier-A oracles: " + ", ".join(missing))
print("ok: all", len(ids), "Tier-A oracles tagged or declared as real gaps")
