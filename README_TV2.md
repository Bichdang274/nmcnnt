# Phần thực hiện của TV2 – Lê Minh Đạo

> Đọc nhanh toàn bộ bài và phần TV2: [`TongQuan_Nhom02_PhanTV2.md`](TongQuan_Nhom02_PhanTV2.md).
> Demo tích hợp cả nhóm: thư mục [`DemoTichHop/`](DemoTichHop/README.md).

## 1. Nhiệm vụ
LAN, máy chủ, bảo mật (phân quyền, ACL, quản trị, cổng switch) và sao lưu. Kiêm vai trò SV2 (phần LAN, máy chủ,
phân quyền) và phần đối chiếu dữ liệu sau sự cố của SV4.

Nhận từ TV1: `Nhom02_TV1.pkt` (topology, WAN, OSPF, IP máy trạm, dịch vụ máy chủ – chưa có ACL).

## 2. Công cụ
- Cisco Packet Tracer (file `.pkt` lưu ở định dạng 7.3.1, mở được bằng bản mới hơn).
- Python 3 + SQLite (`sqlite3`), chỉ thư viện chuẩn.

## 3. Các file
| File | Nội dung |
|---|---|
| `Nhom02_v2.pkt` | File TV1 + phần TV2: ACL 4 router, access-class 8 thiết bị, **SSH thay Telnet**, **port security** 4 switch, **NTP + Syslog** về Server-Backup (= bản final) |
| `Script_TV2/R-xx_ACL.txt`, `SW-xx_VTY.txt` | Dán vào CLI: ACL, áp vào G0/0, access-class |
| `Script_TV2/R-xx_SSH_NTP_SYSLOG.txt` | Dán vào CLI 4 router: SSH, NTP, Syslog |
| `Script_TV2/SW-xx_SSH_PORTSEC.txt` | Dán vào CLI 4 switch: SSH, port security, tắt cổng không dùng, NTP, Syslog |
| `Script_TV2/KiemThu_TV2.txt` | Lệnh kiểm thử SEC-1 – SEC-4, LOG-1, quyền PC-Admin, sao lưu TFTP qua ACL |
| `Script_TV2/SaoLuu_DoiChieu_CSDL.txt` | Lệnh BK-1 và đối chiếu dữ liệu |
| `Script/sao_luu_tru_so.py` | Sao lưu / xóa thử / khôi phục CSDL trụ sở `DuLieu/truso.db` (CSDL của TV3), giữ 7 bản |
| `Script/doi_chieu.py` | Đối chiếu `cuahang01.db` ↔ `truso.db` (mã trùng, ACKED mà trụ sở thiếu), gửi bù |
| `CauHinh_TV2/` | running-config 8 thiết bị (Phụ lục A) |
| `CSDL/schema_tru_so.sql`, `truy_van_doi_chieu.sql` | CSDL trung tâm, truy vấn Q1–Q5 |
| `MinhChung_TV2/` | Log BK-1, KT3 (đối chiếu), KT3-b, khôi phục từ bản sao lưu cũ |
| `TV2_HuongDan_TungBuoc.docx` | Hướng dẫn từ file TV1 đến `Nhom02_v2.pkt` (mục L: SSH, port security, NTP + Syslog) |
| `cong_nghe_nen_tang_TV2.docx` | Báo cáo nhóm (bản TV1) + mục TV2: 2.5, 2.6, 3.2 (3.2.5–3.2.7 mới), 3.4, 3.5, 3.6, mục 4 (SEC-1 – SEC-4, LOG-1, BK-1), 5.1, Phụ lục A |
| `Lop_Nhom02_DeTai02_B24DCCC___BaoCaoCaNhan_LeMinhDao.docx` | Phiếu đóng góp cá nhân TV2 |
| `TV2_OnTap_KiemTraCheo.html` | Trang ôn tập, câu hỏi kiểm tra chéo |
| `DemoTichHop/` | Demo xuyên suốt TV1 → TV2 → TV3 (sơ đồ kiểu Packet Tracer, chạy script thật của TV3) |

## 4. Phân quyền và bảo mật
- `CHx_LAN_IN` (**in** trên G0/0 router cửa hàng): POS chỉ tới Server-TT bằng HTTP/HTTPS và ping; không tới
  Server-Backup, không sang cửa hàng khác.
- `HQ_SERVERS_OUT` (**out** trên G0/0 R-HQ): lớp bảo vệ thứ hai cho vùng máy chủ.
- Quản trị: `access-class 10` (chỉ PC-Admin 192.168.0.20) + `transport input ssh`, `login local` → chỉ SSH,
  Telnet bị từ chối.
- Port security trên cổng POS (1 MAC sticky/cổng, vi phạm → err-disabled), bpduguard, cổng không dùng shutdown.
- NTP + Syslog: 8 thiết bị lấy giờ từ Server-Backup, gửi nhật ký sự cố về đó. ACL không phải sửa (UDP tới .11
  đã cho phép).

**Mở `Nhom02_v2.pkt` lần đầu:** trên 8 thiết bị chạy `crypto key generate rsa general-keys modulus 1024` rồi
`ip ssh version 2` (Packet Tracer không lưu sẵn khóa RSA trong file).

## 5. Cách chạy kiểm thử
1. Mở `Nhom02_v2.pkt`, chờ OSPF hội tụ (hoặc Fast Forward Time), tạo khóa RSA như trên.
2. Chạy lệnh trong `Script_TV2/KiemThu_TV2.txt`: SEC-1, SEC-2 (ACL), SEC-3 (SSH), SEC-4 (cắm laptop lạ),
   LOG-1 (NTP, Syslog).
3. Dữ liệu (thư mục gốc repo, sau khi gộp với nhánh tv3):
   `python Script/sao_luu_tru_so.py sao-luu | xoa-thu --chac-chan | khoi-phuc`, `python Script/doi_chieu.py`.

## 6. Trạng thái
- Đã xong: cấu hình (file `.pkt`, CLI, running-config), script sao lưu/đối chiếu trên CSDL của TV3, các mục báo
  cáo TV2, demo tích hợp.
- Chưa xong: kết quả và ảnh SEC-1 – SEC-4, LOG-1 trong Packet Tracer (ô `[...]` trong báo cáo).
- Log `MinhChung_TV2/` chạy bằng bộ script thử nghiệm của nhóm; nhóm thống nhất một bộ script để số liệu báo cáo
  khớp nhau.
