# TV2 (Lê Minh Đạo) – những gì đã làm, để báo nhóm

Cập nhật 03/11/2026 · Nhánh GitHub: `tv2` (repo Bichdang274/nmcnnt)
Demo trực tuyến: https://fimbrillate-uncraven-antonietta.ngrok-free.dev (lần đầu mở bấm **Visit Site**)

---

## 1. Ba phần bảo mật mới thêm (đã xong, đã đẩy lên `tv2`)

| Phần | Làm gì | Vì sao | Kiểm thử |
|---|---|---|---|
| **SSH thay Telnet** | 8 thiết bị: tài khoản `admin`/`cisco`, `login local`, `transport input ssh`, giữ `access-class 10` (chỉ PC-Admin) | Khắc phục hạn chế báo cáo tự nêu ở mục 3.1.5: Telnet gửi mật khẩu dạng rõ | **SEC-3**: PC-Admin SSH vào được, Telnet bị từ chối, POS bị từ chối |
| **NTP + Syslog** | 8 thiết bị lấy giờ và gửi nhật ký về Server-Backup (đã bật NTP, SYSLOG trên máy này). Không phải sửa ACL | Giờ đứt/nối WAN được ghi tự động, không phải ghi tay `show clock`. Giúp TV1, TV3 đối chiếu thời điểm KT2, KT3 | **LOG-1**: `show ntp status` đồng bộ; SYSLOG có sự kiện Serial down/up |
| **Port security** | 4 switch: mỗi cổng POS chỉ nhận 1 MAC (sticky, ghi sẵn MAC 18 máy), vi phạm thì tắt cổng; portfast, bpduguard; tắt cổng không dùng | Máy POS đặt ngoài quầy, ai cũng có thể cắm laptop lạ vào | **SEC-4**: cắm laptop lạ thì cổng Secure-shutdown |

**Ảnh hưởng tới thành viên khác:**
- Script dữ liệu của TV3 – Đức (HTTP tới Server-TT) **không bị ảnh hưởng**.
- TV3 (Đức) **đừng thêm hoặc đổi máy vào switch** trong Packet Tracer, vì port security sẽ khóa cổng đó.
- Bản v1 của TV1 (Bích) giữ nguyên.

**Mở `Nhom02_v2.pkt` lần đầu phải làm thêm 1 bước:** trên 8 thiết bị chạy
`crypto key generate rsa general-keys modulus 1024`, rồi `ip ssh version 2`, rồi `write memory`.
Packet Tracer không lưu khóa RSA trong file.

## 2. Phần việc TV2 theo phân công (đã xong)

| Hạng mục | Kết quả |
|---|---|
| Bảng phân quyền (mục 2.5) | 9 quy tắc, triển khai 4 lớp: ACL cửa hàng, ACL vùng máy chủ, SSH + access-class, port security |
| ACL | `CH1/2/3_LAN_IN` (in, router cửa hàng), `HQ_SERVERS_OUT` (out, R-HQ). POS chỉ vào được Server-TT; máy sao lưu và cửa hàng khác bị chặn |
| Máy chủ | Server-TT: HTTP/HTTPS. Server-Backup: TFTP, FTP, NTP, SYSLOG |
| Lịch sao lưu (mục 2.6) | CSDL trụ sở cuối ngày, giữ 7 bản; kho cửa hàng cuối ca; cấu hình thiết bị qua TFTP. Tự động hóa bằng cron / Task Scheduler |
| CSDL trụ sở, chống trùng | Khóa chính `ma_gd`; gửi lại bản đã có thì không ghi thêm nhưng vẫn ACK |
| Sao lưu – khôi phục (BK-1) | **Đạt**: 45 → 0 → 45 bản ghi, 0 mã trùng |
| Đối chiếu sau sự cố WAN (KT3) | Trụ sở 12 → 20 (+8, 2 bản trùng bị bỏ qua), 0 mã trùng |
| Khôi phục từ bản cũ | Phát hiện thiếu 2 giao dịch, gửi bù xong đủ, 0 trùng |
| Script mới chạy trên CSDL của TV3 | `Script/sao_luu_tru_so.py` (sao lưu, xóa thử, khôi phục `truso.db`), `Script/doi_chieu.py` (đối chiếu, gửi bù). Tên file không trùng với file của TV3 |

