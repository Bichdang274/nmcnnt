# HƯỚNG DẪN DEMO NHÓM TV2–TV3

## 1. Mục đích và cách sử dụng

Tài liệu giúp các thành viên trình bày cơ chế giữ giao dịch khi dịch vụ trụ sở dừng, tự gửi lại, chống trùng, sao lưu, phục hồi và gửi bù. Đây là demo dữ liệu trên localhost, một CH01/POS01; không tuyên bố chạy qua WAN thật hoặc đã tích hợp chính thức.

Hai phiên ngày 09/11/2026 đã có kết quả thực tế trong [báo cáo kiểm thử](BAO_CAO_KIEM_THU_TICH_HOP.md). Hướng dẫn chạy mới bên dưới là kịch bản trình diễn cho lần sau; không được ghi kết quả kỳ vọng thành kết quả đã đạt khi chưa quan sát. Lần biên soạn tài liệu này không chạy lại demo.

## 2. Phương án xem minh chứng đã có, không chạy chương trình

Có thể bàn giao hoặc thuyết trình bằng các file đã lưu:

1. Mở [Terminal giai đoạn 1](PhienThu/Phien_20261109_014617_838147/MinhChung/terminal_giai_doan_1.txt), [auto sync](PhienThu/Phien_20261109_014617_838147/MinhChung/auto_sync_log.txt) và [kết quả cuối 5 ACKED](PhienThu/Phien_20261109_014617_838147/MinhChung/GD1_SAU_DONG_BO_5_ACKED.json). Chỉ ra 5 lần lỗi khi receiver tắt, rồi 5 ACK khi receiver hoạt động.
2. Mở [Terminal giai đoạn 2](PhienThu/Phien_GD2_20261109_020609_227458/MinhChung/terminal_giai_doan_2.txt). Chỉ ra gửi lặp có 5 DA_TON_TAI, bản sao 5, trụ sở 10 → 5 và gửi bù 5/5.
3. Đối chiếu các bản chụp [trước phục hồi](PhienThu/Phien_GD2_20261109_020609_227458/MinhChung/GD2_TRUOC_PHUC_HOI_10_ACKED.json), [sau phục hồi](PhienThu/Phien_GD2_20261109_020609_227458/MinhChung/GD2_SAU_PHUC_HOI_KHO10_HQ5.json) và [sau gửi bù](PhienThu/Phien_GD2_20261109_020609_227458/MinhChung/GD2_SAU_GUI_BU_10_ACKED.json).
4. Kết thúc bằng [bằng chứng bảo toàn giai đoạn 1](PhienThu/Phien_GD2_20261109_020609_227458/MinhChung/BAO_TOAN_GIAI_DOAN_1.json).

Không chạy script trực tiếp trong hai phiên lưu minh chứng, không sửa CSDL để dựng lại ảnh và không ghi log mới vào chúng. Bộ điều khiển hiện chưa có lệnh mở lại phiên đã tồn tại.

## 3. Chuẩn bị nếu nhóm chọn trình diễn trực tiếp

Một người thao tác Terminal; TV3 giải thích luồng lưu/gửi/ACK, TV2 giải thích đối chiếu/sao lưu/phục hồi. Người còn lại theo dõi log và ghi nhận số liệu. Chỉ dùng một bộ điều khiển tại một thời điểm.

Mở PowerShell trong đúng thư mục:

```powershell
Set-Location -LiteralPath 'THU_MUC_BAN_GIAO'
Get-NetTCPConnection -LocalPort 18000 -State Listen -ErrorAction SilentlyContinue
```

Nếu có listener, xác định tiến trình sở hữu trước khi tiếp tục. Nếu không thuộc phiên demo của nhóm, dừng trình diễn và báo lại; không tự đóng tiến trình đó. Không dùng cổng 8000, không chạy repository gốc hoặc `TV3_TuDong_Test`.

