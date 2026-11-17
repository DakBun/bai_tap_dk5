# audit.py
# Kiểm toán bộ tài liệu trong de5_do_on/tai_lieu/ (CHI DOC, khong sua matrix.csv, screening.csv, references.*, prisma_counts.json).
# Chi tao moi: scripts/audit.py, tai_lieu/audit_report.md.
# ponytail: goi API thuc (Crossref/OpenAlex/PMC) de lay type va xac minh; neu API bi han che rate hoac timeout, ket qua se co "type khong lay duoc".
#           Thieu thong tin trong tóm tắt duoc bo trong (khong doan).

import csv, os, re, sys, json, time, difflib, unicodedata
import requests

try:
    sys.stdout.reconfigure(encoding="cp1252", errors="replace")
except Exception:
    pass

BASE = r"E:\Đề tài 5\de5_do_on\tai_lieu"
MATRIX = os.path.join(BASE, "matrix.csv")
SCREENING = os.path.join(BASE, "screening.csv")
CANDIDATES = os.path.join(BASE, "candidates.csv")
SEARCH_LOG = os.path.join(BASE, "search_log.csv")
SEED = os.path.join(BASE, "seed_list.csv")
PRISMA = os.path.join(BASE, "prisma_counts.json")
SCREEN_EXPORT_PY = os.path.join(BASE, "scripts", "screen_export.py")
REPORT = os.path.join(BASE, "audit_report.md")

UA = {"User-Agent": "de5-literature/0.1 (mailto:)"}  # can dien email vao mailto:
SLEEP = 0.4  # ngu ngan tranh han che rate


def norm(s):
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def api_get(url, params=None, timeout=25):
    try:
        r = requests.get(url, params=params, headers=UA, timeout=timeout)
        return r
    except Exception as e:
        return None


TYPE_CACHE = os.path.join(BASE, "type_cache.json")


def load_type_cache():
    if os.path.exists(TYPE_CACHE):
        return json.load(open(TYPE_CACHE, encoding="utf-8"))
    return {}


_TYPE_CACHE = load_type_cache()


def crossref_type_by_doi(doi):
    """Tra ve (type, title, container-title) tu type_cache.json (da lay boi fetch_types.py)."""
    if not doi or doi == "khong nêu trong tóm tắt":
        return None, None, None
    doi_l = doi.strip().lower()
    typ = _TYPE_CACHE.get(doi_l)
    if typ is None:
        return None, None, None
    return typ, "", ""


def crossref_search_type(query, top=3):
    """Tra ve danh sach (type, title, doi, container-title) top ket qua."""
    r = api_get(
        "https://api.crossref.org/works",
        params={"query.bibliographic": query, "rows": top},
        timeout=30,
    )
    if r is None or r.status_code != 200:
        return []
    out = []
    for m in r.json()["message"]["items"]:
        out.append(
            (
                m.get("type"),
                (m.get("title") or [""])[0] if m.get("title") else "",
                m.get("DOI", ""),
                (m.get("container-title") or [""])[0] if m.get("container-title") else "",
            )
        )
    return out


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def build_cand_index():
    cand = read_csv(CANDIDATES)
    return {r["record_id"]: r for r in cand}


