# Nhóm 02 – Hạ tầng CNTT cho chuỗi cửa hàng bán lẻ

**Tổng quan cả nhóm, chi tiết phần Thành viên 2 (Lê Minh Đạo)**

RIPT1304 · Đề 02. Tài liệu này tóm tắt cả bài từ đầu: đề bài, hệ thống, ai làm gì. Phần TV2 được viết chi tiết để tự
học và để kiểm tra chéo trong nhóm.

---

## 1. Đề bài yêu cầu gì

Chuỗi bán lẻ có **1 trụ sở** và **3 cửa hàng**, mỗi cửa hàng **5 máy bán hàng (POS)**. Cần thiết kế hạ tầng sao cho:

1. Các địa điểm kết nối được với nhau. Hai phương án kết nối liên điểm được đem ra so sánh.
2. Cửa hàng vẫn bán được khi **mất kết nối WAN**: giao dịch lưu tại chỗ, có mạng lại thì gửi về.
3. **Phân quyền từng cửa hàng, lịch sao lưu, và cách xử lý dữ liệu trùng khi gửi lại.** Đề ghi rõ: *không yêu cầu
   viết phần mềm bán hàng*.
4. Kiểm thử: **KT1** cả 3 cửa hàng dùng được dịch vụ trung tâm; **KT2** mất WAN thì giao dịch được lưu lại; **KT3**
   có mạng lại thì gửi đủ, không trùng.

### Yêu cầu số 3 có demo trên Packet Tracer được không?

| Phần | Làm trên Packet Tracer? | Nhóm làm thế nào |
|---|---|---|
| Phân quyền từng cửa hàng | **Được** | ACL trên router, SSH và `access-class` cho quản trị, port security trên switch. Thấy được bằng ping, `show access-lists`, chế độ Simulation |
| Lịch sao lưu | **Một phần** | Sao lưu **cấu hình thiết bị** bằng TFTP lên Server-Backup làm được trong Packet Tracer. Sao lưu **CSDL giao dịch** thì Packet Tracer không có CSDL thật, nên làm bằng script Python + SQLite |
| Xử lý dữ liệu trùng | **Không** | Packet Tracer không chạy được CSDL, nên làm bằng script: khóa chính `ma_gd` và trụ sở vẫn trả xác nhận (ACK) cho bản trùng |

Vì vậy bài có **hai nửa chạy song song**:
- **Packet Tracer** chứng minh mạng: kết nối, định tuyến, phân quyền.
- **Script** chứng minh dữ liệu: lưu tạm, gửi lại, chống trùng, sao lưu.

Trang demo tích hợp nối hai nửa này thành một kịch bản liền mạch (mục 6).

---

## 2. Hệ thống nhìn từ trên xuống

```
                    ┌──────────── TRỤ SỞ 192.168.0.0/24 ─────────────┐
                    │ Server-TT .10   Server-Backup .11   PC-Admin .20│
                    │          └────── SW-HQ .2 ──────┘               │
                    │                  R-HQ .1                         │
                    └─── S0/0/0 ───── S0/0/1 ───── S0/1/0 ────────────┘
                  10.0.1.0/30 │   10.0.2.0/30 │   10.0.3.0/30 │
        ┌─ CỬA HÀNG 1 ─┐      │  ┌─ CỬA HÀNG 2 ┴┐   ┌─ CỬA HÀNG 3 ┴┐
        │ R-CH1 ═══════╪══════╪══╪═ R-CH2       │   │ R-CH3        │
        │  dự phòng 10.0.12.0/30 (cost 100)     │   │              │
        │ SW-CH1       │         │ SW-CH2       │   │ SW-CH3       │
        │ POS1-1…1-5   │         │ POS2-1…2-5   │   │ POS3-1…3-5   │
        └ 192.168.10.0 ┘         └ 192.168.20.0 ┘   └ 192.168.30.0 ┘
```

- **Thiết bị:** 4 router Cisco 2911 (gắn module HWIC-2T để có cổng Serial), 4 switch 2960, 15 POS, 2 máy chủ, 1 PC
  quản trị.
