"""Bo dieu khien thu tich hop rieng. Chi tao du lieu khi nguoi dung ra lenh."""
import json
import os
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
ENV = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1",
           TV23_HQ_PORT=str(HQ_PORT),
           TV23_HQ_URL="http://127.0.0.1:" + str(HQ_PORT) + "/giao-dich")


def port_busy(port):
    with socket.socket() as sock:
        sock.settimeout(0.3)
        return sock.connect_ex(("127.0.0.1", port)) == 0


class Child:
    """Chi quan ly tien trinh do chinh bo dieu khien nay tao."""
    def __init__(self, label, filename, logfile):
        self.label, self.filename, self.logfile = label, filename, logfile
        self.process = None

    def running(self):
        return self.process is not None and self.process.poll() is None

    def start(self, session):
        if self.running():
            print(self.label + " da chay.")
            return
        if self.filename == "hq_receiver.py" and port_busy(HQ_PORT):
            raise RuntimeError("Cong 18000 dang co chu. Khong dung/chiem dich vu ben ngoai.")
        with (session / "MinhChung" / self.logfile).open("ab") as log:
            self.process = subprocess.Popen(
                [sys.executable, "-B", "-u", str(session / "Script" / self.filename)],
                cwd=session, env=ENV, stdin=subprocess.DEVNULL,
                stdout=log, stderr=subprocess.STDOUT)
        try:
            if self.filename == "hq_receiver.py":
                deadline = time.monotonic() + 5
                while time.monotonic() < deadline:
                    if not self.running():
                        raise RuntimeError("Tru so dung khi khoi dong; xem receiver_log.txt.")
                    if port_busy(HQ_PORT):
                        break
                    time.sleep(0.1)
                else:
                    raise RuntimeError("Tru so khong mo cong 18000 trong 5 giay.")
            else:
                time.sleep(0.3)
                if not self.running():
                    raise RuntimeError("Auto sync dung khi khoi dong; xem auto_sync_log.txt.")
        except BaseException:
            self.stop()
            raise
        print(self.label + " da bat; PID " + str(self.process.pid))

    def stop(self):
        process = self.process
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
            print(self.label + " da dung (chi tien trinh do demo tao).")
        self.process = None