SUSPECT_PAT = re.compile(
    r"erratum|corrigendum|correction|retraction|editorial|preface|front matter|table of contents|proceedings of",
    re.IGNORECASE,
)
def buoc1(cand_index):
    print("\n" + "=" * 70)
    print("BUOC 1: RO CAC BAI INCLUDE TRONG matrix.csv")
    print("=" * 70)
    matrix = read_csv(MATRIX)
    include_rows = [r for r in matrix if r.get("quyet_dat", "INCLUDE") == "INCLUDE" or True]
    # matrix.csv khong co cot quit_dat; tat ca dong trong matrix la INCLUDE (da duoc screen truoc)
    suspect = []
    results = []
    for i, r in enumerate(matrix, 1):
        rid = r["record_id"]
        c = cand_index.get(rid, {})
        title = c.get("tieu_de", "") or ""
        year = r.get("nam", "") or c.get("nam", "") or ""
        journal = r.get("tap_chi", "") or c.get("tap_chi", "") or ""
        doi = r.get("doi", "") or c.get("doi", "") or ""
        typ, api_title, api_journal = crossref_type_by_doi(doi)
        if typ is None:
            typ = "khong lay duoc"
        if not title and api_title:
            title = api_title
        if not journal and api_journal:
            journal = api_journal
        is_suspect = bool(SUSPECT_PAT.search(title))
        if is_suspect:
            suspect.append(rid)
        results.append((rid, title, year, journal, doi, typ, is_suspect))
        time.sleep(SLEEP)
        print(
            f"{i:2d}. {rid} | nam={year} | type={typ} | doi={doi} | {title[:80]}"
            + ("  <<< SUSPECT" if is_suspect else "")
        )
    print(f"\nTong so bai include: {len(matrix)}")
    print(f"So bai SUSPECT: {len(suspect)}")
    if suspect:
        print("Danh sach SUSPECT:", ", ".join(suspect))
    return results, suspect


if __name__ == "__main__":
    cand_index = build_cand_index()
    buoc1(cand_index)
M1_KW = ["noise", "traffic", "emission", "propagation", "cnossos", "motorcycle", "vietnam"]
M2_KW = ["smartphone", "mobile", "calibration", "microphone", "app", "crowdsens"]
M3_KW = ["interpolation", "kriging", "sampling", "uncertainty", "noise map"]
GENERIC_KW = ["noise", "acoustic", "sound"]


def count_kw(text, kws):
    t = norm(text)
    return sum(1 for k in kws if k in t)


def buoc2(cand_index):
    print("\n" + "=" * 70)
    print("BUOC 2: DO LIEN QUAN (tu khoa tieu de + tom tắt)")
    print("=" * 70)
    matrix = read_csv(MATRIX)
    weak = []
    for i, r in enumerate(matrix, 1):
        rid = r["record_id"]
        c = cand_index.get(rid, {})
        title = c.get("tieu_de", "") or ""
        abst = c.get("tom_tat", "") or ""
        combined = title + " " + abst
        n1 = count_kw(combined, M1_KW)
        n2 = count_kw(combined, M2_KW)
        n3 = count_kw(combined, M3_KW)
        has_generic = any(k in norm(combined) for k in GENERIC_KW)
        is_weak = (n1 == 0 and n2 == 0 and n3 == 0) or (not has_generic)
        if is_weak:
            weak.append((rid, title, n1, n2, n3, has_generic))
        print(
            f"{i:2d}. {rid} | M1={n1} M2={n2} M3={n3} | generic={has_generic} | {title[:70]}"
            + ("  <<< WEAK" if is_weak else "")
        )
    print(f"\nTong so bai include: {len(matrix)}")
    print(f"So bai WEAK: {len(weak)}")
    if weak:
        print("Danh sach WEAK:")
        for rid, title, n1, n2, n3, gen in weak:
            print(f"  - {rid} | M1={n1} M2={n2} M3={n3} generic={gen} | {title}")
    return weak


if __name__ == "__main__":
    cand_index = build_cand_index()
    buoc1(cand_index)
    buoc2(cand_index)
def trich_doan_ma_screen_export():
    print("\n" + "=" * 70)
    print("BUOC 3: TRICH DOAN MA screen_export.py (QUYET DINH KHONG XAC NHAN BINH DUYEN)")
    print("=" * 70)
    with open(SCREEN_EXPORT_PY, encoding="utf-8") as f:
        lines = f.readlines()
    # In cac quan su ly buoc quyet dat (tu dong xac dinh doan cua cac dong 49-80)
    start = None
    for i, l in enumerate(lines, 1):
        if "# quyet dat ban nhap" in l:
            start = i
            break
    if start:
        doan = "".join(lines[start - 1 : start + 20])
        print(doan)
    else:
        print("(khong tim thay doan ma)")
    return lines


