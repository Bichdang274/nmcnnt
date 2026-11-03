"""Demo tích hợp Nhóm 02 – một trang web chạy xuyên suốt phần của TV1, TV2, TV3.

- Phần mạng: làm trong Packet Tracer (Nhom02_v2.pkt); trang hướng dẫn từng thao tác và tra ACL theo
  đúng running-config của 8 thiết bị (thư mục CauHinh/) để giải thích vì sao gói được qua / bị chặn.
- Phần dữ liệu: các nút trên trang chạy script THẬT của TV3 (Script_TV3/, không sửa) và TV2 (Script_TV2/)
  trong một thư mục phiên riêng PhienDemo/, không đụng dữ liệu trong repo.
- Mất WAN cửa hàng 1 được giả lập giống cách TV3 làm: dừng hq_receiver.py (cổng 8000).

Chạy:   python demo_tich_hop.py        (macOS: python3)   rồi mở http://localhost:8765
Docker: docker compose up --build                             rồi mở http://localhost:8765
"""
import ipaddress
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from collections import deque
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

GOC = Path(__file__).resolve().parent
PHIEN = GOC / "PhienDemo"
# Trong Docker đặt DEMO_HOST=0.0.0.0 để máy ngoài container mở được trang
DIA_CHI_NGHE = os.environ.get("DEMO_HOST", "127.0.0.1")
CONG_WEB = 8765
CONG_TRU_SO = 8000

sys.path.insert(0, str(GOC / "Script_TV2"))
import doi_chieu as DC  # noqa: E402

KHOA = threading.Lock()
NHAT_KY = deque(maxlen=400)
TRANG_THAI = {"wan": "binh-thuong", "cong_khoa": False}   # wan: binh-thuong | dut-chinh | co-lap
SYSLOG = deque(maxlen=200)   # nhật ký Server-Backup nhận được (mô phỏng theo cấu hình logging 192.168.0.11)


def ghi(nguon, dong):
    NHAT_KY.append({"gio": datetime.now().strftime("%H:%M:%S"), "nguon": nguon, "text": dong.rstrip()})


# ---------------------------------------------------------------- chạy script trong thư mục phiên
def moi_truong():
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUNBUFFERED"] = "1"
    return env


def chay(nguon, *tham_so, lenh_hien=None):
    ghi("LENH", "$ python " + (lenh_hien or " ".join(tham_so)))
    kq = subprocess.run([sys.executable, *tham_so], cwd=PHIEN, capture_output=True, text=True,
                        encoding="utf-8", errors="replace", env=moi_truong(), timeout=120)
    for dong in (kq.stdout + kq.stderr).splitlines():
        if dong.strip():
            ghi(nguon, dong)
    return kq.returncode


