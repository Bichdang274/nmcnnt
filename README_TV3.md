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
- Ban đầu chương trình gửi giao dịch bằng lệnh thủ công. Ngày 08/11/2026, TV3 bổ sung chương trình auto_sync.py để tự động kiểm tra và gửi lại các giao dịch chưa được xác nhận.

## 6. Bộ kết quả chính ngày 01/11/2026

- KT2: tạo 5 giao dịch mới khi dịch vụ nhận dừng; thử gửi bị từ chối kết nối. Cửa hàng giữ đủ 15 giao dịch (10 ACKED cũ và 5 SENT mới).
- KT3: bật lại dịch vụ và gửi 5 giao dịch còn chờ. Trụ sở tăng từ 10 lên 15; hai bên khớp toàn bộ 5 trường dữ liệu; cửa hàng có 15 ACKED.
- KT3-b: gửi lặp 15 giao dịch, nhận 15 ACK hợp lệ; trụ sở vẫn 15, không có mã trùng.
- Packet Tracer V2: đã có ảnh ping/HTTP mất WAN và HTTP phục hồi.
- Đọc [danh mục minh chứng](MinhChung/README.md) và [báo cáo TV3](BaoCao_TV3.md). Các ca trên đã có kết quả, không cần chạy lại để tạo thêm ảnh/log.
- Log cũ và ảnh TV1 đã chuyển vào `MinhChung/LichSu`; không dùng chúng để thay cho kết quả V2 ngày 01/11.

## 7. Phạm vi và sử dụng đúng dữ liệu

- Mở mô hình hiện tại: `PacketTracer/Nhom02_TV3_KiemThu_TuBanV2.pkt`. Bản `TuBanTV1` chỉ để đối chiếu lịch sử.
- Python chạy tại `127.0.0.1:8000`, độc lập với mạng mô phỏng Packet Tracer. Trong thử nghiệm Python, dừng/bật receiver mô phỏng mất/khôi phục khả năng truy cập dịch vụ.
- CSDL hiện tại có 15 giao dịch; CSV, sao lưu và bản phục hồi ngày 26/10 có 10 giao dịch. Đây là khác thời điểm, không phải mất dữ liệu.
- Các lệnh mục 4 là hướng dẫn tái hiện khi cần. Chọn 1 sẽ tạo thêm dữ liệu; để chỉ xem, chọn 2.
- Cần thống nhất schema và phần ghép báo cáo với TV2; gói này chưa chứng minh tích hợp CSDL TV2.
- Khi đóng receiver, chọn đúng terminal đang chạy `hq_receiver.py`, nhấn Ctrl+C, chờ dấu nhắc trở lại rồi mới nén thư mục.

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

## 9. Kiểm thử phục hồi bản sao lưu

Chạy tại thư mục gốc dự án:

```powershell
python Script/kiem_tra_phuc_hoi.py
```

- Bản sao được dùng: `DuLieu/SaoLuu/cuahang01_20261026_081101_081521.db`.
- Phục hồi vào file thử nghiệm riêng trong `DuLieu/PhucHoiThu`.
- Không ghi đè database cửa hàng đang sử dụng.
- Đối chiếu toàn bộ dữ liệu của bảng `giao_dich` và `bo_dem` với bản sao lưu.
- Kiểm tra tính toàn vẹn database sau phục hồi.

Kết quả ngày 26/10/2026:

- Bảng `giao_dich`: khớp 10 bản ghi.
- Bảng `bo_dem`: khớp 1 bản ghi.
- `integrity_check`: ok.
- Log: `MinhChung/kiem_tra_phuc_hoi.txt`.

Chưa kiểm thử tạo giao dịch mới bằng chương trình cửa hàng trên database đã phục hồi.


## 10. Cải tiến chức năng tự động đồng bộ (08/11/2026)

### 10.1. Mục đích

Trước đây, việc gửi lại giao dịch cần thực hiện bằng lệnh thủ công. Em bổ sung chức năng tự động đồng bộ để cửa hàng chủ động gửi lại giao dịch khi dịch vụ trụ sở hoạt động trở lại.

### 10.2. Các file bổ sung

- `Script/auto_sync.py`: kiểm tra và thử gửi lại giao dịch định kỳ.
- `chay_auto_sync.ps1`: khởi chạy chương trình và lưu log.
- `MinhChung/TuDong/`: lưu ảnh minh chứng kiểm thử.

### 10.3. Cách chạy

Mở Terminal tại thư mục gốc dự án.

Chạy chương trình đồng bộ:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\chay_auto_sync.ps1
```

Chạy dịch vụ nhận tại trụ sở ở Terminal khác:

```powershell
python Script/hq_receiver.py
```

Chương trình đồng bộ sẽ thử gửi các giao dịch PENDING hoặc SENT. Sau mỗi lượt xử lý, chương trình chờ 10 giây trước khi kiểm tra tiếp.

Nếu dịch vụ trụ sở không hoạt động, giao dịch vẫn được giữ trong SQLite. Khi dịch vụ phục hồi, chương trình tự động thử gửi lại.

### 10.4. Kết quả kiểm thử

Ngày 08/11/2026, em thực hiện kiểm thử trên bản sao dự án với 5 giao dịch mới.

- Khi trụ sở chưa hoạt động: 5 giao dịch được giữ lại để gửi tiếp.
- Khi trụ sở hoạt động lại: 5 giao dịch được gửi thành công.
- Cửa hàng: 5 giao dịch, tất cả ACKED.
- Trụ sở: 5 giao dịch.
- Đối chiếu 5 trường dữ liệu: khớp hoàn toàn.
- Chương trình tiếp tục kiểm tra và không còn giao dịch chờ gửi.

### 10.5. Minh chứng

- `MinhChung/TuDong/TV3_TuDong_DoiChieu_5GD.png`
- `MinhChung/TuDong/TV3_TuDong_TruSo_Nhan5GD.png`

### 10.6. Phạm vi kiểm thử

Kiểm thử tự động đồng bộ được thực hiện bằng HTTP trên localhost, mô phỏng tình huống dịch vụ nhận ngừng hoạt động và phục hồi.

Chưa kiểm thử chức năng tự động mới trên đường truyền WAN thực tế hoặc tích hợp trực tiếp với hệ thống của TV2.

Bộ 15 giao dịch và các minh chứng KT2, KT3, KT3-b trước đó được giữ nguyên.


