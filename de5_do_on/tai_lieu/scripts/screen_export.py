# screen_export.py
# Sang loc candidates.csv -> screening.csv.
# Tieu chuan (ban nhap AI):
#   INCLUDE: duoc binh duyen (co tap chi/khuyen hoc) LIEN QUAN thuc tiep den it nhat 1 nhom
#            M1 (mo hinh nguon/lan truyen/nghia vu VN), M2 (sai so/hieu chuan dien thoai),
#            M3 (noi suy/do khong dam bao); uu tien 10 nam gan nhat ma cho phep bai nen tang.
#   EXCLUDE: khong binh duyen, khong lien quan, trung lap, khong truy cap duoc tom tat.
# decided_by = "AI-draft"; user_confirmed de trong (nguoi dung dien sau).
# ponytail: phan loai tu dong dap tu tieu de/tom tắt API (chua doc toan van); co the bo sot hoac nham lan.
#           Nguoi dung can xet duyet user_confirmed truoc khi chot ma tran.

import csv, os, re, sys, unicodedata

try:
    sys.stdout.reconfigure(encoding="cp1252", errors="replace")
except Exception:
    pass

BASE = r"E:\Đề tài 5\de5_do_on\tai_lieu"
CANDIDATES = os.path.join(BASE, "candidates.csv")
SCREENING = os.path.join(BASE, "screening.csv")

M1 = ["cnossos","nord2000","tranex","emission","propagation","road traffic noise model",
      "noise mapping","vietnam","hanoi","ho chi minh","motorcycle","xe may","source model","traffic noise"]
M2 = ["smartphone","mobile phone","calibration","accuracy","measurement","error","crowdsensing",
      "noisecapture","ear-phone","phone-based","android","ios","dien thoai","hieu chuan","chuan"]
M3 = ["kriging","interpolation","spatial","uncertainty","sampling","geostatistics","density",
      "noi suy","do khong dam bao","ban do on"]

def norm(s):
    if not s: return ""
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()

def themes(title, abst):
    t = norm(title + " " + abst)
    found = []
    for kw in M1:
        if kw in t: found.append("M1"); break
    for kw in M2:
        if kw in t: found.append("M2"); break
    for kw in M3:
        if kw in t: found.append("M3"); break
    return ",".join(found)

def main():
    with open(CANDIDATES, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    out = []
    n_inc = n_exc = 0
    for row in rows:
        rid = row["record_id"]
        title = row["tieu_de"] or ""
        abst = row["tom_tat"] or ""
        reviewed = row["trinh_duoc_binh_duyen"]
        year = row["nam"] or ""
        thm = themes(title, abst)
        try:
            y = int(year)
        except Exception:
            y = 0
        recent = y >= 2016

        # quyet dat ban nhap
        if reviewed != "Co":
            decision = "EXCLUDE"; reason = "Khong co tap chi/don vi phat hanh (chua xac nhan binh duyen)"
            n_exc += 1
        elif not title and not abst:
            decision = "EXCLUDE"; reason = "Khong tieu de hoac tom tat de xet duyet"
            n_exc += 1
        elif not thm:
            decision = "EXCLUDE"; reason = "Khong lien quan den M1/M2/M3 (dien gia theo tieu de/tom tắt)"
            n_exc += 1
        else:
            decision = "INCLUDE"; reason = "Lien quan thuc tiep den nhom " + thm
            n_inc += 1
        out.append([rid, decision, reason, thm, "AI-draft", ""])

    with open(SCREENING, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["record_id","quyet_dat","ly_do","nhom","decided_by","user_confirmed"])
        for r in out:
            w.writerow(r)
    print(f"INCLUDE={n_inc} | EXCLUDE={n_exc} | tong={len(rows)}. Da luu {SCREENING}")

if __name__ == "__main__":
    main()