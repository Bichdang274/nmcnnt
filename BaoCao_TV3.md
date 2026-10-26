# Báo cáo tiến độ – Thành viên 3

- Họ tên: Phan Hải Đức.
- Đề tài: Thiết kế hạ tầng CNTT cho chuỗi cửa hàng bán lẻ.
- Nhánh Git: tv3.
- Ngày cập nhật: 26/10/2026.

## 1. Nhiệm vụ phụ trách

Xây dựng chương trình lưu giao dịch tại cửa hàng bằng Python và SQLite; gửi giao dịch về trụ sở, xử lý xác nhận ACK và gửi lại khi kết nối được khôi phục. Kiểm tra chống ghi trùng, xuất giao dịch mẫu và sao lưu dữ liệu cục bộ.

## 2. Phạm vi đã triển khai

Chương trình hiện mô phỏng cửa hàng CH01, máy POS01 và máy chủ trụ sở trên cùng một máy tính, giao tiếp qua địa chỉ 127.0.0.1:8000.

- Cơ sở dữ liệu cửa hàng: DuLieu/cuahang01.db.
- Cơ sở dữ liệu trụ sở: DuLieu/truso.db.
- Mã nguồn: thư mục Script.
- Log kiểm thử: thư mục MinhChung.
- Giao dịch mẫu CSV: thư mục DuLieu/Xuat.
- Bản sao lưu cửa hàng: thư mục DuLieu/SaoLuu.

Các kết quả hiện tại là kiểm thử chương trình trên máy cục bộ, chưa chứng minh hoạt động qua mạng WAN thực tế hoặc mô hình Packet Tracer của nhóm.

Việc gửi lại giao dịch và sao lưu hiện được thực hiện bằng lệnh thủ công, chưa có cơ chế chạy tự động theo lịch.

## 3. Cơ chế hoạt động

### 3.1. Lưu giao dịch tại cửa hàng

Mỗi giao dịch được lưu vào SQLite trước khi gửi về trụ sở, gồm mã giao dịch, mã cửa hàng, mã máy POS, thời gian, số tiền và trạng thái.

Mã giao dịch có dạng CH01-POS01-YYYYMMDD-XXXXXX. Bộ đếm được lưu trong database để tiếp tục cấp mã khi chạy lại chương trình.

Các trạng thái xử lý:

- PENDING: giao dịch mới tạo, chưa gửi.
- SENT: đã bắt đầu gửi nhưng chưa nhận được ACK hợp lệ.
- ACKED: đã nhận được xác nhận hợp lệ từ trụ sở.

### 3.2. Gửi giao dịch và nhận ACK

Chương trình chọn các giao dịch có trạng thái PENDING hoặc SENT để gửi bằng HTTP POST.

Trụ sở lưu giao dịch và commit vào SQLite trước khi trả ACK. Cửa hàng chỉ chuyển giao dịch sang ACKED khi phản hồi có ack bằng true và mã giao dịch khớp với giao dịch đã gửi.

Nếu kết nối thất bại hoặc phản hồi không hợp lệ, giao dịch vẫn được giữ tại cửa hàng để gửi lại trong lần chạy sau.

### 3.3. Chống ghi trùng tại trụ sở

Trụ sở sử dụng mã giao dịch làm khóa chính và kiểm tra dữ liệu khi nhận:

- Mã chưa tồn tại: lưu giao dịch và trả ACK với kết quả DA_LUU.
- Mã đã tồn tại, nội dung giống nhau: không thêm bản ghi, trả ACK với kết quả DA_TON_TAI.
- Mã đã tồn tại, nội dung khác nhau: trả lỗi HTTP 409, không xác nhận thành công.

Nhờ đó, cửa hàng có thể gửi lại giao dịch mà không làm tăng số bản ghi nếu trụ sở đã nhận giao dịch trước đó.

## 4. Kết quả kiểm thử

### 4.1. Không kết nối được tới trụ sở – KT2

Cách thực hiện:

- Dừng chương trình nhận tại trụ sở.
- Tạo thêm 5 giao dịch tại cửa hàng.
- Chạy lệnh gửi giao dịch.

Kết quả:

- Cả 5 giao dịch gửi không thành công và được giữ ở trạng thái SENT.
- Cửa hàng vẫn có đủ 10 giao dịch: 5 giao dịch đã ACKED trước đó và 5 giao dịch chờ gửi lại.
- Log: MinhChung/KT2_khong_ket_noi.txt.

