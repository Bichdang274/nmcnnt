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