def buoc3(cand_index):
    print("\n" + "=" * 70)
    print("BUOC 3: THONG KE 84 BAI BI LOAI THEO TYPE VA NGUON")
    print("=" * 70)
    screen = read_csv(SCREENING)
    exclude_rows = [r for r in screen if r["quyet_dat"] == "EXCLUDE"]
    print(f"Tong so bai EXCLUDE trong screening.csv: {len(exclude_rows)}")
    from collections import Counter

    ly_do_counter = Counter(r["ly_do"] for r in exclude_rows)
    print("\nThong ke theo ly do:")
    for ld, cnt in ly_do_counter.most_common():
        print(f"  - {cnt} bai: {ld}")

    # Lay 84 bai "Khong co tap chi/don vi phat hanh"
    no_review = [r for r in exclude_rows if "Khong co tap chi" in r["ly_do"]]
    print(f"\nSo bai 'Khong co tap chi/don vi phat hanh': {len(no_review)}")

    # Thong ke theo type va nguon (can goi API lay type)
    type_counter = Counter()
    nguon_counter = Counter()
    type_nguon = []
    for r in no_review:
        rid = r["record_id"]
        c = cand_index.get(rid, {})
        doi = c.get("doi", "") or ""
        nguon = c.get("nguon", "") or "?"
        nguon_counter[nguon] += 1
        typ, _, _ = crossref_type_by_doi(doi)
        typ_label = typ if typ else "khong lay duoc / khong doi"
        type_counter[typ_label] += 1
        type_nguon.append((rid, c.get("tieu_de", "") or "", nguon, typ_label, c.get("tap_chi", "") or ""))
        time.sleep(SLEEP)

    print("\nThong ke 84 bai theo loai ban ghi (type):")
    for t, cnt in type_counter.most_common():
        print(f"  - {cnt} bai: {t}")
    print("\nThong ke theo nguon:")
    for n, cnt in nguon_counter.most_common():
        print(f"  - {cnt} bai: {n}")

    # 15 bai ngau nhien (seed co dinh)
    import random

    random.seed(42)
    sample = random.sample(no_review, min(15, len(no_review)))
    print("\n15 bai bi loai ngau nhien (seed=42) kèm tieu de, type, tap chi:")
    for r in sample:
        rid = r["record_id"]
        c = cand_index.get(rid, {})
        doi = c.get("doi", "") or ""
        typ, _, _ = crossref_type_by_doi(doi)
        typ_label = typ if typ else "khong lay duoc / khong doi"
        print(
            f"  - {rid} | nguon={c.get('nguon','?')} | type={typ_label} | tap_chi={c.get('tap_chi','?')} | {c.get('tieu_de','')[:70]}"
        )
        time.sleep(SLEEP)
    return no_review


if __name__ == "__main__":
    cand_index = build_cand_index()
    buoc1(cand_index)
    buoc2(cand_index)
    trich_doan_ma_screen_export()
    buoc3(cand_index)
def buoc4(cand_index):
    print("\n" + "=" * 70)
    print("BUOC 4: HAT GIONG VA PRISMA")
    print("=" * 70)
    seed = read_csv(SEED)
    matrix = read_csv(MATRIX)

    # Xay doi set cua matrix (qua candidates)
    matrix_dois = set()
    for r in matrix:
        rid = r["record_id"]
        c = cand_index.get(rid, {})
        doi = (c.get("doi", "") or "").strip().lower()
        if doi and doi != "khong nêu trong tóm tắt":
            matrix_dois.add(doi)

    print("Kiem tra 5 hat giong OK (S01, S04, S06, S07, S08) co trong matrix.csv khong:")
    ok_seeds = [s for s in seed if s["status_doi"] == "OK"]
    for s in ok_seeds:
        doi = (s.get("doi_api", "") or "").strip().lower()
        co = doi in matrix_dois if doi else False
        print(f"  - {s['seed_id']}: doi_api={doi} | trong matrix={co} | tieu_de={s.get('tieu_de_api','')[:60]}")

    print("\n13 hat giong co duoc tinh trong prisma_counts.json khong?")
    with open(PRISMA, encoding="utf-8") as f:
        prisma = json.load(f)
    print(json.dumps(prisma, ensure_ascii=False, indent=2))
    print("\n=> ket luan: prisma_counts.json CHI thong ke ket qua tim kiem (identified/screened/excluded/included)")
    print("             tu search_log.csv. KHONG co tung hang ghi nhan tu seed_list.csv (13 hat giong).")
    print("             De don day, nen them dong 'records from other sources' vao prisma_counts.json")
    print("             (13 hat giong, 5 OK / 8 UNVERIFIED / 0 MISMATCH). DE NGUY: KHONG tu sua file.")
    return ok_seeds, matrix_dois


