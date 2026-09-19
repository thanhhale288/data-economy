# Task 2 — Script hướng dẫn: VSIC/ISIC mapping + seed

Thực hiện theo thứ tự. Mỗi bước có lệnh kiểm chứng.

## Mục tiêu nghiệm thu

- [ ] Mapping có Section C + đủ VSIC division **10–33** (level 2) + các class 4-digit của 10 DN
- [ ] 10 DN seed khớp list: RAL, HPG, VNM, FPT, GVR, DGC, MSN, PNJ, REE, BMP; metadata nhất quán
- [ ] Có Alembic migration (không chỉ `create_all`)
- [ ] `alembic upgrade head` rồi `PYTHONPATH=. python -m backend.app.seed` chạy được

---

## Bước 0 — Chuẩn bị môi trường

```bash
cd "/Users/hale/Code/AI in Data Economy"
source .venv/bin/activate   # hoặc python3 -m venv .venv && pip install -r requirements.txt
```

Kiểm tra `alembic` đã có trong `requirements.txt` (đã có `alembic==1.14.0`).

---

## Bước 1 — Mở rộng file mapping

**File:** `data/mappings/vsic_isic_section_c.json`

**Việc làm:**

1. Giữ record level 1: `vsic_code` / `isic_code` = `"C"`.
2. Thêm **đủ** division level 2: `"10"` … `"33"` (mỗi dòng: `vsic_code`, `isic_code`, `level: 2`, `name_vi`, `name_en`, `parent_code: "C"`).
3. Giữ / bổ sung class level 4 dùng bởi 10 DN: `1050`, `1071`, `2011`, `2211`, `2220`, `2410`, `2620`, `2710`, `2740`, `3211` (và parent division tương ứng).
4. Schema mỗi object:

```json
{
  "vsic_code": "27",
  "isic_code": "27",
  "level": 2,
  "name_vi": "Sản xuất thiết bị điện",
  "name_en": "Manufacture of electrical equipment",
  "parent_code": "C"
}
```

**Kiểm chứng:**

```bash
python -c "
import json
from pathlib import Path
m = json.loads(Path('data/mappings/vsic_isic_section_c.json').read_text())
divs = {x['vsic_code'] for x in m if x['level']==2}
assert 'C' in {x['vsic_code'] for x in m if x['level']==1}
assert divs == {str(i) for i in range(10, 34)}, f'missing {set(map(str, range(10,34)))-divs}'
print('OK mapping:', len(m), 'rows,', len(divs), 'divisions')
"
```

---

## Bước 2 — Sửa seed 10 DN (nhất là BMP)

**File:** `data/seeds/companies.json`

**Việc làm:**

1. Xác nhận đủ đúng 10 mã: RAL, HPG, VNM, FPT, GVR, DGC, MSN, PNJ, REE, BMP.
2. Mỗi DN có: `stock_code`, `name`, `vsic_code` (có trong mapping), `exchange`, `website_url`, `financial`, `digital_presence`.
3. **BMP**: theo plan = mẫu ngành nhựa VSIC `2220`. Ticker HOSE thật “BMP” là DN nước; trong seed dự án giữ mã **BMP** theo `AGENTS.md` / plan, gắn profile nhựa (website `bmp.com.vn`) và ghi rõ trong `description` đây là **sample seed theo plan**, không phải thay đổi danh sách ticker.
4. Đảm bảo mọi `vsic_code` của DN tồn tại trong file mapping (level 4 hoặc level 2).

**Kiểm chứng:**

```bash
python -c "
import json
from pathlib import Path
codes = [c['stock_code'] for c in json.loads(Path('data/seeds/companies.json').read_text())]
assert codes == ['RAL','HPG','VNM','FPT','GVR','DGC','MSN','PNJ','REE','BMP'], codes
m = {x['vsic_code'] for x in json.loads(Path('data/mappings/vsic_isic_section_c.json').read_text())}
for c in json.loads(Path('data/seeds/companies.json').read_text()):
    assert c['vsic_code'] in m, c['stock_code']
print('OK seeds')
"
```

---

## Bước 3 — Cài Alembic + migration đầu

**Việc làm:**

1. Tạo `alembic.ini` (root hoặc `backend/`) trỏ `script_location = backend/alembic`.
2. Tạo `backend/alembic/env.py` đọc `settings.database_url` từ `backend.app.config`, import `Base.metadata` từ models.
3. Sinh revision đầu (autogenerate hoặc viết tay) khớp toàn bộ bảng trong `backend/app/models/__init__.py`.
4. Chạy migrate trước khi seed.

```bash
# lần đầu (nếu chưa có env/versions)
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```

**Lưu ý SQLite mặc định:** `database_url` mặc định = `sqlite:///./data/mfg_economy.db`. Nếu DB cũ lệch schema, xóa file DB demo rồi `upgrade` lại (chỉ an toàn với data demo).

**Kiểm chứng:**

```bash
alembic current
alembic history
```

---

## Bước 4 — Wire seed: không còn phụ thuộc `create_all` làm nguồn sự thật

**File:** `backend/app/seed.py` (+ tùy chọn `backend/app/main.py`)

**Việc làm:**

1. `run_seed()` **không** gọi `Base.metadata.create_all` làm bước chính — schema đến từ Alembic.
2. `load_vsic_mappings`: insert mã mới; **update** `name_vi` / `name_en` / `parent_code` nếu đã có (để re-seed sau khi mở rộng mapping).
3. `load_companies`: nếu company đã tồn tại, **update** metadata cơ bản (name, website, vsic, …) để sửa BMP khi re-seed.
4. Giữ seed GSO/OECD sample như cũ (demo fallback) — không đổi công thức Digital VA.

**Chạy:**

```bash
alembic upgrade head
PYTHONPATH=. python -m backend.app.seed
```

**Kiểm chứng:**

```bash
PYTHONPATH=. python -c "
from backend.app.database import SessionLocal
from backend.app.models import VsicCode, Company
db = SessionLocal()
divs = db.query(VsicCode).filter(VsicCode.level==2).count()
n = db.query(Company).count()
bmp = db.query(Company).filter(Company.stock_code=='BMP').one()
print(f'divisions={divs} companies={n} BMP={bmp.name} vsic={bmp.vsic_code}')
assert divs >= 24
assert n == 10
db.close()
"
```

---

## Bước 5 — (Tuỳ chọn) Docker / Postgres

```bash
docker compose up -d db
export DATABASE_URL=postgresql://mfg_economy:mfg_economy_pass@localhost:5432/mfg_economy
alembic upgrade head
PYTHONPATH=. python -m backend.app.seed
```

---

## Sau Task 2

Task mở tiếp (cùng blocked-by Task 2):

- **#3 GSO crawler** — IIP / shipment / inventory thật + fallback rõ ràng
- **#4 OECD SDMX** — MEI / INDIGO / ICT, nội suy quý→tháng

