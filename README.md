# Nhóm 02 – Đề tài 02: Thiết kế hạ tầng CNTT cho chuỗi cửa hàng bán lẻ

Môn: Nhập môn công nghệ nền tảng (RIPT1304-20261-03) · GVHD: Nguyễn Xuân Dũng

| Thành viên | MSSV | Vai trò | Nhánh |
|---|---|---|---|
| Đặng Thị Bích | B24DCCC037 | TV1 – topology, WAN, OSPF, bảo mật thiết bị, sao lưu cấu hình (TFTP), so sánh PA1/PA2 | `tv1` |
| Lê Minh Đạo | B24DCCC058 | TV2 – IP máy trạm, dịch vụ máy chủ, ACL, SSH, port security, NTP/Syslog, sao lưu – đối chiếu CSDL | `tv2` |
| Phan Hải Đức | B24DCCC072 | TV3 – lưu tạm, gửi lại, chống trùng, tự đồng bộ, kiểm thử tích hợp | `tv3`, `tich-hop-tv2-tv3-test`, `tv3-nang-cao-demo` |

- Báo cáo: https://ptiteduvn-my.sharepoint.com/:w:/g/personal/bichdt_b24cc037_stu_ptit_edu_vn/IQAcswg67c-ZQLoimqu4YfpSAV4u8EceoSSUfD6wOJEOCQY?e=xd4F8E
- Video demo: https://drive.google.com/drive/folders/1B1mVk81plK14Q8pVvmNtc4KDcfttziR7?usp=sharing

## Phiên bản

| Thành phần | Phiên bản |
|---|---|
| Cisco Packet Tracer | 9.0.1 (build 9.0.1.0858). Bản cũ hơn không mở được file `.pkt` của nhóm |
| Thiết bị mô phỏng | Router Cisco 2911 + HWIC-2T, switch Cisco 2960-24TT, PC-PT, Server-PT |
| Python | 3.8 trở lên, chỉ dùng thư viện chuẩn (sqlite3, http.server, urllib, json) |
| Hệ điều hành đã chạy | Windows 11, macOS |

## Nội dung từng nhánh

| Nhánh | File, thư mục | Nội dung |
|---|---|---|
| `tv1` | `Nhom02_TV1.pkt`, `Nhom02_PA1.pkt` | Topology, WAN, OSPF; phương án 1 (không dự phòng) để so sánh |
| `tv1` | `Nhom02-TV1 (1)/Nhom02-TV1/cau-hinh/`, `kiem-thu/`, `sao-luu/` | Lệnh cấu hình 8 thiết bị, lệnh kiểm thử, sao lưu TFTP |
| `tv2` | `Nhom02_v2.pkt` | **Bản cuối của nhóm**: thêm ACL, SSH, port security, NTP, Syslog |
| `tv2` | `Script_TV2/`, `CauHinh_TV2/` | Lệnh cấu hình phần TV2; running-config 8 thiết bị |
| `tv2` | `Script/sao_luu_tru_so.py`, `Script/doi_chieu.py`, `CSDL/` | Sao lưu – khôi phục – đối chiếu – gửi bù CSDL trụ sở |
| `tv3` | `Script/*.py`, `chay_auto_sync.ps1` | Lưu tạm, nhận giao dịch, tự đồng bộ, kiểm tra trùng, sao lưu kho |
| `tv3` | `MinhChung/` | Log và ảnh minh chứng KT2, KT3, KT3-b |
| `tich-hop-tv2-tv3-test` | `TichHop_TV2_TV3_Test/` | Bộ kiểm thử tích hợp, `PhienThu/`, `MinhChungBoSung/` |

## Cách dựng lại

### Mạng (Packet Tracer)
1. Mở `Nhom02_v2.pkt` (nhánh `tv2`) bằng Packet Tracer 9.0.1 trở lên.
2. Chờ OSPF hội tụ khoảng 1 phút, hoặc bấm **Fast Forward Time**.
3. Dựng lại từ đầu (nếu cần):
   - Dán lệnh trong `cau-hinh/` của TV1 vào CLI từng thiết bị (trả lời `no` ở hộp thoại ban đầu).
   - Dán các file trong `Script_TV2/` (ACL, SSH/NTP/Syslog, port security).
   - Chạy `crypto key generate rsa general-keys modulus 1024` trên từng thiết bị.

### Dữ liệu (Python, nhánh `tv3`)
Không cần cài thêm thư viện. Mở 3 cửa sổ terminal tại thư mục gốc:

```
python Script/hq_receiver.py        # cửa sổ 1: trụ sở nhận giao dịch (http://127.0.0.1:8000)
python Script/store_agent.py        # cửa sổ 2: chọn 1 để tạo 5 giao dịch
python Script/auto_sync.py          # cửa sổ 3: tự gửi lại mỗi 10 giây
```

Các phép thử làm thay đổi dữ liệu, nên chạy trên bản sao của thư mục `DuLieu/`.

## Cách chạy kiểm thử

| Mã | Cách chạy | Kết quả mong đợi |
|---|---|---|
| KT1 | POS1-1, POS2-1, POS3-1: `ping 192.168.0.10`; POS1-1 mở `http://192.168.0.10` | Thành công |
| KT2 | Dừng `hq_receiver.py` (Ctrl + C), tạo 5 giao dịch bằng `store_agent.py` | 5 giao dịch ở trạng thái PENDING/SENT, vẫn còn trong kho cửa hàng |
| KT3 | Bật lại `hq_receiver.py`, gửi lại (hoặc chờ `auto_sync.py`) | Trụ sở thêm đúng 5, cửa hàng = trụ sở, trùng 0 |
| KT3-b | `python Script/kiem_tra_trung.py` | Trả `DA_TON_TAI`, trụ sở không đổi, 0 mã trùng |
| WAN-1a | R-CH1: `interface s0/0/0` → `shutdown`; Simulation ICMP POS1-1 → R-HQ | Gói đi R-CH1 → R-CH2 → R-HQ |
| WAN-1b | R-CH1: shutdown cả S0/0/0 và S0/0/1 | POS1-1 ping gateway được, không tới Server-TT |
| SEC-1 – SEC-4, LOG-1 | Theo `Script_TV2/KiemThu_TV2.txt` (nhánh `tv2`) | ACL chặn đúng, chỉ PC-Admin SSH được, port security shutdown cổng lạ, NTP đồng bộ |
| BK-1 – BK-3 | `python Script/sao_luu_tru_so.py sao-luu \| xoa-thu --chac-chan \| khoi-phuc`, sau đó `python Script/doi_chieu.py` (và `gui-bu` nếu thiếu) | Khôi phục đủ, đối chiếu khớp, giữ 7 bản sao mới nhất |

Kiểm tra không trùng trực tiếp trên CSDL trụ sở:

```sql
SELECT ma_gd, COUNT(*) FROM giao_dich GROUP BY ma_gd HAVING COUNT(*) > 1;  -- phải rỗng
```

Bảng kiểm thử đầy đủ (19 ca, có kết quả thực tế và thời gian) nằm ở mục 4 của báo cáo.

## Sử dụng AI

Nhóm dùng Claude (Anthropic) để biên tập báo cáo, trình bày bảng, cắt ảnh minh chứng từ video, rà soát file và hỗ trợ thao tác Git. Cấu hình, script và kiểm thử do nhóm tự thực hiện; mọi số liệu được đối chiếu với log gốc.

## Lưu ý

Toàn bộ dữ liệu là dữ liệu giả. Packet Tracer chỉ chứng minh cấu hình và kết nối, không dùng để khẳng định thông lượng hay khả năng chịu tải thật.
