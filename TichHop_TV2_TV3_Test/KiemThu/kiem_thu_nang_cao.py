"""Kiểm thử nâng cao TV3 trên runtime MỚI; không chạm phiên minh chứng cũ."""
import argparse
import contextlib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import time
import traceback

SOURCE = Path(__file__).resolve().parents[1]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


FAKE = r"""
import json, os
from http.server import HTTPServer
import hq_receiver as real

class Fake(real.BoNhan):
    def do_POST(self):
        payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        mode = os.environ["TV3_FAKE_MODE"]
        replies = {
            "wrong_id": {"ack": True, "ma_gd": payload["ma_gd"] + "-WRONG"},
            "array": [{"ack": True, "ma_gd": payload["ma_gd"]}],
            "ack_false": {"ack": False, "ma_gd": payload["ma_gd"]},
            "ack_number": {"ack": 1, "ma_gd": payload["ma_gd"]},
            "ack_string": {"ack": "true", "ma_gd": payload["ma_gd"]},
            "missing_ack": {"ma_gd": payload["ma_gd"]}
        }
        body = b"{invalid-json" if mode == "invalid_json" else json.dumps(replies[mode]).encode()
        print("FAKE_REPLY", mode, body.decode(), flush=True)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

real.khoi_tao()  # HQ rỗng; receiver giả không ghi giao dịch.
server = HTTPServer(("127.0.0.1", int(os.environ["TV23_HQ_PORT"])), Fake)
try:
    server.serve_forever()
finally:
    server.server_close()
"""


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--only-guards", action="store_true", help="Chỉ kiểm tra giới hạn công cụ cũ, không chạy lại các ca đã đạt")
    parser.add_argument("--only-port-guard", action="store_true", help="Chỉ thử từ chối nối lại tới cổng ngoài phiên")
    args = parser.parse_args()
    runtime = args.runtime_root.resolve()
    if runtime.exists() or runtime.is_relative_to(SOURCE):
        raise SystemExit("Runtime cần mới hoàn toàn và nằm ngoài mã nguồn")
    helper = load(SOURCE / "KiemThu" / "kiem_thu_bo_sung.py", "helpers_tv3")
    helper.free_port()
    runtime.parent.mkdir(parents=True, exist_ok=True)
    helper.copy_runtime(runtime)
    module = helper.load_controller(runtime)
    monitor = load(runtime / "Script" / "giam_sat.py", "monitor_tv3")
    evidence = runtime / "MinhChung"
    evidence.mkdir()
    results, demos = [], []
    error, active = None, "SETUP"
    started = helper.stamp()

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

    def command(demo, text):
        return helper.command(demo, text)

    def new():
        demo = module.Demo()
        demos.append(demo)
        command(demo, "phien-moi")
        return demo

    def create(demo, count):
        demo.run(code="from Script.store_agent import tao_giao_dich\n"
                      f"for i in range({count}): tao_giao_dich(10000+i)")

    def snapshot(demo):
        files = list((demo.session / "DuLieu").rglob("*.db"))
        before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
        value = monitor.collect(demo.session)
        assert {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in files} == before
        assert set(files) == set((demo.session / "DuLieu").rglob("*.db"))
        monitor.display(value)
        return value

    def wait_for(check, seconds=40):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            value = check()
            if value:
                return value
            time.sleep(0.15)
        raise AssertionError("Hết thời gian chờ điều kiện thực tế")

    def states(demo, db="cuahang01.db"):
        return helper.read_db(demo.session, db, True)["states"]

    def pass_case(name, actual):
        results.append({"case": name, "status": "PASS", "time": helper.stamp(), "actual": actual})
        print("\n" + name + " PASS", flush=True)
        with (evidence / (name + ".json")).open("x", encoding="utf-8") as f:
            json.dump(results[-1], f, ensure_ascii=False, indent=2)

    with (evidence / "terminal_nang_cao.txt").open("x", encoding="utf-8") as log:
        with contextlib.redirect_stdout(Tee(sys.stdout, log)):
            try:
                if args.only_port_guard:
                    active = "NC09_NOI_LAI_TU_CHOI_CONG_LA"
                    demo = new()
                    command(demo, "ngat-cua-hang")
                    with module.socket.socket() as blocker:
                        if hasattr(module.socket, "SO_EXCLUSIVEADDRUSE"):
                            blocker.setsockopt(module.socket.SOL_SOCKET, module.socket.SO_EXCLUSIVEADDRUSE, 1)
                        blocker.bind(("127.0.0.1", 18000))
                        blocker.listen(2)
                        helper.expect_error(RuntimeError, lambda: command(demo, "noi-cua-hang"), "ngoài phiên")
                        assert demo.links[demo.selected]
                        assert demo.agent.env["TV3_OFFLINE"] == "1"
                        assert blocker.fileno() >= 0 and demo.agent.process is None
                    helper.free_port()
                    demo.close()
                    pass_case(active, {"foreign_port_preserved": True, "sender_not_started": True,
                                       "offline_retained": True, "transactions_created": 0})
                elif args.only_guards:
                    active = "NC08_CHAN_CONG_CU_CO_DINH_KHO"
                    demo = new()
                    command(demo, "cua-hang CH02 POS01")
                    before = {p.relative_to(demo.session).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in demo.session.rglob("*") if p.is_file()}
                    blocked = []
                    for action in ["doi-chieu", "gui-bu", "xuat-csv", "sao-luu-kho",
                                   "phuc-hoi-kho khong_ton_tai.db"]:
                        helper.expect_error(RuntimeError, lambda action=action: command(demo, action), "Công cụ")
                        blocked.append(action)
                    after = {p.relative_to(demo.session).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                             for p in demo.session.rglob("*") if p.is_file()}
                    assert before == after, "Lệnh bị chặn không được thực hiện tác dụng phụ"
                    assert not demo.receiver.running() and all(not a.running() for a in demo.agents.values())
                    demo.close()
                    pass_case(active, {"blocked": blocked, "files_and_databases_unchanged": True,
                                       "transactions_created": 0, "services_started": False})
                else:
                    active = "NC01_GIAM_SAT_RONG"
                    demo = new()
                    absent = snapshot(demo)
                    assert absent["hq_total"] is None and absent["errors"] and not absent["sync_complete"]
                    assert not (demo.session / "DuLieu" / "truso.db").exists()
                    command(demo, "tru-so-bat")
                    empty = snapshot(demo)
                    assert empty["store_total"] == empty["hq_total"] == 0
                    assert not empty["sync_complete"] and empty["service"]["reachable"]
                    command(demo, "giam-sat")
                    demo.close()
                    pass_case(active, {"missing_db": absent, "empty_pair": empty, "read_only_hashes": "unchanged"})

                    for mode in ["wrong_id", "array", "invalid_json", "ack_false", "ack_number", "ack_string", "missing_ack"]:
                        active = "NC02_ACK_" + mode
                        demo = new()
                        create(demo, 1)
                        pending = helper.read_db(demo.session, "cuahang01.db", True)
                        fake_path = demo.session / "Script" / "receiver_gia_lap.py"
                        with fake_path.open("x", encoding="utf-8") as f:
                            f.write(FAKE)
                        demo.receiver = module.Child("Receiver giả " + mode, fake_path.name,
                            "receiver_gia_lap.txt", env=dict(module.ENV, TV3_FAKE_MODE=mode))
                        helper.free_port()
                        command(demo, "tru-so-bat")
                        wait_for(lambda: module.port_busy(18000), 5)
                        command(demo, "gui-mot-luot")
                        rejected = snapshot(demo)
                        assert rejected["states"] == {"PENDING": 0, "SENT": 1, "ACKED": 0}
                        assert rejected["hq_total"] == 0 and not rejected["sync_complete"]
                        retained = helper.read_db(demo.session, "cuahang01.db", True)
                        assert all(pending["rows"][0][k] == retained["rows"][0][k] for k in ("ma_gd","ma_cua_hang","ma_may","thoi_gian","so_tien"))
                        command(demo, "tru-so-tat")
                        demo.receiver = module.Child("Trụ sở", "hq_receiver.py", "receiver_log.txt")
                        command(demo, "tru-so-bat")
                        command(demo, "gui-mot-luot")
                        recovered = snapshot(demo)
                        assert recovered["sync_complete"] and recovered["states"]["ACKED"] == 1 and recovered["hq_total"] == 1
                        demo.close()
                        helper.free_port()
                        pass_case(active, {"rejected": rejected, "recovered": recovered, "payload_retained": True})

                    active = "NC03_CHO_20_VA_TU_PHUC_HOI"
                    demo = new()
                    create(demo, 20)
                    command(demo, "dong-bo-bat")
                    wait_for(lambda: states(demo) == {"SENT": 20})
                    held = snapshot(demo)
                    assert held["store_total"] == held["unconfirmed"] == 20 and held["states"]["ACKED"] == 0
                    sender_pid = demo.agent.process.pid
                    command(demo, "tru-so-bat")
                    wait_for(lambda: states(demo) == {"ACKED": 20})
                    assert demo.agent.process.pid == sender_pid, "Không được gọi gửi thủ công hoặc thay sender"
                    command(demo, "dong-bo-tat")
                    complete = snapshot(demo)
                    assert complete["sync_complete"] and complete["hq_total"] == 20 and not complete["duplicate_ids"]
                    command(demo, "gui-lap")
                    assert snapshot(demo)["hq_total"] == 20
                    demo.close()
                    pass_case(active, {"held": held, "recovered": complete, "same_auto_sync_process": True, "duplicate_replay": 20})

                    active = "NC04_HAI_CUA_HANG"
                    demo = new()
                    command(demo, "tru-so-bat")
                    create(demo, 5)
                    command(demo, "dong-bo-bat")
                    ch1_pid = demo.agent.process.pid
                    command(demo, "cua-hang CH02 POS01")
                    command(demo, "ngat-cua-hang")
                    create(demo, 5)
                    command(demo, "dong-bo-bat")
                    wait_for(lambda: states(demo) == {"ACKED": 5}
                             and states(demo, "CuaHang/CH02_POS01.db") == {"SENT": 5})
                    isolated = snapshot(demo)
                    assert isolated["store_total"] == 10 and isolated["hq_total"] == 5
                    assert isolated["unconfirmed"] == 5 and not isolated["sync_complete"]
                    assert demo.agents[("CH01","POS01")].process.pid == ch1_pid
                    command(demo, "noi-cua-hang")
                    wait_for(lambda: states(demo, "CuaHang/CH02_POS01.db") == {"ACKED": 5})
                    command(demo, "dong-bo-tat")
                    command(demo, "cua-hang CH01 POS01")
                    command(demo, "dong-bo-tat")
                    final = snapshot(demo)
                    assert final["sync_complete"] and final["store_total"] == final["hq_total"] == 10
                    assert final["states"]["ACKED"] == 10 and not final["duplicate_ids"]
                    hq_file = demo.session / "DuLieu" / "truso.db"
                    before = hashlib.sha256(hq_file.read_bytes()).hexdigest()
                    command(demo, "gui-lap")
                    command(demo, "cua-hang CH02 POS01")
                    command(demo, "gui-lap")
                    assert hashlib.sha256(hq_file.read_bytes()).hexdigest() == before
                    helper.expect_error(RuntimeError, lambda: command(demo, "gui-bu"), "TV2")
                    command(demo, "trang-thai")
                    demo.close()
                    pass_case(active, {"isolated": isolated, "final": final, "replay_each_store": 5,
                                      "hq_unchanged_after_replay": True, "tv2_multistore_guard": True})

                    active = "NC05_CAU_HINH_VA_BO_DEM"
                    demo = new()
                    create(demo, 1)
                    create(demo, 1)  # Hai subprocess riêng, bộ đếm không reset.
                    rows = helper.read_db(demo.session, "cuahang01.db", True)["rows"]
                    assert len(rows) == 2 and rows[0]["ma_gd"] != rows[1]["ma_gd"]
                    assert rows[1]["ma_gd"].endswith("-000002")
                    demo.run(code="from Script.store_agent import tao_giao_dich\n"
                             "for value in [0,-1,True,1.5,'1000']:\n"
                             " try: tao_giao_dich(value)\n"
                             " except ValueError: pass\n"
                             " else: raise AssertionError('Accepted invalid amount')\n")
                    assert helper.read_db(demo.session, "cuahang01.db", True)["count"] == 2
                    for override in [
                        {"TV3_STORE_ID": "../BAD"}, {"TV3_DB_PATH": "../ngoai_phien.db"},
                        {"TV3_STORE_ID": "CH02", "TV3_DB_PATH": "DuLieu/cuahang01.db"}
                    ]:
                        db = demo.session / "DuLieu" / "cuahang01.db"
                        before = hashlib.sha256(db.read_bytes()).hexdigest()
                        child = subprocess.run([sys.executable,"-B","-c","from Script.store_agent import khoi_tao; khoi_tao()"],
                            cwd=demo.session, env=dict(demo.store_env(),**override),
                            text=True,encoding="utf-8",capture_output=True,timeout=10)
                        print("CONFIG_REJECTED", override, child.returncode, child.stderr, flush=True)
                        assert child.returncode != 0
                        assert hashlib.sha256(db.read_bytes()).hexdigest() == before
                    demo.close()
                    pass_case(active, {"restart_counter_unique": True, "invalid_amounts_rejected": 5,
                                      "unsafe_or_mixed_config_rejected": 3, "rows_preserved": 2})

                    active = "NC06_GIAM_SAT_LECH_VA_LOI_SCHEMA"
                    demo = new()
                    command(demo, "tru-so-bat")
                    create(demo, 1)
                    command(demo, "gui-mot-luot")
                    demo.close()
                    # Fixture cố ý sai trong phiên MỚI; không phải kết quả giao dịch thật.
                    with sqlite3.connect(demo.session / "DuLieu" / "truso.db") as conn:
                        conn.execute("UPDATE giao_dich SET so_tien = so_tien + 1")
                    changed = snapshot(demo)
                    assert changed["store_total"] == changed["hq_total"] == 1
                    assert len(changed["changed"]) == 1 and not changed["sync_complete"]
                    schema_demo = new()
                    with sqlite3.connect(schema_demo.session / "DuLieu" / "truso.db") as conn:
                        conn.execute("CREATE TABLE fixture_khong_phai_giao_dich (x INTEGER)")
                    schema = snapshot(schema_demo)
                    assert schema["hq_total"] is None and schema["errors"] and not schema["sync_complete"]
                    schema_demo.close()
                    pass_case(active, {"injected_content_mismatch": changed, "injected_wrong_schema": schema,
                                      "fixture_only": True, "monitor_read_only": True})

                    active = "NC07_CLI_DON_HAI_SENDER"
                    cli = subprocess.run([sys.executable,"-B","-u",str(runtime/"demo_tich_hop.py")],
                        input="phien-moi\ntru-so-bat\ndong-bo-bat\ncua-hang CH02 POS01\ndong-bo-bat\nthoat\n",
                        cwd=runtime,env=module.ENV,capture_output=True,text=True,encoding="utf-8",timeout=25)
                    print(cli.stdout + cli.stderr, flush=True)
                    pids = [int(p) for p in re.findall(r"PID (\d+)",cli.stdout)]
                    assert cli.returncode == 0 and len(pids) == 3
                    assert all(not helper.process_running(pid) for pid in pids)
                    helper.free_port()
                    pass_case(active, {"exit": cli.returncode, "owned_pids": pids, "all_stopped": True})
            except BaseException as exc:
                error = type(exc).__name__ + ": " + str(exc)
                results.append({"case":active,"status":"FAIL","error":error})
                traceback.print_exc(file=log)
                print("CHƯA ĐẠT: " + error, flush=True)
            finally:
                for demo in reversed(demos):
                    try:
                        demo.close()
                    except BaseException as exc:
                        error = (error + "; " if error else "") + "Cleanup: " + str(exc)
                try:
                    helper.free_port()
                except OSError as exc:
                    error = (error + "; " if error else "") + "Port: " + str(exc)
                result = {"status":"PASS" if error is None else "FAIL",
                          "started":started,"finished":helper.stamp(),"cases":results,"error":error,
                          "base_commit":"c88fdb963ecc93efcac0584f2da9b9c740b3e1d8",
                          "runtime_root":str(runtime),"old_sessions_used":False,
                          "source_sha256":{p.relative_to(SOURCE).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in [SOURCE/"demo_tich_hop.py",SOURCE/"chay_demo.ps1",
                                        SOURCE/"KiemThu/kiem_thu_nang_cao.py"] + sorted((SOURCE/"Script").glob("*.py"))}}
                with (evidence/"KET_QUA_NANG_CAO.json").open("x",encoding="utf-8") as f:
                    json.dump(result,f,ensure_ascii=False,indent=2)
                print("RESULT="+json.dumps({"status":result["status"],"cases":len(results),"error":error}),flush=True)
    return 0 if error is None else 1


if __name__ == "__main__":
    raise SystemExit(main())
