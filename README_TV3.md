# Phần thực hiện của TV3 – Phan Hải Đức

## 1. Nhiệm vụ
Xây dựng minh chứng lưu tạm giao dịch tại cửa hàng, gửi lại khi
kết nối được phục hồi và chống ghi trùng tại trụ sở.

## 2. Công cụ
- Python 3, sử dụng thư viện có sẵn.
- SQLite để lưu dữ liệu.
- HTTP POST để truyền giao dịch dưới dạng JSON.
- Bản demo chạy cửa hàng 01 và trụ sở trên cùng một máy tính.

## 3. Các file
- Script/store_agent.py: tạo giao dịch, lưu cục bộ, gửi và xử lý xác nhận.
- Script/hq_receiver.py: nhận giao dịch, lưu tại trụ sở và trả xác nhận.
- Script/kiem_tra_trung.py: cố ý gửi lặp và đối chiếu dữ liệu hai bên.
- DuLieu/cuahang01.db: dữ liệu cửa hàng.
- DuLieu/truso.db: dữ liệu trụ sở.
- MinhChung/: log kiểm thử.

## 4. Cách chạy
Mở Terminal tại thư mục gốc nmcnnt.

Terminal thứ nhất – chạy trụ sở:
```powershell
python Script/hq_receiver.py
```

Terminal thứ hai – tạo hoặc xem giao dịch:
```powershell
python Script/store_agent.py
```
- Chọn 1: tạo thêm 5 giao dịch mới.
- Chọn 2: xem giao dịch đã lưu.

Gửi các giao dịch chưa được xác nhận:
```powershell
python -c "from Script.store_agent import gui_giao_dich, xem_giao_dich; gui_giao_dich(); xem_giao_dich()"
```

Kiểm thử gửi lặp khi dữ liệu hai bên đã khớp:
```powershell
python Script/kiem_tra_trung.py
```

## 5. Cơ chế hoạt động
- PENDING: giao dịch đã lưu, chưa thử gửi.
- SENT: đã thử gửi nhưng chưa nhận xác nhận hợp lệ.
- ACKED: đã nhận xác nhận đúng mã giao dịch.
- Chương trình gửi lại các giao dịch PENDING hoặc SENT.
- Không xóa giao dịch khi gửi lỗi.
- Trụ sở dùng mã giao dịch làm khóa chính.
- Nhận lại cùng mã và cùng nội dung: không ghi thêm, vẫn trả ACK.
- Cùng mã nhưng nội dung khác: trả lỗi 409.
- Hiện tại người dùng chủ động chạy lệnh gửi lại, chưa có gửi tự động.

## 6. Kết quả kiểm thử ngày 24/10/2026
- Gửi ban đầu: 5 giao dịch được xác nhận.
- Dừng máy chủ, tạo thêm 5 giao dịch và thử gửi:
  cửa hàng giữ đủ 10 giao dịch, trong đó 5 giao dịch mới ở trạng thái SENT.
- Bật lại máy chủ và gửi lại:
  trụ sở có 10 giao dịch, cửa hàng có 10 giao dịch ACKED.
- Cố ý gửi lặp cả 10 giao dịch:
  nhận 10 xác nhận hợp lệ, trụ sở vẫn có 10 bản ghi,
  không có mã trùng và nội dung hai bên khớp.

Log:
- MinhChung/KT2_khong_ket_noi.txt
- MinhChung/KT3_truoc_gui.txt
- MinhChung/KT3_gui_lai.txt
- MinhChung/KT3_sau_gui.txt
- MinhChung/KT3b_gui_lap.txt

## 7. Phạm vi và công việc còn lại
- Đã kiểm thử lỗi kết nối bằng cách dừng máy chủ trên laptop.
  Đây chưa phải minh chứng ngắt WAN trong Packet Tracer.
- Phối hợp TV1, TV2 để thống nhất cấu trúc dữ liệu và kịch bản mạng.
- Bổ sung minh chứng mạng từ mô hình Packet Tracer của nhóm.
- Hoàn thiện các mục báo cáo được phân công.

## 8. Xuất giao dịch mẫu và sao lưu cục bộ

### Xuất giao dịch ra CSV

Chạy tại thư mục gốc dự án:

```powershell
python Script/xuat_giao_dich.py
```

- Xuất các giao dịch của cửa hàng CH01 vào thư mục `DuLieu/Xuat`.
- File CSV có 6 cột: ma_gd, ma_cua_hang, ma_may, thoi_gian, so_tien, trang_thai.
- Tên file chứa thời gian xuất để phân biệt các lần chạy.
- Chương trình chỉ đọc database gốc.

### Sao lưu SQLite

```powershell
python Script/sao_luu.py
```

- Sử dụng SQLite backup để sao lưu toàn bộ database cửa hàng.
- Bản sao nằm trong `DuLieu/SaoLuu`, tên file có thời gian tạo.
- Giữ cả bảng giao dịch và bảng bộ đếm mã.
- Kiểm tra bản sao bằng `PRAGMA integrity_check`.
- Hiện chạy sao lưu bằng lệnh thủ công, chưa lập lịch tự động.

### Kết quả kiểm thử ngày 26/10/2026

- Xuất CSV thành công: 10 giao dịch, tất cả ở trạng thái ACKED.
- Sao lưu thành công: bản sao chứa 10 giao dịch.
- Kiểm tra toàn vẹn bản sao: ok.
- Log: `MinhChung/xuat_giao_dich.txt` và `MinhChung/sao_luu.txt`.

