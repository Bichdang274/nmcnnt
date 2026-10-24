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