- **Phương án PA2:** đường thuê Serial hình sao về trụ sở, thêm đường dự phòng CH1–CH2. Định tuyến **OSPF** (area 0).
  Đứt đường chính thì OSPF tự đi đường dự phòng.
- **IP:** cửa hàng N dùng `192.168.N0.0/24`. Quy ước: `.1` là gateway, `.2` là switch, POS từ `.11` đến `.15`. Các
  đường WAN dùng dải `/30`.
- **Dữ liệu:** mỗi cửa hàng có **kho lưu tạm** (SQLite); trụ sở có **CSDL trung tâm** `truso.db`. Giao dịch đi theo
  trạng thái PENDING → SENT → ACKED.

---

## 3. Phân công 3 thành viên

| | TV1 | **TV2 (Lê Minh Đạo)** | TV3 (Phan Hải Đức) |
|---|---|---|---|
| Phụ trách | WAN, định tuyến, đặc tả đồng bộ | **LAN, máy chủ, bảo mật, sao lưu, đối chiếu dữ liệu** | Lưu tạm, gửi lại, chống trùng |
| Sản phẩm chính | `Nhom02_TV1.pkt` (topology, Serial, OSPF, IP, mật khẩu cơ bản), so sánh PA1/PA2 | `Nhom02_v2.pkt` = file TV1 + phân quyền và bảo mật, CSDL trụ sở, lịch sao lưu, script sao lưu/đối chiếu | `store_agent.py`, `hq_receiver.py`, `kiem_tra_trung.py`, `sao_luu.py` (kho cửa hàng) |
| Kiểm thử | KT1, WAN-1a, WAN-1b | **SEC-1 – SEC-4, LOG-1, BK-1, đối chiếu KT3** | KT2, KT3, KT3-b |
| Mục báo cáo | 1.3, 2.1–2.4, 3.1, 3.5 (mạng), 5.2, Phụ lục A | **2.5, 2.6, 3.2, 3.4, 3.5 (đối chiếu), 5.1** | 2.7, 3.3 |

**Thứ tự bàn giao:**
1. TV1 giao `Nhom02_TV1.pkt` cho TV2.
2. TV2 thêm phân quyền và bảo mật, ra `Nhom02_v2.pkt` (cũng là bản final).
3. TV2 gửi bản này cho TV1 chạy lại KT1, và cho TV3 làm phần mạng của KT2, KT3.
4. TV3 chạy script gửi lại; TV2 đối chiếu dữ liệu phía trụ sở.

---

## 4. Phần của TV2 – chi tiết

### 4.1. Bảng phân quyền (Bảng 2.5)

| Ai | Tới đâu | Dịch vụ | Quyết định |
|---|---|---|---|
| Máy POS 3 cửa hàng | Server-TT (máy chủ trung tâm) | Web HTTP/HTTPS, ping | **Cho** |
| Máy POS | Server-Backup | Mọi thứ | **Chặn** |
| Cửa hàng X | Cửa hàng Y | Mọi thứ | **Chặn** |
| PC-Admin | Mọi thiết bị | Mọi thứ | **Cho** |
| Vào cấu hình router/switch | — | **SSH** (Telnet bị từ chối) | **Chỉ PC-Admin** |
| Router, switch | Server-Backup | TFTP, NTP, Syslog (UDP) | **Cho** |
| Máy lạ cắm vào cổng switch cửa hàng | — | Mọi thứ | **Chặn** (port security) |

Bảng được hiện thực bằng **4 lớp bảo vệ**:
- ACL ở cửa hàng;
- ACL trước vùng máy chủ;
- SSH kèm `access-class` cho quản trị;
- port security ở cổng switch.

### 4.2. ACL – "bảo vệ đứng ở cửa"

ACL giống bảo vệ cầm danh sách, **đọc từ trên xuống, khớp dòng nào thì dừng ở dòng đó**. Không có tên trong danh sách
thì không được qua.

**Lớp 1 – `CH1_LAN_IN`**, áp chiều `in` trên G0/0 của R-CH1 (R-CH2, R-CH3 tương tự):

