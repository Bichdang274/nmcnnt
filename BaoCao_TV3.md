# Phần báo cáo TV3 – Lưu cục bộ, gửi lại và chống trùng

**Sinh viên:** Phan Hải Đức — B24DCCC072 — D24CQCC06-B  
**Đề tài:** Thiết kế hạ tầng CNTT cho chuỗi cửa hàng bán lẻ  
**Cập nhật:** 01/11/2026. Phần nội dung để ghép vào báo cáo nhóm, không thay thế báo cáo toàn nhóm.

## Phạm vi triển khai

Python 3 và SQLite mô phỏng cửa hàng CH01/POS01 và trụ sở trên cùng laptop, trao đổi HTTP POST tại `127.0.0.1:8000/giao-dich`. Packet Tracer dùng mô hình `Nhom02_TV3_KiemThu_TuBanV2.pkt` để kiểm tra mạng. Hai môi trường được kiểm thử độc lập: kết quả ping/HTTP chứng minh khả năng kết nối, còn log và CSDL chứng minh đồng bộ giao dịch. Đây phù hợp cách phân biệt minh chứng trong tài liệu phân công; không tuyên bố Python truyền qua WAN của Packet Tracer.

## 2.7. Mã giao dịch duy nhất và xử lý trùng

Mã có dạng `CH01-POS01-YYYYMMDD-XXXXXX`. Mã cửa hàng và máy POS hiện cố định cho bản demo. Bảng `bo_dem` lưu số cuối theo ngày; việc tăng bộ đếm và thêm giao dịch nằm trong giao dịch SQLite dùng `BEGIN IMMEDIATE`. Vì bộ đếm lưu trên đĩa, mở lại chương trình không làm đặt lại số thứ tự.

Trụ sở dùng `ma_gd` làm khóa chính. Khi nhận mã mới, máy chủ ghi dữ liệu và commit trước khi trả ACK. Với mã cũ, máy chủ so sánh đủ năm trường: cùng nội dung thì trả `DA_TON_TAI` và ACK, không thêm dòng; khác nội dung thì trả HTTP 409. Cửa hàng chỉ đánh dấu ACKED khi ACK hợp lệ và đúng mã. Giao dịch chưa được xác nhận vẫn được giữ để gửi lại.

## 3.3. Lưu cục bộ, gửi lại và chống trùng

`Script/store_agent.py` tạo, xem và gửi giao dịch; `Script/hq_receiver.py` nhận, ghi và xác nhận. `Script/kiem_tra_trung.py` gửi lặp dữ liệu đã đồng bộ rồi so sánh CSDL trước/sau.

| Trạng thái | Ý nghĩa |
|---|---|
| PENDING | Đã lưu cục bộ, chưa thử gửi |
| SENT | Đã thử gửi, chưa nhận ACK hợp lệ; không đồng nghĩa trụ sở đã lưu |
| ACKED | Đã nhận ACK đúng mã giao dịch |

Chương trình gửi lại các dòng PENDING/SENT bằng lệnh thủ công. Lỗi kết nối, phản hồi không hợp lệ hoặc lỗi đọc phản hồi không làm xóa giao dịch. Chưa triển khai gửi lại tự động hoặc lịch sao lưu tự động.

Đoạn mã kiểm tra ACK, trích từ `store_agent.py` (8 dòng):

```python
if (
    not isinstance(xac_nhan, dict)
    or xac_nhan.get("ack") is not True
    or xac_nhan.get("ma_gd") != ma_gd
):
    raise ValueError("Xac nhan khong hop le")
# Chỉ sau khi vượt qua kiểm tra này, chương trình cập nhật ACKED.
```

Phần chống trùng ở receiver kiểm tra bản ghi cũ trong cùng giao dịch ghi SQLite; nhánh `ban_cu == gia_tri` chỉ đặt kết quả `DA_TON_TAI`, không INSERT. Mã nguồn đầy đủ nằm trong Phụ lục C.

## 4. Kết quả kiểm thử

Bộ kết quả chính ngày 01/11/2026 có sẵn trong [danh mục minh chứng](MinhChung/README.md). Thời gian dưới đây lấy nguyên từ nội dung log trên máy người thực hiện.

