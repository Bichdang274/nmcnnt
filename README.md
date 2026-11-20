Nhóm 02 – Đề tài 02: Hạ tầng CNTT cho chuỗi cửa hàng bán lẻ

Phần của TV1 – Đặng Thị Bích (B24DCCC037):** topology, WAN, định tuyến OSPF, bảo mật thiết bị, sao lưu cấu hình

- Môn: Nhập môn công nghệ nền tảng (RIPT1304-20261-03) · GVHD: Nguyễn Xuân Dũng
- Công cụ: Cisco Packet Tracer 9.0.1 (build 9.0.1.0858), Windows 11
- Báo cáo cá nhân: https://ptiteduvn-my.sharepoint.com/:w:/g/personal/bichdt_b24cc037_stu_ptit_edu_vn/IQAdJIOYRNawRILHtRU6yx1SAdO0tGO-MqnDovsK2SJo0n4?e=ixFo7C

Cấu trúc thư mục

```
.
├── Nhom02_TV1.pkt                 # Topology, WAN, OSPF, bảo mật cơ bản (PA2: có dự phòng CH1–CH2)
├── Nhom02_PA1.pkt                 # Phương án 1 (không có đường dự phòng) để so sánh
├── README.md
└── Nhom02-TV1 (1)/Nhom02-TV1/
    ├── cau-hinh/
    │   ├── router/                # R-HQ, R-CH1, R-CH2, R-CH3
    │   └── switch/                # SW-HQ, SW-CH1, SW-CH2, SW-CH3
    ├── kiem-thu/
    │   ├── 01_kiem-tra-cau-hinh.txt   # show ip int brief, ospf neighbor, route, ping
    │   └── 02_thu-loi-wan.txt         # WAN-1a, WAN-1b, khôi phục, đo PA1
    └── sao-luu/
        └── sao-luu-tftp.txt           # copy running-config tftp và khôi phục
```

## Topology

- 4 địa điểm: trụ sở (R-HQ) và 3 cửa hàng (R-CH1, R-CH2, R-CH3).
- Mỗi địa điểm có 1 router Cisco 2911 (lắp module HWIC-2T; R-HQ lắp 2 module) và 1 switch Cisco 2960-24TT.
- WAN: 3 đường serial hình sao về R-HQ (R-HQ là đầu DCE, `clock rate 128000`) và 1 đường dự phòng R-CH1 ↔ R-CH2 (R-CH1 là đầu DCE).
- Định tuyến: OSPF process 1, area 0. Đường dự phòng đặt `ip ospf cost 100`.

## Bảng địa chỉ

| Phân đoạn | Network | Gateway / hai đầu |
|---|---|---|
| LAN trụ sở | 192.168.0.0/24 | 192.168.0.1 |
| LAN cửa hàng 1 | 192.168.10.0/24 | 192.168.10.1 |
| LAN cửa hàng 2 | 192.168.20.0/24 | 192.168.20.1 |
| LAN cửa hàng 3 | 192.168.30.0/24 | 192.168.30.1 |
| WAN HQ – CH1 | 10.0.1.0/30 | R-HQ .1 – R-CH1 .2 |
| WAN HQ – CH2 | 10.0.2.0/30 | R-HQ .1 – R-CH2 .2 |
| WAN HQ – CH3 | 10.0.3.0/30 | R-HQ .1 – R-CH3 .2 |
| Dự phòng CH1 – CH2 | 10.0.12.0/30 | R-CH1 .1 – R-CH2 .2 |

Quy ước trong mỗi LAN: `.1` router, `.2` switch, `.11–.15` máy POS. Riêng trụ sở: Server-TT `.10`, Server-Backup `.11`, PC-Admin `.20`.

| Router | Router-ID |
|---|---|
| R-HQ | 1.1.1.1 |
| R-CH1 | 2.2.2.2 |
| R-CH2 | 3.3.3.3 |
| R-CH3 | 4.4.4.4 |

## Cách sử dụng

1. Mở `Nhom02_TV1.pkt` bằng Packet Tracer 9.0.1 trở lên (bản cũ hơn không mở được file).
2. Nếu cần cấu hình lại từ đầu: mở tab CLI của thiết bị, trả lời `no` ở hộp thoại ban đầu, rồi dán toàn bộ nội dung file tương ứng trong `cau-hinh/`.
3. Kiểm tra theo `kiem-thu/01_kiem-tra-cau-hinh.txt`.
4. Thử lỗi WAN theo `kiem-thu/02_thu-loi-wan.txt`.
5. Sao lưu và khôi phục cấu hình theo `sao-luu/sao-luu-tftp.txt` (Server-Backup 192.168.0.11 bật TFTP).

## Bảo mật thiết bị

- `enable secret`, `service password-encryption`, mật khẩu console/VTY (`password` + `login`).
- Mật khẩu `cisco` / `class` chỉ dùng cho mô phỏng; hệ thống thật cần mật khẩu mạnh.
- SSH, ACL, port security do TV2 cấu hình thêm trong `Nhom02_v2.pkt` (nhánh `tv2`).

## Người thực hiện

TV1 – Đặng Thị Bích: topology, WAN, OSPF, bảo mật thiết bị, sao lưu cấu hình.