| Dòng | Lệnh | Ý nghĩa |
|---|---|---|
| 10–30 | `permit tcp … host 192.168.0.10 eq www / 443`, `permit icmp … host 192.168.0.10` | POS vào web, ping máy chủ trung tâm |
| 40 | `permit icmp … host 192.168.10.1` | Ping gateway của chính cửa hàng (để thử lúc mất WAN) |
| 50 | `permit icmp … host 192.168.0.20 echo-reply` | Chỉ cho **gói trả lời** ping về PC-Admin |
| 60 | `permit tcp host 192.168.10.2 host 192.168.0.20 established` | Gói trả lời phiên SSH từ switch về PC-Admin |
| 70 | `permit udp host 192.168.10.2 host 192.168.0.11` | Switch gửi sao lưu cấu hình, NTP, Syslog. **Phải đứng trước dòng 80**, vì `.2` cũng thuộc dải `.10.x` |
| 80 | `deny ip 192.168.10.0 0.0.0.255 host 192.168.0.11` | Chặn POS vào máy sao lưu |
| 90–100 | `deny ip … 192.168.20.0 / 30.0 …` | Chặn sang cửa hàng 2, 3 |
| 110 | `deny ip any any` | Chặn phần còn lại. Viết ra để `show access-lists` đếm được số gói bị chặn |

**Lớp 2 – `HQ_SERVERS_OUT`**, áp chiều `out` trên G0/0 của R-HQ: chỉ cho cửa hàng vào Server-TT bằng web và ping. Lớp
này bảo vệ máy chủ ngay cả khi ACL ở một cửa hàng bị cấu hình sai.

**Vì sao không đặt hết ở trụ sở?** Vì có **đường dự phòng CH1–CH2**: gói từ CH1 sang CH2 đi thẳng, không qua trụ sở.
Đặt ACL ở cửa hàng thì chặn được ngay tại nguồn và không tốn băng thông WAN.

Không ghi `eq tftp` vì TFTP chỉ dùng cổng 69 cho gói đầu, phần dữ liệu đi trên cổng tạm.

### 4.3. SSH thay Telnet – "khóa cửa phòng máy"

```
username admin privilege 15 secret cisco
ip domain-name nhom02.local
crypto key generate rsa general-keys modulus 1024
ip ssh version 2
access-list 10 permit host 192.168.0.20
line vty 0 4                 (switch: 0 15)
 access-class 10 in          ← AI được vào: chỉ PC-Admin
 login local                 ← đăng nhập bằng tài khoản riêng
 transport input ssh         ← VÀO BẰNG GÌ: chỉ SSH
```

- Telnet gửi mật khẩu dạng chữ thường trên dây, ai bắt được gói là đọc được. SSH mã hóa cả phiên. Báo cáo đã tự nêu
  hạn chế này ở mục 3.1.5; TV2 khắc phục.
- **Lưu ý:** file `.pkt` không lưu sẵn khóa RSA. Mở file lần đầu phải chạy `crypto key generate rsa general-keys modulus 1024`
  và `ip ssh version 2` trên từng thiết bị.
- Thử: PC-Admin chạy `ssh -l admin 192.168.10.2` thì **vào được**. `telnet 192.168.10.2` thì **bị từ chối**. POS chạy
  `ssh` thì **bị từ chối**.

### 4.4. Port security – "ổ cắm chỉ nhận đúng máy của nó"

Mỗi card mạng có một **địa chỉ MAC** riêng, giống số CCCD của máy. Switch nhớ MAC của máy POS ở mỗi cổng; **máy khác
cắm vào thì cổng tự tắt** (err-disabled).

```
interface range fa0/1 - 5
 switchport mode access
 switchport port-security
 switchport port-security maximum 1
 switchport port-security mac-address sticky      ← tự nhớ MAC máy POS
 switchport port-security violation shutdown      ← máy lạ → tắt cổng
 spanning-tree portfast
 spanning-tree bpduguard enable                   ← cắm switch lạ cũng bị tắt
interface range fa0/6 - 24
 shutdown                                         ← cổng không dùng
```

