# verify.py
# Xac minh DOI/tieu de cua 13 hat giong trong seed_list.cfg qua Crossref API.
# Luat: toan metadata lay tu phan hoi API. Khong du doan, khong bo sung.
# status_doi: OK (DOI hop le va khop), UNVERIFIED (khong lay duoc / khong co DOI), MISMATCH (tieu de API khac nhieu so voi tieu de cung cap).
# ponytail: User-Agent can mail hop le de tranh bi Crossref han che rate. Neu can lay toan van (full-text) phai them API/tu khoa tai nguyen them.

import csv, os, re, unicodedata, sys, time
import requests

# ponytail: console Windows mac dinh la cp1252 khong hien thi duoc kyatu Unicode
# (vi du "De tai 5") -> in bi UnicodeEncodeError. Giai han: ep stdout ve cp1252
# voi errors="replace" de khong crash khi chay truc tiep; khi chay qua run_all.py
# (bat dau/subprocess) du lieu duoc lay tu file CSV, khong qua console.
try:
    sys.stdout.reconfigure(encoding="cp1252", errors="replace")
except Exception:
    pass

BASE = r"E:\Đề tài 5\de5_do_on\tai_lieu"
SEED = os.path.join(BASE, "seed_list.csv")
UA = {"User-Agent": "de5-literature/0.1 (mailto:)"}  # TODO: nguoi dung dien email vao mailto:


def norm(s):
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def title_similarity(a, b):
    A = set(norm(a).split()); B = set(norm(b).split())
    if not A or not B:
        return 0.0
    return len(A & B) / max(len(A), len(B))


def crossref_by_doi(doi):
    url = "https://api.crossref.org/works/" + requests.utils.quote(doi, safe="")
    r = requests.get(url, headers=UA, timeout=30)
    if r.status_code != 200:
        return None, r.status_code
    return r.json()["message"], r.status_code


def crossref_search(query, rows=5):
    params = {"query.bibliographic": query, "rows": rows}
    r = requests.get("https://api.crossref.org/works", params=params, headers=UA, timeout=30)
    if r.status_code != 200:
        return [], r.status_code
    return r.json()["message"]["items"], r.status_code


def extract(m):
    if not m:
        return {}
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
    return {
        "doi": m.get("DOI", ""),
        "title": title,
        "authors": "; ".join(authors),
        "year": year,
        "journal": journal,
    }


def main():
    rows = []
    with open(SEED, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(row)

    out_cols = ["seed_id", "ten_tac_gia", "nam", "ten_tap_chi", "doi_cung_cap",
                "tieu_de_cung_cap", "mo_ta", "doi_api", "tieu_de_api", "tac_gia_api",
                "nam_api", "tap_chi_api", "status_doi", "ghi_chu"]

    for i, row in enumerate(rows, 1):
        row.setdefault("seed_id", f"S{i:02d}")
        doi_prov = (row.get("doi_cung_cap") or "").strip()
        title_prov = (row.get("tieu_de_cung_cap") or "").strip()
        author_prov = (row.get("ten_tac_gia") or "").strip()
        year_prov = (row.get("nam") or "").strip()
        journal_prov = (row.get("ten_tap_chi") or "").strip()
        desc = (row.get("mo_ta") or "").strip()

        best = None
        status = "UNVERIFIED"
        note = ""

        if doi_prov:
            m, sc = crossref_by_doi(doi_prov)
            if m:
                best = m
                status = "OK"
                if title_prov:
                    sim = title_similarity(title_prov, best.get("title", [""])[0] if best.get("title") else "")
                    if sim < 0.4:
                        status = "MISMATCH"
                        note = f"do giong tieu de = {sim:.2f} (thap)"
                    else:
                        note = f"doi hop le, do giong tieu de = {sim:.2f}"
                else:
                    note = "xac minh theo DOI (khong co tieu de de so sanh)"
            else:
                note = f"Crossref tra ve status {sc} cho DOI {doi_prov}"
                q = " ".join(p for p in [title_prov, author_prov, desc] if p) or doi_prov
                items, sc2 = crossref_search(q, rows=5)
                if items:
                    best = items[0]
                    status = "UNVERIFIED"
                    note += "; tim duoc bo sung qua tim kiem (chua xac chinh DOI)"
        else:
            parts = [p for p in [title_prov, author_prov, journal_prov, desc, year_prov] if p]
            q = " ".join(parts)
            items, sc = crossref_search(q, rows=5)
            if items:
                best = items[0]
                status = "UNVERIFIED"
                note = "khong co DOI, lay qua tim kiem tieu ke (chua xac chinh)"
            else:
                note = "khong tim thay tren Crossref"

        ex = extract(best)
        row["doi_api"] = ex.get("doi", "")
        row["tieu_de_api"] = ex.get("title", "")
        row["tac_gia_api"] = ex.get("authors", "")
        row["nam_api"] = ex.get("year", "")
        row["tap_chi_api"] = ex.get("journal", "")
        row["status_doi"] = status
        row["ghi_chu"] = note
        time.sleep(0.25)

    with open(SEED, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=out_cols, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({c: row.get(c, "") for c in out_cols})

    print(f"Da xu ly {len(rows)} hat giong. Ket qua o {SEED}")


if __name__ == "__main__":
    main()