| Ca | Thao tác và thời điểm | Kết quả thực tế | Đánh giá |
|---|---|---|---|
| KT2 | Dừng receiver; 15:45:03 tạo 5 giao dịch, 15:47:18 thử gửi | 5 mới PENDING rồi SENT; lỗi WinError 10061; giữ đủ 15 dòng ở cửa hàng | Đạt giữ giao dịch khi không kết nối được dịch vụ |
| KT3 | 18:07:59 trụ sở có 10; bật receiver; 18:13:05 gửi lại | 5 mới ACKED; 18:15:24 hai bên đều 15, dữ liệu khớp True, 15 ACKED | Đạt gửi lại và đối chiếu trong demo TV3 |
| KT3-b | 18:17:06 gửi lặp toàn bộ 15 giao dịch | 15 ACK hợp lệ với DA_TON_TAI; trụ sở vẫn 15; mã trùng 0; dữ liệu không đổi | Đạt chống ghi trùng |

Minh chứng chính:

- KT2: [tạo giao dịch](MinhChung/KT2_PENDING_20261101.txt), [gửi lỗi và giữ dữ liệu](MinhChung/KT2_GUI_LOI_20261101.txt).
- KT3: [trước gửi](MinhChung/KT3_TRUOC_GUI_20261101.txt), [gửi lại](MinhChung/KT3_GUI_LAI_20261101.txt), [đối chiếu sau gửi](MinhChung/KT3_SAU_GUI_20261101.txt).
- KT3-b: [log gửi lặp](MinhChung/KT3b_GUI_LAP_20261101.txt).

### Minh chứng mạng V2 bổ trợ

Khi tắt cả Serial0/0/0 và Serial0/0/1 của R-CH1, POS1-1 vẫn ping được gateway `192.168.10.1` nhưng không ping được HQ `192.168.0.10`; HTTP tới HQ báo timeout. Sau khi bật lại các cổng, trang HQ truy cập được.

![V2: ping gateway thành công, ping HQ thất bại khi mất WAN](MinhChung/PT_V2_KT2_mat_WAN.png)

![V2: HTTP timeout khi mất WAN](MinhChung/PT_V2_KT2_HTTP_mat_WAN.png)

![V2: HTTP hoạt động sau khôi phục](MinhChung/PT_V2_KT3_HTTP_phuc_hoi.png)

Ảnh HTTP ban đầu trên TV1 được lưu ở thư mục lịch sử. Dù trang web giống ảnh phục hồi V2, hai ảnh thuộc hai giai đoạn khác nhau. Không sử dụng ảnh TV1 làm ảnh ban đầu của V2. Gói hiện không có ảnh ping phục hồi V2 riêng.

### Xuất CSV, sao lưu và phục hồi ngày 26/10/2026

Đã xuất 10 giao dịch ACKED ra CSV; sao lưu bằng SQLite backup có `integrity_check = ok`. Phục hồi bản sao vào file thử riêng: 10 giao dịch và 1 bản ghi bộ đếm khớp bản sao; toàn vẹn ok. Xem [xuất CSV](MinhChung/xuat_giao_dich.txt), [sao lưu](MinhChung/sao_luu.txt), [phục hồi](MinhChung/kiem_tra_phuc_hoi.txt).

Bản sao và bản phục hồi có dữ liệu giống nhau là kết quả mong đợi, cần giữ cả hai vai trò. Chúng phản ánh ngày 26/10 với 10 giao dịch; không phải bản sao mới nhất của dữ liệu 15 giao dịch ngày 01/11. Không dùng kết quả này để tuyên bố đã hoàn thành ca sao lưu CSDL trụ sở của TV2.

## Giới hạn và phần ghép báo cáo còn lại

- Cần thống nhất schema với TV2 trước khi tuyên bố tích hợp vào CSDL chung. Đối chiếu hiện tại là giữa hai CSDL của demo TV3.
- Bản demo mới cấu hình CH01/POS01; không tuyên bố đã chạy đồng thời 15 máy POS.
- Nhánh xử lý cùng mã khác nội dung có trong mã nguồn, nhưng bộ log này chưa có phép thử riêng cho HTTP 409 hay mất ACK sau khi trụ sở đã commit.
- Phục hồi đã đối chiếu dữ liệu và bộ đếm; chưa kiểm thử tạo giao dịch mới trực tiếp trên file phục hồi.
- Khi ghép báo cáo nhóm, bổ sung phiên bản công cụ thực dùng, nguồn tham khảo và khai báo phần hỗ trợ AI theo yêu cầu môn học, dựa trên quá trình thực tế. Không suy đoán thông tin chưa có trong gói.

