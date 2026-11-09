"""Bộ điều khiển bản thử TV2–TV3; mỗi phiên có dữ liệu và tiến trình riêng."""
import json
import os
import re
from pathlib import Path
import shlex
import socket
import subprocess
import sys
from datetime import datetime
import time

ROOT = Path(__file__).resolve().parent
SESSION_ROOT = ROOT / "PhienThu"
TEMPLATES = ROOT / "Script"
HQ_PORT = 18000
ENV = dict({key: value for key, value in os.environ.items()
            if key not in {"TV3_STORE_ID", "TV3_POS_ID", "TV3_DB_PATH", "TV3_OFFLINE"}},
           PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1",
           TV23_HQ_PORT=str(HQ_PORT),
           TV23_HQ_URL="http://127.0.0.1:" + str(HQ_PORT) + "/giao-dich")


def port_busy(port):
    with socket.socket() as sock:
        sock.settimeout(0.3)
        return sock.connect_ex(("127.0.0.1", port)) == 0


class Child:
    """Chỉ quản lý tiến trình do chính bộ điều khiển này tạo."""
    def __init__(self, label, filename, logfile, env=None):
        self.label, self.filename, self.logfile = label, filename, logfile
        self.process = None
        self.env = env

    def running(self):
        return self.process is not None and self.process.poll() is None

    def start(self, session):
        if self.running():
            print(self.label + " đang chạy.")
            return
        script = session / "Script" / self.filename
        if not script.is_file():
            raise FileNotFoundError(f"Thiếu script của phiên: {script.name}")
        if self.filename == "hq_receiver.py" and port_busy(HQ_PORT):
            raise RuntimeError("Cổng 18000 đang được dùng; không dừng hoặc chiếm dịch vụ bên ngoài.")
        with (session / "MinhChung" / self.logfile).open("ab") as log:
            self.process = subprocess.Popen(
                [sys.executable, "-B", "-u", str(script)],
                cwd=session, env=self.env if self.env is not None else ENV, stdin=subprocess.DEVNULL,
                stdout=log, stderr=subprocess.STDOUT)
        try:
            if self.filename == "hq_receiver.py":
                deadline = time.monotonic() + 5
                while time.monotonic() < deadline:
                    if not self.running():
                        raise RuntimeError("Receiver dừng khi khởi động; xem receiver_log.txt.")
                    if port_busy(HQ_PORT):
                        break
                    time.sleep(0.1)
                else:
                    raise RuntimeError("Receiver chưa mở cổng 18000 trong 5 giây.")
            else:
                time.sleep(0.3)
                if not self.running():
                    raise RuntimeError("Auto sync dừng khi khởi động; xem auto_sync_log.txt.")
        except BaseException:
            self.stop()
            raise
        print(self.label + " đã bật; PID " + str(self.process.pid))

    def stop(self):
        process = self.process
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
            print(self.label + " đã dừng (chỉ tiến trình do demo tạo).")
        self.process = None