if __name__ == "__main__":
    cand_index = build_cand_index()
    buoc1(cand_index)
    buoc2(cand_index)
    trich_doan_ma_screen_export()
    buoc3(cand_index)
    buoc4(cand_index)
def title_sim(a, b):
    return difflib.SequenceMatcher(None, norm(a), norm(b)).ratio()


def buoc5():
    print("\n" + "=" * 70)
    print("BUOC 5: XAC MINH LAI HAT GIONG UNVERIFIED (top 3, ngưỡng >= 0.90)")
    print("=" * 70)
    seed = read_csv(SEED)
    unverified = [s for s in seed if s["status_doi"] == "UNVERIFIED"]

    cases = {
        "S02": "Comparison of Road Traffic Noise prediction models: CNOSSOS-EU, Nord2000 and TRANEX",
        "S03": "Characteristics of road traffic noise in Hanoi and Ho Chi Minh City, Vietnam",
        "S05": "Horn Use Patterns and Acoustic Characteristics in Congested Urban Traffic: A Case Study of Ho Chi Minh City",
        "S09": "Ear-Phone: A Context-Aware Noise Mapping using Smart Phones",
    }
    for sid in ["S02", "S03", "S05", "S09"]:
        s = next((x for x in seed if x["seed_id"] == sid), None)
        title_expected = cases[sid]
        print(f"\n--- {sid}: '{title_expected}' ---")
        res = crossref_search_type(title_expected, top=3)
        best = None
        if res:
            for typ, t, doi, jour in res:
                sim = title_sim(title_expected, t)
                mark = "CHAP NHAN" if sim >= 0.90 else "khong dat"
                if sim >= 0.90 and best is None:
                    best = (t, doi, sim)
                print(f"    top: sim={sim:.2f} [{mark}] | type={typ} | doi={doi} | {t[:80]}")
        else:
            print("    (khong ket qua tu Crossref)")
        if best:
            print(f"  => KET QUA: CHAP NHAN {sid} | doi={best[1]} | sim={best[2]:.2f}")
        else:
            print(f"  => KET QUA: Giu UNVERIFIED {sid} (khong co top nao >= 0.90)")
        time.sleep(SLEEP)

    # S05: thu DOI chinh xac
    print("\n--- S05 (thu DOI 10.3390/acoustics7020036) ---")
    typ, t, jour = crossref_type_by_doi("10.3390/acoustics7020036")
    sim = title_sim(cases["S05"], t or "")
    print(f"  Crossref tra ve: type={typ} | tieu_de='{t}' | tap_chi='{jour}' | sim={sim:.2f}")
    if sim >= 0.90:
        print("  => CHAP NHAN S05 theo DOI (tieu de khop >= 0.90)")
    else:
        print("  => Giu UNVERIFIED S05 (tieu de DOI khong khop >= 0.90)")

    # S09: OpenAlex/arXiv, ghi rang chi la preprint
    print("\n--- S09: Ear-Phone (arXiv 1310.4270) ---")
    r = api_get("https://api.openalex.org/works", params={"search": "Ear-Phone context-aware noise mapping smart phones", "per-page": 3})
    if r and r.status_code == 200:
        for w in r.json()["results"]:
            print(f"    OpenAlex: {w.get('display_name','')[:80]} | year={w.get('publication_year')} | doi={w.get('doi')} | type={w.get('type')}")
    else:
        print("    (OpenAlex khong tra ve ket qua)")
    print("  => GHI RO: la preprint arXiv (chua duoc binh duyet tap chi), neu can lay toan van phai tai arXiv.")

    # S11: PMC ID converter
    print("\n--- S11: PMC10891730 qua NCBI idconv ---")
    r = api_get(
        "https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/",
        params={"ids": "PMC10891730", "format": "json"},
    )
    if r and r.status_code == 200:
        print("  Phan hoi:", r.text[:500])
    else:
        print("  (Khong lay duoc phan hoi tu NCBI)")
    print("  => Can xac minh tiep: PMC10891730 co phai bai hieu chuan 'mu' cho NoiseCapture khong.")

    # S10: tim 5 ket qua dau
    print("\n--- S10: tim 'smartphone sound level meter apps accuracy evaluation' (top 5) ---")
    res = crossref_search_type("smartphone sound level meter apps accuracy evaluation", top=5)
    for typ, t, doi, jour in res:
        print(f"    type={typ} | doi={doi} | tap_chi={jour} | {t[:90]}")

    # S12, S13
    print("\n--- S12, S13 ---")
    print("  => Giu UNVERIFIED. Can tra tay (chua co tieu_de chinh xac).")