Phép thử này mô phỏng tình huống không kết nối được tới dịch vụ nhận bằng cách dừng dịch vụ trên máy cục bộ.

### 4.2. Gửi lại sau khi khôi phục dịch vụ – KT3

Cách thực hiện:

- Khởi động lại chương trình nhận tại trụ sở.
- Chạy lại lệnh gửi giao dịch từ cửa hàng.

Kết quả:

- 5 giao dịch còn chờ được gửi và nhận ACK thành công.
- Cả 10 giao dịch tại cửa hàng chuyển sang ACKED.
- Trụ sở có tổng cộng 10 giao dịch.
- Log: MinhChung/KT3_gui_lai.txt và MinhChung/KT3_sau_gui.txt.

### 4.3. Gửi lặp giao dịch – KT3-b

Cách thực hiện:

- Gửi lại toàn bộ 10 giao dịch đã có tại trụ sở bằng chương trình kiểm tra trùng.

Kết quả:

- Cả 10 phản hồi đều có ACK hợp lệ và kết quả DA_TON_TAI.
- Số giao dịch tại trụ sở vẫn là 10.
- Không có mã giao dịch bị trùng.
- Dữ liệu trụ sở trước và sau phép thử giống nhau.
- Log: MinhChung/KT3b_gui_lap.txt.

### 4.4. Xuất CSV và sao lưu cục bộ

Kết quả kiểm thử ngày 26/10/2026:

- Xuất thành công 10 giao dịch ra CSV, tất cả có trạng thái ACKED.
- Tạo thành công bản sao database cửa hàng bằng SQLite backup.
- Bản sao chứa 10 giao dịch và có kết quả integrity_check là ok.
- Log: MinhChung/xuat_giao_dich.txt và MinhChung/sao_luu.txt.

Hiện đã kiểm tra tính toàn vẹn và số lượng giao dịch của bản sao; chưa thực hiện kiểm thử phục hồi để chạy tiếp chương trình từ bản sao lưu.

## 5. Công việc còn lại

### 5.1. Hoàn thiện kiểm thử chương trình

- Kiểm thử phục hồi từ bản sao lưu trên database thử nghiệm riêng.
- Kiểm tra khả năng tạo giao dịch mới sau phục hồi, bảo đảm bộ đếm tiếp tục cấp mã đúng.
- Bổ sung kiểm thử trường hợp cùng mã giao dịch nhưng nội dung khác nhau.
- Bổ sung kiểm thử trường hợp trụ sở đã lưu giao dịch nhưng cửa hàng chưa nhận được ACK.

### 5.2. Phối hợp với các thành viên

- Thống nhất với TV2 cấu trúc dữ liệu và quy tắc chống ghi trùng tại trụ sở.
- Phối hợp với TV1 về địa chỉ máy chủ, kết nối giữa cửa hàng và trụ sở, kịch bản mất và khôi phục kết nối.
- Phân biệt minh chứng kiểm thử chương trình Python với minh chứng mạng trên Packet Tracer.
- Thống nhất cách mở rộng cấu hình cho 3 cửa hàng, mỗi cửa hàng 5 máy POS.

### 5.3. Hoàn thiện báo cáo chung

- Đưa nội dung phần TV3 vào các mục được phân công trong báo cáo nhóm.
- Bổ sung ảnh minh chứng và giải thích kết quả kiểm thử.
- Cập nhật hướng dẫn chạy khi có thay đổi sau tích hợp.

## 6. Tổng kết tiến độ

Đã xây dựng và kiểm thử trên máy cục bộ các chức năng: lưu giao dịch bằng SQLite, gửi và nhận ACK, giữ giao dịch khi không kết nối được, gửi lại bằng lệnh thủ công, chống ghi trùng, xuất CSV và sao lưu database cửa hàng.

Mã nguồn, dữ liệu mẫu, log và hướng dẫn sử dụng đã được đẩy lên nhánh tv3. Hai commit đã đẩy:

- 97bd688: lưu giao dịch, gửi lại, ACK và kiểm tra trùng.
- 95094b8: bổ sung xuất CSV, sao lưu SQLite và minh chứng.

Phần tích hợp với hệ thống chung và các kiểm thử bổ sung vẫn đang tiếp tục. Báo cáo này ghi nhận tiến độ hiện tại, chưa phải kết quả nghiệm thu toàn bộ đề tài.