class Demo:
    def __init__(self):
        self.session = None
        self.receiver = Child("Tru so", "hq_receiver.py", "receiver_log.txt")
        self.agent = Child("Tu dong dong bo", "auto_sync.py", "auto_sync_log.txt")

    def require_session(self):
        if self.session is None:
            raise RuntimeError("Chua co phien. Dung lenh phien-moi.")
        resolved = self.session.resolve()
        if not resolved.is_relative_to(SESSION_ROOT.resolve()):
            raise RuntimeError("Tu choi duong dan ngoai PhienThu.")
        if not (resolved / "phien.json").is_file():
            raise RuntimeError("Thieu dau nhan dien phien.")
        return resolved

    def require_paused(self):
        if self.agent.running():
            raise RuntimeError("Dung dong-bo-tat truoc de co moc doi chieu on dinh.")

    def run(self, filename=None, *args, code=None):
        session = self.require_session()
        command = [sys.executable, "-B", "-u"]
        if code is not None:
            command += ["-c", code]
        else:
            if filename not in {p.name for p in TEMPLATES.glob("*.py")}:
                raise RuntimeError("Script khong nam trong bo mau.")
            command += [str(session / "Script" / filename), *args]
        result = subprocess.run(command, cwd=session, env=ENV,
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
            raise RuntimeError("Lenh chua dat (ma thoat " + str(result.returncode)
                               + "). Xem log; khong coi la thanh cong.")
        return result

    def new_session(self):
        self.agent.stop()
        self.receiver.stop()
        SESSION_ROOT.mkdir(exist_ok=True)
        session = SESSION_ROOT / datetime.now().strftime("Phien_%Y%m%d_%H%M%S_%f")
        session.mkdir(exist_ok=False)
        for name in ("Script", "DuLieu", "MinhChung"):
            (session / name).mkdir()
        for source in sorted(TEMPLATES.glob("*.py")):
            with (session / "Script" / source.name).open("xb") as target:
                target.write(source.read_bytes())
        with (session / "phien.json").open("x", encoding="utf-8") as target:
            json.dump({"muc_dich": "du lieu thu rieng; khong phai minh chung da dat",
                       "schema": "truso.db TV3 - tam thoi",
                       "tao_luc": datetime.now().isoformat()}, target, ensure_ascii=False, indent=2)
        self.session = session
        self.run(code="from Script.store_agent import khoi_tao; khoi_tao()")
        print("Phien moi:", session)
        print("Chua tao giao dich; tru so va auto sync van TAT. Phien cu duoc giu nguyen.")

    def backup_name(self, value, subdir):
        session = self.require_session()
        if not value or Path(value).name != value or "/" in value or "\\" in value:
            raise ValueError("Chi nhap ten file .db, khong nhap duong dan.")
        directory = (session / "DuLieu" / subdir).resolve()
        candidate = (directory / value).resolve()
        if candidate.parent != directory or candidate.suffix != ".db" or not candidate.is_file():
            raise ValueError("Khong tim thay ban sao hop le trong phien hien tai.")
        return value

    def restore_hq(self, name):
        name = self.backup_name(name, "SaoLuuTruSo")
        self.agent.stop()
        self.receiver.stop()
        # Giu them mot ban hien trang truoc khi phuc hoi; khong xoa ban nao.
        self.run("sao_luu_tru_so.py", "sao-luu")
        self.run("sao_luu_tru_so.py", "khoi-phuc", "--file", name)
        print("Da phuc hoi. Auto sync va tru so VAN TAT.")
        print("Tiep: doi-chieu -> tru-so-bat -> gui-bu -> doi-chieu -> dong-bo-bat.")

    def execute(self, line):
        parts = shlex.split(line)
        if not parts:
            return True
        action, *args = parts
        arity = {"phien-moi": 0, "tru-so-bat": 0, "tru-so-tat": 0, "tao-5": 0,
                 "dong-bo-bat": 0, "dong-bo-tat": 0, "gui-mot-luot": 0, "gui-lap": 0,
                 "doi-chieu": 0, "gui-bu": 0, "sao-luu-tru-so": 0, "danh-sach-ban-sao": 0,
                 "phuc-hoi": 1, "xuat-csv": 0, "sao-luu-kho": 0, "phuc-hoi-kho": 1,
                 "trang-thai": 0, "tro-giup": 0, "thoat": 0}
        if action not in arity or len(args) != arity[action]:
            raise ValueError("Lenh/tham so khong hop le. Dung tro-giup.")
        if action == "thoat":
            return False
        if action == "tro-giup":
            print(HELP)
            return True
        if action == "phien-moi":
            self.new_session()
            return True
        session = self.require_session()
        if action == "tru-so-bat":
            self.receiver.start(session)
        elif action == "tru-so-tat":
            self.receiver.stop()
        elif action == "dong-bo-bat":
            if not self.receiver.running() and port_busy(HQ_PORT):
                raise RuntimeError("Cong 18000 do tien trinh ben ngoai chiem; khong gui.")
            self.agent.start(session)
        elif action == "dong-bo-tat":
            self.agent.stop()
        elif action == "tao-5":
            self.run(code="from Script.store_agent import tao_giao_dich\n"
                     "for x in [50000,75000,120000,35000,200000]: tao_giao_dich(x)")
        elif action == "gui-mot-luot":
            self.require_paused()
            if not self.receiver.running() and port_busy(HQ_PORT):
                raise RuntimeError("Cong 18000 do tien trinh ben ngoai chiem; khong gui.")
            self.run(code="from Script.store_agent import gui_giao_dich; gui_giao_dich()")
        elif action == "gui-lap":
            self.require_paused()
            if not self.receiver.running():
                raise RuntimeError("Bat tru so cua phien truoc khi gui lap.")
            self.run("kiem_tra_trung.py")
        elif action == "doi-chieu":
            self.require_paused()
            self.run("doi_chieu.py")
        elif action == "gui-bu":
            self.require_paused()
            if not self.receiver.running():
                raise RuntimeError("Bat tru so cua phien truoc khi gui bu.")
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
            self.require_paused()
            self.run("xuat_giao_dich.py")
        elif action == "sao-luu-kho":
            self.require_paused()
            self.run("sao_luu.py")
        elif action == "phuc-hoi-kho":
            self.require_paused()
            name = self.backup_name(args[0], "SaoLuu")
            self.run("kiem_tra_phuc_hoi.py", "--file", name)
        elif action == "trang-thai":
            print("Phien:", session)
            print("Tru so:", "DANG CHAY" if self.receiver.running() else "TAT")
            print("Auto sync:", "DANG CHAY" if self.agent.running() else "TAT")
            print("Log:", session / "MinhChung")
        return True

    def close(self):
        self.agent.stop()
        self.receiver.stop()


HELP = """
Lenh trong bo dieu khien (khong phai lenh PowerShell):
  phien-moi                 Tao phien RIENG; giu nguyen moi phien cu
  tru-so-bat | tru-so-tat    Bat/tat receiver cua phien, localhost:18000
  tao-5                     Tao 5 GD MAU trong phien hien tai
  dong-bo-bat | dong-bo-tat  Bat/tat auto_sync.py cua TV3
  gui-mot-luot              Gui thu cong; auto sync phai tat
  gui-lap                   KT3-b; auto sync phai tat
  doi-chieu                 0/0 khong duoc coi la DAT; can auto sync tat
  sao-luu-tru-so            Tao ban sao HQ, giu tat ca ban
  danh-sach-ban-sao         In ten file de chon ban phuc hoi
  phuc-hoi TEN_FILE.db      Dung ca 2 tien trinh; sao luu hien trang; phuc hoi
  gui-bu                    Gui ACKED ma HQ thieu; doi chieu lai
  xuat-csv | sao-luu-kho    Cong cu TV3, chi tren du lieu phien
  phuc-hoi-kho TEN_FILE.db  Thu phuc hoi kho vao file rieng, khong ghi de kho
  trang-thai | tro-giup | thoat
Du lieu 15 GD goc KHONG duoc sao chep vao day. Schema TV3 la lua chon TAM THOI.
"""


def main():
    if not TEMPLATES.is_dir() or not (ROOT / "MANIFEST.json").is_file():
        raise SystemExit("Thieu bo mau/manifest; khong khoi dong.")
    demo = Demo()
    print("MOI TRUONG THU TICH HOP TV2 + TV3 - CHUA CO KET QUA KIEM THU")
    print(HELP)
    try:
        while True:
            try:
                if not demo.execute(input("tich-hop> ")):
                    break
            except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
                print("CHUA HOAN TAT:", exc)
    except (KeyboardInterrupt, EOFError):
        print("\nDung bo dieu khien.")
    finally:
        demo.close()


if __name__ == "__main__":
    main()
