import os
import re
import json
from urllib.request import Request, urlopen
from urllib.error import URLError
from datetime import datetime
import sqlite3
from pathlib import Path

# Xác định thư mục gốc của dự án nmcnnt
THU_MUC_GOC = Path(__file__).resolve().parent.parent

# Mỗi cặp cửa hàng/POS dùng file riêng; mặc định tương thích demo cũ.
MA_CUA_HANG = os.environ.get("TV3_STORE_ID", "CH01")
MA_MAY = os.environ.get("TV3_POS_ID", "POS01")
if any(not re.fullmatch(r"[A-Z][A-Z0-9]{1,15}", value) for value in (MA_CUA_HANG, MA_MAY)):
    raise ValueError("Mã cửa hàng/POS: 2–16 ký tự A–Z, 0–9; bắt đầu bằng chữ")
FILE_DB = (THU_MUC_GOC / os.environ.get("TV3_DB_PATH", "DuLieu/cuahang01.db")).resolve()
if not FILE_DB.is_relative_to(THU_MUC_GOC.resolve()):
    raise ValueError("CSDL phải nằm trong phiên hiện tại")
OFFLINE = os.environ.get("TV3_OFFLINE", "0")
if OFFLINE not in {"0", "1"}:
    raise ValueError("TV3_OFFLINE chỉ nhận 0 hoặc 1")


def kiem_tra_danh_tinh(ket_noi):
    if ket_noi.execute(
        "SELECT 1 FROM giao_dich WHERE ma_cua_hang != ? OR ma_may != ? LIMIT 1",
        (MA_CUA_HANG, MA_MAY)
    ).fetchone():
        raise ValueError("CSDL đã có giao dịch của cặp cửa hàng/POS khác; cần file riêng")


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

    # Chặn dùng nhầm file đã có dữ liệu của cửa hàng/POS khác.
    with sqlite3.connect(FILE_DB) as ket_noi:
        kiem_tra_danh_tinh(ket_noi)
    print(f"Da khoi tao kho giao dich {MA_CUA_HANG}/{MA_MAY}.")
    print("Vi tri:", FILE_DB)


def tao_giao_dich(so_tien):
    if type(so_tien) is not int or so_tien <= 0:
        raise ValueError("Số tiền phải là số nguyên dương")
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
        kiem_tra_danh_tinh(ket_noi)

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

        ma_gd = f"{MA_CUA_HANG}-{MA_MAY}-{ngay}-{so_thu_tu:06d}"

        # Ghi giao dịch xuống ổ đĩa trước khi thực hiện gửi
        ket_noi.execute("""
            INSERT INTO giao_dich
                (ma_gd, ma_cua_hang, ma_may,
                 thoi_gian, so_tien, trang_thai)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (ma_gd, MA_CUA_HANG, MA_MAY, thoi_gian, so_tien, "PENDING"))

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
    dia_chi = os.environ.get("TV23_HQ_URL", "http://127.0.0.1:18000/giao-dich")
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

            if OFFLINE == "1":
                print(f"MO PHONG NGAT KET NOI: {ma_gd} | SENT; giu du lieu, khong gui HTTP.")
                continue
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