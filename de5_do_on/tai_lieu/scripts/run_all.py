# run_all.py
# Chay hoan chen: build_outputs (ma tran + tham chieu), tinh prisma_counts.json tu CSV
# (khong gõ tay), chay kiem tra tu dong va in ket qua THAT.
# ponytail: verify/search/screen da chay o buoc tren va luu CSV; run_all xay dung lai ma tran,
#           tham chieu, prisma va kiem tra tu du lieu co san (nhanh, khong go API lai).

import csv, json, os, re, sys, unicodedata
from collections import Counter

try:
    sys.stdout.reconfigure(encoding="cp1252", errors="replace")
except Exception:
    pass

BASE = r"E:\Đề tài 5\de5_do_on\tai_lieu"
CANDIDATES = os.path.join(BASE, "candidates.csv")
SCREENING = os.path.join(BASE, "screening.csv")
MATRIX = os.path.join(BASE, "matrix.csv")
SEARCH_LOG = os.path.join(BASE, "search_log.csv")
BIB = os.path.join(BASE, "references.bib")
RIS = os.path.join(BASE, "references.ris")
PRISMA = os.path.join(BASE, "prisma_counts.json")
PLACE = "khong nêu trong tóm tắt"


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def count_bib(path):
    n = 0
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.startswith("@"):
                    n += 1
    return n


def count_ris(path):
    n = 0
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.startswith("TY  -"):
                    n += 1
    return n


def is_valid_doi(doi):
    if not doi or doi == PLACE:
        return False
    d = doi.strip().lower()
    return d.startswith("10.") and "/" in d
def build_prisma():
    cand = read_csv(CANDIDATES)
    screen = read_csv(SCREENING)
    matrix = read_csv(MATRIX)
    log = read_csv(SEARCH_LOG) if os.path.exists(SEARCH_LOG) else []

    identified_by_source = Counter()
    total_fetched = 0
    for row in log:
        try:
            c = int(row.get("so_ket_qua", "0") or 0)
        except Exception:
            c = 0
        identified_by_source[row.get("nguon", "?")] += c
        total_fetched += c

    kept = len(cand)
    duplicates_removed = total_fetched - kept
    screened = len(screen)
    excluded_rows = [r for r in screen if r["quyet_dat"] == "EXCLUDE"]
    included_rows = [r for r in screen if r["quyet_dat"] == "INCLUDE"]
    excluded = len(excluded_rows)
    included = len(included_rows)
    excluded_by_reason = Counter(r["ly_do"] for r in excluded_rows)

    prisma = {
        "identified": dict(identified_by_source),
        "identified_total": total_fetched,
        "duplicates_removed": duplicates_removed,
        "screened": screened,
        "excluded": excluded,
        "excluded_by_reason": dict(excluded_by_reason),
        "included": included,
        "matrix_rows": len(matrix),
        "bib_records": count_bib(BIB),
        "ris_records": count_ris(RIS),
    }
    with open(PRISMA, "w", encoding="utf-8") as f:
        json.dump(prisma, f, ensure_ascii=False, indent=2)
    return prisma, matrix, cand, screen


def run_checks(prisma, matrix, cand, screen):
    results = []

    def check(name, ok, detail=""):
        results.append((name, "PASS" if ok else "FAIL", detail))

    unverified = 0; no_doi_unverified = 0; bad = []
    for r in matrix:
        doi = r.get("doi", "") or ""
        sd = r.get("status_doi", "") or ""
        if is_valid_doi(doi):
            continue
        if sd == "UNVERIFIED":
            unverified += 1
            if not doi:
                no_doi_unverified += 1
        else:
            bad.append(r["record_id"])
    check("doi hop le hoac status_doi=UNVERIFIED", len(bad) == 0,
          f"unverified={unverified} (khong doi={no_doi_unverified}), loi={bad}")

    dois = [r.get("doi", "").strip().lower() for r in matrix
            if r.get("doi") and r.get("doi") != PLACE and is_valid_doi(r.get("doi", ""))]
    check("khong DOI trung", len(dois) == len(set(dois)),
          f"so DOI={len(dois)}, unique={len(set(dois))}")

    check("bib=ris=matrix", prisma["bib_records"] == prisma["ris_records"] == len(matrix),
          f"bib={prisma['bib_records']} ris={prisma['ris_records']} matrix={len(matrix)}")

    ok_prisma = (prisma["identified_total"] - prisma["duplicates_removed"] == prisma["screened"]
                 and prisma["screened"] - prisma["excluded"] == prisma["included"]
                 and prisma["included"] == len(matrix))
    check("prisma khop CSV", ok_prisma,
          f"ident={prisma['identified_total']} dup={prisma['duplicates_removed']} "
          f"screened={prisma['screened']} excl={prisma['excluded']} incl={prisma['included']}")

    import random
    random.seed(7)
    sample = random.sample(matrix, min(3, len(matrix)))
    print("\n=== MAU 3 HANG MA TRAN (de doc chieu voi tom sat goc) ===")
    cand_by_id = {r["record_id"]: r for r in cand}
    for r in sample:
        rid = r["record_id"]
        c = cand_by_id.get(rid, {})
        abst = (c.get("tom_tat", "") or "")[:220]
        print("----", rid, "|", r["nhom"], "| doi=", r["doi"], "| status=", r["status_doi"])
        print("  tom sat goc:", abst.encode("cp1252", "replace").decode("cp1252"))
        print("  ket_qua_chinh:", r["ket_qua_chinh"].encode("cp1252", "replace").decode("cp1252"))
        print("  han_che     :", r["han_che"].encode("cp1252", "replace").decode("cp1252"))

    return results


def main():
    import build_outputs
    build_outputs.main()
    prisma, matrix, cand, screen = build_prisma()
    results = run_checks(prisma, matrix, cand, screen)
    print("\n=== KIEM TRA TU DONG ===")
    allpass = True
    for name, status, detail in results:
        print(f"[{status}] {name}: {detail}")
        if status == "FAIL":
            allpass = False
    print("TAT CA KIEM TRA:", "PASS" if allpass else "CO THAT BAI")
    print("Da ghi", PRISMA)


if __name__ == "__main__":
    main()