## Phụ lục C. Mã nguồn, CSDL và dữ liệu mẫu

### Mã nguồn đầy đủ

#### hq_receiver.py

```python
import json
import sqlite3
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

THU_MUC_GOC = Path(__file__).resolve().parent.parent
FILE_DB = THU_MUC_GOC / "DuLieu" / "truso.db"

CAC_COT = ("ma_gd", "ma_cua_hang", "ma_may", "thoi_gian", "so_tien")


def khoi_tao():
    FILE_DB.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(FILE_DB) as ket_noi:
        ket_noi.execute("""
            CREATE TABLE IF NOT EXISTS giao_dich (
                ma_gd TEXT PRIMARY KEY NOT NULL,
                ma_cua_hang TEXT NOT NULL,
                ma_may TEXT NOT NULL,
                thoi_gian TEXT NOT NULL,
                so_tien INTEGER NOT NULL CHECK (so_tien > 0)
            )
        """)


class BoNhan(BaseHTTPRequestHandler):
    def tra_json(self, ma_http, noi_dung):
        du_lieu = json.dumps(noi_dung).encode("utf-8")

        self.send_response(ma_http)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(du_lieu)))
        self.end_headers()
        self.wfile.write(du_lieu)

    def do_POST(self):
        if self.path != "/giao-dich":
            self.tra_json(404, {"loi": "Duong dan khong ton tai"})
            return

        # Đọc và kiểm tra giao dịch cửa hàng gửi lên
        try:
            do_dai = int(self.headers.get("Content-Length", "0"))

            if not 0 < do_dai <= 10000:
                raise ValueError("Kich thuoc du lieu khong hop le")

            giao_dich = json.loads(self.rfile.read(do_dai))

            if not isinstance(giao_dich, dict):
                raise ValueError("Can gui mot doi tuong JSON")

            gia_tri = tuple(giao_dich[cot] for cot in CAC_COT)

            for gia_tri_chuoi in gia_tri[:4]:
                if not isinstance(gia_tri_chuoi, str) or not gia_tri_chuoi.strip():
                    raise ValueError("Truong thong tin bi trong")

            if type(gia_tri[4]) is not int or gia_tri[4] <= 0:
                raise ValueError("So tien phai la so nguyen duong")

        except (ValueError, KeyError, TypeError):
            self.tra_json(400, {"loi": "Du lieu giao dich khong hop le"})
            return

        ma_gd = giao_dich["ma_gd"]

        try:
            with sqlite3.connect(FILE_DB) as ket_noi:
                ket_noi.execute("BEGIN IMMEDIATE")

                ban_cu = ket_noi.execute("""
                    SELECT ma_gd, ma_cua_hang, ma_may, thoi_gian, so_tien
                    FROM giao_dich
                    WHERE ma_gd = ?
                """, (ma_gd,)).fetchone()

                if ban_cu is None:
                    ket_noi.execute("""
                        INSERT INTO giao_dich
                            (ma_gd, ma_cua_hang, ma_may, thoi_gian, so_tien)
                        VALUES (?, ?, ?, ?, ?)
                    """, gia_tri)
                    ket_qua = "DA_LUU"

                elif ban_cu == gia_tri:
                    # Gửi lại đúng giao dịch cũ: không thêm bản ghi
                    ket_qua = "DA_TON_TAI"

                else:
                    # Cùng mã nhưng nội dung khác: báo lỗi để kiểm tra
                    self.tra_json(409, {
                        "loi": "Cung ma giao dich nhung khac noi dung",
                        "ma_gd": ma_gd
                    })
                    return

            # Ra khỏi khối with thành công: dữ liệu đã được commit
        except sqlite3.Error as loi:
            print("Loi SQLite:", loi, flush=True)
            self.tra_json(500, {"loi": "Chua luu duoc giao dich"})
            return

        thoi_gian = datetime.now().isoformat(timespec="seconds")
        print(f"[{thoi_gian}] {ma_gd} | {ket_qua}", flush=True)

        # Chỉ xác nhận sau khi đã lưu thành công
        self.tra_json(200, {
            "ack": True,
            "ma_gd": ma_gd,
            "ket_qua": ket_qua
        })


if __name__ == "__main__":
    khoi_tao()

    may_chu = HTTPServer(("127.0.0.1", 8000), BoNhan)
    print("TRU SO DANG CHO NHAN GIAO DICH")
    print("Dia chi: http://127.0.0.1:8000/giao-dich")
    print("Du lieu:", FILE_DB)
    print("Nhan Ctrl + C de dung.")

    try:
        may_chu.serve_forever()
    except KeyboardInterrupt:
        print("\nDa dung may chu.")
    finally:
        may_chu.server_close()
```