## 3. Tài liệu (đã cập nhật)

- **Báo cáo nhóm** `cong_nghe_nen_tang_TV2.docx`:
  - mục 2.5, 2.6, 3.2 (thêm 3.2.5 SSH, 3.2.6 Port security, 3.2.7 NTP + Syslog), 3.4, 3.5 (đối chiếu), 3.6;
  - mục 4: thêm SEC-3, SEC-4, LOG-1;
  - mục 5.1; **Phụ lục A** lấy theo cấu hình mới;
  - mục 3.4 có link demo và lệnh cron.
- **Báo cáo cá nhân** TV2, **hướng dẫn từng bước** (mục L mới), **script CLI** cho 8 thiết bị, **lệnh kiểm thử** `KiemThu_TV2.txt`.
- `TongQuan_Nhom02_PhanTV2.md`: giải thích cả bài từ đầu, phần TV2 chi tiết.
- `TV2_OnTap_KiemTraCheo.html`: 25 câu hỏi kiểm tra chéo, trắc nghiệm tự chấm.

## 4. Demo tích hợp cả nhóm (web, chạy trên server của TV2)

Một trang đi xuyên suốt 15 bước theo thứ tự dựng hệ thống. Packet Tracer để bên trái, trang demo bên phải.

| Bước | Ai | Nội dung |
|---|---|---|
| 1–3 | TV1 | Nối dây (Serial DCE/DTE), đặt IP, OSPF, KT1 |
| 4–7 | TV2 | ACL, SSH, port security (nút **cắm laptop lạ**), NTP + Syslog (bảng SYSLOG tự ghi sự kiện) |
| 8 | TV3 | Bán hàng, gửi về trụ sở (PENDING → SENT → ACKED) |
| 9–10 | TV1 + TV3 | Đứt đường chính → OSPF đi dự phòng; cửa hàng bị cô lập (KT2) |
| 11–12 | TV3 | Gửi lại (KT3), gửi lặp không trùng (KT3-b) |
| 13–14 | TV2 | Sao lưu – xóa – khôi phục (BK-1), **lịch sao lưu tự động**, khôi phục bản cũ và gửi bù |

- **Sơ đồ kiểu Packet Tracer, hiện dần theo bước:** 4 router, 4 switch, 15 POS, máy chủ, cáp, tên cổng, IP, OSPF, khiên
  ACL, khóa SSH, port security, NTP.
- **Gói tin chạy trên dây** theo đúng đường OSPF. Bị chặn thì hiện ✕ tại router chặn, kèm dòng ACL.
- Các nút dữ liệu chạy **script thật của TV3** cùng 2 script của TV2.
- Port security và Syslog trên web là **mô phỏng theo cấu hình**. Bằng chứng thật vẫn phải lấy trong Packet Tracer.
- Cả nhóm **dùng chung một phiên**: khi tập, để một người bấm.
- Server chỉ tốn khoảng 50 MB RAM và tự bật lại khi khởi động lại.

## 5. Còn lại – cần nhóm phối hợp

- [ ] **TV2:** tạo khóa RSA, chạy SEC-1 – SEC-4, LOG-1 trong Packet Tracer, chụp ảnh, điền các ô `[...]` trong báo cáo.
- [ ] **Cả nhóm:** thống nhất **một bộ script** (của TV3 cộng 2 script TV2) và chạy lại số liệu BK-1 và đối chiếu,
  để báo cáo chỉ có một bộ số.
- [ ] **TV3 (Đức):** nếu cần chụp lại ảnh KT2, KT3 thì dùng `Nhom02_v2.pkt` mới. Ảnh cũ vẫn hợp lệ vì phần WAN không đổi.
- [ ] **TV1 (Bích):** sửa tên trong báo cáo cá nhân (đang ghi Lê Minh Đạo). Ảnh KT1 nên chụp lại trên bản v2.
- [ ] **Video:** quay theo 15 bước của trang demo. Mỗi người trình bày phần của mình.
