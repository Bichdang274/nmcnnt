# Nhóm 02 – Đề tài 02: Hạ tầng CNTT cho chuỗi cửa hàng bán lẻ

**Phần của TV1 – WAN, định tuyến, bảo mật thiết bị, sao lưu cấu hình**

Môn: Nhập môn công nghệ nền tảng (RIPT1304-20261-03) · GVHD: Nguyễn Xuân Dũng
Công cụ: Cisco Packet Tracer 7.3.1

## Cấu trúc thư mục

```
.
├── packet-tracer/
│   ├── Nhom02_TV1.pkt        # Topology, WAN, OSPF, bảo mật cơ bản (chưa có ACL của TV2)
│   └── Nhom02_PA1.pkt        # Phương án 1 (không có đường dự phòng) để so sánh
├── cau-hinh/
│   ├── router/               # R-HQ, R-CH1, R-CH2, R-CH3
│   └── switch/               # SW-HQ, SW-CH1, SW-CH2, SW-CH3
├── kiem-thu/
│   ├── 01_kiem-tra-cau-hinh.txt   # show ip int brief, ospf neighbor, route, ping
│   ├── 02_thu-loi-wan.txt         # WAN-1a, WAN-1b, khôi phục, đo PA1
│   └── 03_kiem-tra-telnet.txt     # Telnet từ PC-Admin / POS
└── sao-luu/
    └── sao-luu-tftp.txt           # copy running-config tftp và khôi phục
```

## Topology

- 4 địa điểm: trụ sở (R-HQ) và 3 cửa hàng (R-CH1, R-CH2, R-CH3).
- Mỗi địa điểm: 1 router Cisco 2911 (module HWIC-2T) và 1 switch Cisco 2960-24TT.
- WAN: 3 đường serial hình sao về R-HQ (R-HQ là đầu DCE, clock rate 128000) và 1 đường dự phòng R-CH1 ↔ R-CH2.
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

Quy ước trong mỗi LAN: `.1` router, `.2` switch, `.10–.20` máy chủ và PC-Admin, `.11–.15` máy POS.

| Router | Router-ID |
|---|---|
| R-HQ | 1.1.1.1 |
| R-CH1 | 2.2.2.2 |
| R-CH2 | 3.3.3.3 |
| R-CH3 | 4.4.4.4 |

## Cách sử dụng

1. Mở `packet-tracer/Nhom02_TV1.pkt` bằng Packet Tracer 7.3.1 trở lên.
2. Nếu cần cấu hình lại từ đầu: mở tab **CLI** của thiết bị, trả lời `no` ở hộp thoại ban đầu, rồi dán toàn bộ nội dung file tương ứng trong `cau-hinh/`.
3. Kiểm tra theo `kiem-thu/01_kiem-tra-cau-hinh.txt`.
4. Thử lỗi WAN theo `kiem-thu/02_thu-loi-wan.txt`.

## Bảo mật thiết bị

- `enable secret`, mật khẩu console/VTY, `service password-encryption`, banner.
- Chỉ PC-Admin (192.168.0.20) được Telnet vào router và switch (`access-list 10` + `access-class 10 in`).
- Mật khẩu `cisco` / `class` chỉ dùng cho mô phỏng; hệ thống thật cần mật khẩu mạnh và SSH thay Telnet.

## Phân công liên quan

- **TV1**: file này (topology, WAN, OSPF, bảo mật thiết bị, sao lưu cấu hình).
- **TV2**: IP cho PC/máy chủ, dịch vụ máy chủ, ACL phân quyền (`Nhom02_v2.pkt`).
- **TV3**: script lưu tạm / gửi lại / chống trùng.
