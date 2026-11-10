"""Demo tự động TV3 và TV2–TV3; chỉ ghi vào runtime mới, dùng thư viện chuẩn."""
import argparse
import contextlib
from datetime import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import runpy
import socket
import subprocess
import sys
import threading
import time
import traceback
import uuid

import demo_tich_hop as existing
from giao_dien_demo import MODE_NAMES, Screen, ScreenLog, short_error

ROOT = Path(__file__).resolve().parent
RUNTIME = ROOT / "runtime"
HISTORY = []
STEP_TIMEOUT = 45


def save(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def free_port():
    """Bind độc quyền cả IPv4/IPv6; không gửi dữ liệu tới dịch vụ bên ngoài."""
    families = [(socket.AF_INET, "0.0.0.0")]
    if socket.has_ipv6:
        families.append((socket.AF_INET6, "::"))
    for family, address in families:
        with socket.socket(family, socket.SOCK_STREAM) as probe:
            if family == socket.AF_INET6:
                probe.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)
            if os.name == "nt":
                probe.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            try:
                probe.bind((address, 18000))
            except OSError as exc:
                raise RuntimeError("Cổng 18000 chưa an toàn/đang bị chiếm. "
                                   "Không dừng tiến trình lạ; xem kiem_tra_moi_truong.json.") from exc


def preflight(directory):
    require(sys.version_info >= (3, 9), "Cần Python 3.9 trở lên.")
    needed = ["store_agent.py", "hq_receiver.py", "auto_sync.py", "doi_chieu.py",
              "sao_luu_tru_so.py", "giam_sat.py"]
    for name in needed:
        require((existing.TEMPLATES / name).is_file(), "Thiếu Script/" + name)
    info = {"python": sys.version, "executable": sys.executable,
            "port": 18000, "processes": [], "port_safe": False}
    try:
        if os.name == "nt":
            command = (
                "$ErrorActionPreference='Stop'; "
                "$p=@(Get-CimInstance Win32_Process | Where-Object { "
                "$_.Name -match '^python(w)?(\\d+(\\.\\d+)?)?\\.exe$' -and "
                "$_.CommandLine -match 'hq_receiver|auto_sync|demo_tich_hop|demo_1_click' } | "
                "Select-Object ProcessId,Name,CommandLine); "
                "$ports=@(Get-NetTCPConnection -ErrorAction Stop | "
                "Where-Object { $_.LocalPort -eq 18000 } | "
                "Select-Object LocalAddress,State,OwningProcess); "
                "@{processes=$p;port_connections=$ports} | ConvertTo-Json -Depth 4 -Compress"
            )
            result = subprocess.run(
                ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=15,
                creationflags=subprocess.CREATE_NO_WINDOW)
            require(result.returncode == 0, "Không đọc được danh sách tiến trình: " + result.stderr)
            info.update(json.loads(result.stdout))
        print("Tiến trình liên quan hiện có (chỉ quan sát):")
        for process in info["processes"]:
            print(f"  PID {process['ProcessId']} | {process['Name']} | {process['CommandLine']}")
        free_port()
        info["port_safe"] = True
        print("Cổng 18000 trống; đã kiểm tra bind độc quyền IPv4/IPv6.")
    except BaseException as exc:
        info["error"] = str(exc)
        raise
    finally:
        save(directory / "kiem_tra_moi_truong.json", info)