class Demo:
    def __init__(self):
        self.session = None
        self.receiver = Child("Trụ sở", "hq_receiver.py", "receiver_log.txt")
        self.reset_stores()

    def reset_stores(self):
        self.selected = ("CH01", "POS01")
        self.links = {self.selected: False}
        self.agents = {self.selected: Child("Tự đồng bộ CH01/POS01", "auto_sync.py", "auto_sync_log.txt")}
        self.agent = self.agents[self.selected]

    def store_env(self):
        store, pos = self.selected
        path = ("DuLieu/cuahang01.db" if self.selected == ("CH01", "POS01")
                else f"DuLieu/CuaHang/{store}_{pos}.db")
        return dict(ENV, TV3_STORE_ID=store, TV3_POS_ID=pos, TV3_DB_PATH=path,
                    TV3_OFFLINE="1" if self.links[self.selected] else "0")

    def select_store(self, store, pos):
        session = self.require_session()
        if any(not re.fullmatch(r"[A-Z][A-Z0-9]{1,15}", value) for value in (store, pos)):
            raise ValueError("Mã cửa hàng/POS: 2–16 ký tự A–Z, 0–9; bắt đầu bằng chữ")
        self.selected = (store, pos)
        if self.selected not in self.agents:
            self.links[self.selected] = False
            self.agents[self.selected] = Child("Tự đồng bộ " + store + "/" + pos,
                "auto_sync.py", f"auto_sync_{store}_{pos}.txt")
        self.agent = self.agents[self.selected]
        self.agent.env = self.store_env()
        self.run(code="from Script.store_agent import khoi_tao; khoi_tao()")
        print("Đang chọn:", store + "/" + pos)

    def set_offline(self, offline):
        session = self.require_session()
        if not offline and not self.receiver.running() and port_busy(HQ_PORT):
            raise RuntimeError("Cổng 18000 do tiến trình ngoài phiên sử dụng; giữ ngắt HTTP, không gửi.")
        was_running = self.agent.running()
        self.agent.stop()
        self.links[self.selected] = offline
        self.agent.env = self.store_env()
        if was_running:
            self.agent.start(session)
        print("Mô phỏng ngắt HTTP cho cửa hàng đang chọn." if offline
              else "Đã nối lại HTTP cho cửa hàng đang chọn.")

    def require_single_store_tv2(self, label="TV2"):
        if self.selected != ("CH01", "POS01") or list(
                (self.require_session() / "DuLieu" / "CuaHang").glob("*.db")):
            raise RuntimeError(f"Công cụ {label} hiện dành cho phiên chỉ có CH01/POS01; "
                               "dùng giam-sat để đối chiếu nhiều kho. "
                               "Chưa mở rộng công cụ này cho nhiều cửa hàng.")

    def require_session(self):
        if self.session is None:
            raise RuntimeError("Chưa có phiên; dùng lệnh phien-moi.")
        resolved = self.session.resolve()
        if not resolved.is_relative_to(SESSION_ROOT.resolve()):
            raise RuntimeError("Từ chối đường dẫn ngoài PhienThu.")
        if not (resolved / "phien.json").is_file():
            raise RuntimeError("Thiếu file nhận diện phien.json của phiên.")
        return resolved

    def require_paused(self):
        if self.agent.running():
            raise RuntimeError("Dùng dong-bo-tat trước để chốt số liệu đối chiếu ổn định.")

    def run(self, filename=None, *args, code=None):
        session = self.require_session()
        command = [sys.executable, "-B", "-u"]
        if code is not None:
            command += ["-c", code]
        else:
            if filename not in {p.name for p in TEMPLATES.glob("*.py")}:
                raise RuntimeError("Script không thuộc bộ mã mẫu.")
            script = session / "Script" / filename
            if not script.is_file():
                raise FileNotFoundError(f"Thiếu script của phiên: {filename}")
            command += [str(script), *args]
        result = subprocess.run(command, cwd=session, env=self.store_env(),
                                capture_output=True, text=True, encoding="utf-8",
                                errors="replace", timeout=120)
        output = result.stdout + result.stderr
        print(output, end="" if output.endswith("\n") else "\n")
        with (session / "MinhChung" / "dieu_khien_log.txt").open("a", encoding="utf-8") as log:
            log.write("\n[" + datetime.now().isoformat(timespec="seconds") + "] "
                      + (filename or "khoi-tao-kho") + " " + " ".join(args) + "\n")
            log.write(output)
            log.write("\nMa thoat: " + str(result.returncode) + "\n")
        if result.returncode != 0:
            raise RuntimeError("Lệnh chưa đạt (mã thoát " + str(result.returncode)
                               + "). Xem log để xác định nguyên nhân; không coi bước này đã đạt.")
        return result

    def new_session(self):
        self.close()
        self.reset_stores()
        SESSION_ROOT.mkdir(exist_ok=True)
        session = SESSION_ROOT / datetime.now().strftime("Phien_%Y%m%d_%H%M%S_%f")
        session.mkdir(exist_ok=False)
        for name in ("Script", "DuLieu", "MinhChung"):
            (session / name).mkdir()
        for source in sorted(TEMPLATES.glob("*.py")):
            with (session / "Script" / source.name).open("xb") as target:
                target.write(source.read_bytes())
        with (session / "phien.json").open("x", encoding="utf-8") as target:
            json.dump({"muc_dich": "Dữ liệu phiên mới; kết quả phải được kiểm tra trong phiên này.",
                       "schema": "Schema truso.db TV3 tạm thời, cần TV2 xác nhận.",
                       "tao_luc": datetime.now().isoformat()}, target, ensure_ascii=False, indent=2)
        self.session = session
        self.run(code="from Script.store_agent import khoi_tao; khoi_tao()")
        print("Phiên mới:", session)
        print("Chưa tạo giao dịch; receiver và auto sync đang TẮT. Phiên cũ được giữ nguyên.")

    def backup_name(self, value, subdir):
        session = self.require_session()
        if not value or Path(value).name != value or "/" in value or "\\" in value:
            raise ValueError("Chỉ nhập tên file .db, không nhập đường dẫn.")
        directory = (session / "DuLieu" / subdir).resolve()
        candidate = (directory / value).resolve()
        if candidate.parent != directory or candidate.suffix != ".db" or not candidate.is_file():
            raise ValueError("Không tìm thấy bản sao hợp lệ trong phiên hiện tại.")
        return value

    def restore_hq(self, name):
        name = self.backup_name(name, "SaoLuuTruSo")
        self.close()
        # Giu them mot ban hien trang truoc khi phuc hoi; khong xoa ban nao.
        self.run("sao_luu_tru_so.py", "sao-luu")
        self.run("sao_luu_tru_so.py", "khoi-phuc", "--file", name)
        print("Đã phục hồi. Auto sync và receiver vẫn TẮT.")
        print("Tiếp theo: doi-chieu, tru-so-bat, gui-bu, doi-chieu; chỉ bật lại auto sync khi đã khớp.")

    def execute(self, line):
        parts = shlex.split(line)
        if not parts:
            return True
        action, *args = parts
        arity = {"phien-moi": 0, "tru-so-bat": 0, "tru-so-tat": 0, "tao-5": 0,
                 "dong-bo-bat": 0, "dong-bo-tat": 0, "gui-mot-luot": 0, "gui-lap": 0,
                 "doi-chieu": 0, "gui-bu": 0, "sao-luu-tru-so": 0, "danh-sach-ban-sao": 0,
                 "phuc-hoi": 1, "xuat-csv": 0, "sao-luu-kho": 0, "phuc-hoi-kho": 1,
                 "trang-thai": 0, "tro-giup": 0, "thoat": 0,
                 "giam-sat": 0, "cua-hang": 2, "ngat-cua-hang": 0, "noi-cua-hang": 0}
        if action not in arity or len(args) != arity[action]:
            raise ValueError("Lệnh hoặc tham số không hợp lệ; dùng tro-giup.")
        if action == "thoat":
            return False
        if action == "tro-giup":
            print(HELP)
            return True
        if action == "phien-moi":
            self.new_session()
            return True
        session = self.require_session()
        if action == "cua-hang":
            self.select_store(*args)
        elif action == "ngat-cua-hang":
            self.set_offline(True)
        elif action == "noi-cua-hang":
            self.set_offline(False)
        elif action == "giam-sat":
            self.run("giam_sat.py", "--session", str(session))
        elif action == "tru-so-bat":
            self.receiver.start(session)
        elif action == "tru-so-tat":
            self.receiver.stop()
        elif action == "dong-bo-bat":
            if not self.receiver.running() and port_busy(HQ_PORT):
                raise RuntimeError("Cổng 18000 do tiến trình ngoài phiên sử dụng; không gửi.")
            self.agent.env = self.store_env()
            self.agent.start(session)
        elif action == "dong-bo-tat":
            self.agent.stop()
        elif action == "tao-5":
            self.run(code="from Script.store_agent import tao_giao_dich\n"
                     "for x in [50000,75000,120000,35000,200000]: tao_giao_dich(x)")
        elif action == "gui-mot-luot":
            self.require_paused()
            if not self.receiver.running() and port_busy(HQ_PORT):
                raise RuntimeError("Cổng 18000 do tiến trình ngoài phiên sử dụng; không gửi.")
            self.run(code="from Script.store_agent import gui_giao_dich; gui_giao_dich()")
        elif action == "gui-lap":
            self.require_paused()
            if not self.receiver.running():
                raise RuntimeError("Bật receiver của phiên trước khi gửi lặp.")
            self.run("kiem_tra_trung.py")
        elif action == "doi-chieu":
            self.require_single_store_tv2()
            self.require_paused()
            self.run("doi_chieu.py")
        elif action == "gui-bu":
            self.require_single_store_tv2()
            self.require_paused()
            if not self.receiver.running():
                raise RuntimeError("Bật receiver của phiên trước khi gửi bù.")
            self.run("doi_chieu.py", "gui-bu")
            self.run("doi_chieu.py")
        elif action == "sao-luu-tru-so":
            self.require_paused()
            self.run("sao_luu_tru_so.py", "sao-luu")
        elif action == "danh-sach-ban-sao":
            self.run("sao_luu_tru_so.py", "danh-sach")
        elif action == "phuc-hoi":
            self.restore_hq(args[0])
        elif action == "xuat-csv":
            self.require_single_store_tv2("TV3 xuất/sao lưu/phục hồi kho")
            self.require_paused()
            self.run("xuat_giao_dich.py")
        elif action == "sao-luu-kho":
            self.require_single_store_tv2("TV3 xuất/sao lưu/phục hồi kho")
            self.require_paused()
            self.run("sao_luu.py")
        elif action == "phuc-hoi-kho":
            self.require_single_store_tv2("TV3 xuất/sao lưu/phục hồi kho")
            self.require_paused()
            name = self.backup_name(args[0], "SaoLuu")
            self.run("kiem_tra_phuc_hoi.py", "--file", name)
        elif action == "trang-thai":
            print("Cửa hàng/POS đang chọn:", "/".join(self.selected))
            print("Phiên:", session)
            print("Trụ sở:", "ĐANG CHẠY" if self.receiver.running() else "TẮT")
            print("Auto sync:", "ĐANG CHẠY" if self.agent.running() else "TẮT")
            print("Log:", session / "MinhChung")
            for key, agent in self.agents.items():
                print("/".join(key), "| auto sync:", agent.running(),
                      "| mô phỏng ngắt HTTP:", self.links[key])
            self.run("giam_sat.py", "--session", str(session))
        return True

    def close(self):
        # Luôn thử dừng receiver, kể cả khi dừng sender phát sinh lỗi.
        error = None
        try:
            for agent in self.agents.values():
                try:
                    agent.stop()
                except Exception as exc:
                    if error is None:
                        error = exc
        finally:
            self.receiver.stop()
        if error is not None:
            raise error


