# Kế hoạch kiểm thử tích hợp TV2 + TV3

**Chưa thực hiện. Các số liệu bên dưới là KỲ VỌNG, không phải kết quả đã đạt.**
Chỉ dùng phiên mới do bộ điều khiển tạo. Không dùng database 15 giao dịch hoặc log cũ.

## Chuẩn bị

Chạy bộ điều khiển theo [README](README_TICH_HOP.md). Nhập `phien-moi`, lưu đường dẫn phiên. Chưa tạo giao dịch.
Có thể chờ hơn 10 giây cho mỗi lượt; timeout gửi làm một lượt kéo dài thêm. Không hiểu thành gửi chính xác mỗi 10 giây.

## Các ca chính, thực hiện theo thứ tự

| Mã | Lệnh/thao tác tại tich-hop> | Kỳ vọng cần ghi nhận |
|---|---|---|
| TH0 | `tru-so-bat`, `doi-chieu` khi cả hai kho còn rỗng | Báo CHƯA ĐẠT/0-0 chưa có dữ liệu; không báo khớp thành công. Mã thoát khác 0 là đúng cho ca âm này |
| TH1 | `tru-so-tat`, `tao-5`, `dong-bo-bat`; chờ ít nhất một lượt gửi thất bại; `dong-bo-tat` | Kho giữ đủ 5; sau một lượt lỗi có 5 SENT; log có lỗi kết nối. Không mất giao dịch |
| TH2 | `tru-so-bat`, `dong-bo-bat`; chờ log đủ ACK; `dong-bo-tat`, `doi-chieu` | 5 ở kho, 5 ACKED, HQ 5; dữ liệu năm trường khớp, thiếu và lệch nội dung đều 0 |
| TH3 | `gui-lap`, `doi-chieu` | 5 ACK DA_TON_TAI; HQ vẫn 5, không trùng, dữ liệu không đổi |
| TH4 | `sao-luu-tru-so`, `danh-sach-ban-sao` | Bản sao có 5 giao dịch; integrity_check ok. Ghi lại chính xác tên bản 5 GD, gọi là B5 |
| TH5 | `dong-bo-bat`, `tao-5`; chờ ACK; `dong-bo-tat`, `doi-chieu` | Kho 10, ACKED 10, HQ 10, dữ liệu khớp |
| TH6 | `phuc-hoi TEN_B5_THUC_TE.db`, `trang-thai`, `doi-chieu` | Bộ điều khiển sao lưu HQ 10 trước khi phục hồi. Sau phục hồi cả hai tiến trình tắt; kho vẫn 10 ACKED, HQ 5, phát hiện thiếu đúng 5. Đối chiếu báo chưa đạt là đúng |
| TH7 | `tru-so-bat`, `gui-bu`, `doi-chieu` | TV2 gửi bù 5 giao dịch ACKED còn thiếu; HQ trở lại 10, kho 10 ACKED, lệch/trùng/thiếu đều 0 |
| TH8 | `gui-lap`, `doi-chieu` | Gửi lặp cả 10; HQ vẫn 10, 10 ACK DA_TON_TAI |
| TH9 | `dong-bo-bat`, `trang-thai`, `dong-bo-tat`, `trang-thai`, `thoat` | Chỉ một auto sync; dừng được; thoát dừng receiver và auto sync thuộc phiên; không dừng dịch vụ ngoài |
| TH10 | Mở lại bộ điều khiển, `phien-moi` | Tạo thư mục phiên khác; toàn bộ file phiên cũ và bản sao vẫn còn, không reset/ghi đè |

Thay `TEN_B5_THUC_TE.db` bằng tên chính xác của bản sao B5. Không gõ ký hiệu mô tả như một tên file thật.

## Ca bổ sung sau khi ca chính đạt

- `sao-luu-kho` rồi `phuc-hoi-kho TEN_BAN_SAO_KHO.db`: dữ liệu và bộ đếm khớp; file phục hồi ở `PhucHoiThu`, không ghi đè kho.
- `xuat-csv`: CSV có đúng số giao dịch và trạng thái tại thời điểm xuất.
- Thiếu file CSDL/lỗi schema: chỉ thực hiện trong một phiên lỗi riêng sau khi được cho phép thao tác dữ liệu. Đối chiếu phải báo lỗi, không chuyển thành 0-0 thành công.
- Cùng mã khác nội dung (HTTP 409), ACK sai mã, mất ACK sau commit: cần bổ sung cách kích lỗi có kiểm soát, chưa có bộ gây lỗi trong bản chuẩn bị này. Không tuyên bố đã kiểm thử các nhánh đó.
- Chạy khôi phục lại cùng bản sao và gửi bù lại: dữ liệu vẫn đúng, không tạo bản trùng.

## Minh chứng cần lưu khi chạy thật

Trong `PhienThu/Phien_.../MinhChung`, giữ log receiver, auto sync và điều khiển; chụp số liệu đối chiếu từng mốc.
Ghi tên ca, thời gian, phiên, số kho/HQ/ACKED, số thiếu/trùng/lệch, tên bản sao và kết luận thực tế.

Nếu kết quả khác kỳ vọng: dừng auto sync, giữ nguyên phiên và log, không làm mới/xóa dữ liệu để che lỗi.
Không cộng bộ 5/10 của phép thử này với bộ TV3 gốc 15 hoặc log TV2 cũ 45.
