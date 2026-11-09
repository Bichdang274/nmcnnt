"""TV2 – Sao lưu và khôi phục CSDL trụ sở (DuLieu/truso.db do hq_receiver.py của TV3 tạo).

Chạy tại thư mục gốc dự án (thư mục chứa Script/ và DuLieu/):
    python Script/sao_luu_tru_so.py sao-luu
    python Script/sao_luu_tru_so.py danh-sach
    python Script/sao_luu_tru_so.py khoi-phuc [--file truso_....db]
"""
import argparse
import sqlite3
from datetime import datetime
from pathlib import Path

THU_MUC_GOC = Path(__file__).resolve().parent.parent
FILE_DB = THU_MUC_GOC / "DuLieu" / "truso.db"
THU_MUC_SAO_LUU = THU_MUC_GOC / "DuLieu" / "SaoLuuTruSo"

# Nguon TV2 giu 7 ban; ban thu nay khong ap dung tu xoa
SO_BAN_GIU = 7


def mo_chi_doc(duong_dan):
    return sqlite3.connect(duong_dan.resolve().as_uri() + "?mode=ro", uri=True)


def dem_giao_dich(duong_dan):
    if not duong_dan.is_file():
        return 0

    ket_noi = mo_chi_doc(duong_dan)
    try:
        return ket_noi.execute("SELECT COUNT(*) FROM giao_dich").fetchone()[0]
    except sqlite3.OperationalError:
        return 0
    finally:
        ket_noi.close()


def chep_bang_api_backup(nguon_db, dich_db):
    # API backup của SQLite chụp một bản nhất quán, an toàn cả khi hq_receiver đang chạy
    nguon = mo_chi_doc(nguon_db)
    try:
        dich = sqlite3.connect(dich_db)
        try:
            nguon.backup(dich)
            if dich.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
                raise RuntimeError("Ban sao khong dat kiem tra toan ven")
        finally:
            dich.close()
    finally:
        nguon.close()


def danh_sach_ban_sao():
    if not THU_MUC_SAO_LUU.is_dir():
        return []
    return sorted(THU_MUC_SAO_LUU.glob("truso_*.db"))


def sao_luu():
    if not FILE_DB.is_file():
        raise SystemExit(f"Chua co CSDL tru so: {FILE_DB}")

    THU_MUC_SAO_LUU.mkdir(parents=True, exist_ok=True)
    moc = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    file_sao_luu = THU_MUC_SAO_LUU / f"truso_{moc}.db"

    # Không ghi đè bản sao lưu đã có
    file_sao_luu.touch(exist_ok=False)
    chep_bang_api_backup(FILE_DB, file_sao_luu)

    # Ban thu giu tat ca ban sao, khong tu xoa minh chung.

    print("Thoi gian:", datetime.now().isoformat(timespec="seconds"))
    print("Sao luu CSDL tru so thanh cong:", file_sao_luu.name)
    print("Kiem tra toan ven: ok")
    print("So giao dich trong ban sao:", dem_giao_dich(file_sao_luu))
    print(f"Dang giu {len(danh_sach_ban_sao())} ban sao (ban thu khong tu xoa)")


def in_danh_sach():
    cac_ban = danh_sach_ban_sao()
    print(f"--- BAN SAO LUU CSDL TRU SO ({len(cac_ban)}) ---")
    for ban in cac_ban:
        print(f"{ban.name} | {dem_giao_dich(ban)} giao dich")


def khoi_phuc(ten_file=None):
    cac_ban = danh_sach_ban_sao()
    if not cac_ban:
        raise SystemExit("Chua co ban sao luu nao")

    if ten_file:
        ban_sao = THU_MUC_SAO_LUU / ten_file
        if ban_sao not in cac_ban:
            raise SystemExit(f"Khong tim thay ban sao: {ten_file}")
    else:
        ban_sao = cac_ban[-1]

    truoc = dem_giao_dich(FILE_DB)
    chep_bang_api_backup(ban_sao, FILE_DB)

    print("Thoi gian:", datetime.now().isoformat(timespec="seconds"))
    print("Khoi phuc tu ban sao:", ban_sao.name)
    print(f"So giao dich tru so: {truoc} -> {dem_giao_dich(FILE_DB)}")
    print("Kiem tra toan ven: ok")
    print("Tiep theo: python Script/doi_chieu.py (kiem tra giao dich con thieu)")


if __name__ == "__main__":
    bo_doc = argparse.ArgumentParser(description="Sao luu / khoi phuc CSDL tru so")
    lenh = bo_doc.add_subparsers(dest="lenh", required=True)
    lenh.add_parser("sao-luu")
    lenh.add_parser("danh-sach")
    lenh_kp = lenh.add_parser("khoi-phuc")
    lenh_kp.add_argument("--file")
    tham_so = bo_doc.parse_args()

    if tham_so.lenh == "sao-luu":
        sao_luu()
    elif tham_so.lenh == "danh-sach":
        in_danh_sach()
    else:
        khoi_phuc(tham_so.file)