HELP = """
Lệnh nhập tại tich-hop> (không phải lệnh PowerShell):
  phien-moi                 Tạo phiên mới riêng; giữ nguyên mọi phiên cũ
  tru-so-bat | tru-so-tat    Bật/tắt receiver của phiên trên localhost:18000
  tao-5                     Tạo thêm đúng 5 giao dịch mẫu trong phiên hiện tại
  dong-bo-bat | dong-bo-tat  Bật/tắt auto sync; chờ 10 giây sau mỗi lượt
  gui-mot-luot              Gửi thủ công khi auto sync đã tắt
  gui-lap                   Gửi lặp và kiểm tra; auto sync phải tắt
  doi-chieu                 Đối chiếu; 0/0 hoặc thiếu dữ liệu không coi là đạt
  sao-luu-tru-so            Sao lưu trụ sở, giữ tất cả bản sao
  danh-sach-ban-sao         Xem tên bản sao để lựa chọn
  phuc-hoi TEN_FILE.db      Dừng sender/receiver, sao lưu hiện trạng, phục hồi
  gui-bu                    Gửi ACKED mà trụ sở thiếu rồi đối chiếu lại
  xuat-csv | sao-luu-kho    Công cụ kho cửa hàng; chỉ dùng dữ liệu phiên
  phuc-hoi-kho TEN_FILE.db  Thử phục hồi kho vào file riêng
  cua-hang CH02 POS01       Chọn/tạo kho riêng; không dừng sender cửa hàng khác
  ngat-cua-hang             Mô phỏng chặn gửi HTTP riêng cửa hàng đang chọn
  noi-cua-hang              Nối lại; giữ auto sync nếu trước đó đang chạy
  giam-sat                  Tổng hợp chỉ đọc mọi kho và trụ sở
  trang-thai | tro-giup | thoat
Dùng thoat để dừng các tiến trình của phiên trước khi đóng Terminal.
Schema TV3 là lựa chọn tạm thời, cần TV2 xác nhận.
"""


