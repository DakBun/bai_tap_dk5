import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audit
import csv

ci = {}
with open(os.path.join(os.path.dirname(__file__), "candidates.csv"), encoding="utf-8") as f:
    for row in csv.DictReader(f):
        ci[row["record_id"]] = row

print("=== BUOC 1: SUSPECT ===")
r1, sus = audit.buoc1(ci)
print("SO SUSPECT:", len(sus))
print("DANH SACH:", sus)

print("\n=== BUOC 2: WEAK ===")
r2 = audit.buoc2(ci)
print("SO WEAK:", len(r2))
print("DANH SACH:")
for x in r2:
    print("  ", x[0], "M1=%s M2=%s M3=%s generic=%s" % (x[2], x[3], x[4], x[5]))