- Đúng rủi ro của cửa hàng bán lẻ: máy POS đặt ngoài quầy, ai cũng có thể rút dây cắm laptop vào. ACL lọc theo IP
  không chặn được, vì laptop có thể tự đặt IP giống POS.
- `Nhom02_v2.pkt` đã ghi sẵn MAC sticky của 18 máy trạm.
- Thử: thay POS1-5 bằng một laptop ở Fa0/5 rồi cho laptop ping. Ping thất bại và `show port-security interface fa0/5`
  báo **Secure-shutdown**.
- Mở lại cổng: gỡ laptop, cắm lại POS, chạy `shutdown` rồi `no shutdown` trên cổng đó.

### 4.5. NTP + Syslog – "đồng hồ chung, sổ nhật ký chung"

```
service timestamps log datetime msec
ntp server 192.168.0.11
logging 192.168.0.11
```

- **NTP:** cả 8 thiết bị lấy giờ từ Server-Backup nên cùng một giờ.
- **Syslog:** khi cổng đứt hoặc nối lại, neighbor OSPF thay đổi, port security khóa cổng…, thiết bị **tự gửi một dòng
  kèm giờ** về Server-Backup (Services → SYSLOG). Không cần ghi tay `show clock`.
- **Không phải sửa ACL:** UDP tới `.11` đã được cho phép từ trước, ở dòng dành cho TFTP.
- **Nói đúng giới hạn:**
  - Khi cửa hàng 1 bị cô lập hẳn, R-CH1 không gửi Syslog được vì mất đường. Bù lại, R-HQ và R-CH2 ở đầu bên kia vẫn
    ghi sự kiện mất neighbor 2.2.2.2.
  - NTP chỉ đồng bộ giờ các thiết bị trong Packet Tracer với nhau. Script Python vẫn chạy theo giờ của máy tính.

### 4.6. Máy chủ

| Máy | Bật | Tắt |
|---|---|---|
| Server-TT 192.168.0.10 | HTTP, HTTPS (nhận giao dịch) | TFTP, FTP, DNS, DHCP, Email |
| Server-Backup 192.168.0.11 | TFTP, FTP, **NTP, SYSLOG** | HTTP, HTTPS |

### 4.7. Lịch sao lưu (Bảng 2.6)

| Cái gì | Khi nào | Giữ | Ai |
|---|---|---|---|
| CSDL giao dịch trụ sở | Cuối ngày và trước mỗi lần đồng bộ lớn | 7 bản | TV2 |
| Kho lưu tạm cửa hàng | Cuối ca | Đến khi mọi giao dịch ACKED | TV3 |
| Cấu hình router/switch | Sau mỗi lần sửa (TFTP lên Server-Backup) | Bản mới nhất và bản trước | TV1 |

- **Mất dữ liệu tối đa (RPO):** theo lịch là 1 ngày. Nhưng các giao dịch ghi sau lần sao lưu **vẫn còn trong kho cửa
  hàng**, nên gửi bù được. Mức mất thực tế bằng 0 nếu kho cửa hàng còn.
- **Khôi phục:** chọn bản sao lưu → chép đè bằng API backup của SQLite (an toàn cả khi trụ sở đang nhận) → đối chiếu →
  thiếu thì gửi bù.

### 4.8. CSDL trụ sở, chống trùng và đối chiếu

- Bảng `giao_dich` dùng **mã giao dịch `ma_gd` làm khóa chính**, ví dụ `CH01-POS01-20261103-000001`. Mã có cả cửa hàng,
  máy và số thứ tự trong ngày nên không bao giờ trùng.
- Gửi lại một mã đã có: trụ sở **không ghi thêm** (`DA_TON_TAI`) nhưng **vẫn trả ACK**. Nếu không ACK, cửa hàng sẽ gửi
  lại mãi.
- **Đối chiếu** dùng các truy vấn sau:
  - đếm số giao dịch hai bên;
  - tìm mã trùng (`GROUP BY ma_gd HAVING COUNT(*) > 1`, phải rỗng);
  - đếm giao dịch **đã ACKED mà trụ sở thiếu** (phải bằng 0).

  Nếu số này lớn hơn 0 thì đó là mất dữ liệu thật, vì cửa hàng sẽ không tự gửi lại giao dịch đã ACKED.

