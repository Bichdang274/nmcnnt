"""Màn hình trình chiếu UTF-8, không cần thư viện giao diện ngoài."""
import os
import re
import shutil
import textwrap
import unicodedata

ANSI = re.compile(r"\x1b\[[0-9;]*m")
MODE_NAMES = {"TV3": "DEMO TV3 NÂNG CAO", "TV2-TV3": "DEMO TÍCH HỢP TV2–TV3"}


class ScreenLog:
    """Console có thể có màu; terminal.txt luôn là văn bản thuần."""
    def __init__(self, console, logfile):
        self.console, self.logfile = console, logfile

    def write(self, value):
        self.console.write(value)
        self.logfile.write(ANSI.sub("", value))
        self.flush()
        return len(value)

    def flush(self):
        self.console.flush()
        self.logfile.flush()

    def isatty(self):
        return self.console.isatty()


def enable_color(stream):
    if not stream.isatty() or "NO_COLOR" in os.environ or os.environ.get("TERM") == "dumb":
        return False
    if os.name != "nt":
        return True
    try:
        import ctypes
        from ctypes import wintypes
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.GetStdHandle.argtypes = [wintypes.DWORD]
        kernel.GetStdHandle.restype = wintypes.HANDLE
        kernel.GetConsoleMode.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        kernel.SetConsoleMode.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        handle = kernel.GetStdHandle(-11 & 0xFFFFFFFF)
        mode = wintypes.DWORD()
        return bool(kernel.GetConsoleMode(handle, mode) and kernel.SetConsoleMode(handle, mode.value | 4))
    except (OSError, AttributeError):
        return False


def short_error(error):
    if isinstance(error, (KeyboardInterrupt, EOFError)):
        return "Đã dừng theo yêu cầu hoặc đầu vào đã đóng."
    message = str(error).splitlines()[0] if str(error) else type(error).__name__
    if "Không đọc được danh sách tiến trình" in message:
        return "Không đọc được tiến trình Windows. Kiểm tra quyền CIM/WMI."
    message = re.sub(r"[A-Za-z]:[\\/][^\s]+", "[đường dẫn trong log]", message)
    return textwrap.shorten(message, width=145, placeholder="…")


class Screen:
    def __init__(self, stream, no_color=False):
        self.stream = stream
        self.color = not no_color and enable_color(stream)
        self.width = max(64, min(100, shutil.get_terminal_size((100, 30)).columns - 2))

    def say(self, text="", tone=None):
        text = unicodedata.normalize("NFC", str(text))
        colors = {"title": "36;1", "pass": "32;1", "fail": "31;1", "wait": "33", "muted": "90"}
        if self.color and tone in colors:
            text = f"\033[{colors[tone]}m{text}\033[0m"
        self.stream.write(text + "\n")

    def rule(self):
        self.say("═" * self.width, "muted")

    def banner(self, run_name, paused):
        self.rule()
        self.say("HỆ THỐNG GIAO DỊCH CHUỖI CỬA HÀNG", "title")
        self.say("BẢN TÍCH HỢP THỬ NGHIỆM | " + ("THUYẾT TRÌNH" if paused else "TỰ ĐỘNG"))
        self.say("CH02: mô phỏng ngắt HTTP; chưa mô phỏng mất WAN thật.", "muted")
        self.say("Phiên minh chứng: runtime/" + run_name, "muted")
        self.rule()

    def stage(self, mode, number, total, title):
        self.say()
        self.say(MODE_NAMES[mode], "title")
        self.say(f"GIAI ĐOẠN {number}/{total} — {title}", "title")
        filled = round(20 * (number - 1) / total)
        self.say("[" + "■" * filled + "·" * (20 - filled) + "] "
                 f"{round(100 * (number - 1) / total)}% | ĐANG THỰC HIỆN", "wait")

    def status(self, passed, reason=None):
        self.say("TRẠNG THÁI: " + ("ĐẠT" if passed else "CHƯA ĐẠT"), "pass" if passed else "fail")
        if reason:
            for line in textwrap.wrap(reason, self.width):
                self.say(line, "muted" if passed else "fail")

    def table(self, value, mode):
        self.say("─" * min(66, self.width), "muted")
        self.say(f"{'CỬA HÀNG / POS':20} {'TỔNG':>6} {'PENDING':>9} {'SENT':>7} {'ACKED':>8}")
        for store in value["stores"]:
            states = store["states"] or dict.fromkeys(("PENDING", "SENT", "ACKED"), "?")
            name = "CH01/POS01" if store["db"].endswith("cuahang01.db") else "CH02/POS01"
            self.say(f"{name:20} {str(store['total']):>6} {states['PENDING']:>9} "
                     f"{states['SENT']:>7} {states['ACKED']:>8}")
        if mode == "TV3" and len(value["stores"]) < 2:
            self.say("CH02/POS01           Chưa khởi tạo", "muted")
        self.say(f"TRỤ SỞ: {value['hq_total']} giao dịch")
        self.say(f"Thiếu: {len(value['missing_hq'])} | Thừa: {len(value['extra_hq'])} | "
                 f"Trùng mã: {len(value['duplicate_ids'])} | Lệch nội dung: {len(value['changed'])}")

    def summary(self, results, passed, run_name):
        self.say()
        self.rule()
        self.say("BẢNG TỔNG KẾT TRÌNH DIỄN", "title")
        self.say(f"{'NỘI DUNG':25} {'KHO / ACKED':>13} {'TRỤ SỞ':>8} {'KẾT QUẢ':>11}")
        for result in results:
            value = result.get("final_state") or {}
            counts = f"{value.get('store_total', '?')}/{value.get('states', {}).get('ACKED', '?')}"
            name = "TV3 nâng cao" if result["mode"] == "TV3" else "Tích hợp TV2–TV3"
            self.say(f"{name:25} {counts:>13} {str(value.get('hq_total', '?')):>8} "
                     f"{'ĐẠT' if result['passed'] else 'CHƯA ĐẠT':>11}",
                     "pass" if result["passed"] else "fail")
        self.say("KẾT QUẢ CHUNG: " + ("ĐẠT" if passed else "CHƯA ĐẠT"), "pass" if passed else "fail")
        self.say("Không mất / không trùng / không lệch: " + ("ĐẠT" if passed else "CHƯA XÁC NHẬN"))
        self.say("Tiến độ: " + ("100% — HOÀN TẤT" if passed else "DỪNG — xem nguyên nhân và log"))
        self.say("Log & minh chứng: runtime/" + run_name, "muted")
        self.say("terminal.txt: màn hình | chi_tiet.txt: kỹ thuật | tong_ket.json: kết quả", "muted")
        self.rule()