def worker(filename, session_text, ready_text):
    """Host vòng đời; nghiệp vụ dùng nguyên bản sao Script của phiên."""
    session, ready = Path(session_text).resolve(), Path(ready_text).resolve()
    require(session.is_relative_to(RUNTIME.resolve()) and (session / "phien.json").is_file(),
            "Worker chỉ được chạy trong phiên runtime đã nhận diện.")
    require(ready.parent == session / "MinhChung", "Ready file phải thuộc phiên.")
    require(filename in {"hq_receiver.py", "auto_sync.py"}, "Worker không hợp lệ.")
    sys.path.insert(0, str(session / "Script"))
    module = runpy.run_path(str(session / "Script" / filename))
    stop = threading.Event()

    def read_stop():
        # EOF cũng dừng worker nếu bộ điều phối bị đóng đột ngột.
        sys.stdin.readline()
        stop.set()

    threading.Thread(target=read_stop, daemon=True).start()
    if filename == "hq_receiver.py":
        module["khoi_tao"]()
        server = module["HTTPServer"](("127.0.0.1", 18000), module["BoNhan"],
                                      bind_and_activate=False)
        try:
            server.allow_reuse_address = False
            if os.name == "nt":
                server.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            server.socket.settimeout(5)
            server.server_bind()
            server.server_activate()
            server.timeout = 0.25
            save(ready, {"pid": os.getpid(), "port": 18000})
            print("TRỤ SỞ SẴN SÀNG |", session / "DuLieu" / "truso.db", flush=True)
            while not stop.is_set():
                server.handle_request()
        finally:
            server.server_close()
        print("Trụ sở đã đóng an toàn.", flush=True)
    else:
        original_send = module["tu_dong_dong_bo"].__globals__["gui_giao_dich"]

        def send_with_current_link():
            # Chỉ làm mới cờ mô phỏng HTTP giữa các lượt; hàm giao dịch giữ nguyên.
            link = json.loads(Path(os.environ["TV3_DEMO_LINK_FILE"]).read_text(encoding="utf-8"))
            require(type(link["offline"]) is bool, "Cờ mô phỏng HTTP không hợp lệ.")
            original_send.__globals__["OFFLINE"] = "1" if link["offline"] else "0"
            original_send()

        def interruptible_sleep(seconds):
            if stop.wait(seconds):
                raise KeyboardInterrupt

        # Giữ nguyên hàm auto sync và chu kỳ 10 giây; chỉ cho phép ngắt lúc chờ.
        module["tu_dong_dong_bo"].__globals__["sleep"] = interruptible_sleep
        module["tu_dong_dong_bo"].__globals__["gui_giao_dich"] = send_with_current_link
        save(ready, {"pid": os.getpid(), "cycle_seconds": module["CHU_KY"]})
        module["tu_dong_dong_bo"]()


class ManagedChild(existing.Child):
    def start(self, session):
        if self.running():
            return
        if self.filename == "hq_receiver.py":
            free_port()
        ready = session / "MinhChung" / ("san_sang_" + uuid.uuid4().hex + ".json")
        env = dict(self.env if self.env is not None else existing.ENV)
        if self.filename == "auto_sync.py":
            link = session / "MinhChung" / ("http_" + env.get("TV3_STORE_ID", "CH01")
                                             + "_" + env.get("TV3_POS_ID", "POS01") + ".json")
            if not link.exists():
                save(link, {"offline": env.get("TV3_OFFLINE", "0") == "1"})
            env["TV3_DEMO_LINK_FILE"] = str(link)
        with (session / "MinhChung" / self.logfile).open("ab") as log:
            self.process = subprocess.Popen(
                [sys.executable, "-B", "-u", str(Path(__file__).resolve()),
                 "--worker", self.filename, str(session), str(ready)],
                cwd=session, env=env, stdin=subprocess.PIPE, stdout=log, stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        self.record = {"label": self.label, "pid": self.process.pid, "session": str(session),
                       "started": datetime.now().isoformat(), "stopped": False}
        HISTORY.append(self.record)
        deadline = time.monotonic() + min(STEP_TIMEOUT, 10)
        while not ready.exists():
            require(self.running(), self.label + " dừng khi khởi động; xem " + self.logfile)
            require(time.monotonic() < deadline, "Hết thời gian khởi động " + self.label)
            time.sleep(0.1)
        require(json.loads(ready.read_text(encoding="utf-8"))["pid"] == self.process.pid,
                "Ready file không khớp PID của phiên.")
        require(self.running(), self.label + " đã dừng bất thường.")
        print(f"{self.label} đã bật | PID {self.process.pid}")

    def stop(self):
        process = self.process
        if process is None:
            return
        forced = False
        try:
            if process.poll() is None:
                try:
                    process.stdin.write(b"stop\n")
                    process.stdin.flush()
                except (BrokenPipeError, OSError):
                    pass
                try:
                    process.wait(timeout=STEP_TIMEOUT)
                except subprocess.TimeoutExpired:
                    forced = True
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=5)
        finally:
            process.stdin.close()
            self.record.update(stopped=process.poll() is not None, exit_code=process.poll(),
                               forced=forced, ended=datetime.now().isoformat())
            if process.poll() is not None:
                self.process = None
        print(f"{self.label} đã dừng | PID {process.pid} | mã thoát {process.returncode}")
        require(not forced and process.returncode == 0, self.label + " chưa dừng bình thường.")