#### kiem_tra_phuc_hoi.py

```python
import sqlite3
from pathlib import Path
from datetime import datetime

GOC = Path(__file__).resolve().parent.parent
BAN_SAO = (
    GOC / "DuLieu" / "SaoLuu"
    / "cuahang01_20261026_081101_081521.db"
)


def kiem_tra_phuc_hoi():
    if not BAN_SAO.is_file():
        raise FileNotFoundError(f"Khong tim thay ban sao: {BAN_SAO}")

    thu_muc = GOC / "DuLieu" / "PhucHoiThu"
    thu_muc.mkdir(parents=True, exist_ok=True)

    moc = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    file_thu = thu_muc / f"cuahang01_phuchoi_{moc}.db"

    nguon = sqlite3.connect(BAN_SAO.as_uri() + "?mode=ro", uri=True)
    try:
        file_thu.touch(exist_ok=False)
        dich = sqlite3.connect(file_thu)
        try:
            nguon.backup(dich)

            toan_ven = dich.execute("PRAGMA integrity_check").fetchall()
            if toan_ven != [("ok",)]:
                raise RuntimeError("Database phuc hoi khong toan ven")

            for bang, cot in [
                ("giao_dich", "ma_gd"),
                ("bo_dem", "ngay"),
            ]:
                sql = f"SELECT * FROM {bang} ORDER BY {cot}"
                du_lieu_goc = nguon.execute(sql).fetchall()
                du_lieu_thu = dich.execute(sql).fetchall()

                if du_lieu_goc != du_lieu_thu:
                    raise RuntimeError(f"Du lieu bang {bang} khong khop")

                print(f"Bang {bang}: khop, {len(du_lieu_thu)} ban ghi")

            print("Kiem tra toan ven: ok")
        finally:
            dich.close()
    finally:
        nguon.close()

    print("Thoi gian:", datetime.now().isoformat(timespec="seconds"))
    print("File phuc hoi thu:", file_thu)
    print("KET QUA: Phuc hoi va doi chieu du lieu thanh cong")


if __name__ == "__main__":
    kiem_tra_phuc_hoi()
```

#### kiem_tra_trung.py

```python
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen

THU_MUC_GOC = Path(__file__).resolve().parent.parent
DB_CUA_HANG = THU_MUC_GOC / "DuLieu" / "cuahang01.db"
DB_TRU_SO = THU_MUC_GOC / "DuLieu" / "truso.db"

CAU_LENH = """
    SELECT ma_gd, ma_cua_hang, ma_may, thoi_gian, so_tien
    FROM giao_dich
    ORDER BY ma_gd
"""


def doc_du_lieu(duong_dan):
    # Chỉ đọc file đã có, không tự tạo cơ sở dữ liệu mới
    ket_noi = sqlite3.connect(
        duong_dan.resolve().as_uri() + "?mode=ro",
        uri=True
    )
    ket_noi.row_factory = sqlite3.Row

    try:
        return [
            dict(dong)
            for dong in ket_noi.execute(CAU_LENH).fetchall()
        ]
    finally:
        ket_noi.close()


def kiem_tra():
    print("KIEM THU GUI LAP:", datetime.now().isoformat())

    cua_hang = doc_du_lieu(DB_CUA_HANG)
    truoc_gui = doc_du_lieu(DB_TRU_SO)

    print("So giao dich cua hang:", len(cua_hang))
    print("So giao dich tru so truoc gui:", len(truoc_gui))

    if not cua_hang or cua_hang != truoc_gui:
        print("CHUA DAT: Du lieu hai ben chua khop truoc khi thu.")
        return

    so_xac_nhan = 0

    for giao_dich in cua_hang:
        yeu_cau = Request(
            "http://127.0.0.1:8000/giao-dich",
            data=json.dumps(giao_dich).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with urlopen(yeu_cau, timeout=5) as phan_hoi:
            xac_nhan = json.loads(phan_hoi.read())

        hop_le = (
            isinstance(xac_nhan, dict)
            and xac_nhan.get("ack") is True
            and xac_nhan.get("ma_gd") == giao_dich["ma_gd"]
            and xac_nhan.get("ket_qua") == "DA_TON_TAI"
        )

        if not hop_le:
            print("CHUA DAT: Phan hoi khong dung:", xac_nhan)
            return

        so_xac_nhan += 1
        print(giao_dich["ma_gd"], "| DA_TON_TAI | ACK hop le")

    sau_gui = doc_du_lieu(DB_TRU_SO)
    so_ma_trung = len(sau_gui) - len({
        dong["ma_gd"] for dong in sau_gui
    })

    print("\n--- KET QUA ---")
    print("So phan hoi xac nhan hop le:", so_xac_nhan)
    print("So giao dich tru so sau gui:", len(sau_gui))
    print("So ban ghi du ma:", so_ma_trung)
    print("Du lieu hai ben khop:", cua_hang == sau_gui)

    if sau_gui == truoc_gui and so_ma_trung == 0:
        print("DAT: Gui lap khong lam thay doi du lieu tru so.")
    else:
        print("CHUA DAT: Can kiem tra lai du lieu.")


if __name__ == "__main__":
    try:
        kiem_tra()
    except Exception as loi:
        print("KIEM THU CHUA HOAN TAT:", loi)
        raise
```

