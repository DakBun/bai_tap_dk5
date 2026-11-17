# Thu muc tai_lieu - De tai 5: on giao thong thanh pho tu dien thoai

## Cau truc
- `seed_list.csv` : 13 hat giong da xac minh qua Crossref (cot status_doi: OK / UNVERIFIED / MISMATCH)
- `search_log.csv` : lich su truy van API (ngay, nguon, truy van, so ket qua)
- `candidates.csv` : tat ca ung vien tim duoc, da khuyen trung DOI
- `screening.csv` : quyết định include/exclude + ly do + nhom M1/M2/M3 (ban nhap AI)
- `matrix.csv` : ma tran tong quan cac bai include (chi lay tu tom tắt API)
- `references.bib` : BibTeX cua bai include (ta tu metadata Crossref)
- `references.ris` : RIS cua bai include (ta tu metadata Crossref)
- `prisma_counts.json` : thong ke PRISA tinh toan boi script (khong go tay)
- `scripts/` : verify.py, search.py, screen_export.py, build_outputs.py, run_all.py

## Quy tuc du lieu
- Tat metadata (DOI, tac gia, nam, tap chi, tom tắt) lay tu phan hoi API Crossref / OpenAlex. KHONG du doan, KHONG bo sung theo thu.
- Neu khong lay duoc => de trong va ghi status_doi = UNVERIFIED.
- status_read = "abstract_only" mac dinh; chi du len "fulltext" neu da tai va doc toan van.
- User-Agent: `de5-literature/0.1 (mailto:)` -> CAN DUN EMAIL VAO `mailto:` truoc khi chay API lai (xem log_AI.md).