Khi cổng sẵn sàng, chạy:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\chay_demo.ps1
```

Lệnh này mở bộ điều khiển. Nó chưa tạo giao dịch hoặc bật receiver. Các lệnh ở những mục tiếp theo nhập tại dấu nhắc `tich-hop>`, không nhập vào PowerShell.

## 4. Tạo phiên mới và trình bày trường hợp hai kho rỗng

```text
phien-moi
trang-thai
tru-so-bat
doi-chieu
```

Ghi lại đường dẫn `PhienThu/Phien_...` mà chương trình in ra. Đây phải là phiên mới, không phải tên hai phiên đã lưu minh chứng.

Kỳ vọng: cửa hàng 0, trụ sở 0; công cụ báo chưa đạt, mã thoát 2. Giải thích: hai kho cùng rỗng chưa chứng minh dữ liệu đã được đồng bộ. Thông báo `CHUA HOAN TAT` ở ca này là cách bộ điều khiển chuyển tiếp mã 2 của phép đối chiếu.

## 5. Mất dịch vụ, tạo 5 và tự gửi lại

```text
tru-so-tat
tao-5
dong-bo-bat
```

Chỉ gọi `tao-5` một lần ở bước này. Trong một Terminal PowerShell khác, thay đường dẫn dưới đây bằng đúng phiên mới vừa tạo:

```powershell
$thuMucPhienDemo = 'THU_MUC_BAN_GIAO\PhienThu\Phien_...'
Get-Content -LiteralPath (Join-Path $thuMucPhienDemo 'MinhChung\auto_sync_log.txt') -Wait
```

Chờ log đủ 5 lần gửi không được xác nhận và thông báo giữ giao dịch. Không bấm tạo thêm để “thử lại”. Các giao dịch vẫn nằm tại cửa hàng; trạng thái sau lượt gửi lỗi là SENT.

Giữ auto sync chạy, quay lại `tich-hop>`:

```text
tru-so-bat
```

Không gọi `gui-mot-luot`. Chờ chính auto sync ghi đủ 5 ACKED; receiver ghi 5 DA_LUU và HTTP 200. Sau đó:

```text
dong-bo-tat
doi-chieu
```

Kỳ vọng: cửa hàng 5, ACKED 5, trụ sở 5; số thiếu, lệch nội dung và trùng đều 0. Auto sync chờ 10 giây sau mỗi lượt xử lý; thời gian gửi lỗi làm lượt đó kéo dài thêm.

## 6. Gửi lặp và tạo bản sao trụ sở tại mốc 5

Receiver giữ chạy, auto sync phải tắt:

```text
gui-lap
sao-luu-tru-so
danh-sach-ban-sao
```

Kỳ vọng: 5 ACK DA_TON_TAI; trụ sở vẫn 5. Bản sao mới có 5 giao dịch và integrity_check ok.

Ghi lại chính xác tên bản sao 5 của **phiên demo hiện tại**, gọi là B5. Khi phục hồi về sau phải chọn B5 này; không chép bản sao từ hai phiên lưu minh chứng, không chọn nhầm bản sao an toàn 10.

## 7. Tạo thêm đúng 5 và đồng bộ lên 10

```text
tao-5
dong-bo-bat
```

Đây là lần thứ hai và cuối cùng gọi `tao-5` trong kịch bản. Chờ log thêm 5 ACK cho các mã mới, rồi:

```text
dong-bo-tat
doi-chieu
```

Kỳ vọng: cửa hàng 10, ACKED 10, trụ sở 10; năm trường khớp, thiếu/trùng/lệch đều 0. Nếu chưa đạt, giữ nguyên phiên và log để phân tích, không tạo thêm giao dịch.

## 8. Phục hồi bản 5 và phát hiện dữ liệu thiếu

```text
tru-so-tat
trang-thai
```

Xác nhận receiver và auto sync đều tắt. Trong dòng tiếp theo, thay `TEN_B5_CUA_PHIEN_DEMO.db` bằng tên thật đã ghi ở mục 6:

```text
phuc-hoi TEN_B5_CUA_PHIEN_DEMO.db
doi-chieu
```

Bộ điều khiển sao lưu hiện trạng 10 trước khi phục hồi, giữ mọi bản sao, rồi để cả hai tiến trình tắt.

Kỳ vọng: cửa hàng vẫn 10 ACKED, trụ sở còn 5; đối chiếu liệt kê đúng 5 mã ACKED mà trụ sở thiếu và trả mã 2. Đây là tình trạng cần được phát hiện. Không báo “hai bên khớp” ở mốc này.

Điểm cần giải thích: ACKED là xác nhận đã nhận trước đây. Khi trụ sở quay lại bản sao cũ, auto sync chỉ chọn PENDING/SENT nên không tự gửi lại những dòng ACKED này; chức năng gửi bù của TV2 xử lý phần thiếu.

## 9. Gửi bù và đối chiếu cuối

Giữ auto sync tắt:

```text
tru-so-bat
gui-bu
trang-thai
```

Kỳ vọng: TV2 chọn đúng 5 giao dịch thiếu, báo 5/5 được xác nhận và tự gọi đối chiếu lại. Kết quả cuối phải là cửa hàng 10, ACKED 10, trụ sở 10; dữ liệu khớp, thiếu/trùng/lệch đều 0. Bản sao B5 vẫn còn trong `DuLieu/SaoLuuTruSo`.

Không dùng `tao-5` để bù thiếu và không sửa trực tiếp bảng SQLite. Việc tạo giao dịch mới không khôi phục được các mã cũ đã thiếu.

## 10. Dừng và lưu minh chứng

Tại bộ điều khiển:

```text
dong-bo-tat
tru-so-tat
trang-thai
thoat
```

`thoat` cũng gọi hàm dừng hai tiến trình do bộ điều khiển tạo. Ưu tiên thoát bình thường, không đóng cưỡng bức cửa sổ. Mã có xử lý `Ctrl+C` để đi qua phần dọn dẹp; hai phiên đã kiểm tra kết thúc bằng `thoat` hoặc `Demo.close()`, chưa có ca riêng gây lỗi dọn dẹp.

Ở Terminal đọc log, `Ctrl+C` chỉ dừng theo dõi `Get-Content -Wait`, không thay cho lệnh dừng auto sync. Sau khi thoát, có thể đọc lại trạng thái cổng:

```powershell
Get-NetTCPConnection -LocalPort 18000 -State Listen -ErrorAction SilentlyContinue
```

Nếu còn listener, ghi nhận PID và báo lại; không tự dừng tiến trình không rõ nguồn gốc.

Giữ nguyên thư mục phiên, hai CSDL, bản sao và toàn bộ `MinhChung/`. Khi trình diễn mới, ghi lại kết quả thực tế của lần đó; tên phiên, thời gian và mã giao dịch có thể khác các phiên đã kiểm thử.

## 11. Cách trả lời về phạm vi demo

- Đã có kết quả thực tế cho mất dịch vụ, tự gửi lại, gửi lặp 5, sao lưu trụ sở, phục hồi bản cũ, phát hiện thiếu và gửi bù.
- HTTP 409 có nhánh xử lý trong mã nhưng chưa thử riêng.
- Chưa thử mất ACK sau commit, nhiều POS/cửa hàng, gửi đồng thời hoặc WAN thật.
- Lỗi từ chối kết nối khi receiver tắt không phải phép thử mất ACK sau commit.
- Các chức năng xuất CSV, sao lưu và thử phục hồi kho cửa hàng có trong bộ mã; chưa được chạy trong hai phiên tích hợp.
- Không nhận bản thử là sản phẩm đã tích hợp chính thức. Các điểm cần TV2 xác nhận nằm trong [tài liệu bàn giao](BAN_GIAO_CHO_TV2.md).