**Kết quả đã chạy:**

| Ca | Kết quả |
|---|---|
| BK-1: sao lưu, xóa thử, khôi phục | **45 → 0 → 45** bản ghi, 0 mã trùng (`MC-BK1.log`) |
| Đối chiếu KT3 | Trụ sở **12 → 20** (+8 mới; 2 bản mất ACK nhận là trùng và bỏ qua), 0 mã trùng. **12 + 8 = 20, không phải 22** |
| Khôi phục từ bản cũ | Trụ sở 8 → 6, script cảnh báo thiếu 2; gửi bù xong đủ 8, 0 trùng (`MC-TV2-KhoiPhucCu.log`) |

Các số trên chạy bằng bộ script thử nghiệm trong `demo-cisco/Script/`. Trang demo tích hợp thì chạy **script thật của
TV3** cộng 2 script của TV2 (`sao_luu_tru_so.py`, `doi_chieu.py`) trên cùng CSDL `truso.db` của TV3. Nhóm nên thống
nhất dùng một bộ để báo cáo có một bộ số liệu.

### 4.9. Kiểm thử của TV2

| Mã | Kiểm tra gì | Trạng thái |
|---|---|---|
| SEC-1 | POS 3 cửa hàng vẫn vào được Server-TT sau khi có ACL | ☐ chạy trong Packet Tracer, chụp `MC-TV2-SEC1` |
| SEC-2 | POS vào máy sao lưu hoặc cửa hàng khác: bị chặn, bộ đếm ACL tăng | ☐ `MC-TV2-SEC2`, `MC-TV2-ACL` |
| SEC-3 | PC-Admin SSH được; Telnet bị từ chối; POS bị từ chối | ☐ `MC-TV2-SSH` |
| SEC-4 | Cắm laptop lạ thì cổng Secure-shutdown | ☐ `MC-TV2-PORTSEC` |
| LOG-1 | `show ntp status` đồng bộ; SYSLOG có sự kiện WAN kèm giờ | ☐ `MC-TV2-SYSLOG` |
| BK-1 | Sao lưu – xóa thử – khôi phục CSDL trụ sở | ✅ Đạt |

Lệnh chi tiết của từng ca nằm trong `Script_TV2/KiemThu_TV2.txt`.

### 4.10. File của TV2

| File | Nội dung |
|---|---|
| `Nhom02_v2.pkt` | File TV1 + ACL, SSH, port security, NTP, Syslog (= `Nhom02_final.pkt`) |
| `Script_TV2/*_ACL.txt`, `*_VTY.txt` | ACL và `access-class`, dán vào CLI |
| `Script_TV2/*_SSH_*.txt` | SSH, NTP, Syslog (router); thêm port security (switch) |
| `Script_TV2/KiemThu_TV2.txt` | Lệnh kiểm thử SEC-1 – SEC-4, LOG-1 |
| `CauHinh_TV2/` | running-config 8 thiết bị |
| `CSDL/` | Schema CSDL trụ sở, truy vấn đối chiếu Q1–Q5 |
| `TV2_HuongDan_TungBuoc.docx` | Hướng dẫn làm lại từ file TV1 |
| `cong_nghe_nen_tang_TV2.docx` | Báo cáo nhóm (bản TV1 + các mục TV2) |
| `…BaoCaoCaNhan_LeMinhDao.docx` | Báo cáo cá nhân TV2 |
| `TV2_OnTap_KiemTraCheo.html` | Trang ôn tập: 25 câu hỏi, trắc nghiệm tự chấm |

---

## 5. Hạn chế – nên tự nói khi bị hỏi

- **ACL không phải tường lửa có trạng thái:** `established` chỉ xem cờ TCP.
- **Port security chặn được máy lạ cắm vào, nhưng chưa chống được giả mạo MAC.** Muốn chống thì cần 802.1X.
- **Mỗi địa điểm chỉ có 1 VLAN.** Nếu tách VLAN máy chủ và VLAN quản trị thì an toàn hơn.
- **Cửa hàng 3 chưa có đường dự phòng**, vì R-CH2 đã dùng hết 2 cổng Serial.
- **Sao lưu CSDL đang chạy bằng lệnh tay, bản sao nằm cùng máy.** Thực tế nên chạy theo lịch tự động và chép sang máy
  khác.
