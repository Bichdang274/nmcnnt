"""Giám sát SQLite chỉ đọc; mỗi lần lấy ảnh chụp riêng, không kết luận từ 0/0."""
import argparse
from collections import Counter
from datetime import datetime
import json
from pathlib import Path
import sqlite3
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

FIELDS = ("ma_gd", "ma_cua_hang", "ma_may", "thoi_gian", "so_tien")
STATES = ("PENDING", "SENT", "ACKED")


def read_rows(path, session, store=False):
    path = path.resolve()
    if not path.is_relative_to(session.resolve()):
        raise ValueError("Từ chối CSDL ngoài phiên")
    if not path.is_file():
        raise FileNotFoundError("CSDL chưa được tạo: " + path.name)
    conn = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=2)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA query_only = ON")
        conn.execute("BEGIN")
        columns = ", ".join(FIELDS) + (", trang_thai" if store else "")
        rows = [dict(row) for row in conn.execute(
            "SELECT " + columns + " FROM giao_dich ORDER BY ma_gd")]
        if store and any(row["trang_thai"] not in STATES for row in rows):
            raise ValueError("Trạng thái giao dịch ngoài PENDING/SENT/ACKED")
        return rows
    finally:
        conn.close()


def service_status(url):
    # GET không tạo giao dịch. 501 cũng chứng minh có HTTP phản hồi,
    # nhưng không xác thực danh tính receiver hoặc đảm bảo POST/ACK hoạt động.
    try:
        with urlopen(Request(url, method="GET"), timeout=1) as response:
            return {"reachable": True, "http": response.status, "identity_verified": False}
    except HTTPError as exc:
        return {"reachable": True, "http": exc.code, "identity_verified": False}
    except (URLError, OSError, ValueError) as exc:
        return {"reachable": False, "error": type(exc).__name__, "identity_verified": False}


def collect(session, url="http://127.0.0.1:18000/giao-dich"):
    session = Path(session).resolve()
    if not (session / "phien.json").is_file():
        raise ValueError("Thiếu phien.json; chỉ giám sát phiên thử được nhận diện")
    errors, warnings, stores, local = [], [], [], []
    paths = [session / "DuLieu" / "cuahang01.db"]
    paths += sorted((session / "DuLieu" / "CuaHang").glob("*.db"))
    for path in paths:
        try:
            rows = read_rows(path, session, True)
            states = dict.fromkeys(STATES, 0)
            states.update(Counter(row["trang_thai"] for row in rows))
            stores.append({"db": path.relative_to(session).as_posix(),
                           "total": len(rows), "states": states})
            local.extend(rows)
        except (OSError, sqlite3.Error, ValueError) as exc:
            errors.append(path.name + ": " + str(exc))
            stores.append({"db": path.relative_to(session).as_posix(),
                           "total": None, "states": None})
    hq = None
    try:
        hq = read_rows(session / "DuLieu" / "truso.db", session)
    except (OSError, sqlite3.Error, ValueError) as exc:
        errors.append("Trụ sở: " + str(exc))
    states = dict.fromkeys(STATES, 0)
    states.update(Counter(row["trang_thai"] for row in local))
    unacked = states["PENDING"] + states["SENT"]
    if unacked:
        warnings.append(f"Còn {unacked} giao dịch chưa có ACK hợp lệ")
    local_ids = Counter(row["ma_gd"] for row in local)
    duplicates = sorted(key for key, count in local_ids.items() if count > 1)
    missing, extra, changed, acked_missing = [], [], [], []
    matched = False
    if hq is not None:
        index = {row["ma_gd"]: row for row in hq}
        duplicates += sorted(key for key, count in Counter(row["ma_gd"] for row in hq).items() if count > 1)
        missing = sorted(set(local_ids) - set(index))
        extra = sorted(set(index) - set(local_ids))
        changed = sorted({row["ma_gd"] for row in local
                          if row["ma_gd"] in index and any(
                              row[field] != index[row["ma_gd"]][field] for field in FIELDS)})
        acked_missing = sorted(row["ma_gd"] for row in local
                               if row["trang_thai"] == "ACKED" and row["ma_gd"] in missing)
        matched = bool(local) and not errors and not (missing or extra or changed or duplicates)
        if missing or extra or changed or duplicates:
            warnings.append("Hai phía thiếu/thừa/lệch nội dung hoặc có mã trùng")
    if not local and not errors:
        warnings.append("Chưa có giao dịch; 0/0 không chứng minh đồng bộ thành công")
    service = service_status(url)
    if not service["reachable"]:
        warnings.append("Dịch vụ nhận hiện không phản hồi HTTP")
    if errors:
        warnings.append("Không đủ dữ liệu để kết luận; xem lỗi CSDL")
    return {"time": datetime.now().isoformat(timespec="seconds"),
            "stores": stores, "store_total": len(local) if not any(s["total"] is None for s in stores) else None,
            "states": states, "unconfirmed": unacked, "hq_total": len(hq) if hq is not None else None,
            "service": service, "data_match": matched,
            "sync_complete": matched and unacked == 0,
            "missing_hq": missing, "extra_hq": extra, "changed": changed,
            "acked_missing": acked_missing, "duplicate_ids": sorted(set(duplicates)),
            "errors": errors, "warnings": warnings,
            "snapshot_note": "Ảnh chụp từng CSDL; khi đang gửi, số liệu hai file có thể khác thời điểm."}


