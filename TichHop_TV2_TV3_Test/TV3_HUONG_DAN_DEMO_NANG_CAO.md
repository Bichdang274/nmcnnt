# Demo TV3 nâng cao – dùng bộ điều khiển hiện có

## Chuẩn bị

Làm việc trong thư mục TichHop_TV2_TV3_Test của worktree tv3-nang-cao-demo. Python 3.9 trở lên; chỉ thư viện chuẩn. Không mở lại hai phiên minh chứng cũ để ghi dữ liệu. Cổng 18000 phải rảnh; nếu có dịch vụ lạ thì dừng demo, không đóng tiến trình đó.

```powershell
Get-NetTCPConnection -LocalPort 18000 -State Listen -ErrorAction SilentlyContinue
powershell -NoProfile -ExecutionPolicy Bypass -File .\chay_demo.ps1
```

Các lệnh tiếp theo nhập ở tich-hop>, mỗi lần một lệnh. Kết quả dưới đây là kỳ vọng cho lần trình diễn mới; chỉ kết luận sau khi quan sát.

## Cảnh 1 – dịch vụ dừng và tự gửi lại

```text
phien-moi
tru-so-bat
tao-5
dong-bo-bat
giam-sat
```

Chờ đủ 5 ACKED, HQ 5 rồi tiếp tục. Nếu màn hình đang chuyển trạng thái, gọi giam-sat lại; không gọi tao-5 thêm ngoài kịch bản.

```text
tru-so-tat
tao-5
giam-sat
```

Chờ sender thử gửi: tổng kho 10, ACKED cũ 5, 5 mới chuyển PENDING sang SENT, chưa ACK 5. Thấy dịch vụ không phản hồi, dữ liệu vẫn được giữ.

```text
tru-so-bat
giam-sat
```

Không gọi gui-mot-luot. Chờ cùng auto sync tự gửi phần còn lại, rồi:

```text
dong-bo-tat
gui-lap
giam-sat
```

Kỳ vọng tổng 10 ACKED, HQ 10, khớp năm trường; gửi lặp không tăng số bản ghi. Trên máy thử, 20 yêu cầu bị từ chối đã mất khoảng 40 giây vì gửi tuần tự; chu kỳ còn chờ 10 giây sau lượt xử lý. Với 5 yêu cầu, dành thời gian chờ thay vì coi chậm là mất dữ liệu.

## Cảnh 2 – hai cửa hàng độc lập

phien-moi giữ phiên trước, dừng tiến trình cũ và tạo dữ liệu mới, vì vậy mốc 5+5 dưới đây không cộng với cảnh 1.

```text
phien-moi
tru-so-bat
tao-5
dong-bo-bat
cua-hang CH02 POS01
ngat-cua-hang
tao-5
dong-bo-bat
giam-sat
```

Chờ CH01 ACKED 5, CH02 SENT 5, HQ 5. CH01 vẫn có sender riêng hoạt động; CH02 bị chặn gửi HTTP bằng cấu hình mô phỏng. Đây không phải tắt WAN hay rút dây mạng.

```text
noi-cua-hang
giam-sat
```

Nối lại sẽ dừng/bật lại riêng sender CH02 để nạp cấu hình; sender CH01 giữ nguyên. Nếu cổng 18000 do tiến trình ngoài phiên chiếm, lệnh từ chối và giữ trạng thái ngắt; không đóng tiến trình lạ. Chờ tổng 10 ACKED, HQ 10, khớp. Dừng cả hai sender trước gửi lặp để có mốc HQ ổn định:

```text
dong-bo-tat
cua-hang CH01 POS01
dong-bo-tat
gui-lap
cua-hang CH02 POS01
gui-lap
giam-sat
trang-thai
thoat
```

Kỳ vọng mỗi cửa hàng nhận 5 DA_TON_TAI; HQ giữ 10. thoat dừng receiver và mọi sender do phiên tạo. Ctrl+C/EOF cũng đi qua close; không đóng cưỡng bức cửa sổ. CLI thoát với hai sender đã có ca kiểm tra riêng. Sau demo kiểm tra lại cổng; giữ phiên, CSDL và log, không xóa minh chứng.

## Giám sát ở Terminal thứ hai

Thay đường dẫn phiên dưới đây bằng tên mà phien-moi vừa in:

```powershell
python -B .\Script\giam_sat.py --session ".\PhienThu\TEN_PHIEN_MOI" --watch 2
```

Ctrl+C ở cửa sổ giám sát chỉ dừng xem, không dừng auto sync. Có thể bỏ --watch để lấy một ảnh chụp hoặc dùng --json. Giám sát dùng SQLite mode=ro và query_only, báo lỗi rõ khi thiếu DB/sai schema; 0/0 không được đánh giá đã đồng bộ.

HTTP 501 ở dòng dịch vụ là phản hồi GET từ receiver chưa có do_GET, không phải lỗi gửi POST giao dịch. Probe này không chứng minh danh tính receiver. Mỗi CSDL có ảnh chụp riêng; khi sender đang chạy, có thể thấy chênh lệch thoáng qua. Muốn chốt số liệu, dừng tất cả sender rồi xem lại.

## Cấu hình và giới hạn

| Biến của tiến trình gửi | Ý nghĩa |
|---|---|
| TV3_STORE_ID | Mặc định CH01; 2–16 ký tự A–Z/0–9, bắt đầu bằng chữ |
| TV3_POS_ID | Mặc định POS01; cùng quy tắc |
| TV3_DB_PATH | File trong phiên; mặc định DuLieu/cuahang01.db |
| TV3_OFFLINE | 0/1; 1 mô phỏng chặn gửi HTTP, giữ dữ liệu SENT |

Bộ điều khiển tự thiết lập các biến này cho từng sender. Kho khác nằm tại DuLieu/CuaHang/CH02_POS01.db; HQ dùng DuLieu/truso.db. Không chạy các script mẫu trực tiếp tại thư mục bàn giao vì chúng cần đường dẫn của phiên.

Các lệnh tao-5, dong-bo-bat/tat, ngat/noi-cua-hang và gui-lap áp dụng cặp đang chọn. giam-sat tổng hợp mọi kho được phát hiện. doi-chieu/gui-bu của TV2 và xuat-csv/sao-luu-kho/phuc-hoi-kho cũ bị chặn trong phiên nhiều kho vì chúng đang cố định CH01. Chưa mở rộng các công cụ đó và chưa kiểm thử sao lưu/phục hồi HQ nhiều cửa hàng; dùng riêng phiên một kho nếu cần xem luồng TV2 đã đạt trước đây.

ACK sai được trình bày bằng [báo cáo kiểm thử](TV3_BAO_CAO_NANG_CAO.md) và log đã có; không cần kích receiver giả giữa buổi họp. Trường hợp muốn chạy lại phải chủ động chọn runtime-root mới hoàn toàn, không dùng runtime đã đạt. Không tuyên bố bản này đã chạy qua WAN Packet Tracer hoặc đã tích hợp chính thức.