- **Packet Tracer không chứng minh được** thông lượng hay khả năng chịu tải thật.

---

## 6. Demo tích hợp (cả 3 thành viên)

**Link:** https://fimbrillate-uncraven-antonietta.ngrok-free.dev. Lần đầu mở, ngrok hiện trang cảnh báo, bấm
**Visit Site** để vào.

- Packet Tracer để bên trái, trang demo để bên phải. Bấm **Bước tiếp** hoặc phím →.
- **Sơ đồ hiện dần theo bước:** thiết bị và dây → IP → OSPF → khiên ACL → khóa SSH → port security → NTP/Syslog →
  CSDL.
- Gói tin chạy trên dây theo đúng đường OSPF đang chọn. Bị chặn thì hiện ✕ tại router chặn.

| Bước | Ai | Nội dung |
|---|---|---|
| 1–3 | TV1 | Nối dây, IP, OSPF, KT1 |
| 4–7 | **TV2** | **ACL, SSH, port security (cắm laptop lạ), NTP + Syslog** |
| 8 | TV3 | Bán hàng, gửi về trụ sở |
| 9–10 | TV1 + TV3 | Đứt đường chính, cửa hàng bị cô lập (KT2); Syslog tự ghi giờ |
| 11–12 | TV3 | Gửi lại (KT3), gửi lặp (KT3-b) |
| 13–14 | **TV2** | **Sao lưu – xóa – khôi phục (BK-1), khôi phục bản cũ và gửi bù** |

Cả nhóm **dùng chung một phiên**. Lúc tập chỉ nên để một người bấm.

---

## 7. Việc còn lại của TV2

- [ ] Mở `Nhom02_v2.pkt`, tạo khóa RSA trên 8 thiết bị (`crypto key generate rsa general-keys modulus 1024`), lưu file.
- [ ] Chạy SEC-1 – SEC-4, LOG-1, chụp ảnh (có `show clock`), gửi kết quả để điền vào các ô `[...]` trong báo cáo.
- [ ] Thống nhất với TV3 dùng một bộ script để có một bộ số liệu.
- [ ] Nhắc TV1 sửa tên trong báo cáo cá nhân (đang ghi tên Lê Minh Đạo).
- [ ] Điền mã sinh viên, lớp, ngày trong báo cáo cá nhân.

## 8. Câu hỏi hay gặp (trả lời ngắn)

| Hỏi | Trả lời |
|---|---|
| Sao không đặt hết ACL ở trụ sở? | Vì có đường dự phòng CH1–CH2 không đi qua trụ sở. Chặn ở nguồn còn đỡ tốn WAN |
| Sao dòng 70 phải đứng trước dòng 80? | Switch `.2` cũng thuộc dải `.10.x`. Nếu đặt sau, dòng 80 chặn mất gói sao lưu và Syslog |
| `access-class` khác `access-group` thế nào? | `access-group` lọc gói **đi qua** cổng; `access-class` lọc **ai được đăng nhập** vào thiết bị |
| Đã có ACL rồi sao còn cần port security? | ACL lọc theo IP, laptop lạ có thể đặt trùng IP của POS. Port security lọc theo MAC ngay ở cổng |
| Syslog lúc cô lập thì sao? | R-CH1 không gửi được, nhưng R-HQ và R-CH2 ghi mất neighbor 2.2.2.2 kèm giờ |
| Sao 12 + 8 = 20 mà không phải 22? | 2 bản bị mất ACK thì trụ sở đã có từ trước. Gửi lại bị nhận là trùng nên bỏ qua |
| Khôi phục từ bản sao lưu cũ thì sao? | Đối chiếu phát hiện giao dịch ACKED mà trụ sở thiếu. Gửi bù: trụ sở chỉ ghi bản thiếu |