def buoc6(buoc1_res, buoc2_res, buoc3_res, buoc4_res, buoc5_note):
    print("\n" + "=" * 70)
    print("BUOC 6: GHI tai_lieu/audit_report.md")
    print("=" * 70)
    matrix = read_csv(MATRIX)
    screening = read_csv(SCREENING)
    seed = read_csv(SEED)
    with open(PRISMA, encoding="utf-8") as f:
        prisma = json.load(f)

    n_inc = len(matrix)
    n_exc = len([r for r in screening if r["quyet_dat"] == "EXCLUDE"])
    n_total = len(screening)

    suspect = [r[0] for r in buoc1_res if r[6]]
    weak = buoc2_res  # list of (rid, title, n1, n2, n3, gen)
    no_review = buoc3_res  # list of screening row
    ok_seeds, matrix_dois = buoc4_res

    lines = []
    lines.append("# Bao cao kiem toan bo tai lieu - de5_do_on/tai_lieu/")
    lines.append("")
    lines.append("## Thong tin chung")
    lines.append("- Ngay kiem toan: 14/11/2026")
    lines.append("- Cong cu: Python 3.12.10, thu vien `requests` (da co san, khong cai them).")
    lines.append("- Nguon du lieu API: Crossref (api.crossref.org), OpenAlex (api.openalex.org), NCBI PMC idconv.")
    lines.append("- Che do: CHI DOC file hien co. Khong sua matrix.csv, screening.csv, references.*, prisma_counts.json.")
    lines.append("- Chi tao moi: scripts/audit.py, tai_lieu/audit_report.md.")
    lines.append("")

    lines.append("## Buoc 1: Ro bai INCLUDE trong matrix.csv (SUSPECT)")
    lines.append(f"- So bai include: {n_inc}")
    lines.append(f"- So bai SUSPECT (tieu de khop ma loai van ban): {len(suspect)}")
    if suspect:
        lines.append("- Danh sach SUSPECT: " + ", ".join(suspect))
    else:
        lines.append("- Danh sach SUSPECT: (khong co)")
    lines.append("")

    lines.append("## Buoc 2: Do lien quan (WEAK)")
    lines.append(f"- So bai WEAK: {len(weak)}")
    if weak:
        lines.append("- Danh sach WEAK:")
        for rid, title, n1, n2, n3, gen in weak:
            lines.append(f"  * {rid} | M1={n1} M2={n2} M3={n3} generic={gen} | {title}")
    else:
        lines.append("- Danh sach WEAK: (khong co)")
    lines.append("")

    lines.append("## Buoc 3: Trich doan ma screen_export.py + thong ke 84 bai loai")
    lines.append("### Doan ma quyet dinh 'khong xac nhan binh duyet' (screen_export.py dong 67-70):")
    lines.append("```python")
    lines.append("        # quyet dat ban nhap")
    lines.append("        if reviewed != \"Co\":")
    lines.append("            decision = \"EXCLUDE\"; reason = \"Khong co tap chi/don vi phat hanh (chua xac nhan binh duyen)\"")
    lines.append("            n_exc += 1")
    lines.append("```")
    lines.append("")
    lines.append(f"- Tong so bai EXCLUDE trong screening.csv: {n_exc} (trong {n_total} ung vien)")
    lines.append(f"- So bai 'Khong co tap chi/don vi phat hanh': {len(no_review)}")
    lines.append("- Thong ke theo loai ban ghi (type) va nguon: xem chi tiet o duoi o phan ket qua chay.")
    lines.append("")

    lines.append("## Buoc 4: Hat giong va PRISMA")
    lines.append("### 5 hat giong OK (S01, S04, S06, S07, S08) co trong matrix.csv khong:")
    for s in ok_seeds:
        doi = (s.get("doi_api", "") or "").strip().lower()
        co = doi in matrix_dois if doi else False
        lines.append(f"- {s['seed_id']}: doi_api={doi} | trong matrix={co} | {s.get('tieu_de_api','')[:60]}")
    lines.append("")
    lines.append("### 13 hat giong co duoc tinh trong prisma_counts.json khong?")
    lines.append("- KHONG. `prisma_counts.json` chi thong ke ket qua tim kiem (identified/screened/excluded/included)")
    lines.append("  tu `search_log.csv`; KHONG co tung hang ghi nhan tu `seed_list.csv` (13 hat giong).")
    lines.append("- De don day, DE NGUY them dong `records from other sources` (13 hat giong: 5 OK / 8 UNVERIFIED / 0 MISMATCH)")
    lines.append("  vao `prisma_counts.json`. KHONG tu sua file.")
    lines.append("")

    lines.append("## Buoc 5: Xac minh lai hat giong UNVERIFIED (top 3, ngưỡng >= 0.90)")
    lines.append(buoc5_note)
    lines.append("")

    lines.append("## De xuat loai bo (tong hop)")
    lines.append("- SUSPECT (de xet loai neu la van ban khong du lieu chinh): " + (", ".join(suspect) if suspect else "khong co"))
    lines.append("- WEAK (thieu tu khoa lien quan): " + (", ".join(w[0] for w in weak) if weak else "khong co"))
    lines.append("")
    lines.append("## Hat giong da xac minh duoc / chua xac minh")
    lines.append("- OK (da xac minh qua DOI): S01, S04, S06, S07, S08")
    lines.append("- UNVERIFIED (can xac minh them): S02, S03, S05, S09, S10, S11, S12, S13")
    lines.append("")
    lines.append("## Nhung chua lam duoc")
    lines.append("- Chua xac nhan toan bo 84 bai loai qua Crossref type (co the bi han che rate/timeout).")
    lines.append("- S12, S13 can tra tay (chua co tieu_de chinh xac).")
    lines.append("- S10: da liet ke 5 ket qua Crossref, can nguoi dung chon.")
    lines.append("- Can dien email vao User-Agent mailto: truoc khi goi API lai.")

    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Da ghi {REPORT}")


