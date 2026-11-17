import csv, json, urllib.request, time, glob, os, sys
import html

# Step 0: Tim matrix.csv
csv_paths = glob.glob('**/matrix.csv', recursive=True)
print('Found:', csv_paths)
if len(csv_paths) != 1:
    print('ERROR: expected 1'); sys.exit(1)
SRC = csv_paths[0]
out_dir = os.path.dirname(SRC)
OUT = os.path.join(out_dir, 'matrix_core.csv')
print('SRC:', SRC)
print('OUT:', OUT)

with open(SRC, 'r', encoding='utf-8', newline='') as f:
    reader = csv.DictReader(f)
    matrix_rows = list(reader)

# Bỏ 3 record_id C43, C44, C114 khỏi danh sách xử lý
target_ids = ['C14', 'C15', 'C17', 'C21', 'C57', 'C39', 'C65', 'C137', 'C109', 'C16', 'C18', 'C135']
matrix_dois = {}
for r in matrix_rows:
    rid = r['record_id']
    if rid in target_ids:
        matrix_dois[rid] = r['doi']

all_entries = []
for rid in target_ids:
    if rid in matrix_dois:
        all_entries.append((rid, matrix_dois[rid], 'matrix.csv'))

supplementary = [('N1','10.1016/j.apacoust.2016.06.012'),('N2','10.1007/s11270-021-05210-3'),('N3','10.1080/00051144.2018.1534927'),('N4','10.1121/1.5034799'),('N5','10.3846/gac.2024.18751')]
for rid, doi in supplementary:
    all_entries.append((rid, doi, 'bo_sung'))

print('Total entries:', len(all_entries))

if len(all_entries) != 17:
    print('WARNING: expected 17 entries (after removing C43,C44,C114), got', len(all_entries))

output_cols = ['record_id', 'nguon', 'tieu_de', 'nam', 'doi', 'tap_chi', 'type', 'status_read', 'ghi_chu']

# Mở file để ghi dùng DictWriter với quoting=csv.QUOTE_MINIMAL và newline=""
# TOÀN BỘ VÒNG LẶP XỬ LÝ Ở DÒNG NÀY ĐẶC BIỆT - TẤT CẢ code gọi API nằm trong đây
with open(OUT, 'w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=output_cols, quoting=csv.QUOTE_MINIMAL)
    writer.writeheader()

    # Xử lý từng DOI - ĐÃ ĐỘNG TRONG Khối WITH NÀY
    for idx, (rid, doi, src) in enumerate(all_entries, 1):
        print(f'\\nProcessing {rid} ({idx}/17)')
        url = f'https://api.crossref.org/works/{doi}'
        req = urllib.request.Request(url, headers={'User-Agent': 'de5-literature/0.1'})
        http_status = None
        title = ''
        year = ''
        container_title = ''
        dtype = ''
        error_msg = ''

        try:
            resp = urllib.request.urlopen(req, timeout=30)
            http_status = resp.status
            data = json.loads(resp.read().decode('utf-8'))
            msg = data.get('message', {})

            # title[0] - qua html.unescape()
            titles = msg.get('title', [])
            if titles and len(titles) > 0:
                title = html.unescape(titles[0])
            else:
                error_msg = 'No title found for DOI ' + doi

            # nam: year from issued.date-parts[0][0]
            issued = msg.get('issued', {})
            date_parts = issued.get('date-parts', [])
            if date_parts and len(date_parts) > 0 and len(date_parts[0]) > 0:
                year = str(date_parts[0][0])
            else:
                error_msg = error_msg + 'No year found. '

            # container-title[0] - qua html.unescape()
            container_titles = msg.get('container-title', [])
            if container_titles and len(container_titles) > 0:
                container_title = html.unescape(container_titles[0])
            else:
                error_msg = error_msg + 'No journal found. '

            # type
            dtype = msg.get('type', '')
        except Exception as e:
            http_status = 'error'
            error_msg = 'Error fetching DOI ' + doi + ': ' + str(e)
            print('  Loi:', error_msg)

        ghi_chu = error_msg if error_msg else ''

        # Ghi row dùng DictWriter (con file vẫn mở)
        row_dict = {col: '' for col in output_cols}
        row_dict['record_id'] = rid
        row_dict['nguon'] = src
        row_dict['tieu_de'] = title
        row_dict['nam'] = year
        row_dict['doi'] = doi
        row_dict['tap_chi'] = container_title
        row_dict['type'] = dtype
        row_dict['status_read'] = 'abstract_only'
        row_dict['ghi_chu'] = ghi_chu
        writer.writerow(row_dict)

        # In ra terminal: record_id | HTTP status | nam | tieu_de[:80]
        tdisplay = title[:80] if len(title) > 80 else title
        print(f'{rid} | {http_status} | {year} | {tdisplay}')

        # Ngủ 1 giây giữa các lần gọi API (còn trong khối with)
        time.sleep(1)

# Bước kiểm tra tự động: đọc lại file bằng csv.DictReader - SAU KHI ĐÃ ĐÓNG
print('\\n=== BAT DAO KIEM TRA TU DINH ===')
violations = []
with open(OUT, 'r', encoding='utf-8', newline='') as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    print('So dong doc duoc:', len(rows))
    if len(rows) != 17:
        print('CANH BAO: Mong 17 dong (11 matrix + 5 bo_sung sau khi bo 3 record), co', len(rows), 'dong.')
    else:
        ok_count = 0
        for i, row in enumerate(rows, 1):
            # Kiểm tra số trường
            fields = list(row.values())
            if len(fields) != 9:
                violations.append(f'Dong {i}: so truong khac 9 ({len(fields)} fields)')
            # Kiểm tra ghi_chu chỉ khác rỗng khi có lỗi API
            if row['ghi_chu'] and row['ghi_chu'].strip() != '' and row.get('http_status', '') != 'error':
                violations.append(f'Dong {i}: ghi_chu khong phai rong khi khong co loi API: {row["ghi_chu"][:50]}')
            else:
                ok_count += 1
        if not violations and ok_count == 17:
            print('KET QUA: OK - Toan bo 17 dong hop le, ghi_chu chinh xac.')
        else:
            print('Cac dong vi pham:')
            for v in violations:
                print(f'  - {v}')