#### sao_luu.py

```python
import sqlite3
from pathlib import Path
from datetime import datetime

THU_MUC_GOC = Path(__file__).resolve().parent.parent
FILE_DB = THU_MUC_GOC / "DuLieu" / "cuahang01.db"


def sao_luu():
    thu_muc = THU_MUC_GOC / "DuLieu" / "SaoLuu"
    thu_muc.mkdir(parents=True, exist_ok=True)

    thoi_gian = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    file_sao_luu = thu_muc / f"cuahang01_{thoi_gian}.db"

    # Mở dữ liệu gốc ở chế độ chỉ đọc.
    nguon = sqlite3.connect(FILE_DB.as_uri() + "?mode=ro", uri=True)

    try:
        # Không ghi đè bản sao lưu đã có.
        file_sao_luu.touch(exist_ok=False)
        dich = sqlite3.connect(file_sao_luu)

        try:
            # Sao lưu toàn bộ cơ sở dữ liệu bằng SQLite.
            nguon.backup(dich)

            ket_qua = dich.execute("PRAGMA integrity_check").fetchall()
            if ket_qua != [("ok",)]:
                raise RuntimeError("Ban sao luu khong dat kiem tra toan ven")

            so_luong = dich.execute(
                "SELECT COUNT(*) FROM giao_dich"
            ).fetchone()[0]
        finally:
            dich.close()
    finally:
        nguon.close()

    print("Thoi gian:", datetime.now().isoformat(timespec="seconds"))
    print("Sao luu thanh cong:", file_sao_luu)
    print("Kiem tra toan ven: ok")
    print("So giao dich trong ban sao:", so_luong)


if __name__ == "__main__":
    sao_luu()
```

#### store_agent.py