class TruSo:
    """Tiến trình hq_receiver.py của TV3. Đang chạy = WAN cửa hàng 1 còn kết nối tới trụ sở."""

    def __init__(self):
        self.tien_trinh = None

    def dang_chay(self):
        return self.tien_trinh is not None and self.tien_trinh.poll() is None

    @staticmethod
    def cong_dang_mo():
        with socket.socket() as s:
            s.settimeout(0.3)
            return s.connect_ex(("127.0.0.1", CONG_TRU_SO)) == 0

    def bat(self):
        if self.dang_chay():
            return
        if self.cong_dang_mo():
            raise RuntimeError("Cổng 8000 đang bận – có thể đang chạy hq_receiver.py ở cửa sổ khác. Tắt nó (Ctrl+C) rồi thử lại.")
        ghi("LENH", "$ python Script/hq_receiver.py")
        self.tien_trinh = subprocess.Popen(
            [sys.executable, "-u", "Script/hq_receiver.py"], cwd=PHIEN, env=moi_truong(),
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
        threading.Thread(target=self._doc_log, args=(self.tien_trinh,), daemon=True).start()
        for _ in range(30):
            if self.cong_dang_mo():
                return
            if self.tien_trinh.poll() is not None:
                break
            time.sleep(0.1)
        raise RuntimeError("hq_receiver.py không khởi động được – xem nhật ký.")

    @staticmethod
    def _doc_log(tien_trinh):
        for dong in tien_trinh.stdout:
            if dong.strip():
                ghi("TRU SO", dong)

    def tat(self):
        if self.dang_chay():
            self.tien_trinh.terminate()
            try:
                self.tien_trinh.wait(5)
            except subprocess.TimeoutExpired:
                self.tien_trinh.kill()
            ghi("TRU SO", "(đã dừng hq_receiver.py – trụ sở không nhận được giao dịch)")
        self.tien_trinh = None


TRU_SO = TruSo()


def lam_moi():
    TRU_SO.tat()
    if PHIEN.exists():
        shutil.rmtree(PHIEN)
    (PHIEN / "Script").mkdir(parents=True)
    (PHIEN / "DuLieu").mkdir()
    for thu_muc in ("Script_TV3", "Script_TV2"):
        for f in (GOC / thu_muc).glob("*.py"):
            shutil.copy2(f, PHIEN / "Script" / f.name)
    NHAT_KY.clear()
    SYSLOG.clear()
    TRANG_THAI["cong_khoa"] = False
    ghi("DEMO", "Phiên demo mới: dữ liệu trống, script TV3 + TV2 đã chép vào PhienDemo/Script")
    TRANG_THAI["wan"] = "binh-thuong"
    TRU_SO.bat()
    chay("CUA HANG", "-c", "from Script.store_agent import khoi_tao; khoi_tao()",
         lenh_hien="-c \"from Script.store_agent import khoi_tao; khoi_tao()\"")


# ---------------------------------------------------------------- tra ACL theo running-config
TEN_CONG = {"www": 80, "telnet": 23, "tftp": 69, "ftp": 21}


def ip_so(dia_chi):
    return int(ipaddress.IPv4Address(dia_chi))


def doc_dia_chi(tu, i):
    if tu[i] == "any":
        return (0, 0xFFFFFFFF), i + 1
    if tu[i] == "host":
        return (ip_so(tu[i + 1]), 0), i + 2
    return (ip_so(tu[i]), ip_so(tu[i + 1])), i + 2


def doc_dong_mo_rong(dong):
    tu = dong.split()
    quy_tac = {"text": dong, "hanh_dong": tu[0], "giao_thuc": tu[1]}
    quy_tac["nguon"], i = doc_dia_chi(tu, 2)
    quy_tac["dich"], i = doc_dia_chi(tu, i)
    phan_con = tu[i:]
    quy_tac["cong"] = None
    quy_tac["established"] = "established" in phan_con
    quy_tac["icmp"] = None
    if "eq" in phan_con:
        gia_tri = phan_con[phan_con.index("eq") + 1]
        quy_tac["cong"] = TEN_CONG.get(gia_tri) or int(gia_tri)
    elif quy_tac["giao_thuc"] == "icmp" and phan_con:
        quy_tac["icmp"] = phan_con[0]
    return quy_tac


def khop_dia_chi(mau, dia_chi):
    mang, wildcard = mau
    return (ip_so(dia_chi) & ~wildcard & 0xFFFFFFFF) == (mang & ~wildcard & 0xFFFFFFFF)


def doc_cau_hinh():
    thiet_bi = {}
    for f in sorted((GOC / "CauHinh").glob("*_running-config.txt")):
        ten = f.name.split("_")[0]
        cau_hinh = {"acl": {}, "ap": {}, "acl_chuan": {}, "vty": None, "transport": "telnet", "sticky": {}}
        acl_hien, cong_hien, trong_vty = None, None, False
        for dong in f.read_text(encoding="utf-8").splitlines():
            if not dong.startswith(" "):
                acl_hien, cong_hien, trong_vty = None, None, False
            if m := re.match(r"ip access-list extended (\S+)", dong):
                acl_hien = m.group(1)
                cau_hinh["acl"][acl_hien] = []
            elif acl_hien and dong.startswith(" "):
                cau_hinh["acl"][acl_hien].append(doc_dong_mo_rong(dong.strip()))
            elif m := re.match(r"interface (\S+)", dong):
                cong_hien = m.group(1)
            elif cong_hien and (m := re.match(r" ip access-group (\S+) (in|out)", dong)):
                cau_hinh["ap"][(cong_hien, m.group(2))] = m.group(1)
            elif m := re.match(r"access-list (\d+) (permit|deny) (.+)", dong):
                tu = m.group(3).split()
                mau = (0, 0xFFFFFFFF) if tu[0] == "any" else (
                    (ip_so(tu[1]), 0) if tu[0] == "host" else (ip_so(tu[0]), ip_so(tu[1])))
                cau_hinh["acl_chuan"].setdefault(m.group(1), []).append(
                    {"text": f"{m.group(2)} {m.group(3)}", "hanh_dong": m.group(2), "mau": mau})
            elif dong.startswith("line vty"):
                trong_vty = True
            elif trong_vty and (m := re.match(r" access-class (\S+) in", dong)):
                cau_hinh["vty"] = m.group(1)
            elif trong_vty and (m := re.match(r" transport input (\S+)", dong)):
                cau_hinh["transport"] = m.group(1)
            elif cong_hien and (m := re.match(r" switchport port-security mac-address sticky (\S+)", dong)):
                cau_hinh["sticky"][cong_hien] = m.group(1)
        thiet_bi[ten] = cau_hinh
    return thiet_bi


CAU_HINH = doc_cau_hinh()

MAY = {
    "POS1-1": "192.168.10.11", "POS2-1": "192.168.20.11", "POS3-1": "192.168.30.11",
    "PC-Admin": "192.168.0.20", "Server-TT": "192.168.0.10", "Server-Backup": "192.168.0.11",
    "SW-CH1": "192.168.10.2", "SW-CH2": "192.168.20.2", "R-CH1 (G0/0)": "192.168.10.1",
    "R-CH1 (WAN)": "10.0.1.2", "R-HQ (G0/0)": "192.168.0.1", "R-CH2 (WAN)": "10.0.2.2",
}
DIA_DIEM = {"192.168.0.": "HQ", "192.168.10.": "CH1", "192.168.20.": "CH2", "192.168.30.": "CH3"}
ROUTER = {"HQ": "R-HQ", "CH1": "R-CH1", "CH2": "R-CH2", "CH3": "R-CH3"}
THIET_BI_IP = {
    "192.168.0.1": "R-HQ", "192.168.10.1": "R-CH1", "192.168.20.1": "R-CH2", "192.168.30.1": "R-CH3",
    "192.168.0.2": "SW-HQ", "192.168.10.2": "SW-CH1", "192.168.20.2": "SW-CH2", "192.168.30.2": "SW-CH3",
    "10.0.1.1": "R-HQ", "10.0.2.1": "R-HQ", "10.0.3.1": "R-HQ", "10.0.1.2": "R-CH1",
    "10.0.2.2": "R-CH2", "10.0.3.2": "R-CH3", "10.0.12.1": "R-CH1", "10.0.12.2": "R-CH2",
}
DICH_VU_MAY_CHU = {"192.168.0.10": {"ping", "web"}, "192.168.0.11": {"ping", "tftp", "ntp", "syslog"}}
DICH_VU = {"ping": ("icmp", None), "web": ("tcp", 80), "ssh": ("tcp", 22), "telnet": ("tcp", 23),
           "tftp": ("udp", 69), "ntp": ("udp", 123), "syslog": ("udp", 514)}
TEN_DICH_VU = {"ping": "ping", "web": "mở web (HTTP)", "ssh": "SSH", "telnet": "Telnet", "tftp": "gửi file TFTP",
               "ntp": "lấy giờ NTP", "syslog": "gửi Syslog"}
QUAN_TRI = ("ssh", "telnet")


def dia_diem(ip):
    return next((v for k, v in DIA_DIEM.items() if ip.startswith(k)), None)


def cac_chang(nguon, dich):
    """Các điểm có thể đặt ACL mà gói đi qua: (router, chiều)."""
    dd_nguon, dd_dich = dia_diem(nguon), dia_diem(dich)
    tb_nguon, tb_dich = THIET_BI_IP.get(nguon), THIET_BI_IP.get(dich)
    chang = []
    # Ra khỏi LAN nguồn: đi VÀO router qua G0/0 (gói do chính router sinh ra thì không qua)
    if dd_nguon and tb_nguon != ROUTER[dd_nguon] and not (dd_dich == dd_nguon and tb_dich != ROUTER[dd_nguon]):
        chang.append((ROUTER[dd_nguon], "in"))
    # Vào LAN đích: RỜI router qua G0/0 (gói gửi tới chính router thì không ra G0/0)
    if dd_dich and dd_dich != dd_nguon and tb_dich != ROUTER[dd_dich] and tb_nguon != ROUTER[dd_dich]:
        chang.append((ROUTER[dd_dich], "out"))
    return chang


def qua_acl(goi, router, chieu):
    ten_acl = CAU_HINH[router]["ap"].get(("GigabitEthernet0/0", chieu))
    if not ten_acl:
        return {"router": router, "chieu": chieu, "acl": None, "cho_qua": True}
    for so, quy_tac in enumerate(CAU_HINH[router]["acl"][ten_acl], start=1):
        if quy_tac["giao_thuc"] != "ip" and quy_tac["giao_thuc"] != goi["giao_thuc"]:
            continue
        if not (khop_dia_chi(quy_tac["nguon"], goi["nguon"]) and khop_dia_chi(quy_tac["dich"], goi["dich"])):
            continue
        if quy_tac["cong"] is not None and quy_tac["cong"] != goi["cong"]:
            continue
        if quy_tac["established"] and not goi["established"]:
            continue
        if quy_tac["icmp"] and quy_tac["icmp"] != goi["icmp"]:
            continue
        return {"router": router, "chieu": chieu, "acl": ten_acl, "dong": f"{so * 10} {quy_tac['text']}",
                "cho_qua": quy_tac["hanh_dong"] == "permit"}
    return {"router": router, "chieu": chieu, "acl": ten_acl, "dong": "(deny ngầm cuối ACL)", "cho_qua": False}


def bi_mat_wan(nguon, dich):
    wan = TRANG_THAI["wan"]
    ben = {dia_diem(nguon) or ("CH1" if THIET_BI_IP.get(nguon) == "R-CH1" else "WAN"),
           dia_diem(dich) or ("CH1" if THIET_BI_IP.get(dich) == "R-CH1" else "WAN")}
    return wan == "co-lap" and "CH1" in ben and len(ben) > 1


def tra_acl(ten_nguon, ten_dich, dich_vu):
    nguon, dich = MAY[ten_nguon], MAY[ten_dich]
    giao_thuc, cong = DICH_VU[dich_vu]
    goi_di = {"giao_thuc": giao_thuc, "nguon": nguon, "dich": dich, "cong": cong,
              "established": False, "icmp": "echo"}
    buoc = []

    def ket_luan(dat, loi, pt):
        return {"buoc": buoc, "dat": dat, "ket_luan": loi, "pt": pt,
                "mo_ta": f"{ten_nguon} ({nguon}) {TEN_DICH_VU[dich_vu]} tới {ten_dich} ({dich})"}

    if nguon == dich:
        return ket_luan(False, "Nguồn và đích trùng nhau.", "")

    for router, chieu in cac_chang(nguon, dich):
        kq = qua_acl(goi_di, router, chieu)
        kq["huong"] = "đi"
        buoc.append(kq)
        if not kq["cho_qua"]:
            pt = {"ping": "Destination host unreachable", "web": "Request Timeout", "ssh": "% Connection timed out",
                  "telnet": "% Connection timed out"}.get(dich_vu, "(gói bị bỏ, không có phản hồi)")
            return ket_luan(False, f"Bị CHẶN tại {router} – ACL {kq['acl']}, dòng {kq['dong']}.", pt)

    if bi_mat_wan(nguon, dich):
        return ket_luan(False, "ACL cho qua, nhưng cửa hàng 1 đang MẤT WAN (cả hai đường Serial đều shutdown).",
                        "Request timed out / Destination host unreachable")

    tb_dich = THIET_BI_IP.get(dich)
    if dich_vu in QUAN_TRI:
        if not tb_dich:
            return ket_luan(False, f"{ten_dich} là máy trạm/máy chủ, không nhận {TEN_DICH_VU[dich_vu]}.",
                            "% Connection refused")
        cho_nhan = CAU_HINH[tb_dich]["transport"]
        if cho_nhan not in ("all", dich_vu):
            buoc.append({"router": tb_dich, "chieu": "vty", "acl": f"transport input {cho_nhan}",
                         "dong": f"transport input {cho_nhan}", "cho_qua": False, "huong": "đăng nhập"})
            return ket_luan(False, f"{tb_dich} chỉ nhận {cho_nhan.upper()} (transport input {cho_nhan}) – "
                                   f"{TEN_DICH_VU[dich_vu]} bị từ chối.", "% Connection refused by remote host")
        so_acl = CAU_HINH[tb_dich]["vty"]
        cho_phep = any(khop_dia_chi(q["mau"], nguon) and q["hanh_dong"] == "permit"
                       for q in CAU_HINH[tb_dich]["acl_chuan"].get(so_acl, []))
        buoc.append({"router": tb_dich, "chieu": "vty", "acl": f"access-class {so_acl}",
                     "dong": "10 permit host 192.168.0.20", "cho_qua": cho_phep, "huong": "đăng nhập"})
        if not cho_phep:
            return ket_luan(False, f"Gói tới được {tb_dich} nhưng bị access-class {so_acl} TỪ CHỐI "
                                   f"(chỉ PC-Admin 192.168.0.20 được quản trị).", "% Connection refused by remote host")
    elif dich in DICH_VU_MAY_CHU and dich_vu not in DICH_VU_MAY_CHU[dich]:
        return ket_luan(False, f"{ten_dich} không bật dịch vụ này.", "Request Timeout")
    elif dich_vu in ("web", "tftp") and dich not in DICH_VU_MAY_CHU:
        return ket_luan(False, f"{ten_dich} không chạy dịch vụ này.", "Request Timeout")

    goi_ve = {"giao_thuc": giao_thuc, "nguon": dich, "dich": nguon, "cong": None,
              "established": giao_thuc == "tcp", "icmp": "echo-reply"}
    for router, chieu in cac_chang(dich, nguon):
        kq = qua_acl(goi_ve, router, chieu)
        kq["huong"] = "về"
        buoc.append(kq)
        if not kq["cho_qua"]:
            return ket_luan(False, f"Gói đi tới nơi nhưng gói TRẢ LỜI bị chặn tại {router} ({kq['dong']}).",
                            "Request timed out")

    pt = {"ping": "Reply from " + dich, "web": "Hiện trang web", "ssh": "Password: (tài khoản admin / cisco)",
          "telnet": "Hỏi Password: (gõ cisco)", "tftp": "Copy thành công", "ntp": "show ntp status: Clock is synchronized",
          "syslog": "Server-Backup > Services > SYSLOG có dòng mới"}[dich_vu]
    ghi_chu = ""
    if TRANG_THAI["wan"] == "dut-chinh" and {"CH1"} & {dia_diem(nguon), dia_diem(dich)} and \
            dia_diem(nguon) != dia_diem(dich):
        ghi_chu = " Đường chính CH1 đang đứt: OSPF đưa gói đi đường dự phòng 10.0.12.0/30 qua R-CH2."
    return ket_luan(True, "ĐƯỢC – mọi ACL trên đường đi và đường về đều cho qua." + ghi_chu, pt)


# ---------------------------------------------------------------- Syslog + port security (mô phỏng theo cấu hình)
# Thiết bị gửi Syslog về 192.168.0.11 (logging + service timestamps, giờ đồng bộ NTP). Mô phỏng các thông báo IOS
# khi cổng Serial đổi trạng thái; R-CH1 chỉ gửi được khi còn đường về trụ sở.
NGUON_LOG = {"R-HQ": "192.168.0.1", "R-CH2": "10.0.2.2", "SW-CH1": "192.168.10.2"}
LIEN_KET = {  # tên: ((thiết bị, cổng, router-id), (thiết bị, cổng, router-id))
    "hq-ch1": (("R-CH1", "Serial0/0/0", "2.2.2.2"), ("R-HQ", "Serial0/0/0", "1.1.1.1")),
    "ch1-ch2": (("R-CH1", "Serial0/0/1", "2.2.2.2"), ("R-CH2", "Serial0/0/1", "3.3.3.3")),
}
DUT_THEO_WAN = {"binh-thuong": set(), "dut-chinh": {"hq-ch1"}, "co-lap": {"hq-ch1", "ch1-ch2"}}


def ghi_syslog(thiet_bi, nguon_ip, thong_bao, toi_noi=True):
    gio = datetime.now().strftime("%b %d %H:%M:%S.%f")[:-3]
    SYSLOG.append({"gio": gio, "thiet_bi": thiet_bi, "ip": nguon_ip, "text": thong_bao, "toi": toi_noi})


def syslog_doi_wan(cu, moi):
    dut_truoc, dut_sau = DUT_THEO_WAN[cu], DUT_THEO_WAN[moi]
    ch1_con_duong = moi != "co-lap"
    ip_ch1 = "10.0.1.2" if moi == "binh-thuong" else "10.0.12.1"
    for ten, dau in LIEN_KET.items():
        if (ten in dut_sau) == (ten in dut_truoc):
            continue
        xuong = ten in dut_sau
        for (tb, cong, _), (_, _, rid_ben_kia) in (dau, dau[::-1]):
            toi = tb != "R-CH1" or ch1_con_duong
            ip = ip_ch1 if tb == "R-CH1" else NGUON_LOG[tb]
            if tb == "R-CH1":  # đầu bị shutdown / no shutdown bằng tay
                ghi_syslog(tb, ip, f"%LINK-5-CHANGED: Interface {cong}, changed state to "
                                   f"{'administratively down' if xuong else 'up'}", toi)
            else:
                ghi_syslog(tb, ip, f"%LINK-3-UPDOWN: Interface {cong}, changed state to {'down' if xuong else 'up'}", toi)
            ghi_syslog(tb, ip, f"%LINEPROTO-5-UPDOWN: Line protocol on Interface {cong}, changed state to "
                               f"{'down' if xuong else 'up'}", toi)
            ghi_syslog(tb, ip, f"%OSPF-5-ADJCHG: Process 1, Nbr {rid_ben_kia} on {cong} from "
                               + ("FULL to DOWN, Neighbor Down: Interface down or detached" if xuong
                                  else "LOADING to FULL, Loading Done"), toi)


def cam_may_la():
    """Thay POS1-5 bằng laptop lạ ở SW-CH1 Fa0/5: MAC khác MAC sticky -> violation shutdown (err-disabled)."""
    mac_dung = CAU_HINH["SW-CH1"]["sticky"].get("FastEthernet0/5", "?")
    mac_la = "0060.5C2B.9E41"
    TRANG_THAI["cong_khoa"] = True
    ghi("MANG", f"Laptop lạ (MAC {mac_la}) cắm vào SW-CH1 Fa0/5 – cổng chỉ nhận MAC sticky {mac_dung} của POS1-5")
    toi = TRANG_THAI["wan"] != "co-lap"
    ghi_syslog("SW-CH1", "192.168.10.2", "%PM-4-ERR_DISABLE: psecure-violation error detected on Fa0/5, "
                                         "putting Fa0/5 in err-disable state", toi)
    ghi_syslog("SW-CH1", "192.168.10.2", "%PORT_SECURITY-2-PSECURE_VIOLATION: Security violation occurred, caused by "
                                         f"MAC address {mac_la} on port FastEthernet0/5.", toi)
    ghi_syslog("SW-CH1", "192.168.10.2", "%LINK-5-CHANGED: Interface FastEthernet0/5, changed state to "
                                         "administratively down", toi)


def mo_lai_cong():
    TRANG_THAI["cong_khoa"] = False
    ghi("MANG", "Gỡ laptop lạ, cắm lại POS1-5; SW-CH1: interface fa0/5 -> shutdown -> no shutdown")
    ghi_syslog("SW-CH1", "192.168.10.2", "%LINK-3-UPDOWN: Interface FastEthernet0/5, changed state to up",
               TRANG_THAI["wan"] != "co-lap")


# ---------------------------------------------------------------- trạng thái cho giao diện
def doc_bang(duong_dan, cau_lenh):
    return DC.doc(duong_dan, cau_lenh)


def trang_thai():
    db_ch = PHIEN / "DuLieu" / "cuahang01.db"
    db_ts = PHIEN / "DuLieu" / "truso.db"
    thu_muc_sl = PHIEN / "DuLieu" / "SaoLuuTruSo"
    sao_luu = []
    if thu_muc_sl.is_dir():
        for f in sorted(thu_muc_sl.glob("truso_*.db")):
            dong = doc_bang(f, "SELECT COUNT(*) AS n FROM giao_dich")
            sao_luu.append({"ten": f.name, "so": dong[0]["n"] if dong else 0})
    return {
        "co_phien": PHIEN.exists(),
        "wan": TRANG_THAI["wan"],
        "tru_so_chay": TRU_SO.dang_chay(),
        "cua_hang": doc_bang(db_ch, "SELECT ma_gd, so_tien, trang_thai FROM giao_dich ORDER BY ma_gd"),
        "tru_so": doc_bang(db_ts, "SELECT ma_gd, so_tien FROM giao_dich ORDER BY ma_gd"),
        "sao_luu": sao_luu,
        "doi_chieu": DC.tinh_doi_chieu(db_ch, db_ts) if PHIEN.exists() else None,
        "nhat_ky": list(NHAT_KY)[-160:],
        "syslog": list(SYSLOG)[-60:],
        "cong_khoa": TRANG_THAI["cong_khoa"],
        "sticky_fa05": CAU_HINH["SW-CH1"]["sticky"].get("FastEthernet0/5"),
        "may": list(MAY),
    }


SO_TIEN = [50000, 75000, 120000, 35000, 200000, 90000, 45000, 150000]


def thuc_hien(viec, tham_so):
    if viec == "lam-moi":
        lam_moi()
        return
    if not PHIEN.exists():
        raise RuntimeError("Chưa có phiên demo – bấm “Làm mới phiên” trước.")
    if viec == "wan":
        muc = tham_so["muc"]
        if muc not in DUT_THEO_WAN:
            raise RuntimeError("Mức WAN không hợp lệ")
        syslog_doi_wan(TRANG_THAI["wan"], muc)
        TRANG_THAI["wan"] = muc
        ghi("MANG", {"binh-thuong": "WAN cửa hàng 1 bình thường (cả hai đường Serial up)",
                     "dut-chinh": "Đứt đường chính S0/0/0 – OSPF chuyển sang đường dự phòng qua R-CH2, "
                                  "cửa hàng vẫn gửi được",
                     "co-lap": "Cửa hàng 1 bị CÔ LẬP (S0/0/0 + S0/0/1 shutdown) – giả lập bằng dừng hq_receiver"}[muc])
        if muc == "co-lap":
            TRU_SO.tat()
        else:
            TRU_SO.bat()
    elif viec == "may-la":
        cam_may_la()
    elif viec == "mo-cong":
        mo_lai_cong()
    elif viec == "ban":
        so = max(1, min(int(tham_so.get("so", 5)), 20))
        danh_sach = [SO_TIEN[i % len(SO_TIEN)] for i in range(so)]
        chay("CUA HANG", "-c", f"from Script.store_agent import tao_giao_dich\nfor x in {danh_sach}: tao_giao_dich(x)",
             lenh_hien=f"-c \"from Script.store_agent import tao_giao_dich; [tao_giao_dich(x) for x in {danh_sach}]\"")
    elif viec == "gui":
        chay("CUA HANG", "-c", "from Script.store_agent import gui_giao_dich; gui_giao_dich()",
             lenh_hien="-c \"from Script.store_agent import gui_giao_dich; gui_giao_dich()\"")
    elif viec == "gui-lap":
        chay("TV3 KT3-b", "Script/kiem_tra_trung.py")
    elif viec == "sao-luu-ch":
        chay("TV3 SAO LUU", "Script/sao_luu.py")
    elif viec == "doi-chieu":
        chay("TV2 DOI CHIEU", "Script/doi_chieu.py")
    elif viec == "gui-bu":
        chay("TV2 GUI BU", "Script/doi_chieu.py", "gui-bu")
    elif viec == "sao-luu":
        chay("TV2 SAO LUU", "Script/sao_luu_tru_so.py", "sao-luu")
    elif viec == "xoa-thu":
        chay("TV2 SAO LUU", "Script/sao_luu_tru_so.py", "xoa-thu", "--chac-chan")
    elif viec == "khoi-phuc":
        them = ["--file", tham_so["file"]] if tham_so.get("file") else []
        chay("TV2 SAO LUU", "Script/sao_luu_tru_so.py", "khoi-phuc", *them)
    else:
        raise RuntimeError("Việc không hợp lệ: " + viec)


# ---------------------------------------------------------------- máy chủ web
class XuLy(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def tra(self, ma, noi_dung, kieu="application/json; charset=utf-8"):
        du_lieu = noi_dung if isinstance(noi_dung, bytes) else json.dumps(noi_dung, ensure_ascii=False).encode()
        self.send_response(ma)
        self.send_header("Content-Type", kieu)
        self.send_header("Content-Length", str(len(du_lieu)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(du_lieu)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self.tra(200, (GOC / "giao_dien.html").read_bytes(), "text/html; charset=utf-8")
        elif self.path == "/api/trang-thai":
            self.tra(200, trang_thai())
        else:
            self.tra(404, {"loi": "không có"})

    def do_POST(self):
        do_dai = int(self.headers.get("Content-Length", "0") or 0)
        tham_so = json.loads(self.rfile.read(do_dai) or b"{}") if do_dai else {}
        try:
            if self.path == "/api/acl":
                self.tra(200, tra_acl(tham_so["nguon"], tham_so["dich"], tham_so["dich_vu"]))
                return
            if not self.path.startswith("/api/viec/"):
                self.tra(404, {"loi": "không có"})
                return
            with KHOA:
                thuc_hien(self.path.rsplit("/", 1)[1], tham_so)
            self.tra(200, {"ok": True})
        except Exception as loi:  # báo lỗi ra giao diện thay vì làm sập máy chủ demo
            ghi("LOI", str(loi))
            self.tra(400, {"loi": str(loi)})


def main():
    may_chu = ThreadingHTTPServer((DIA_CHI_NGHE, CONG_WEB), XuLy)
    dia_chi = f"http://localhost:{CONG_WEB}"
    print("DEMO TICH HOP NHOM 02 dang chay:", dia_chi)
    print("Nhan Ctrl + C de dung (hq_receiver.py cung se dung).")
    if "--khong-mo" not in sys.argv:
        threading.Timer(0.8, lambda: webbrowser.open(dia_chi)).start()
    try:
        may_chu.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        TRU_SO.tat()
        may_chu.server_close()
        print("Da dung demo.")


if __name__ == "__main__":
    main()
