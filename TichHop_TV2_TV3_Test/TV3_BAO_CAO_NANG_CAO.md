# Báo cáo nâng cao TV3 – kết quả thực tế

## 1. Phạm vi

Nhánh tv3-nang-cao-demo được tạo từ commit tích hợp c88fdb963ecc93efcac0584f2da9b9c740b3e1d8. Không checkout hoặc sửa các worktree cũ. Đợt xây dựng và kiểm thử hoàn thành độc lập trước bước công bố; kết quả dưới đây giữ theo log thực tế. Bước công bố chỉ rà soát, cập nhật trạng thái tài liệu và đưa lên nhánh riêng, không chạy lại kiểm thử, merge hoặc tạo PR.

P0 gồm giám sát chỉ đọc, kiểm tra ACK lỗi, giữ dữ liệu và hồi quy. P1 là hai cửa hàng/POS cấu hình độc lập, cùng receiver, không đổi schema. Mọi ca dùng runtime mới; không dùng CSDL 15 giao dịch hoặc hai phiên giai đoạn 1/2 đã đạt. Các phép thử dùng localhost:18000.

## 2. Những gì thay đổi

| File | Điều chỉnh |
|---|---|
| Script/store_agent.py | Cấu hình cửa hàng/POS/file DB; kiểm tra mã và đường dẫn trong phiên, ngăn dùng chung file khác danh tính; kiểm tra số tiền nguyên dương; cờ mô phỏng chặn gửi HTTP |
| Script/kiem_tra_trung.py | Chọn DB và phạm vi cửa hàng/POS từ cấu hình; so sánh toàn bộ HQ trước/sau gửi lặp, không yêu cầu HQ chỉ có một cửa hàng |
| Script/giam_sat.py | Công cụ mới: SQLite mode=ro, query_only; thống kê, so sánh năm trường, phát hiện thiếu/thừa/lệch/trùng, cảnh báo và kiểm tra phản hồi HTTP bằng GET |
| demo_tich_hop.py | Tận dụng controller cũ; chọn kho, quản lý sender riêng, ngắt/nối mô phỏng, giám sát; đóng mọi sender và receiver; giới hạn công cụ cũ cố định CH01 |
| KiemThu/kiem_thu_bo_sung.py | Chỉ bổ sung giam_sat.py vào danh sách chép bắt buộc; giữ tiêu chí bảy ca hồi quy |
| KiemThu/kiem_thu_nang_cao.py | Bộ thử mới, receiver giả có kiểm soát, runtime độc lập; có chế độ chỉ thử giới hạn công cụ |

Không sửa hq_receiver.py, auto_sync.py, hai script TV2, schema hoặc Nguon/. Mặc định vẫn CH01/POS01 và DuLieu/cuahang01.db. Kho thứ hai nằm tại DuLieu/CuaHang/CH02_POS01.db, có bộ đếm riêng; mã giao dịch gồm cả mã cửa hàng/POS. Không có chuyển đổi schema.

SENT cho biết lượt xử lý gửi đã bắt đầu, chưa có ACK hợp lệ. Trong chế độ mô phỏng ngắt riêng, chương trình không thực hiện HTTP, vẫn giữ SENT; không suy ra request đã tới mạng hay trụ sở.

## 3. Các lượt thực thi và phiên bản

| Runtime | Thời gian ngày 09/11/2026, +07:00 | Thực tế |
|---|---|---|
| HoiQuy_20261109_174201_4848616 | 17:42:01–17:42:08 | PASS 7/7 |
| NangCao_20261109_174308_0814826 | 17:43:08–17:44:21 | PASS 13/13 |
| GioiHan_20261109_175222_2296345 | 17:52:23 | PASS 1/1, chặn năm lệnh |
| CongLa_20261109_180721_0013856 | 18:07:21 | PASS 1/1, từ chối nối lại tới cổng ngoài phiên |

Sau khi đạt 13 ca, rà soát phát hiện xuat-csv/sao-luu-kho/phuc-hoi-kho cũ vẫn cố định CH01. Controller được bổ sung điều kiện chặn ba lệnh đó trong phiên nhiều kho và điều chỉnh lời báo giới hạn. NC08 kiểm tra đúng phần thay đổi này, không chạy lại toàn bộ các ca đã đạt. Kịch bản thử có thêm --only-guards. Rà soát tiếp phát hiện lệnh nối lại chưa kiểm tra cổng ngoài phiên; bổ sung kiểm tra trước khi đổi cấu hình hoặc bật sender, rồi chạy riêng NC09 bằng --only-port-guard. Không chạy lại các ca không bị ảnh hưởng. Không thay đổi mã gửi/receiver/monitor sau lượt 13 ca.

Mỗi JSON tổng kết giữ source_sha256 của đúng mã tại thời điểm chạy. Hash controller/bộ thử giữa các lượt có thể khác vì bổ sung giới hạn kể trên; không thay các hash cũ bằng hash mới để giả lập một lần thử lại. MANIFEST.json ghi hash mã hiện tại và phạm vi xác minh theo từng lượt.

## 4. Chi tiết ca nâng cao