class Demo(existing.Demo):
    def set_offline(self, offline):
        session = self.require_session()
        if not offline and not self.receiver.running():
            raise RuntimeError("Chỉ nối lại khi receiver của phiên đang chạy.")
        store, pos = self.selected
        link = session / "MinhChung" / f"http_{store}_{pos}.json"
        temporary = link.with_name(link.name + "." + uuid.uuid4().hex + ".tmp")
        save(temporary, {"offline": offline})
        temporary.replace(link)
        self.links[self.selected] = offline
        self.agent.env = self.store_env()
        print(("Đã ngắt" if offline else "Đã nối lại") + f" HTTP mô phỏng {store}/{pos}; "
              "worker đang chạy sẽ đọc cờ ở chu kỳ kế tiếp.")

    def reset_stores(self):
        super().reset_stores()
        self.agent = ManagedChild("Tự đồng bộ CH01/POS01", "auto_sync.py", "auto_sync_log.txt")
        self.agents[self.selected] = self.agent

    def select_store(self, store, pos):
        super().select_store(store, pos)
        if not isinstance(self.agent, ManagedChild):
            self.agent = ManagedChild(self.agent.label, self.agent.filename, self.agent.logfile,
                                      self.store_env())
            self.agents[self.selected] = self.agent

    def __init__(self):
        super().__init__()
        self.receiver = ManagedChild("Trụ sở", "hq_receiver.py", "receiver_log.txt")

    def run(self, filename=None, *args, code=None):
        session = self.require_session()
        if code is None:
            require(filename in {p.name for p in existing.TEMPLATES.glob("*.py")},
                    "Script không thuộc bộ mã mẫu.")
        command = [sys.executable, "-B", "-u"] + (
            ["-c", code] if code is not None else [str(session / "Script" / filename), *args])
        process = subprocess.Popen(command, cwd=session, env=self.store_env(),
                                   stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT,
                                   creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        record = {"label": filename or "tạo/khởi tạo kho", "pid": process.pid,
                  "session": str(session), "stopped": False}
        HISTORY.append(record)
        try:
            output, _ = process.communicate(timeout=STEP_TIMEOUT)
        except BaseException:
            process.kill()  # Chỉ PID Popen vừa tạo; không tìm/kill theo tên tiến trình.
            output, _ = process.communicate(timeout=5)
            raise
        finally:
            record.update(stopped=process.poll() is not None, exit_code=process.poll())
            text = output.decode("utf-8", errors="replace").replace("\r\n", "\n") if "output" in locals() else ""
            print(text, end="" if text.endswith("\n") else "\n")
            with (session / "MinhChung" / "dieu_khien_log.txt").open("a", encoding="utf-8") as log:
                log.write(f"\n[{datetime.now().isoformat()}] {filename or 'python -c'} {args}\n")
                log.write(text + f"\nMã thoát: {process.poll()}\n")
        require(process.returncode == 0, "Lệnh chưa đạt; xem dieu_khien_log.txt.")
        return subprocess.CompletedProcess(command, process.returncode, text, "")


class Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, value):
        for stream in self.streams:
            stream.write(value)
            stream.flush()
        return len(value)

    def flush(self):
        for stream in self.streams:
            stream.flush()


