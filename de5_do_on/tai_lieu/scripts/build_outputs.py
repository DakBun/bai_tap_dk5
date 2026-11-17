# build_outputs.py
# Tao matrix.csv cho cac bai include (trich tu tom tắt; thieu = "khong nêu trong tóm tắt")
# va references.bib / references.ris (chi bai include, khoa tacgia_nam_tu-dau khong dau).
# ponytail: muc_tieu/phuong_phap/co_mau/ket_qua_chinh/han_che duoc trich xuat tu cau trong
# tom tắt chua co cau truc -> co the bat nhiu hoac thieu. Neu can trich chu doi can doc toan van.

import csv, os, re, sys, unicodedata

try:
    sys.stdout.reconfigure(encoding="cp1252", errors="replace")
except Exception:
    pass

BASE = r"E:\Đề tài 5\de5_do_on\tai_lieu"
CANDIDATES = os.path.join(BASE, "candidates.csv")
SCREENING = os.path.join(BASE, "screening.csv")
MATRIX = os.path.join(BASE, "matrix.csv")
BIB = os.path.join(BASE, "references.bib")
RIS = os.path.join(BASE, "references.ris")

PLACE = "khong nêu trong tóm tắt"


def norm(s):
    if not s: return ""
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def strip_html(s):
    if not s: return ""
    s = re.sub(r"<[^>]+>", " ", s)
    for a, b in [("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'),
                 ("&#39;", "'"), ("&nbsp;", " ")]:
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s).strip()


def sentences(text):
    if not text:
        return []
    text = strip_html(text)
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if p.strip()]


def field_from(text, keywords, max_sent=2):
    sents = sentences(text)
    picked = []
    for kw in keywords:
        for s in sents:
            if kw in norm(s) and s not in picked:
                picked.append(s)
                if len(picked) >= max_sent:
                    return " | ".join(picked)
    return " | ".join(picked) if picked else PLACE
def cite_key_part(authors):
    first = (authors.split(";")[0] if authors else "").strip()
    first = re.sub(r"\s+.*", "", first)
    first = norm(first)
    first = re.sub(r"\s+", "", first)
    return first if first else "noname"


def slug_title(title):
    s = norm(title)
    words = s.split()[:4]
    return "-".join(words) if words else "khongtiede"


def main():
    with open(CANDIDATES, newline="", encoding="utf-8") as f:
        cand = {r["record_id"]: r for r in csv.DictReader(f)}
    included = []
    with open(SCREENING, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["quyet_dat"] == "INCLUDE":
                included.append(row)

    # ---- matrix.csv ----
    m_cols = ["record_id", "tac_gia", "nam", "doi", "tap_chi", "muc_tieu", "phuong_phap",
              "co_mau", "ket_qua_chinh", "han_che", "nhom", "status_doi", "status_read", "ghi_chu"]
    m_kw = {
        "muc_tieu": ["aim", "objective", "purpose", "goal", "this paper", "we present", "propose",
                     "seek to", "muc tieu", "doi tuong"],
        "phuong_phap": ["method", "methodology", "approach", "model", "we use", "based on",
                        "phuong phap", "mo hinh", "thu thap"],
        "co_mau": ["sample", "dataset", "measurement", "site", "city", "record", "sites",
                   "co so", "mau", "du lieu"],
        "ket_qua_chinh": ["result", "find", "show", "reveal", "demonstrate", "indicate",
                          "ket qua", "chi ra", "thuat toan"],
        "han_che": ["limit", "limitation", "constraint", "however", "but", "han che",
                    "tuy nhien", "che doi"],
    }
    with open(MATRIX, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=m_cols, extrasaction="ignore")
        w.writeheader()
        for row in included:
            rid = row["record_id"]
            c = cand.get(rid, {})
            abst = c.get("tom_tat", "") or ""
            authors = c.get("tac_gia", "") or ""
            year = c.get("nam", "") or ""
            title = c.get("tieu_de", "") or ""
            row_out = {
                "record_id": rid,
                "tac_gia": authors or PLACE,
                "nam": year or PLACE,
                "doi": c.get("doi", "") or PLACE,
                "tap_chi": c.get("tap_chi", "") or PLACE,
                "muc_tieu": field_from(abst, m_kw["muc_tieu"]),
                "phuong_phap": field_from(abst, m_kw["phuong_phap"]),
                "co_mau": field_from(abst, m_kw["co_mau"]),
                "ket_qua_chinh": field_from(abst, m_kw["ket_qua_chinh"]),
                "han_che": field_from(abst, m_kw["han_che"]),
                "nhom": row["nhom"] or "",
                "status_doi": c.get("status_doi", "") or "UNVERIFIED",
                "status_read": "abstract_only",
                "ghi_chu": "",
            }
            w.writerow(row_out)

    # ---- references.bib & references.ris ----
    bib_entries = []
    ris_entries = []
    for row in included:
        rid = row["record_id"]
        c = cand.get(rid, {})
        authors = c.get("tac_gia", "") or ""
        year = c.get("nam", "") or ""
        title = c.get("tieu_de", "") or ""
        doi = c.get("doi", "") or ""
        journal = c.get("tap_chi", "") or ""
        source = c.get("nguon", "")
        key = f"{cite_key_part(authors)}_{year or 'nd'}_{slug_title(title)}"
        key = re.sub(r"[^a-z0-9_-]", "", key)

        bib = ("@article{" + key + ",\n"
               "  author = {" + authors + "},\n"
               "  title = {" + title + "},\n"
               "  journal = {" + journal + "},\n"
               "  year = {" + year + "},\n"
               "  doi = {" + doi + "},\n"
               "  note = {" + source + " abstract-only}\n"
               "}\n")
        bib_entries.append(bib)

        ty = "JOUR" if journal else "GEN"
        ris = f"TY  - {ty}\n"
        for a in authors.split(";"):
            a = a.strip()
            if a:
                ris += f"AU  - {a}\n"
        ris += f"TI  - {title}\n"
        if journal:
            ris += f"JO  - {journal}\n"
        if year:
            ris += f"PY  - {year}\n"
        if doi:
            ris += f"DO  - {doi}\n"
        ris += f"ER  - \n"
        ris_entries.append(ris)

    with open(BIB, "w", encoding="utf-8") as f:
        f.write("\n".join(bib_entries))
    with open(RIS, "w", encoding="utf-8") as f:
        f.write("\n".join(ris_entries))

    print(f"matrix.csv: {len(included)} dong | references.bib: {len(bib_entries)} | references.ris: {len(ris_entries)}")


if __name__ == "__main__":
    main()