# Môi trường thử tích hợp TV2 và TV3

> Trên nhánh tv3-nang-cao-demo có giám sát và cấu hình nhiều kho; xem [hướng dẫn mới](TV3_HUONG_DAN_DEMO_NANG_CAO.md). Phần mô tả dưới đây giữ phạm vi bản c88fdb9 để tham chiếu luồng TV2–TV3 một cửa hàng. Kết quả mới có nguồn riêng, không thay các kết quả lịch sử.


**Trạng thái: giai đoạn 1, giai đoạn 2 và kiểm thử bổ sung đã ĐẠT trên localhost; đây vẫn là bản thử nghiệm. Phiên demo mới chỉ được tạo khi người dùng chọn phien-moi.**

- TV3: `2159cc8987e44a53e20ce4ee3bded194e8122969`.
- TV2: `f4aeed5d29bc72e7a07e73d3c9ff1a5cb3152af8`.
- Nguồn lấy trực tiếp từ Git object của hai commit; không lấy mã đang sửa trong working tree.
- Không sao chép CSDL 15 giao dịch, file Packet Tracer hoặc log 45 giao dịch. Minh chứng giai đoạn 1/2 và bổ sung được tạo riêng trong môi trường thử, rồi đưa bản đã ẩn đường dẫn lên nhánh này.
- **Schema `truso.db` TV3 là lựa chọn TẠM THỜI của bản thử. Cần TV2 xác nhận trước tích hợp chính thức.**

## Thành phần

```text
TichHop_TV2_TV3_Test/
  README_TICH_HOP.md
  KE_HOACH_KIEM_THU.md
  NGUON_VA_DIEU_CHINH.md
  MANIFEST.json
  NGUON_GIT.json
  SCHEMA_TAM_THOI.sql
  chay_demo.ps1
  demo_tich_hop.py
  Script/                 Mã mẫu kết hợp, có điều chỉnh riêng cho bản thử
  Nguon/
    TV3/Script/           Mã TV3 nguyên gốc tại commit đã chốt
    TV3/chay_auto_sync.ps1
    TV2/Script/           Hai script TV2 nguyên gốc
    TV2/CSDL/             SQL cũ, chỉ tham khảo, KHÔNG áp vào CSDL thử
  PhienThu/               Hai phiên minh chứng đã đạt; phien-moi tạo phiên chạy mới riêng
```

Bộ điều khiển dùng Terminal, không cần website, Docker hay Packet Tracer. Không chép demo web cũ của TV2 vì bản đó dùng TV3 cũ và chưa quản lý auto_sync. Cơ chế dữ liệu vẫn dùng script thật của TV3 và hai script TV2, không viết lại receiver hoặc cơ chế ACK.

## Chạy ở bước tiếp theo, khi đã cho phép kiểm thử

Các lệnh bên dưới hướng dẫn một lần demo mới. Kết quả đã chạy được ghi riêng trong [báo cáo tổng hợp](BAO_CAO_KIEM_THU_TICH_HOP.md) và [báo cáo bổ sung](BAO_CAO_KIEM_THU_BO_SUNG.md); không dùng kết quả cũ để kết luận phiên mới đã đạt.

Mở một Terminal PowerShell:

```powershell
Set-Location -LiteralPath 'THU_MUC_BAN_GIAO'
powershell -NoProfile -ExecutionPolicy Bypass -File .\chay_demo.ps1
```

Bộ điều khiển chỉ hiển thị trợ giúp; chưa tạo CSDL, chưa bật dịch vụ. Sau đó nhập các lệnh tại dấu nhắc `tich-hop>`, không nhập vào PowerShell:

```text
phien-moi
tru-so-bat
dong-bo-bat
trang-thai
```