| Ca | Kết quả thực tế | Đánh giá |
|---|---|---|
| NC01 | Thiếu HQ báo lỗi và không tạo DB; sau bật receiver, 0/0 vẫn không coi hoàn tất; hash CSDL không đổi qua giám sát | ĐẠT |
| NC02 wrong_id | ack=true nhưng mã sai: SENT 1, ACKED 0, HQ 0; receiver thật sau đó ACKED 1/HQ 1 | ĐẠT |
| NC02 array | JSON là mảng thay vì object: giữ SENT; gửi lại receiver thật thành công | ĐẠT |
| NC02 invalid_json | Phản hồi không phải JSON hợp lệ: giữ SENT; gửi lại thành công | ĐẠT |
| NC02 ack_false | ack=false: không ACKED; gửi lại thành công | ĐẠT |
| NC02 ack_number | ack=1: không được coi là boolean true, không ACKED; gửi lại thành công | ĐẠT |
| NC02 ack_string | ack="true": không ACKED; gửi lại thành công | ĐẠT |
| NC02 missing_ack | Thiếu ack: không ACKED; gửi lại thành công | ĐẠT |
| NC03 | Receiver tắt, tạo 20; cùng auto sync giữ đủ SENT 20 rồi tự gửi khi bật receiver: ACKED 20/HQ 20; gửi lặp 20 không tăng HQ | ĐẠT |
| NC04 | Hai kho 5+5: chặn CH02, CH01 ACKED 5/CH02 SENT 5/HQ 5; nối lại ACKED 10/HQ 10; lặp từng kho không đổi hash HQ | ĐẠT |
| NC05 | Hai lần tạo từ hai subprocess cho mã 000001/000002; từ chối 5 giá trị tiền sai và 3 cấu hình nguy hiểm/dùng nhầm DB; dữ liệu giữ nguyên | ĐẠT |
| NC06 | Fixture mới cố ý sửa số tiền HQ: cùng tổng 1/1 nhưng phát hiện lệch; HQ fixture sai schema báo lỗi; giám sát không sửa DB | ĐẠT |
| NC07 | CLI có receiver và hai sender; thoat trả 0, ba PID đều dừng | ĐẠT |
| NC08 | doi-chieu, gui-bu, xuat-csv, sao-luu-kho, phuc-hoi-kho bị chặn trong phiên nhiều kho; toàn bộ file/DB không đổi sau các lệnh | ĐẠT |
| NC09 | Socket thử giữ cổng 18000; noi-cua-hang bị từ chối, trạng thái offline còn giữ, sender không bật, socket không bị đóng | ĐẠT |

Bảy NC02 là bảy ca riêng. Mỗi ca tạo đúng một giao dịch trong một phiên mới; receiver giả chỉ trả phản hồi lỗi, không lưu giao dịch. Sau đó thay bằng receiver thật để xác nhận dữ liệu giữ lại vẫn gửi được. Không dùng receiver giả trong demo hoạt động bình thường.

Fixture NC06 là lỗi dữ liệu/schema được chủ động dựng trong phiên mới để thử cảnh báo, không phải lỗi phát sinh từ luồng giao dịch và không được dùng làm kết quả đồng bộ thành công. Các lỗi được chờ đợi trong NC05/NC08 là kết quả từ chối an toàn.

## 5. Hồi quy

KT-BS1 HTTP 409, KT-BS2 mất ACK sau commit và HR-01 đến HR-05 đều ĐẠT. Dù đã có kết quả cũ, lần này cấu hình của sender và quản lý tiến trình thay đổi nên cần chạy bộ hồi quy trên runtime mới.

Bộ thử xác nhận HQ không ghi đè/trùng, SENT được giữ sau mất ACK và chỉ ACKED sau ACK hợp lệ; đồng thời kiểm tra cổng bị chiếm, thiếu script, exit 7/9, lỗi sender.stop, CLI thoat/EOF và launcher/cp1258. Giai đoạn 1/2 về sao lưu/phục hồi/gửi bù không chạy lại toàn bộ; kết quả của chúng vẫn là kết quả tại mốc c88fdb9, không tự nhận đã kiểm chứng lại mọi chức năng với mã mới.

## 6. Minh chứng

- [Tổng kết hồi quy 7 ca](MinhChungNangCao/HoiQuy_20261109_174201_4848616/MinhChung/KET_QUA_BO_SUNG.json) và [Terminal hồi quy](MinhChungNangCao/HoiQuy_20261109_174201_4848616/MinhChung/terminal_bo_sung.txt).
- [Tổng kết nâng cao 13 ca](MinhChungNangCao/NangCao_20261109_174308_0814826/MinhChung/KET_QUA_NANG_CAO.json) và [Terminal nâng cao](MinhChungNangCao/NangCao_20261109_174308_0814826/MinhChung/terminal_nang_cao.txt).
- [Mốc 20 giao dịch](MinhChungNangCao/NangCao_20261109_174308_0814826/MinhChung/NC03_CHO_20_VA_TU_PHUC_HOI.json).
- [Hai cửa hàng 5+5](MinhChungNangCao/NangCao_20261109_174308_0814826/MinhChung/NC04_HAI_CUA_HANG.json).
- [Từ chối nối lại vào cổng lạ](MinhChungNangCao/CongLa_20261109_180721_0013856/MinhChung/KET_QUA_NANG_CAO.json).
- [Giới hạn công cụ cũ](MinhChungNangCao/GioiHan_20261109_175222_2296345/MinhChung/KET_QUA_NANG_CAO.json) và [Terminal ca giới hạn](MinhChungNangCao/GioiHan_20261109_175222_2296345/MinhChung/terminal_nang_cao.txt).

