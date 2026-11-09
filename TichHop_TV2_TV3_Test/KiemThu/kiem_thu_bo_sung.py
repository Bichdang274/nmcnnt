
"""Kiểm thử bổ sung có kiểm soát; chỉ ghi vào runtime-root MỚI được chỉ định."""
import argparse
import contextlib
import ctypes
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import socket
import sqlite3
import subprocess
import sys
import time
import traceback
from urllib.error import HTTPError
from urllib.request import Request, urlopen

SOURCE = Path(__file__).resolve().parents[1]
TZ = timezone(timedelta(hours=7))
PORT = 18000
SCRIPT_NAMES = (
    "store_agent.py", "hq_receiver.py", "auto_sync.py", "kiem_tra_trung.py",
    "doi_chieu.py", "sao_luu_tru_so.py", "sao_luu.py",
    "kiem_tra_phuc_hoi.py", "xuat_giao_dich.py")


def stamp():
    return datetime.now(TZ).isoformat(timespec="seconds")


def free_port():
    with socket.socket() as sock:
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        sock.bind(("127.0.0.1", PORT))


def exclusive_copy(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("xb") as handle:
        handle.write(source.read_bytes())


def copy_runtime(target, omit=None):
    target.mkdir(exist_ok=False)
    (target / "Script").mkdir()
    for name in SCRIPT_NAMES:
        if name != omit:
            exclusive_copy(SOURCE / "Script" / name, target / "Script" / name)
    for name in ("demo_tich_hop.py", "chay_demo.ps1", "MANIFEST.json"):
        exclusive_copy(SOURCE / name, target / name)


def load_controller(root):
    spec = importlib.util.spec_from_file_location("demo_thu_bo_sung", root / "demo_tich_hop.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_db(session, name, local=False):
    path = (session / "DuLieu" / name).resolve()
    if not path.is_relative_to(session.resolve()) or not path.is_file():
        raise RuntimeError("CSDL ngoài phiên hoặc chưa tồn tại")
    connection = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        rows = [dict(r) for r in connection.execute("SELECT * FROM giao_dich ORDER BY ma_gd")]
        integrity = [tuple(r) for r in connection.execute("PRAGMA integrity_check")]
        assert integrity == [("ok",)], integrity
        states = {}
        if local:
            for row in rows:
                states[row["trang_thai"]] = states.get(row["trang_thai"], 0) + 1
        return {"rows": rows, "count": len(rows), "states": states,
                "duplicate_ids": len(rows) - len({r["ma_gd"] for r in rows}),
                "integrity_check": "ok"}
    finally:
        connection.close()


def pair(demo):
    local = read_db(demo.session, "cuahang01.db", True)
    hq = read_db(demo.session, "truso.db")
    fields = ("ma_gd", "ma_cua_hang", "ma_may", "thoi_gian", "so_tien")
    same = [tuple(r[k] for k in fields) for r in local["rows"]] == [
        tuple(r[k] for k in fields) for r in hq["rows"]]
    return {"store": local, "hq": hq, "five_fields_equal": same}


def command(demo, value):
    print("\n[" + stamp() + "] tich-hop> " + value, flush=True)
    return demo.execute(value)


def one_transaction(demo):
    demo.run(code="from Script.store_agent import tao_giao_dich; tao_giao_dich(50000)")


def expect_error(kind, action, contains=None):
    try:
        action()
    except kind as exc:
        if contains and contains not in str(exc):
            raise AssertionError("Thông báo lỗi không đúng: " + str(exc)) from exc
        print("LỖI ĐƯỢC CHỜ ĐỢI: " + type(exc).__name__ + ": " + str(exc), flush=True)
        return str(exc)
    raise AssertionError("Thao tác lỗi đã không báo lỗi")


def process_running(pid):
    if os.name == "nt":
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.restype = ctypes.c_void_p
        kernel.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
        kernel.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
        kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        handle = kernel.OpenProcess(0x100000, False, pid)
        if not handle:
            return False
        try:
            return kernel.WaitForSingleObject(handle, 0) == 258
        finally:
            kernel.CloseHandle(handle)
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False


FAULT_RECEIVER = r'''
"""Chỉ dùng trong phiên thử: ngắt đúng ACK đầu tiên sau commit."""
import contextlib
import json
import os
from pathlib import Path
import socket
import sqlite3
from http.server import HTTPServer
import hq_receiver as real

MARKER = Path(__file__).resolve().parent.parent / "ack_da_ngat.json"

class MatACK(real.BoNhan):
    def tra_json(self, status, content):
        if status == 200 and content.get("ack") is True and not MARKER.exists():
            with sqlite3.connect(real.FILE_DB.as_uri() + "?mode=ro", uri=True) as conn:
                conn.row_factory = sqlite3.Row
                row = conn.execute("SELECT * FROM giao_dich WHERE ma_gd = ?",
                                   (content["ma_gd"],)).fetchone()
                assert row is not None, "Không được ngắt ACK trước commit"
                saved = dict(row)
            with MARKER.open("x", encoding="utf-8") as handle:
                json.dump({"injection": "drop_first_ack_after_commit",
                           "reply_not_delivered": content, "committed_row": saved},
                          handle, ensure_ascii=False, indent=2)
            print("KT-BS2: ĐÃ COMMIT, CHỦ ĐỘNG NGẮT ACK ĐẦU TIÊN", flush=True)
            self.close_connection = True
            with contextlib.suppress(OSError):
                self.connection.shutdown(socket.SHUT_RDWR)
            self.connection.close()
            return
        return super().tra_json(status, content)

if __name__ == "__main__":
    real.khoi_tao()
    server = HTTPServer(("127.0.0.1", int(os.environ.get("TV23_HQ_PORT", "18000"))), MatACK)
    try:
        server.serve_forever()
    finally:
        server.server_close()
'''


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-root", type=Path, required=True,
                        help="Thư mục mới hoàn toàn, ngoài mã nguồn; không dùng phiên cũ")
    args = parser.parse_args()
    runtime = args.runtime_root.resolve()
    if runtime.exists() or runtime == SOURCE or runtime.is_relative_to(SOURCE):
        raise SystemExit("Từ chối: runtime-root phải là đường dẫn MỚI ngoài thư mục mã nguồn")
    free_port()  # Nếu cổng không sẵn sàng: dừng trước khi tạo dữ liệu.
    runtime.parent.mkdir(parents=True, exist_ok=True)
    copy_runtime(runtime)
    evidence = runtime / "MinhChung"
    evidence.mkdir()
    module = load_controller(runtime)
    demos = []
    results = []
    active = "KHỞI TẠO"
    error = None
    started = stamp()

    class Tee:
        def __init__(self, *streams):
            self.streams = streams
        def write(self, text):
            for stream in self.streams:
                stream.write(text)
                stream.flush()
            return len(text)
        def flush(self):
            for stream in self.streams:
                stream.flush()

    def new_demo():
        demo = module.Demo()
        demos.append(demo)
        command(demo, "phien-moi")
        return demo

    def save(name, value):
        with (evidence / name).open("x", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)

    def passed(case, detail, actual=None):
        record = {"case": case, "status": "PASS", "time": stamp(), "detail": detail}
        if actual is not None:
            record["actual"] = actual
        results.append(record)
        print("\n" + case + " ĐẠT: " + detail, flush=True)

    with (evidence / "terminal_bo_sung.txt").open("x", encoding="utf-8") as trace:
        with contextlib.redirect_stdout(Tee(sys.stdout, trace)):
            try:
                active = "KT-BS1"
                demo = new_demo()
                command(demo, "tru-so-bat")
                one_transaction(demo)
                command(demo, "gui-mot-luot")
                before = pair(demo)
                assert before["store"]["states"] == {"ACKED": 1}
                assert before["hq"]["count"] == 1 and before["five_fields_equal"]
                payload = dict(before["hq"]["rows"][0])
                payload["so_tien"] += 1
                request = Request(module.ENV["TV23_HQ_URL"],
                                  data=json.dumps(payload).encode("utf-8"),
                                  headers={"Content-Type": "application/json"}, method="POST")
                try:
                    with urlopen(request, timeout=5) as reply:
                        raise AssertionError("Phải nhận HTTP 409, thực tế " + str(reply.status))
                except HTTPError as exc:
                    assert exc.code == 409, exc.code
                    response = json.loads(exc.read())
                after = pair(demo)
                assert after == before, "Giao dịch đã lưu bị thay đổi sau xung đột"
                assert after["hq"]["duplicate_ids"] == 0
                actual = {"http_status": 409, "response": response,
                          "conflicting_request": payload, "before": before, "after": after}
                save("KT_BS1_HTTP409.json", actual)
                demo.close()
                free_port()
                passed(active, "HTTP 409; HQ giữ nguyên một bản ghi, không ghi đè hoặc ghi trùng.", actual)

                active = "KT-BS2"
                demo = new_demo()
                one_transaction(demo)
                fault = demo.session / "Script" / "receiver_mat_ack.py"
                with fault.open("x", encoding="utf-8", newline="\n") as handle:
                    handle.write(FAULT_RECEIVER)
                demo.receiver = module.Child("Receiver thử mất ACK", fault.name,
                                             "receiver_mat_ack_log.txt")
                free_port()
                command(demo, "tru-so-bat")
                deadline = time.monotonic() + 5
                while not module.port_busy(PORT) and time.monotonic() < deadline:
                    assert demo.receiver.running()
                    time.sleep(0.1)
                assert module.port_busy(PORT)
                command(demo, "gui-mot-luot")
                lost = pair(demo)
                assert lost["hq"]["count"] == 1 and lost["store"]["count"] == 1
                assert lost["store"]["states"] == {"SENT": 1}, lost
                assert lost["five_fields_equal"]
                marker = json.loads((demo.session / "ack_da_ngat.json").read_text(encoding="utf-8"))
                assert marker["committed_row"] == lost["hq"]["rows"][0]
                assert marker["reply_not_delivered"]["ket_qua"] == "DA_LUU"
                command(demo, "gui-mot-luot")
                recovered = pair(demo)
                assert recovered["store"]["states"] == {"ACKED": 1}
                assert recovered["hq"]["count"] == 1 and recovered["hq"]["duplicate_ids"] == 0
                assert recovered["hq"]["rows"] == lost["hq"]["rows"]
                fault_log = (demo.session / "MinhChung" / "receiver_mat_ack_log.txt").read_text(encoding="utf-8")
                assert "DA_TON_TAI" in fault_log
                actual = {"fault": marker, "after_lost_ack": lost, "after_retry": recovered,
                          "retry_result_observed": "DA_TON_TAI", "valid_ack_received_before_acked": True}
                save("KT_BS2_MAT_ACK.json", actual)
                demo.close()
                free_port()
                passed(active, "HQ commit nhưng ACK bị ngắt; kho giữ SENT; gửi lại nhận DA_TON_TAI và ACKED, HQ vẫn 1.", actual)

                active = "HR-01"
                demo = new_demo()
                with socket.socket() as blocker:
                    if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
                        blocker.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
                    blocker.bind(("127.0.0.1", PORT))
                    blocker.listen(2)
                    message = expect_error(RuntimeError, lambda: command(demo, "tru-so-bat"), "Cổng 18000")
                    assert blocker.fileno() >= 0 and demo.receiver.process is None
                free_port()
                passed(active, "Từ chối cổng do socket thử giữ; không tạo/đóng tiến trình ngoài phiên.", {"error": message})

                active = "HR-02"
                demo.agent.filename = "khong_ton_tai.py"
                message = expect_error(FileNotFoundError, lambda: command(demo, "dong-bo-bat"), "Thiếu script")
                assert demo.agent.process is None
                demo.agent.filename = "auto_sync.py"
                exit_error = expect_error(RuntimeError,
                    lambda: demo.run(code="raise SystemExit(7)"), "mã thoát 7")
                stub = demo.session / "Script" / "loi_tien_trinh.py"
                with stub.open("x", encoding="utf-8") as handle:
                    handle.write("raise SystemExit(9)\n")
                child = module.Child("Auto sync thử thất bại", stub.name, "child_fail_log.txt")
                start_error = expect_error(RuntimeError, lambda: child.start(demo.session))
                assert not child.running()
                demo.close()
                passed(active, "Thiếu script và script con exit 7/9 đều báo lỗi, không báo bước đã đạt.",
                       {"missing": message, "exit7": exit_error, "startup_failure": start_error})

                active = "HR-03"
                demo = new_demo()
                command(demo, "tru-so-bat")
                one_transaction(demo)
                command(demo, "dong-bo-bat")
                deadline = time.monotonic() + 15
                while time.monotonic() < deadline:
                    state = pair(demo)
                    if state["store"]["states"] == {"ACKED": 1}:
                        break
                    time.sleep(0.1)
                assert state["store"]["states"] == {"ACKED": 1} and state["five_fields_equal"]
                receiver_pid = demo.receiver.process.pid
                agent_pid = demo.agent.process.pid
                real_stop = demo.agent.stop
                def stop_with_error():
                    real_stop()
                    raise OSError("Mô phỏng lỗi dừng sender sau khi sender đã dừng")
                demo.agent.stop = stop_with_error
                try:
                    expect_error(OSError, demo.close, "Mô phỏng")
                    assert not demo.receiver.running() and not demo.agent.running()
                    assert not process_running(receiver_pid) and not process_running(agent_pid)
                finally:
                    demo.agent.stop = real_stop
                    demo.close()
                free_port()
                passed(active, "Hồi quy auto sync 1 ACKED; close vẫn dừng receiver khi sender.stop báo lỗi.",
                       {"state": state, "receiver_stopped": True, "sender_stopped": True})

                active = "HR-04"
                cli_results = []
                for mode, commands in (
                    ("thoat", "phien-moi\ntru-so-bat\ndong-bo-bat\nthoat\n"),
                    ("EOF", "phien-moi\ntru-so-bat\ndong-bo-bat\n")):
                    cli = subprocess.run([sys.executable, "-B", "-u", str(runtime / "demo_tich_hop.py")],
                        input=commands, capture_output=True, text=True, encoding="utf-8",
                        env=dict(module.ENV, PYTHONIOENCODING="cp1258"), cwd=runtime, timeout=25)
                    print("CLI " + mode + "\n" + cli.stdout + cli.stderr, flush=True)
                    assert cli.returncode == 0, cli
                    assert "Giai đoạn 1 và 2 đã ĐẠT" in cli.stdout
                    assert "Phiên demo mới chưa được tạo hoặc kiểm thử" in cli.stdout
                    assert "CHUA CO KET QUA KIEM THU" not in cli.stdout
                    owned = [int(p) for p in re.findall(r"PID (\d+)", cli.stdout)]
                    assert len(owned) == 2 and all(not process_running(p) for p in owned)
                    free_port()
                    cli_results.append({"mode": mode, "returncode": cli.returncode,
                                        "owned_pids": owned, "all_children_stopped": True})
                launcher = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                    "-File", str(runtime / "chay_demo.ps1")], input="thoat\n",
                    capture_output=True, text=True, encoding="utf-8", env=dict(module.ENV, PYTHONIOENCODING="cp1258"), cwd=runtime, timeout=25)
                print("LAUNCHER\n" + launcher.stdout + launcher.stderr, flush=True)
                assert launcher.returncode == 0 and "BẢN TÍCH HỢP THỬ NGHIỆM" in launcher.stdout
                free_port()
                passed(active, "CLI thoat và EOF dọn cả hai tiến trình; launcher PowerShell thoát 0.",
                       {"cli": cli_results, "launcher_exit": launcher.returncode})

                active = "HR-05"
                missing_root = runtime / "KhoiDongThieuFile"
                copy_runtime(missing_root, omit="auto_sync.py")
                missing = subprocess.run([sys.executable, "-B", "-u", str(missing_root / "demo_tich_hop.py")],
                    input="thoat\n", capture_output=True, text=True, encoding="utf-8",
                    env=module.ENV, cwd=missing_root, timeout=10)
                print("KHỞI ĐỘNG THIẾU FILE\n" + missing.stdout + missing.stderr, flush=True)
                assert missing.returncode != 0
                assert "Thiếu file bắt buộc" in missing.stderr and "auto_sync.py" in missing.stderr
                assert not (missing_root / "PhienThu").exists()
                free_port()
                passed(active, "Khởi động thiếu auto_sync.py dừng trước tạo phiên hoặc dịch vụ.",
                       {"exit": missing.returncode, "error": missing.stderr.strip()})
            except BaseException as exc:
                error = type(exc).__name__ + ": " + str(exc)
                results.append({"case": active, "status": "FAIL", "time": stamp(), "detail": error})
                traceback.print_exc(file=trace)
                print("CHƯA ĐẠT: " + error, flush=True)
            finally:
                for demo in reversed(demos):
                    try:
                        demo.close()
                    except BaseException as exc:
                        error = (error + "; " if error else "") + "Dọn tiến trình: " + str(exc)
                try:
                    free_port()
                except OSError as exc:
                    error = (error + "; " if error else "") + "Cổng chưa giải phóng: " + str(exc)
                result = {"status": "PASS" if error is None else "FAIL",
                          "started": started, "finished": stamp(), "cases": results,
                          "error": error, "runtime_root": str(runtime),
                          "endpoint": "http://127.0.0.1:18000/giao-dich",
                          "schema": "TV3 temporary; TV2 confirmation required",
                          "old_sessions_used": False,
                          "source_sha256": {p.relative_to(SOURCE).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in [SOURCE / "demo_tich_hop.py", SOURCE / "chay_demo.ps1"]
                              + [SOURCE / "Script" / name for name in SCRIPT_NAMES]}}
                save("KET_QUA_BO_SUNG.json", result)
                print("RESULT=" + json.dumps({"status": result["status"], "cases": len(results),
                    "error": error, "runtime_root": str(runtime)}, ensure_ascii=True), flush=True)
    return 0 if error is None else 1


if __name__ == "__main__":
    raise SystemExit(main())