class Presentation:
    def __init__(self, directory, mode, args, screen, detail):
        self.directory, self.mode, self.args = directory, mode, args
        self.screen, self.detail = screen, detail
        self.demo, self.monitor = Demo(), None
        self.results = []
        self.number = 0
        self.total = 6 if mode == "TV3" else 7
        self.latest = None

    @contextlib.contextmanager
    def stage(self, title):
        if self.number and not self.args.pause:
            time.sleep(self.args.delay)
        self.number += 1
        item = {"stage": self.number, "title": title, "passed": False}
        self.results.append(item)
        self.screen.stage(self.mode, self.number, self.total, title)
        try:
            with contextlib.redirect_stdout(self.detail), contextlib.redirect_stderr(self.detail):
                yield
                self.latest = self.snapshot("ket_thuc_giai_doan", display=False)
            self.screen.table(self.latest, self.mode)
            self.screen.status(True)
            if self.args.pause:
                self.safe_pause()
        except BaseException as exc:
            item["error"] = str(exc) or type(exc).__name__
            self.screen.status(False, short_error(exc))
            raise
        else:
            item["passed"] = True

    def checkpoint(self):
        value = self.monitor.collect(self.demo.session)
        require(not value["errors"], "Không đủ dữ liệu để xác nhận điểm dừng.")
        for store in value["stores"]:
            key = ("CH01", "POS01") if store["db"].endswith("cuahang01.db") else ("CH02", "POS01")
            child = self.demo.agents[key]
            if child.process is not None:
                require(child.running(), "Sender dừng bất thường trước điểm tạm dừng.")
            if child.running():
                state = store["states"]
                require(state["PENDING"] == 0 and (state["SENT"] == 0 or self.demo.links[key]),
                        "Điểm dừng chưa ổn định: sender còn giao dịch có thể đổi trạng thái.")
        rows = {s["db"]: self.monitor.read_rows(self.demo.session / s["db"], self.demo.session, True)
                for s in value["stores"]}
        rows["DuLieu/truso.db"] = self.monitor.read_rows(self.demo.session / "DuLieu/truso.db", self.demo.session)
        return {"rows": rows, "receiver_running": self.demo.receiver.running(),
                "senders": {"/".join(key): {"running": child.running(), "offline": self.demo.links[key]}
                            for key, child in self.demo.agents.items()}}

    def safe_pause(self):
        before = self.checkpoint()
        save(self.demo.session / "MinhChung" / f"{self.number:02d}_tam_dung_truoc.json", before)
        started = time.monotonic()
        self.screen.say(f"CHỜ THUYẾT TRÌNH [{self.mode} {self.number}/{self.total}]", "wait")
        self.screen.say("Dữ liệu đã ổn định. Nhấn Enter để tiếp tục; Ctrl+C để dừng an toàn.", "muted")
        input()
        after = self.checkpoint()
        save(self.demo.session / "MinhChung" / f"{self.number:02d}_tam_dung_sau.json",
             {"seconds": round(time.monotonic() - started, 3), "unchanged": before == after, "checkpoint": after})
        require(before == after, "Dữ liệu hoặc tiến trình thay đổi ngoài dự kiến khi tạm dừng.")

    def start(self):
        existing.SESSION_ROOT = self.directory / "PhienThu"
        existing.SESSION_ROOT.mkdir()
        self.demo.new_session()
        session = self.demo.require_session()
        spec = importlib.util.spec_from_file_location("monitor_one_click", session / "Script" / "giam_sat.py")
        self.monitor = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.monitor)
        save(self.directory / "ma_nguon_phien.json", {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted((session / "Script").glob("*.py"))})
        self.demo.execute("tru-so-bat")
        value = self.snapshot("ban_dau")
        require(value["store_total"] == value["hq_total"] == 0 and not value["errors"],
                "Phiên mới phải có 0 giao dịch thực tế.")

    def snapshot(self, label, display=True):
        value = self.monitor.collect(self.demo.session)
        print(json.dumps(value, ensure_ascii=False))
        if label:
            # Lưu cả payload để người xem có thể kiểm tra lại từng trường.
            rows = {s["db"]: self.monitor.read_rows(self.demo.session / s["db"], self.demo.session, True)
                    for s in value["stores"]}
            rows["DuLieu/truso.db"] = self.monitor.read_rows(
                self.demo.session / "DuLieu/truso.db", self.demo.session)
            save(self.demo.session / "MinhChung" / (f"{self.number:02d}_{label}.json"),
                 {"summary": value, "rows": rows})
        return value

    def wait(self, predicate):
        deadline = time.monotonic() + self.args.timeout
        while time.monotonic() < deadline:
            require(self.demo.receiver.running(), "Receiver của phiên đã dừng.")
            for child in self.demo.agents.values():
                if child.process is not None:
                    require(child.running(), "Auto sync của phiên đã dừng bất thường.")
            value = self.snapshot(None, display=False)
            require(not value["errors"], "Không đọc được dữ liệu thực tế: " + str(value["errors"]))
            if predicate(value):
                return value
            time.sleep(0.5)
        self.snapshot("het_thoi_gian")
        raise TimeoutError(f"Không đạt trạng thái mong đợi sau {self.args.timeout:g} giây.")

    @staticmethod
    def complete(value, count, stores):
        return (value["sync_complete"] and value["store_total"] == value["hq_total"] == count
                and len(value["stores"]) == stores and value["states"]["ACKED"] == count)

    def sync(self, count):
        self.demo.execute("dong-bo-bat")
        self.wait(lambda value: self.complete(value, count, 1))
        self.demo.execute("dong-bo-tat")
        value = self.snapshot(f"dong_bo_{count}")
        require(self.complete(value, count, 1), "Đối chiếu sau dừng sender chưa khớp.")

    def tv3(self):
        with self.stage("KHỞI TẠO PHIÊN VÀ TRỤ SỞ"):
            self.start()
        with self.stage("TẠO 5 GIAO DỊCH CH01"):
            self.demo.execute("tao-5")
            value = self.snapshot("ch01_pending")
            require(value["states"] == {"PENDING": 5, "SENT": 0, "ACKED": 0}
                    and value["hq_total"] == 0, "Chưa tạo đúng 5 PENDING.")
        with self.stage("CH01 TỰ ĐỒNG BỘ 5/5"):
            self.demo.execute("dong-bo-bat")
            self.wait(lambda value: self.complete(value, 5, 1))
            require(self.complete(self.snapshot("ch01_acked"), 5, 1), "CH01 chưa khớp.")
        with self.stage("KHỞI TẠO CH02 — NGẮT HTTP MÔ PHỎNG"):
            self.demo.execute("cua-hang CH02 POS01")
            self.demo.execute("ngat-cua-hang")
            value = self.snapshot("ch02_rieng_offline")
            require(len(value["stores"]) == 2 and value["stores"][1]["total"] == 0
                    and self.demo.links[("CH02", "POS01")] and self.demo.receiver.running()
                    and self.demo.agents[("CH01", "POS01")].running(), "Chưa cô lập đúng CH02.")
        with self.stage("CH02 GIỮ 5 GIAO DỊCH CHƯA ACK"):
            self.demo.execute("tao-5")
            before = self.snapshot("ch02_pending")
            require(before["stores"][1]["states"] == {"PENDING": 5, "SENT": 0, "ACKED": 0},
                    "CH02 chưa có 5 PENDING.")
            self.demo.execute("dong-bo-bat")
            self.wait(lambda value: value["stores"][1]["states"] == {"PENDING": 0, "SENT": 5, "ACKED": 0})
            value = self.snapshot("ch02_mat_http_5_sent")
            require(value["hq_total"] == 5 and len(value["missing_hq"]) == 5
                    and value["stores"][0]["states"]["ACKED"] == 5, "Dữ liệu offline sai mong đợi.")
        with self.stage("NỐI LẠI CH02 — AUTO SYNC TỰ GỬI"):
            self.screen.say("Đang chờ chu kỳ auto sync 10 giây; không gọi gửi thủ công.", "wait")
            pid = self.demo.agent.process.pid
            log = self.demo.session / "MinhChung" / self.demo.agent.logfile
            first = log.read_text(encoding="utf-8").count("Kiem tra giao dich...")
            self.demo.execute("noi-cua-hang")
            self.wait(lambda value: self.complete(value, 10, 2))
            require(self.demo.agent.process.pid == pid, "Auto sync bị thay PID ngoài dự kiến.")
            require(log.read_text(encoding="utf-8").count("Kiem tra giao dich...") > first,
                    "Không quan sát được chu kỳ auto sync sau nối lại.")
            save(self.demo.session / "MinhChung/06_auto_sync_tu_gui_lai.json",
                 {"pid_truoc_va_sau": pid, "so_chu_ky_truoc": first,
                  "so_chu_ky_sau": log.read_text(encoding="utf-8").count("Kiem tra giao dich..."),
                  "goi_gui_thu_cong": False})
            self.demo.close()
            value = self.snapshot("tv3_cuoi_5_5_hq10")
            require(self.complete(value, 10, 2)
                    and all(s["states"] == {"PENDING": 0, "SENT": 0, "ACKED": 5}
                            for s in value["stores"]), "Kết quả cuối TV3 chưa khớp 5/5/10.")

    def integrated(self):
        with self.stage("KHỞI TẠO PHIÊN TÍCH HỢP"):
            self.start()
        with self.stage("ĐỒNG BỘ 5 GIAO DỊCH ĐẦU"):
            self.demo.execute("tao-5")
            self.sync(5)
        with self.stage("TV2 SAO LƯU TRỤ SỞ TẠI MỐC 5"):
            self.demo.execute("sao-luu-tru-so")
            backups = list((self.demo.session / "DuLieu/SaoLuuTruSo").glob("*.db"))
            require(len(backups) == 1, "Phải có đúng một bản sao tại mốc 5.")
            self.backup = backups[0]
            backup_rows = self.monitor.read_rows(self.backup, self.demo.session)
            hq_rows = self.monitor.read_rows(self.demo.session / "DuLieu/truso.db", self.demo.session)
            require(len(backup_rows) == 5 and backup_rows == hq_rows, "Bản sao mốc 5 chưa khớp HQ.")
            self.backup_hash = hashlib.sha256(self.backup.read_bytes()).hexdigest()
            save(self.demo.session / "MinhChung/03_ban_sao_5.json",
                 {"file": str(self.backup), "sha256": self.backup_hash, "rows": backup_rows})
            print("Bản sao TV2:", self.backup.name, "| Đã đọc và khớp 5 giao dịch.")
        with self.stage("ĐỒNG BỘ LÊN 10 GIAO DỊCH"):
            self.demo.execute("tao-5")
            self.sync(10)
            before_restore = self.monitor.read_rows(self.demo.session / "DuLieu/truso.db", self.demo.session)
        with self.stage("PHỤC HỒI BẢN SAO — TRỤ SỞ VỀ 5"):
            self.demo.restore_hq(self.backup.name)
            require(not self.demo.receiver.running() and not any(c.running() for c in self.demo.agents.values()),
                    "Chưa dừng hết sender/receiver trước phục hồi.")
            require(hashlib.sha256(self.backup.read_bytes()).hexdigest() == self.backup_hash,
                    "Bản sao mốc 5 bị thay đổi.")
            value = self.snapshot("sau_phuc_hoi_hq5")
            require(value["hq_total"] == 5 and value["states"]["ACKED"] == 10,
                    "Sau phục hồi phải có kho 10 ACKED, HQ5.")
        with self.stage("ĐỐI CHIẾU — PHÁT HIỆN ĐÚNG 5 MÃ THIẾU"):
            result = self.demo.run(code="from Script.doi_chieu import tinh_doi_chieu; import json; "
                                       "print(json.dumps(tinh_doi_chieu(), ensure_ascii=False))")
            comparison = json.loads(result.stdout)
            expected = sorted(set(r["ma_gd"] for r in before_restore) - set(r["ma_gd"] for r in backup_rows))
            require(sorted(comparison["acked_thieu"]) == expected and len(expected) == 5
                    and not comparison["khop"] and not comparison["ma_trung"]
                    and not comparison["lech_noi_dung"] and not comparison["chua_ve"],
                    "TV2 chưa phát hiện đúng 5 giao dịch thiếu.")
            save(self.demo.session / "MinhChung/06_tv2_thieu_dung_5.json", comparison)
            print("ĐÃ PHÁT HIỆN 5 GIAO DỊCH THIẾU (tình huống mong đợi):")
            for transaction in expected:
                print("  ", transaction)
        with self.stage("TV2 GỬI BÙ — ĐỐI CHIẾU 10/10 ACKED"):
            self.demo.execute("tru-so-bat")
            require(not self.demo.agent.running(), "Auto sync phải tắt khi TV2 gửi bù.")
            self.demo.execute("gui-bu")
            self.demo.close()
            value = self.snapshot("tich_hop_cuoi_10_10")
            require(self.complete(value, 10, 1), "Chưa đạt 10/10 và 10 ACKED.")
            require(before_restore == self.monitor.read_rows(
                self.demo.session / "DuLieu/truso.db", self.demo.session), "Payload sau gửi bù bị thay đổi.")
            require(hashlib.sha256(self.backup.read_bytes()).hexdigest() == self.backup_hash,
                    "Bản sao mốc 5 không còn nguyên.")

    def run(self):
        error = None
        try:
            if self.mode == "TV3":
                self.tv3()
            else:
                self.integrated()
        except BaseException as exc:
            error = str(exc) or type(exc).__name__
            traceback.print_exc(file=self.detail)
        finally:
            cleanup = {"stage": "Dừng tiến trình", "title": "Dừng mọi tiến trình của phiên", "passed": False}
            self.results.append(cleanup)
            try:
                self.demo.close()
                mine = [p for p in HISTORY if p["session"].startswith(str(self.directory))]
                require(all(p["stopped"] for p in mine), "Còn tiến trình của phiên chưa dừng.")
                require(all(not p.get("forced", False) and p.get("exit_code") == 0 for p in mine),
                        "Có tiến trình lỗi hoặc phải dừng cưỡng bức; xem tien_trinh.json.")
                cleanup["passed"] = True
            except BaseException as exc:
                cleanup["error"] = str(exc)
                error = error or str(exc)
                traceback.print_exc(file=self.detail)
                self.screen.status(False, short_error(exc))
            passed = error is None and all(item["passed"] for item in self.results)
            result = {"mode": self.mode, "passed": passed, "error": error,
                      "session": str(self.demo.session), "stages": self.results, "final_state": self.latest}
            save(self.directory / "ket_qua.json", result)
            save(self.directory / "tien_trinh.json", [p for p in HISTORY if p["session"].startswith(str(self.directory))])
            self.screen.say()
            self.screen.say("TỔNG KẾT — " + MODE_NAMES[self.mode], "title")
            for item in self.results:
                self.screen.say(f"{'ĐẠT' if item['passed'] else 'CHƯA ĐẠT':9} | {item['title']}",
                                "pass" if item["passed"] else "fail")
            self.screen.status(passed)
        return result


