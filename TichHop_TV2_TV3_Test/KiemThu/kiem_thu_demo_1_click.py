"""Hồi quy giao diện/launcher/điểm dừng; chạy thật trên runtime mới, Windows."""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import queue
import re
import socket
import sqlite3
import subprocess
import sys
import threading
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]


def save(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)


def rows(path, local=False):
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True, timeout=2)
    try:
        assert connection.execute("PRAGMA integrity_check").fetchall() == [("ok",)]
        return connection.execute("SELECT ma_gd,ma_cua_hang,ma_may,thoi_gian,so_tien" +
                                  (",trang_thai" if local else "") + " FROM giao_dich ORDER BY ma_gd").fetchall()
    finally:
        connection.close()


def session_for(run, mode):
    sessions = list((run / mode / "PhienThu").glob("Phien_*"))
    assert len(sessions) == 1
    return sessions[0]


def state(run, mode):
    session = session_for(run, mode)
    value = {"CH01": rows(session / "DuLieu/cuahang01.db", True),
             "HQ": rows(session / "DuLieu/truso.db")}
    other = session / "DuLieu/CuaHang/CH02_POS01.db"
    if other.exists():
        value["CH02"] = rows(other, True)
    return value


def verify(run, expected=True):
    summary = json.loads((run / "tong_ket.json").read_text(encoding="utf-8"))
    assert summary["passed"] is expected
    checked = []
    for result in summary["results"]:
        processes = json.loads((run / result["mode"] / "tien_trinh.json").read_text(encoding="utf-8"))
        assert all(p["stopped"] and p["exit_code"] == 0 and not p.get("forced") for p in processes)
        value = state(run, result["mode"])
        if expected:
            local = value["CH01"] + value.get("CH02", [])
            assert len(local) == len(value["HQ"]) == len({row[0] for row in local}) == 10
            assert all(row[-1] == "ACKED" for row in local)
            assert sorted(tuple(row[:-1]) for row in local) == value["HQ"]
            assert result["passed"]
            if result["mode"] == "TV2-TV3":
                backups = list((session_for(run, result["mode"]) / "DuLieu/SaoLuuTruSo").glob("*.db"))
                assert sorted(len(rows(p)) for p in backups) == [5, 10]
        checked.append({"mode": result["mode"], "hq": len(value["HQ"]), "processes_stopped": True})
    screen = (run / "terminal.txt").read_text(encoding="utf-8")
    assert not any(marker in screen for marker in ("Traceback", "PID ", "C:\\Users\\", "\x1b[", '{"time"'))
    assert "HỆ THỐNG GIAO DỊCH CHUỖI CỬA HÀNG" in screen and "BẢNG TỔNG KẾT TRÌNH DIỄN" in screen
    assert (run / "chi_tiet.txt").is_file()
    return checked


def launch(evidence, label, launcher, arguments, presentation=False, abort=False):
    print("ĐANG KIỂM TRA:", label, flush=True)
    environment = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1", NO_COLOR="1")
    process = subprocess.Popen(["cmd.exe", "/d", "/c", ".\\" + launcher, *arguments], cwd=ROOT,
                               env=environment, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="strict")
    messages = queue.Queue()

    def read_output():
        try:
            for line in process.stdout:
                messages.put(line)
        finally:
            messages.put(None)

    threading.Thread(target=read_output, daemon=True).start()
    output, run, pauses = [], None, []
    deadline = time.monotonic() + 180
    try:
        while True:
            assert time.monotonic() < deadline, "Hết timeout của ca kiểm thử launcher"
            try:
                line = messages.get(timeout=0.5)
            except queue.Empty:
                continue
            if line is None:
                break
            output.append(line)
            if line.startswith("Phiên minh chứng: runtime/"):
                run = ROOT / line.strip().split(": ", 1)[1]
            match = re.search(r"CHỜ THUYẾT TRÌNH \[(TV3|TV2-TV3) (\d+)/(\d+)\]", line)
            if match:
                assert presentation and run is not None
                mode, number, _ = match.groups()
                number = int(number)
                if abort and mode == "TV3" and number == 5:
                    process.stdin.close()  # EOF: yêu cầu thoát thật tại điểm có hai sender.
                    continue
                held = 11 if number == 5 else 0.1
                before = state(run, mode)
                session = session_for(run, mode)
                if number == 5:
                    assert len(before["HQ"]) == 5
                    if mode == "TV3":
                        assert len(before["CH02"]) == 5 and all(row[-1] == "SENT" for row in before["CH02"])
                        log = session / "MinhChung/auto_sync_CH02_POS01.txt"
                        cycles = log.read_text(encoding="utf-8").count("Kiem tra giao dich...")
                    else:
                        assert len(before["CH01"]) == 10 and all(row[-1] == "ACKED" for row in before["CH01"])
                time.sleep(held)
                assert before == state(run, mode), "Dữ liệu đổi trong khi chờ Enter"
                if number == 5 and mode == "TV3":
                    assert log.read_text(encoding="utf-8").count("Kiem tra giao dich...") > cycles
                pauses.append({"mode": mode, "stage": number, "held_seconds": held, "unchanged": True})
                process.stdin.write("\n")
                process.stdin.flush()
        code = process.wait(timeout=10)
    finally:
        if process.stdin and not process.stdin.closed:
            process.stdin.close()
        if process.poll() is None:
            process.wait(timeout=55)
        (evidence / (label + "_terminal.txt")).write_text("".join(output), encoding="utf-8")
    assert run is not None
    assert code == (1 if abort else 0), f"Mã thoát sai: {code}; xem {label}_terminal.txt"
    checked = verify(run, expected=not abort)
    if presentation and not abort:
        assert len(pauses) == 13
        for mode in ("TV3", "TV2-TV3"):
            proofs = list((session_for(run, mode) / "MinhChung").glob("*_tam_dung_sau.json"))
            assert len(proofs) == (6 if mode == "TV3" else 7)
            assert all(json.loads(p.read_text(encoding="utf-8"))["unchanged"] for p in proofs)
    result = {"case": label, "passed": True, "exit_code": code, "runtime": run.name,
              "verified": checked, "pauses": pauses}
    save(evidence / (label + ".json"), result)
    print("ĐẠT:", label, "|", run.name, flush=True)
    return result


