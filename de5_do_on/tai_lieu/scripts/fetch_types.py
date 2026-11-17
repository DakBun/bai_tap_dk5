# fetch_types.py
# Lay type (loai ban ghi) cua tat ban ghi qua Crossref /works/{doi}, luu vao type_cache.json.
# Ho tro batch --start --end de chia chay nhieu lan (tranh timeout 30s).
# Chi doc candidates.csv + matrix.csv, khong sua file nao.
# ponytail: neu Crossref bi han che rate, cac doi that bai se co type=None va duoc bo trong cache.

import csv, os, re, sys, json, time, unicodedata
import requests

try:
    sys.stdout.reconfigure(encoding="cp1252", errors="replace")
except Exception:
    pass

BASE = r"E:\Đề tài 5\de5_do_on\tai_lieu"
MATRIX = os.path.join(BASE, "matrix.csv")
CANDIDATES = os.path.join(BASE, "candidates.csv")
CACHE = os.path.join(BASE, "type_cache.json")
UA = {"User-Agent": "de5-literature/0.1 (mailto:)"}
SLEEP = 0.15


def norm(s):
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def collect_dois(start, end):
    matrix = read_csv(MATRIX)
    cand = read_csv(CANDIDATES)
    ci = {r["record_id"]: r for r in cand}
    dois = []
    seen = set()
    rows = matrix[start:end]
    for r in rows:
        rid = r["record_id"]
        c = ci.get(rid, {})
        doi = (r.get("doi", "") or c.get("doi", "") or "").strip().lower()
        if not doi or doi == "khong nêu trong tóm tắt" or doi in seen:
            continue
        seen.add(doi)
        dois.append((rid, doi, c.get("tieu_de", "") or ""))
    return dois


def fetch_type(doi):
    try:
        r = requests.get(
            "https://api.crossref.org/works/" + requests.utils.quote(doi, safe=""),
            headers=UA, timeout=20,
        )
        if r.status_code == 200:
            return r.json()["message"].get("type")
    except Exception:
        pass
    return None


def main():
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    end = int(sys.argv[2]) if len(sys.argv) > 2 else 999999
    if os.path.exists(CACHE):
        cache = json.load(open(CACHE, encoding="utf-8"))
    else:
        cache = {}
    dois = collect_dois(start, end)
    print(f"Batch [{start}:{end}] co {len(dois)} doi can lay type.")
    n_new = 0
    for rid, doi, title in dois:
        if doi in cache:
            continue
        typ = fetch_type(doi)
        cache[doi] = typ
        n_new += 1
        print(f"  {rid} | {doi} | type={typ} | {title[:60]}")
        time.sleep(SLEEP)
    with open(CACHE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
    print(f"Da them {n_new} doi moi. Tong cache: {len(cache)}. Luu vao {CACHE}")


if __name__ == "__main__":
    main()