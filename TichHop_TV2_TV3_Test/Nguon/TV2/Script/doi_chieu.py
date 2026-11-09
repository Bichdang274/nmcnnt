"""TV2 – Đối chiếu dữ liệu cửa hàng 01 (DuLieu/cuahang01.db) với trụ sở (DuLieu/truso.db) và gửi bù.

Chạy tại thư mục gốc dự án:
    python Script/doi_chieu.py           # đối chiếu hai bên
    python Script/doi_chieu.py gui-bu    # gửi lại giao dịch đã ACKED mà trụ sở thiếu (sau khi khôi phục bản cũ)
"""
import json
import sys
import sqlite3
from datetime import datetime
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

THU_MUC_GOC = Path(__file__).resolve().parent.parent
DB_CUA_HANG = THU_MUC_GOC / "DuLieu" / "cuahang01.db"
DB_TRU_SO = THU_MUC_GOC / "DuLieu" / "truso.db"
DIA_CHI = "http://127.0.0.1:8000/giao-dich"

CAC_COT = ("ma_gd", "ma_cua_hang", "ma_may", "thoi_gian", "so_tien")


def doc(duong_dan, cau_lenh):
    # Chỉ đọc, không tự tạo file mới; chưa có bảng thì coi như rỗng
    if not duong_dan.is_file():
        return []
    ket_noi = sqlite3.connect(duong_dan.resolve().as_uri() + "?mode=ro", uri=True)
    ket_noi.row_factory = sqlite3.Row
    try:
        return [dict(dong) for dong in ket_noi.execute(cau_lenh).fetchall()]
    except sqlite3.OperationalError:
        return []
    finally:
        ket_noi.close()


def tinh_doi_chieu(db_cua_hang=DB_CUA_HANG, db_tru_so=DB_TRU_SO):
    cua_hang = doc(db_cua_hang, """
        SELECT ma_gd, ma_cua_hang, ma_may, thoi_gian, so_tien, trang_thai
        FROM giao_dich ORDER BY ma_gd
    """)
    tru_so = doc(db_tru_so, """
        SELECT ma_gd, ma_cua_hang, ma_may, thoi_gian, so_tien
        FROM giao_dich ORDER BY ma_gd
    """)
    # Truy vấn tìm mã trùng: phải RỖNG
    ma_trung = doc(db_tru_so, """
        SELECT ma_gd, COUNT(*) AS so_lan
        FROM giao_dich GROUP BY ma_gd HAVING COUNT(*) > 1
    """)

    o_tru_so = {dong["ma_gd"]: dong for dong in tru_so}
    trang_thai = {"PENDING": 0, "SENT": 0, "ACKED": 0}
    acked_thieu, chua_ve, lech_noi_dung = [], [], []

    for dong in cua_hang:
        trang_thai[dong["trang_thai"]] += 1
        ban_tru_so = o_tru_so.get(dong["ma_gd"])

        if ban_tru_so is None:
            # ACKED mà trụ sở không có = mất dữ liệu thật (cửa hàng sẽ không tự gửi lại)
            (acked_thieu if dong["trang_thai"] == "ACKED" else chua_ve).append(dong["ma_gd"])
        elif any(ban_tru_so[cot] != dong[cot] for cot in CAC_COT):
            lech_noi_dung.append(dong["ma_gd"])

    return {
        "cua_hang": len(cua_hang),
        "trang_thai": trang_thai,
        "tru_so": len(tru_so),
        "ma_trung": [dong["ma_gd"] for dong in ma_trung],
        "acked_thieu": acked_thieu,
        "chua_ve": chua_ve,
        "lech_noi_dung": lech_noi_dung,
        "khop": len(cua_hang) == len(tru_so) and not acked_thieu and not chua_ve
                and not lech_noi_dung and not ma_trung,
    }


def in_doi_chieu():
    kq = tinh_doi_chieu()
    tt = kq["trang_thai"]
    print("DOI CHIEU DU LIEU:", datetime.now().isoformat(timespec="seconds"))
    print(f"Cua hang 01: {kq['cua_hang']} giao dich "
          f"(PENDING {tt['PENDING']}, SENT {tt['SENT']}, ACKED {tt['ACKED']})")
    print(f"Tru so: {kq['tru_so']} giao dich")
    print("Ma giao dich trung tai tru so:", len(kq["ma_trung"]), "(phai = 0)")
    print("Chua ve tru so (PENDING/SENT):", len(kq["chua_ve"]))
    print("Da ACKED nhung tru so thieu:", len(kq["acked_thieu"]), "(phai = 0)")
    for ma_gd in kq["acked_thieu"]:
        print("  thieu:", ma_gd)
    print("Lech noi dung:", len(kq["lech_noi_dung"]))

    if kq["khop"]:
        print("KET QUA: Hai ben khop, khong mat, khong trung")
    elif kq["acked_thieu"]:
        print("CANH BAO: Tru so thieu giao dich da ACKED -> chay: python Script/doi_chieu.py gui-bu")
    elif kq["chua_ve"]:
        print("CHUA KHOP: Con giao dich chua gui ve -> chay gui lai (store_agent)")
    else:
        print("CHUA KHOP: Can kiem tra lai")


def gui_bu():
    # Sau khi khôi phục từ bản sao cũ: gửi lại giao dịch ACKED mà trụ sở thiếu.
    # Trụ sở kiểm tra mã giao dịch nên bản đã có chỉ trả DA_TON_TAI, không ghi trùng.
    thieu = set(tinh_doi_chieu()["acked_thieu"])
    cua_hang = doc(DB_CUA_HANG, "SELECT ma_gd, ma_cua_hang, ma_may, thoi_gian, so_tien "
                                "FROM giao_dich ORDER BY ma_gd")
    can_gui = [dong for dong in cua_hang if dong["ma_gd"] in thieu]
    print("GUI BU:", datetime.now().isoformat(timespec="seconds"))
    print(f"Co {len(can_gui)} giao dich da ACKED ma tru so thieu.")

    so_ack = 0
    for giao_dich in can_gui:
        yeu_cau = Request(DIA_CHI, data=json.dumps(giao_dich).encode("utf-8"),
                          headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urlopen(yeu_cau, timeout=5) as phan_hoi:
                xac_nhan = json.loads(phan_hoi.read())
        except (URLError, OSError, ValueError) as loi:
            print(f"Chua gui duoc: {giao_dich['ma_gd']} | {loi}")
            continue

        if xac_nhan.get("ack") is True and xac_nhan.get("ma_gd") == giao_dich["ma_gd"]:
            so_ack += 1
            print(f"{giao_dich['ma_gd']} | {xac_nhan.get('ket_qua')} | ACK hop le")
        else:
            print(f"Phan hoi khong hop le: {xac_nhan}")

    print(f"Gui bu xong: {so_ack}/{len(can_gui)} duoc xac nhan")


if __name__ == "__main__":
    if sys.argv[1:] == ["gui-bu"]:
        gui_bu()
    elif sys.argv[1:] in ([], ["--json"]):
        if sys.argv[1:] == ["--json"]:
            print(json.dumps(tinh_doi_chieu(), ensure_ascii=False, indent=2))
        else:
            in_doi_chieu()
    else:
        raise SystemExit(__doc__)
