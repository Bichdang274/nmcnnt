# Demo tích hợp Nhóm 02 – mạng + dữ liệu trên một trang

Một trang web dẫn cả nhóm demo **xuyên suốt** phần của TV1, TV2, TV3 theo đúng thứ tự dựng hệ thống:

| Bước | Ai | Nội dung |
|---|---|---|
| 0 | Cả nhóm | Chuẩn bị, làm mới phiên |
| 1 | TV1 | Thiết bị và nối dây (Serial DCE/DTE, cáp đồng thẳng) |
| 2 | TV1 | Đặt địa chỉ IP |
| 3 | TV1 | Định tuyến OSPF, KT1 |
| 4 | TV2 | ACL phân quyền (tra được gói khớp dòng ACL nào) |
| 5 | TV2 | SSH thay Telnet: chỉ PC-Admin, chỉ SSH (SEC-3) |
| 6 | TV2 | Port security: cắm laptop lạ → cổng err-disabled (SEC-4) |
| 7 | TV2 | NTP + Syslog: đồng hồ chung, nhật ký sự cố về Server-Backup (LOG-1) |
| 8 | TV3 | Chuyển dữ liệu từ cửa hàng về trụ sở (PENDING → SENT → ACKED) |
| 9 | TV1 | Đứt đường chính → OSPF đi đường dự phòng (Syslog ghi giờ) |
| 10 | TV1 + TV3 | Cửa hàng 1 bị cô lập (KT2): vẫn bán, giao dịch giữ trong kho |
| 11 | TV3 | Khôi phục WAN, gửi lại (KT3) |
| 12 | TV3 | Cố ý gửi lặp (KT3-b): không ghi trùng |
| 13 | TV2 | Sao lưu – xóa thử – khôi phục CSDL trụ sở (BK-1) |
| 14 | TV2 | Khôi phục từ bản cũ, đối chiếu, gửi bù |
| 15 | Cả nhóm | Tổng kết với số liệu của phiên |

Mỗi bước có: **Trong Packet Tracer** (thao tác trên `Nhom02_v2.pkt`), **Giải thích** (cấu hình và lý do),
**Trên trang này** (nút chạy script thật / tra ACL), **Lời nói**, **Kết quả mong đợi**.
Bên phải là **sơ đồ chi tiết kiểu Packet Tracer** (4 router, 4 switch, 15 POS, 2 máy chủ, PC-Admin, tên cổng, đèn cáp,
cáp Serial đỏ có DCE). Sơ đồ **hiện dần theo bước**: bước 1 thiết bị + dây → bước 2 IP → bước 3 OSPF (router-id, cost,
hello chạy trên dây) → bước 4 khiên ACL ở cổng G0/0 → bước 5 ổ khóa SSH → bước 6 nhãn port-security (laptop lạ khi cổng bị khóa) → bước 7 đồng hồ NTP, bảng SYSLOG → bước 8 CSDL kho cửa hàng / trụ sở / sao lưu.
Khi bấm gửi, tra ACL, sao lưu, khôi phục: **gói tin chạy trên dây** theo đúng đường OSPF đang chọn; bị chặn thì hiện ✕ tại
router chặn. Đường WAN đổi màu và có dấu ✕ khi shutdown. Dưới sơ đồ: dữ liệu hai bên, kết quả đối chiếu, nhật ký script.

Mở thẳng một bước: `http://127.0.0.1:8765/#buoc=4`.

## Chạy

Cần Python 3.8 trở lên, không cần cài thêm thư viện.

```bash
cd DemoTichHop
python3 demo_tich_hop.py        # Windows: python demo_tich_hop.py
```

Trình duyệt tự mở `http://127.0.0.1:8765`. Bấm **Làm mới phiên**, rồi dùng nút **Bước tiếp** hoặc phím → để đi lần lượt.
Dừng: `Ctrl + C` ở cửa sổ Terminal (hq_receiver.py cũng dừng theo).

Nếu báo **cổng 8000 đang bận**: đang có một `hq_receiver.py` khác chạy, tắt nó trước.

## Cấu trúc

| File | Vai trò |
|---|---|
| `demo_tich_hop.py` | Máy chủ demo: chạy script, quản lý hq_receiver, tra ACL, trả trạng thái cho trang |
| `giao_dien.html` | Trang demo (kịch bản 14 bước) |
| `Script_TV3/` | Bản chép **nguyên** script của TV3 từ nhánh `tv3` (xem `NGUON.txt`) – không sửa |
| `Script_TV2/sao_luu_tru_so.py` | TV2: sao lưu, xóa thử, khôi phục CSDL trụ sở `truso.db` (API backup SQLite, giữ 7 bản) |
| `Script_TV2/doi_chieu.py` | TV2: đối chiếu `cuahang01.db` ↔ `truso.db` (mã trùng, ACKED mà trụ sở thiếu), gửi bù |
| `CauHinh/` | running-config 8 thiết bị bản `Nhom02_v2.pkt` – nguồn để tra ACL |
| `PhienDemo/` | Tạo khi bấm Làm mới phiên: script + dữ liệu của phiên demo (không đụng dữ liệu trong repo) |

Hai script TV2 viết theo đúng cách của TV3 (thư mục gốc = cha của `Script/`, CSDL `DuLieu/truso.db`), nên chép vào
`nmcnnt/Script/` là chạy được trực tiếp:

```bash
python Script/sao_luu_tru_so.py sao-luu | danh-sach | xoa-thu --chac-chan | khoi-phuc [--file ...]
python Script/doi_chieu.py            # đối chiếu
python Script/doi_chieu.py gui-bu     # gửi bù giao dịch ACKED mà trụ sở thiếu
```

## Lưu ý trung thực

- **Mất WAN trên trang được giả lập** bằng cách dừng `hq_receiver.py` – giống cách TV3 kiểm thử KT2. Cửa hàng và trụ sở
  chạy trên cùng máy (127.0.0.1:8000). Phải làm song song thao tác `shutdown` trong Packet Tracer.
- **Port security và Syslog trên trang là mô phỏng theo cấu hình** (thông báo IOS dựng theo `logging`, MAC sticky đọc từ
  running-config); bằng chứng thật xem trong Packet Tracer (`show port-security`, Server-Backup → Services → SYSLOG).
- Ô **Tra ACL** đọc đúng running-config và giải thích gói khớp dòng nào; đây là công cụ giải thích, **bằng chứng thật
  là kết quả trong Packet Tracer** (`show access-lists`, ping, Simulation).
- Packet Tracer chứng minh cấu hình và kết nối; script chứng minh lưu, gửi, xác nhận và chống trùng.
