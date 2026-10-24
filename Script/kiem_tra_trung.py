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