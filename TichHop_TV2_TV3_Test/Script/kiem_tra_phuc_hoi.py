import argparse
import sqlite3
from pathlib import Path
from datetime import datetime

GOC = Path(__file__).resolve().parent.parent


def kiem_tra_phuc_hoi(ban_sao):
    if not ban_sao.is_file():
        raise FileNotFoundError(f"Khong tim thay ban sao: {ban_sao}")

    thu_muc = GOC / "DuLieu" / "PhucHoiThu"
    thu_muc.mkdir(parents=True, exist_ok=True)

    moc = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    file_thu = thu_muc / f"cuahang01_phuchoi_{moc}.db"

    nguon = sqlite3.connect(ban_sao.as_uri() + "?mode=ro", uri=True)
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
    parser = argparse.ArgumentParser(description="Thu phuc hoi kho tu ban sao duoc chon")
    parser.add_argument("--file", required=True, help="Ten file trong DuLieu/SaoLuu")
    args = parser.parse_args()
    directory = (GOC / "DuLieu" / "SaoLuu").resolve()
    candidate = (directory / args.file).resolve()
    if Path(args.file).name != args.file or candidate.parent != directory or candidate.suffix != ".db":
        raise SystemExit("Chi chap nhan ten ban sao .db trong DuLieu/SaoLuu")
    kiem_tra_phuc_hoi(candidate)
