# log_AI - De tai 5

## Thong tin email can dien
User-Agent trong script: `de5-literature/0.1 (mailto:)`. **CAN DUN EMAIL CUA BAN vao `mailto:`** (vi du `mailto:ten@domain.edu`) truoc khi chay cac script goi Crossref/OpenAlex, de tranh bi han che rate.

## 11/14/2026 - Khoi tao cau truc
- Cong cu: Cline (mo hinh dang chay), Python 3.12.10, thu vien `requests` da co san (khong cai them).
- Nguon du lieu: Crossref (api.crossref.org), OpenAlex (api.openalex.org).
- Da tao: de5_do_on/tai_lieu/ (README, seed_list.csv, search_log.csv, candidates.csv, screening.csv, matrix.csv, references.bib/.ris, prisma_counts.json, scripts/), de5_do_on/log_AI.md.
- Viec da lam: tao cau thu muc, khoi tao seed_list.csv (13 hat giong).
- Can nguoi kiem tra: dien email vao User-Agent; xac nhan cac ket qua verify/search; xac nhan user_confirmed trong screening.csv.

## 11/14/2026 - Chay hoan chen pipeline (run_all.py)
- Cong cu: Cline (AI coding agent), Python 3.12.10, thu vien `requests` da co san (khong cai them).
- Nguon du lieu: Crossref (https://api.crossref.org/works), OpenAlex (https://api.openalex.org/works). User-Agent: `de5-literature/0.1 (mailto:)` -> **CAN DUN EMAIL VAO `mailto:`**.
- Da chay: verify.py (13 hat giong), search.py (12 truy van, 144 ban ghi), screen_export.py (137 ung vien -> 36 INCLUDE / 101 EXCLUDE), build_outputs.py (matrix 36, bib 36, ris 36), run_all.py (prisma_counts.json + kiem tra tu dong).
- Ket qua hat giong: OK=5 (S01,S04,S06,S07,S08), UNVERIFIED=8 (S02,S03,S05,S09,S10,S11,S12,S13), MISMATCH=0.
- Ung vien=137; include=36 (nhom M1/M2/M3), exclude=101. Khong co loi API nguyen nhan.
- Loi da sua: search_log ban dau bi gom header voi dong du lieu (file khoi tao khong co xuong dong) -> sua search.py ghi search_log 1 lan o che do ghi moi.
- Can nguoi kiem tra: (1) dien email vao User-Agent mailto:; (2) xet duyet cot user_confirmed trong screening.csv (hien de trong); (3) xac nhan 36 bai include du dung va phu hop; (4) doc chieu 3 hang matrix mau voi tom sat goc (xem o duoi run_all); (5) xac thuc references.bib/.ris (theo metadata Crossref, khong go tay).