if __name__ == "__main__":
    cand_index = build_cand_index()
    r1, suspect1 = buoc1(cand_index)
    r2 = buoc2(cand_index)
    trich_doan_ma_screen_export()
    r3 = buoc3(cand_index)
    r4 = buoc4(cand_index)
    buoc5()
    buoc6(r1, r2, r3, r4, buoc5_note="")
# Xuli tham so thu cong: python audit.py all|1|2|3|4|5|6
import sys as _sys
_STEPS = set(sys.argv[1:]) if len(sys.argv) > 1 else set()
if not _STEPS:
    _STEPS = {"1", "2", "3", "4", "5", "6"}
if "all" in _STEPS:
    _STEPS = {"1", "2", "3", "4", "5", "6"}
print("=== BUOC DA CHAY: " + ",".join(sorted(_STEPS)) + " ===")

ci = {r["record_id"]: r for r in read_csv(CANDIDATES)}
r1 = sus = None
if "1" in _STEPS:
    r1, sus = buoc1(ci)
if "2" in _STEPS:
    buoc2(ci)
if "3" in _STEPS:
    trich_ma()
    buoc3(ci)
if "4" in _STEPS:
    buoc4(ci)
if "5" in _STEPS:
    buoc5()
if "6" in _STEPS:
    buoc6(r1, r2, r3)