Các log con của từng phiên nằm dưới mỗi runtime trong MinhChungNangCao/. Đây là bản sao đã ẩn đường dẫn máy bằng RUNTIME_TV3, MA_NGUON_TV3 hoặc THU_MUC_NGUOI_DUNG. CSDL, log gốc và mã runtime vẫn ở môi trường TV3_NangCao_Runtime bên ngoài repository; không đưa DB/cache vào Git. Không cộng các bộ 20, 5+5, các ca một giao dịch hoặc bộ 15 gốc thành một bộ kết quả.

## 7. Giới hạn và việc cần xác nhận

- Hai cửa hàng là hai DB và hai tiến trình trên một máy; chưa thử hai POS cùng cửa hàng, nhiều máy/POS vật lý, tải lớn hoặc cạnh tranh ghi đồng thời. Bộ đếm đã thử khởi động lại tuần tự; không nhận đây là thử tải song song.
- Chặn HTTP riêng một cửa hàng là mô phỏng có kiểm soát tại sender. Ca dịch vụ tắt NC03 dùng receiver dừng thật trên localhost. Cả hai không phải phép thử WAN/Packet Tracer.
- Chưa có HTTPS/xác thực. GET chỉ phát hiện HTTP phản hồi, không xác minh dịch vụ thuộc phiên hoặc bảo đảm POST/ACK. HTTP 501 ở probe là do receiver chỉ có POST.
- Giám sát chụp từng CSDL; số liệu khi đang gửi có thể khác thời điểm. Dừng tất cả sender trước khi chốt kết quả. Khi có lỗi đọc DB, các số đọc được chỉ là phần đã biết, không kết luận từ các chỉ số thiếu/thừa đang rỗng.
- Chưa mở rộng doi-chieu/gui-bu TV2 và CSV/sao lưu/phục hồi kho TV3 cho nhiều kho. Controller chặn thay vì thao tác nhầm CH01. Sao lưu/phục hồi HQ sau nhiều cửa hàng chưa có ca riêng.
- --watch có trong công cụ nhưng đợt này kiểm tra snapshot và lệnh controller, chưa kiểm thử riêng nhánh chạy lặp/nhấn Ctrl+C của watcher.
- Schema TV3 vẫn tạm thời, cần TV2 xác nhận. Chưa merge vào dự án chính. Cần thống nhất chính sách sao lưu, cấu hình liên máy, phân quyền, bảo mật và thử lại phạm vi tích hợp chính thức.
- Mất điện, tắt cưỡng bức Terminal, nhánh kill timeout và lỗi SQLite hỏng vật lý vẫn chưa kiểm thử.

Đọc [tổng kết họp nhóm](TV3_TONG_KET_HOP_NHOM.md) và [hướng dẫn demo](TV3_HUONG_DAN_DEMO_NANG_CAO.md). Các chức năng đã đạt có thể trình diễn bằng phiên mới, còn phần chưa thử được nêu riêng để nhóm quyết định bước tiếp theo.

## 8. Kiểm tra tĩnh và bảo toàn khi bàn giao

Đã parse 22 file Python và 2 file PowerShell; kiểm tra 14 tài liệu Markdown, 114 liên kết tương đối. Không phát hiện CSDL, cache, ZIP, đường dẫn cá nhân hoặc khóa bí mật trong thư mục tích hợp. Không còn tiến trình Python của runtime và cổng 18000 đã rảnh sau thử.

Đã đối chiếu hash của 46 file repository gốc, 133 file worktree tích hợp và 228 file môi trường thử cũ; không file nào thay đổi. Nguon/, schema và các phiên minh chứng đã đạt trong nhánh mới khớp byte commit gốc, ngoại trừ những file ứng dụng/tài liệu được nêu rõ là nâng cấp. Ở mốc hoàn thành kiểm thử, các thay đổi chưa được stage hoặc commit; đây là thông tin lịch sử trước bước công bố.

Git Windows tự đổi xuống dòng lúc checkout worktree. Các file không sửa đã được khôi phục nguyên byte Git object chỉ trong worktree mới; không ghi DB/Packet Tracer. Tám file ứng dụng/launcher không sửa có hash hiện tại khác bản runtime do duy nhất CRLF/LF; so sánh sau chuẩn hóa xuống dòng khớp hoàn toàn. Hash thực tế trong log vẫn được giữ nguyên, hash bản bàn giao hiện tại nằm trong manifest/danh mục. Không chạy lại thử nghiệp vụ chỉ vì khôi phục xuống dòng không làm đổi mã thực thi.