- `phien-moi`: tạo phiên mới trong `PhienThu/Phien_...`, chép mã mẫu, khởi tạo kho rỗng. Không tạo giao dịch, không bật receiver hoặc auto sync; không xóa phiên cũ.
- `tru-so-bat`: khởi chạy receiver riêng. Receiver tạo CSDL trụ sở trong phiên.
- `dong-bo-bat`: chạy một tiến trình auto_sync thuộc phiên; chờ 10 giây sau mỗi lượt.
- `tru-so-tat`: dừng receiver của phiên, giữ auto sync để thử mất dịch vụ.
- `dong-bo-tat`: dừng tiến trình gửi nền do bộ điều khiển tạo.
- `tao-5`: tạo đúng 5 giao dịch mẫu trong phiên; đây là thao tác ghi dữ liệu chỉ dùng khi bắt đầu kiểm thử.
- `doi-chieu`: cần dừng auto sync để chốt số liệu ổn định. Thiếu dữ liệu/lỗi schema/0-0 không được báo ĐẠT.
- `gui-lap`, `gui-mot-luot`: chạy thủ công khi auto sync đã tắt.
- `sao-luu-tru-so`, `danh-sach-ban-sao`: sao lưu HQ, xem đúng tên file.
- `phuc-hoi TEN_FILE.db`: chỉ nhận tên bản sao trong phiên hiện tại; dừng cả hai tiến trình, sao lưu hiện trạng rồi phục hồi. Không tự bật lại.
- `gui-bu`: cần receiver của phiên đang chạy, auto sync tắt; gửi các giao dịch ACKED mà HQ thiếu, rồi đối chiếu lại.
- `xuat-csv`, `sao-luu-kho`: giữ các công cụ TV3.
- `phuc-hoi-kho TEN_FILE.db`: thử phục hồi bản sao kho vào file riêng, không ghi đè kho đang dùng.
- `thoat` hoặc `Ctrl+C`: bộ điều khiển dừng hai tiến trình con do nó tạo. Nên dùng cách này thay vì đóng cưỡng bức Terminal.

## Cô lập dữ liệu và tiến trình

- Endpoint bản thử: **`http://127.0.0.1:18000/giao-dich`**, khác cổng 8000 của dự án gốc.
- Chỉ lắng nghe localhost. Bộ điều khiển từ chối chiếm cổng 18000 hoặc dừng tiến trình lạ.
- Mã mẫu trong `Script/` không nên chạy trực tiếp; dùng bộ điều khiển để tất cả đường dẫn trỏ tới phiên con.
- Không chạy đồng thời hai bộ điều khiển. Không chạy chương trình khác dùng cổng 18000 trong thời gian thử.
- Mọi bản sao lưu được giữ lại, tạm tắt cơ chế tự xóa bản thứ 8 của TV2 để bảo toàn minh chứng.
- Mỗi phiên có log riêng trong `MinhChung/`: `auto_sync_log.txt`, `receiver_log.txt`, `dieu_khien_log.txt`.
- File log chỉ được tạo khi thực sự chạy thao tác ở bước kiểm thử. Không có log kết quả giả trong bản bàn giao.
- Không có dữ liệu hoặc dịch vụ Python chạy qua WAN Packet Tracer; đây vẫn là phép thử localhost.

## Schema và giới hạn

`SCHEMA_TAM_THOI.sql` trích từ hàm khởi tạo HQ TV3, chỉ để đối chiếu kỹ thuật. Không cần chạy file SQL riêng vì receiver tự khởi tạo.

Giao dịch truyền năm trường: `ma_gd`, `ma_cua_hang`, `ma_may`, `thoi_gian`, `so_tien`. `trang_thai` và `bo_dem` thuộc kho cửa hàng. Receiver commit trước ACK; gửi trùng đúng nội dung trả ACK, khác nội dung trả 409.

SQL cũ TV2 dùng `hq.db`, `ma_ch`, `ma_pos`, `tong_tien`, `so_mat_hang`, `nhat_ky_nhan`; chỉ lưu tham khảo trong `Nguon/TV2/CSDL`, không dùng thay schema thử.

Chưa mở rộng nhiều cửa hàng/POS; chưa triển khai HTTPS, xác thực, mạng thật, lịch sao lưu độc lập hoặc chuyển bản sao sang Server-Backup. Các kết quả đã đạt chỉ áp dụng phạm vi và phiên có minh chứng; bản thử chưa được tích hợp chính thức vào dự án nhóm.

Đọc [kế hoạch kiểm thử](KE_HOACH_KIEM_THU.md) và [nguồn, điều chỉnh](NGUON_VA_DIEU_CHINH.md) trước khi chạy.

## Kiểm thử bổ sung và xử lý lỗi

KT-BS1 xác nhận HTTP 409 không ghi đè HQ. KT-BS2 ngắt ACK sau commit, kiểm tra SENT rồi gửi lại nhận DA_TON_TAI/ACKED. Hồi quy đã kiểm tra cổng bị chiếm, thiếu script, exit 7/9, dọn tiến trình khi dừng sender báo lỗi, thoat/EOF và launcher dưới cp1258. Bộ điều khiển hiện dùng thông báo tiếng Việt, đầu ra UTF-8; launcher có BOM cho PowerShell 5. Không coi phiên mới đã đạt chỉ vì giai đoạn trước đạt. Mã bộ thử: [KiemThu/kiem_thu_bo_sung.py](KiemThu/kiem_thu_bo_sung.py). Những ca ACK sai, CSDL lỗi, đa cửa hàng và WAN vẫn chưa có kết quả.
