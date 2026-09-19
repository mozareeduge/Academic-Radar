import re, sys
from pathlib import Path
md, base = Path(sys.argv[1]), Path(sys.argv[2])
if not md.exists():
    sys.exit(f"missing {md}")
txt = md.read_text(encoding="utf-8")
paths = set(re.findall(r"tests/[\w./-]+\.py", txt))
missing = sorted(p for p in paths if not (base / p).exists())
heads = [h for h in ("source run progress", "partial", "cancel", "dedupe", "saved", "export", "auth") if h not in txt.lower()]
if missing or heads:
    sys.exit(f"missing paths: {missing}; missing headings: {heads}")
print("ok", len(paths), "paths")