```python
import json
from urllib.request import Request, urlopen
from urllib.error import URLError
from datetime import datetime
import sqlite3
from pathlib import Path

# Xác định thư mục gốc của dự án nmcnnt
THU_MUC_GOC = Path(__file__).resolve().parent.parent

# File cơ sở dữ liệu của cửa hàng 01
FILE_DB = THU_MUC_GOC / "DuLieu" / "cuahang01.db"


def khoi_tao():
    # Tạo thư mục dữ liệu nếu chưa có
    FILE_DB.parent.mkdir(parents=True, exist_ok=True)

    # Mở cơ sở dữ liệu; nếu chưa có file thì SQLite tự tạo
    ket_noi = sqlite3.connect(FILE_DB)

    # Mỗi giao dịch có một mã duy nhất, không được trùng
    ket_noi.execute("""
        CREATE TABLE IF NOT EXISTS giao_dich (
            ma_gd TEXT PRIMARY KEY,
            ma_cua_hang TEXT NOT NULL,
            ma_may TEXT NOT NULL,
            thoi_gian TEXT NOT NULL,
            so_tien INTEGER NOT NULL CHECK (so_tien > 0),
            trang_thai TEXT NOT NULL DEFAULT 'PENDING'
                CHECK (trang_thai IN ('PENDING', 'SENT', 'ACKED'))
        )
    """)

    ket_noi.commit()
    ket_noi.close()

    print("Da khoi tao kho luu giao dich cua cua hang 01.")
    print("Vi tri:", FILE_DB)


def tao_giao_dich(so_tien):
    hien_tai = datetime.now()
    ngay = hien_tai.strftime("%Y%m%d")
    thoi_gian = hien_tai.isoformat(timespec="seconds")

    ket_noi = sqlite3.connect(FILE_DB)

    try:
        # Lưu số thứ tự vào SQLite để mở lại chương trình không bị reset
        ket_noi.execute("""
            CREATE TABLE IF NOT EXISTS bo_dem (
                ngay TEXT PRIMARY KEY,
                so_cuoi INTEGER NOT NULL
            )
        """)

        # Khóa lượt ghi để hai lần tạo không lấy cùng một số thứ tự
        ket_noi.execute("BEGIN IMMEDIATE")

        ket_noi.execute("""
            INSERT INTO bo_dem (ngay, so_cuoi)
            VALUES (?, 0)
            ON CONFLICT(ngay) DO NOTHING
        """, (ngay,))

        ket_noi.execute("""
            UPDATE bo_dem
            SET so_cuoi = so_cuoi + 1
            WHERE ngay = ?
        """, (ngay,))

        so_thu_tu = ket_noi.execute(
            "SELECT so_cuoi FROM bo_dem WHERE ngay = ?",
            (ngay,)
        ).fetchone()[0]

        ma_gd = f"CH01-POS01-{ngay}-{so_thu_tu:06d}"

        # Ghi giao dịch xuống ổ đĩa trước khi thực hiện gửi
        ket_noi.execute("""
            INSERT INTO giao_dich
                (ma_gd, ma_cua_hang, ma_may,
                 thoi_gian, so_tien, trang_thai)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (ma_gd, "CH01", "POS01", thoi_gian, so_tien, "PENDING"))

        ket_noi.commit()
        print(f"Da luu: {ma_gd} | {so_tien} VND | PENDING")

    except Exception:
        ket_noi.rollback()
        raise

    finally:
        ket_noi.close()


def xem_giao_dich():
    ket_noi = sqlite3.connect(FILE_DB)

    danh_sach = ket_noi.execute("""
        SELECT ma_gd, so_tien, trang_thai
        FROM giao_dich
        ORDER BY ma_gd
    """).fetchall()

    ket_noi.close()

    print("\n--- GIAO DICH DANG LUU TAI CUA HANG ---")

    for ma_gd, so_tien, trang_thai in danh_sach:
        print(f"{ma_gd} | {so_tien} VND | {trang_thai}")

    print(f"Tong cong: {len(danh_sach)} giao dich")

def gui_giao_dich():
    dia_chi = "http://127.0.0.1:8000/giao-dich"
    ket_noi = sqlite3.connect(FILE_DB)
    ket_noi.row_factory = sqlite3.Row

    try:
        # Chỉ lấy giao dịch chưa được trụ sở xác nhận
        danh_sach = ket_noi.execute("""
            SELECT ma_gd, ma_cua_hang, ma_may, thoi_gian, so_tien
            FROM giao_dich
            WHERE trang_thai IN ('PENDING', 'SENT')
            ORDER BY ma_gd
        """).fetchall()

        print(f"Co {len(danh_sach)} giao dich dang cho gui.")

        for dong in danh_sach:
            giao_dich = dict(dong)
            ma_gd = giao_dich["ma_gd"]

            # Ghi lại việc đã thử gửi, nhưng chưa có xác nhận
            ket_noi.execute("""
                UPDATE giao_dich
                SET trang_thai = 'SENT'
                WHERE ma_gd = ?
            """, (ma_gd,))
            ket_noi.commit()

            du_lieu = json.dumps(giao_dich).encode("utf-8")
            yeu_cau = Request(
                dia_chi,
                data=du_lieu,
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            try:
                with urlopen(yeu_cau, timeout=5) as phan_hoi:
                    xac_nhan = json.loads(phan_hoi.read())

                # Phải nhận xác nhận đúng mã giao dịch
                if (
                    not isinstance(xac_nhan, dict)
                    or xac_nhan.get("ack") is not True
                    or xac_nhan.get("ma_gd") != ma_gd
                ):
                    raise ValueError("Xac nhan khong hop le")

            except (URLError, OSError, ValueError) as loi:
                print(f"Chua xac nhan: {ma_gd} | {loi}")
                print("Van giu giao dich trong kho de gui lai.")
                continue

            ket_noi.execute("""
                UPDATE giao_dich
                SET trang_thai = 'ACKED'
                WHERE ma_gd = ?
            """, (ma_gd,))
            ket_noi.commit()

            print(f"Da xac nhan: {ma_gd} | ACKED")

    finally:
        ket_noi.close()


if __name__ == "__main__":
    khoi_tao()

    print("\n1. Tao them 5 giao dich mau")
    print("2. Xem giao dich da luu")
    lua_chon = input("Chon 1 hoac 2: ").strip()

    if lua_chon == "1":
        for so_tien in [50000, 75000, 120000, 35000, 200000]:
            tao_giao_dich(so_tien)
        xem_giao_dich()

    elif lua_chon == "2":
        xem_giao_dich()

    else:
        print("Lua chon khong hop le.")
```