def display(value):
    def count(number):
        return "?" if number is None else str(number)
    print("\n" + "=" * 78)
    print("TV3 | GIÁM SÁT GIAO DỊCH | " + value["time"])
    print(f"{'Kho / POS':38} {'Tổng':>6} {'PENDING':>8} {'SENT':>6} {'ACKED':>7}")
    for store in value["stores"]:
        state = store["states"] or dict.fromkeys(STATES, None)
        print(f"{store['db']:38} {count(store['total']):>6} "
              f"{count(state['PENDING']):>8} {count(state['SENT']):>6} {count(state['ACKED']):>7}")
    print("Tổng kho:", count(value["store_total"]), "| Trụ sở:", count(value["hq_total"]),
          "| Chưa ACK:", value["unconfirmed"])
    service = value["service"]
    print("Dịch vụ:", ("HTTP phản hồi, mã " + str(service["http"])) if service["reachable"] else "KHÔNG PHẢN HỒI")
    print("GET chỉ kiểm tra HTTP; không xác thực receiver hoặc chứng minh POST/ACK.")
    print("Đối chiếu:", "KHỚP 5 TRƯỜNG" if value["data_match"] else "CHƯA KHỚP / CHƯA ĐỦ DỮ LIỆU")
    print("Đồng bộ:", "HOÀN TẤT" if value["sync_complete"] else "CHƯA HOÀN TẤT")
    print("Thiếu HQ:", len(value["missing_hq"]), "| Thừa HQ:", len(value["extra_hq"]),
          "| Lệch:", len(value["changed"]), "| Trùng:", len(value["duplicate_ids"]))
    for warning in value["warnings"]:
        print("! " + warning)
    for error in value["errors"]:
        print("LỖI: " + error)
    print(value["snapshot_note"])


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", type=Path, required=True)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--watch", type=float, default=0)
    args = parser.parse_args()
    if args.watch and not 1 <= args.watch <= 60:
        parser.error("--watch cần nằm trong khoảng 1–60 giây")
    try:
        while True:
            value = collect(args.session)
            if args.json:
                print(json.dumps(value, ensure_ascii=False, indent=2))
            else:
                display(value)
            if not args.watch:
                return
            time.sleep(args.watch)
    except KeyboardInterrupt:
        print("\nĐã dừng giám sát; không tác động receiver/auto sync.")


if __name__ == "__main__":
    main()