def main():
    global STEP_TIMEOUT
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    if len(sys.argv) == 5 and sys.argv[1] == "--worker":
        worker(*sys.argv[2:])
        return 0
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("tv3", "tich-hop", "all"), default="all")
    parser.add_argument("--pause", action="store_true", help="Nhấn Enter giữa các giai đoạn")
    parser.add_argument("--no-color", action="store_true", help="Tắt màu cho Terminal không hỗ trợ")
    parser.add_argument("--delay", type=float, default=2, help="Khoảng nghỉ quan sát (0–30 giây)")
    parser.add_argument("--timeout", type=float, default=45, help="Timeout mỗi lệnh/lượt chờ (15–120 giây)")
    args = parser.parse_args()
    if not 0 <= args.delay <= 30 or not 15 <= args.timeout <= 120:
        parser.error("--delay cần 0–30; --timeout cần 15–120.")
    STEP_TIMEOUT = args.timeout
    # Không nhận đường dẫn runtime tùy ý, tránh trỏ nhầm tới phiên cũ.
    RUNTIME.mkdir(exist_ok=True)
    directory = RUNTIME / (datetime.now().strftime("Demo1Click_%Y%m%d_%H%M%S_%f_") + uuid.uuid4().hex[:8])
    directory.mkdir(exist_ok=False)
    results, error = [], None
    with (directory / "terminal.txt").open("x", encoding="utf-8") as terminal, \
            (directory / "chi_tiet.txt").open("x", encoding="utf-8") as detail:
        screen = Screen(ScreenLog(sys.stdout, terminal), args.no_color)
        screen.banner(directory.name, args.pause)
        screen.say(f"Kiểm tra môi trường và cổng 18000 | Timeout mỗi lượt: {args.timeout:g} giây", "wait")
        with contextlib.redirect_stdout(detail), contextlib.redirect_stderr(detail):
            try:
                preflight(directory)
                screen.status(True, "Cổng an toàn; mỗi demo dùng một phiên dữ liệu mới.")
                modes = ["TV3", "TV2-TV3"] if args.mode == "all" else ["TV3" if args.mode == "tv3" else "TV2-TV3"]
                for mode in modes:
                    mode_dir = directory / mode
                    mode_dir.mkdir()
                    result = Presentation(mode_dir, mode, args, screen, detail).run()
                    results.append(result)
                    if not result["passed"]:
                        break
            except BaseException as exc:
                error = str(exc) or type(exc).__name__
                screen.status(False, short_error(exc))
                traceback.print_exc()
            passed = bool(results) and error is None and all(r["passed"] for r in results)
            save(directory / "tong_ket.json", {"passed": passed, "error": error, "results": results})
            screen.summary(results, passed, directory.name)
            return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