def main():
    # Windows có thể dùng cp1258 khi stdout được chuyển hướng; giữ tiếng Việt UTF-8.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    required = [ROOT / "MANIFEST.json"] + [
        TEMPLATES / name for name in (
            "store_agent.py", "hq_receiver.py", "auto_sync.py", "kiem_tra_trung.py",
            "doi_chieu.py", "sao_luu_tru_so.py", "sao_luu.py",
            "kiem_tra_phuc_hoi.py", "xuat_giao_dich.py", "giam_sat.py")
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    if missing:
        raise SystemExit("Thiếu file bắt buộc; không khởi động: " + ", ".join(missing))
    demo = Demo()
    print("BẢN TÍCH HỢP THỬ NGHIỆM TV2–TV3 | NHÁNH NÂNG CAO TV3")
    print("Giai đoạn 1 và 2 đã ĐẠT trên localhost; xem báo cáo và log đã lưu.")
    print("Phiên demo mới chưa được tạo hoặc kiểm thử; dùng phien-moi để bắt đầu.")
    print("Kết quả bổ sung được ghi riêng trong BAO_CAO_KIEM_THU_TICH_HOP.md.")
    print(HELP)
    try:
        while True:
            try:
                if not demo.execute(input("tich-hop> ")):
                    break
            except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
                print("CHƯA HOÀN TẤT:", exc)
    except (KeyboardInterrupt, EOFError):
        print("\nDừng bộ điều khiển.")
    finally:
        demo.close()


if __name__ == "__main__":
    main()
