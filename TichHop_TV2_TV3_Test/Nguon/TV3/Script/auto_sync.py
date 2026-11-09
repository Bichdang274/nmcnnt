
from datetime import datetime
from time import sleep
import sqlite3

from store_agent import khoi_tao, gui_giao_dich

# Cu 10 giay thu dong bo mot lan
CHU_KY = 10


def tu_dong_dong_bo():
    khoi_tao()

    print("=== HE THONG DONG BO TU DONG TV3 ===")
    print(f"Chu ky gui lai: {CHU_KY} giay")
    print("Nhan Ctrl + C de dung chuong trinh.")

    try:
        while True:
            hien_tai = datetime.now().strftime("%H:%M:%S")
            print(f"\n[{hien_tai}] Kiem tra giao dich...")

            try:
                gui_giao_dich()
            except (sqlite3.Error, OSError, ValueError) as loi:
                print("Loi dong bo:", loi)

            # Cho 10 giay truoc khi thu lai
            sleep(CHU_KY)

    except KeyboardInterrupt:
        print("\nDa dung dong bo tu dong.")


if __name__ == "__main__":
    tu_dong_dong_bo()
