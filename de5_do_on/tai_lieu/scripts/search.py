# search.py
# Tim kiem them ung vien qua OpenAlex va Crossref (6 nhom truy van).
# Ghi search_log.csv; gop vao candidates.csv, khuyen trung theo DOI (rồi tieu de hoa don neu khong co DOI).
# ponytail: OpenAlex/Crossref co han rate; them mailto va ngu ngat giua cac goi. Neu can lay toan van phai them API/tu khoa them.

import csv, os, re, sys, time, unicodedata
import requests

try:
    sys.stdout.reconfigure(encoding="cp1252", errors="replace")
except Exception:
    pass

BASE = r"E:\Đề tài 5\de5_do_on\tai_lieu"
SEARCH_LOG = os.path.join(BASE, "search_log.csv")
CANDIDATES = os.path.join(BASE, "candidates.csv")
UA = {"User-Agent": "de5-literature/0.1 (mailto:)"}  # TODO: dien email vao mailto:
MAILTO = ""  # TODO: dien email

QUERY_GROUPS = [
    "road traffic noise emission model CNOSSOS-EU motorcycle noise",
    "smartphone noise measurement accuracy calibration",
    "noise mapping spatial interpolation kriging sampling density",
    "noise map uncertainty",
    "road traffic noise Vietnam Southeast Asia motorcycle",
    "A-weighting equivalent continuous sound level Leq",
]


def norm(s):
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def strip_html(s):
    if not s:
        return ""
    s = re.sub(r"<[^>]+>", " ", s)
    s = s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    s = s.replace("&quot;", '"').replace("&#39;", "'").replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", s).strip()


def oalex_abstract(inv):
    if not inv:
        return ""
    pairs = []
    for word, positions in inv.items():
        for p in positions:
            pairs.append((int(p), word))
    pairs.sort(key=lambda x: x[0])
    return " ".join(w for _, w in pairs)
def oalex_search(query, per_page=12):
    params = {"search": query, "per-page": per_page, "mailto": MAILTO}
    r = requests.get("https://api.openalex.org/works", params=params, headers=UA, timeout=18)
    return r


def crossref_search(query, rows=12):
    params = {"query.bibliographic": query, "rows": rows}
    r = requests.get("https://api.crossref.org/works", params=params, headers=UA, timeout=18)
    return r


def record_from_oalex(w):
    title = w.get("display_name") or ""
    authors = []
    for au in w.get("authorships", []):
        a = au.get("author", {})
        if a.get("display_name"):
            authors.append(a["display_name"])
    year = str(w.get("publication_year")) if w.get("publication_year") else ""
    venue = ""
    ps = w.get("primary_source") or {}
    if ps.get("display_name"):
        venue = ps["display_name"]
    doi = (w.get("doi") or "").replace("https://doi.org/", "")
    abst = oalex_abstract(w.get("abstract_inverted_index"))
    reviewed = "Co" if venue else "Khong ro"
    return {
        "nguon": "OpenAlex", "doi": doi, "tieu_de": title, "tac_gia": "; ".join(authors),
        "nam": year, "tap_chi": venue, "tom_tat": abst,
        "trinh_duoc_binh_duyen": reviewed, "status_doi": "OK" if doi else "UNVERIFIED",
        "ghi_chu": "",
    }


def record_from_crossref(m):
    title = m.get("title", [""])[0] if m.get("title") else ""
    authors = []
    for a in m.get("author", []):
        g = a.get("given", ""); f = a.get("family", "")
        authors.append((g + " " + f).strip() or f)
    year = ""
    for key in ["published-print", "published-online", "published", "created"]:
        if m.get(key):
            dp = m[key].get("date-parts", [[None]])[0]
            if dp and dp[0]:
                year = str(dp[0]); break
    journal = m.get("container-title", [""])[0] if m.get("container-title") else ""
    doi = (m.get("DOI") or "").replace("https://doi.org/", "")
    abst = strip_html(m.get("abstract", ""))
    reviewed = "Co" if journal else "Khong ro"
    return {
        "nguon": "Crossref", "doi": doi, "tieu_de": title, "tac_gia": "; ".join(authors),
        "nam": year, "tap_chi": journal, "tom_tat": abst,
        "trinh_duoc_binh_duyen": reviewed, "status_doi": "OK" if doi else "UNVERIFIED",
        "ghi_chu": "",
    }
def main():
    all_rows = []
    log_rows = []
    today = time.strftime("%d/%m/%Y")

    def fetch_oalex(query):
        count = 0; err = ""
        try:
            r = oalex_search(query)
            if r.status_code == 200:
                items = r.json()["results"]
                count = len(items)
                for w in items:
                    all_rows.append(record_from_oalex(w))
                print(f"[OpenAlex] '{query}' -> {count}", flush=True)
            else:
                err = f"status {r.status_code}"
                print(f"[OpenAlex] '{query}' -> {err}", flush=True)
        except Exception as e:
            err = type(e).__name__
            print(f"[OpenAlex] '{query}' -> LOI {err}", flush=True)
        log_rows.append([today, "OpenAlex", query, count])
        time.sleep(0.3)

    def fetch_crossref(query):
        count = 0; err = ""
        try:
            r = crossref_search(query)
            if r.status_code == 200:
                items = r.json()["message"]["items"]
                count = len(items)
                for m in items:
                    all_rows.append(record_from_crossref(m))
                print(f"[Crossref] '{query}' -> {count}", flush=True)
            else:
                err = f"status {r.status_code}"
                print(f"[Crossref] '{query}' -> {err}", flush=True)
        except Exception as e:
            err = type(e).__name__
            print(f"[Crossref] '{query}' -> LOI {err}", flush=True)
        log_rows.append([today, "Crossref", query, count])
        time.sleep(0.3)

    for q in QUERY_GROUPS:
        fetch_oalex(q)
        fetch_crossref(q)

    # ghi search_log (ghi moi, dam dung header dung)
    with open(SEARCH_LOG, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ngay", "nguon", "truy_van", "so_ket_qua"])
        for row in log_rows:
            w.writerow(row)

    # khuyen trung: 1) theo DOI, 2) theo tieu de hoa don neu khong co DOI
    kept = []
    seen_doi = set()
    seen_title = set()
    n_dup = 0
    for row in all_rows:
        doi = (row["doi"] or "").strip().lower()
        key = doi if doi else None
        title_key = norm(row["tieu_de"])
        if key and key in seen_doi:
            n_dup += 1; continue
        if (not key) and title_key and title_key in seen_title:
            n_dup += 1; continue
        if key:
            seen_doi.add(key)
        if title_key:
            seen_title.add(title_key)
        kept.append(row)

    # ma record_id
    for i, row in enumerate(kept, 1):
        row["record_id"] = f"C{i:02d}"
        row["da_khuyen_trung"] = "True"

    cols = ["record_id", "nguon", "doi", "tieu_de", "tac_gia", "nam", "tap_chi",
            "tom_tat", "trinh_duoc_binh_duyen", "status_doi", "da_khuyen_trung", "ghi_chu"]
    with open(CANDIDATES, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for row in kept:
            w.writerow({c: row.get(c, "") for c in cols})

    print(f"Da truy van {len(QUERY_GROUPS)} nhom x 2 nguon.")
    print(f"Tong ban ghi lay duoc: {len(all_rows)} | Da khuyen trung: {n_dup} | Da luu candidates.csv: {len(kept)}")


if __name__ == "__main__":
    main()