def port_guard(evidence):
    print("ĐANG KIỂM TRA: cong_bi_chiem", flush=True)
    with socket.socket() as foreign:
        foreign.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        foreign.bind(("127.0.0.1", 18000))
        foreign.listen()
        result = subprocess.run(["cmd.exe", "/d", "/c", ".\\chay_demo_TV3.cmd", "-KhongGiuManHinh"],
                                cwd=ROOT, env=dict(os.environ, PYTHONIOENCODING="utf-8"),
                                capture_output=True, text=True, encoding="utf-8", timeout=35)
        (evidence / "cong_bi_chiem_terminal.txt").write_text(result.stdout + result.stderr, encoding="utf-8")
        assert result.returncode == 1 and foreign.fileno() != -1 and foreign.getsockname()[1] == 18000
        run_name = re.search(r"Phiên minh chứng: runtime/(\S+)", result.stdout).group(1)
        run = ROOT / "runtime" / run_name
        summary = json.loads((run / "tong_ket.json").read_text(encoding="utf-8"))
        assert not summary["passed"] and not summary["results"] and not list(run.rglob("*.db"))
        assert "CHƯA ĐẠT" in result.stdout and "Traceback" not in result.stdout and "PID " not in result.stdout
    value = {"case": "cong_bi_chiem", "passed": True, "runtime": run_name, "foreign_socket_preserved": True}
    save(evidence / "cong_bi_chiem.json", value)
    print("ĐẠT: cong_bi_chiem", flush=True)
    return value


def main():
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=("all", "auto", "pause", "abort", "port"), default="all")
    args = parser.parse_args()
    evidence = ROOT / "runtime" / (datetime.now().strftime("KiemThuGiaoDien_%Y%m%d_%H%M%S_") + uuid.uuid4().hex[:8])
    evidence.mkdir(parents=True, exist_ok=False)
    print("Minh chứng kiểm thử:", evidence.relative_to(ROOT), flush=True)
    results = []
    try:
        if args.case in ("all", "auto"):
            results.append(launch(evidence, "tu_dong_cmd", "chay_demo_1_click.cmd", ["-KhongGiuManHinh"]))
        if args.case in ("all", "pause"):
            results.append(launch(evidence, "thuyet_trinh_cmd", "chay_demo_thuyet_trinh.cmd",
                                  ["-KhongGiuManHinh"], presentation=True))
        if args.case in ("all", "abort"):
            results.append(launch(evidence, "thoat_tai_diem_dung", "chay_demo_TV3.cmd",
                                  ["-TamDung", "-KhongGiuManHinh"], presentation=True, abort=True))
        if args.case in ("all", "port"):
            results.append(port_guard(evidence))
    finally:
        save(evidence / "ket_qua_hoi_quy.json", {"selected": args.case, "results": results,
                                                "passed": len(results) == (4 if args.case == "all" else 1)})


if __name__ == "__main__":
    main()