#### xuat_giao_dich.py

```python
import csv
import sqlite3
from pathlib import Path
from datetime import datetime

THU_MUC_GOC = Path(__file__).resolve().parent.parent
FILE_DB = THU_MUC_GOC / "DuLieu" / "cuahang01.db"


def xuat_giao_dich():
    # Mở chỉ đọc để không thay đổi dữ liệu đang có.
    ket_noi = sqlite3.connect(FILE_DB.as_uri() + "?mode=ro", uri=True)

    try:
        con_tro = ket_noi.execute("""
            SELECT ma_gd, ma_cua_hang, ma_may,
                   thoi_gian, so_tien, trang_thai
            FROM giao_dich
            ORDER BY ma_gd
        """)
        ten_cot = [cot[0] for cot in con_tro.description]
        danh_sach = con_tro.fetchall()
    finally:
        ket_noi.close()

    thu_muc_xuat = THU_MUC_GOC / "DuLieu" / "Xuat"
    thu_muc_xuat.mkdir(parents=True, exist_ok=True)

    moc_thoi_gian = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    file_csv = thu_muc_xuat / f"giao_dich_CH01_{moc_thoi_gian}.csv"

    # UTF-8 có BOM giúp Excel đọc tiếng Việt.
    with file_csv.open("x", newline="", encoding="utf-8-sig") as tep:
        ghi = csv.writer(tep)
        ghi.writerow(ten_cot)
        ghi.writerows(danh_sach)

    print("Thoi gian:", datetime.now().isoformat(timespec="seconds"))
    print("Da xuat:", len(danh_sach), "giao dich")
    print("File:", file_csv)


if __name__ == "__main__":
    xuat_giao_dich()
```

### Cấu trúc CSDL thực tế

**cuahang01.db**

```sql
CREATE TABLE bo_dem (
                ngay TEXT PRIMARY KEY,
                so_cuoi INTEGER NOT NULL
            );
CREATE TABLE giao_dich (
            ma_gd TEXT PRIMARY KEY,
            ma_cua_hang TEXT NOT NULL,
            ma_may TEXT NOT NULL,
            thoi_gian TEXT NOT NULL,
            so_tien INTEGER NOT NULL CHECK (so_tien > 0),
            trang_thai TEXT NOT NULL DEFAULT 'PENDING'
                CHECK (trang_thai IN ('PENDING', 'SENT', 'ACKED'))
        );
```

**truso.db**

```sql
CREATE TABLE giao_dich (
                ma_gd TEXT PRIMARY KEY NOT NULL,
                ma_cua_hang TEXT NOT NULL,
                ma_may TEXT NOT NULL,
                thoi_gian TEXT NOT NULL,
                so_tien INTEGER NOT NULL CHECK (so_tien > 0)
            );
```

Dữ liệu mẫu hiện tại: cửa hàng và trụ sở cùng 15 giao dịch, tổng tiền 1.440.000 đồng; cửa hàng có 15 ACKED. File CSV ngày 26/10 chứa 10 giao dịch, tổng 960.000 đồng. Hai bộ khác thời điểm và không được trộn số liệu.
