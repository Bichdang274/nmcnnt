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