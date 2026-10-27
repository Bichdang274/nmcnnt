# Phần thực hiện của TV2 – Lê Minh Đạo

## 1. Nhiệm vụ
LAN, máy chủ, bảo mật (phân quyền, ACL) và sao lưu. Kiêm vai trò SV2 (phần LAN, máy chủ, phân quyền)
và phần đối chiếu dữ liệu sau sự cố của SV4.

Nhận từ TV1: `Nhom02_TV1.pkt` (topology, WAN, OSPF, IP máy trạm, dịch vụ máy chủ – chưa có ACL).

## 2. Công cụ
- Cisco Packet Tracer (file `.pkt` lưu ở định dạng 7.3.1, mở được bằng bản mới hơn).
- SQLite (`sqlite3`) cho schema và truy vấn đối chiếu.

## 3. Các file
| File | Nội dung |
|---|---|
| `Nhom02_v2.pkt` | File của TV1 + phân quyền TV2: ACL trên 4 router, access-class trên 8 thiết bị (= bản final) |
| `Script_TV2/R-xx_ACL.txt` | Dán vào CLI 4 router: ACL, áp vào G0/0, giới hạn Telnet |
| `Script_TV2/SW-xx_VTY.txt` | Dán vào CLI 4 switch: giới hạn Telnet |
| `Script_TV2/KiemThu_TV2.txt` | Lệnh kiểm thử SEC-1, SEC-2, quyền PC-Admin, sao lưu TFTP qua ACL |
| `Script_TV2/SaoLuu_DoiChieu_CSDL.txt` | Lệnh BK-1 và đối chiếu dữ liệu |
| `CauHinh_TV2/` | running-config 8 thiết bị (Phụ lục A) |
| `CSDL/schema_tru_so.sql` | CSDL trung tâm, khóa chính `ma_gd` chặn ghi trùng |
| `CSDL/truy_van_doi_chieu.sql` | Q1–Q5: đếm theo cửa hàng, tìm mã trùng, tìm giao dịch thiếu |
| `MinhChung_TV2/` | Log BK-1, KT3 (đối chiếu), KT3-b, khôi phục từ bản sao lưu cũ |
| `TV2_HuongDan_TungBuoc.docx` | Hướng dẫn từ file TV1 đến `Nhom02_v2.pkt`, kiểm thử, sao lưu |
| `cong_nghe_nen_tang_TV2.docx` | Báo cáo nhóm (bản TV1) + mục TV2: 2.5, 2.6, 3.2, 3.4, 3.5 (đối chiếu), 3.6, mục 4 (SEC-1, SEC-2, BK-1), 5.1 |
| `Lop_Nhom02_DeTai02_B24DCCC___BaoCaoCaNhan_LeMinhDao.docx` | Phiếu đóng góp cá nhân TV2 |

## 4. Phân quyền
- `CHx_LAN_IN` áp chiều **in** trên G0/0 của R-CH1/2/3 (chặn gần nguồn): POS chỉ được tới Server-TT
  (192.168.0.10) qua HTTP/HTTPS và ping, không tới Server-Backup và cửa hàng khác.
- `HQ_SERVERS_OUT` áp chiều **out** trên G0/0 của R-HQ: bảo vệ vùng máy chủ trụ sở, cho phép sao lưu
  cấu hình thiết bị qua TFTP tới Server-Backup (192.168.0.11).
- `access-list 10` + `access-class 10 in` trên VTY: chỉ PC-Admin (192.168.0.20) được Telnet.

## 5. Cách chạy kiểm thử
1. Mở `Nhom02_v2.pkt`, chờ OSPF hội tụ (hoặc Fast Forward Time).
2. Chạy lệnh trong `Script_TV2/KiemThu_TV2.txt` (SEC-1: truy cập được phép; SEC-2: truy cập bị chặn,
   `show access-lists` bộ đếm dòng deny tăng).
3. Đối chiếu dữ liệu: `sqlite3 truso.db < CSDL/truy_van_doi_chieu.sql` (truy vấn mã trùng phải rỗng).

## 6. Trạng thái
- Đã xong: cấu hình phân quyền, file `.pkt`, schema và truy vấn đối chiếu, lịch sao lưu, các mục báo cáo TV2.
- Chưa xong: kết quả và ảnh SEC-1, SEC-2, `show access-lists` (ô `[...]` trong báo cáo).
- Log trong `MinhChung_TV2/` được chạy bằng bộ script thử nghiệm của nhóm; sẽ chạy lại BK-1 và đối chiếu
  trên CSDL của TV3 (nhánh `tv3`) để số liệu báo cáo thống nhất.
