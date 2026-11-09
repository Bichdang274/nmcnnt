# BÁO CÁO KIỂM THỬ BỔ SUNG VÀ HỒI QUY TV2–TV3

## 1. Phạm vi và kết luận

Đợt hoàn thiện bắt đầu từ commit tích hợp `a4c19aed4ce07a50b6983a2d95b869cb4ff216fe`. TV2 vẫn ở `f4aeed5`, TV3 vẫn ở `2159cc8` khi kiểm tra remote; không có bản mới cần ghép. Không merge hoặc thay đổi các nhánh nguồn.

**Kết quả cuối: KT-BS1, KT-BS2 và năm nhóm hồi quy đều ĐẠT.** Mỗi ca dùng dữ liệu mới trong runtime riêng trên localhost:18000; không dùng CSDL gốc hoặc hai phiên đã đạt. Không chạy lại toàn bộ giai đoạn 1 và 2.

Các thay đổi chỉ ở bộ điều khiển, launcher, bộ kiểm thử, tài liệu và metadata. Chín script giao dịch/đối chiếu/sao lưu trong Script/ và schema không bị sửa trong đợt này. Nguồn tham chiếu Nguon/ giữ nguyên.

## 2. Các vấn đề thực tế đã sửa

| Vấn đề | Điều chỉnh |
|---|---|
| Banner ghi chưa có kết quả kiểm thử dù giai đoạn 1 và 2 đã đạt | Nêu kết quả lịch sử và phân biệt phiên mới chưa tạo/chưa kiểm thử |
| Tiếng Việt trên stdout chuyển hướng dùng cp1258 có thể lỗi | Bộ điều khiển và bộ thử cấu hình UTF-8; launcher lưu UTF-8 có BOM và cấu hình đầu ra phù hợp |
| close dừng sender trước; sender.stop báo lỗi có thể bỏ qua receiver | Dùng try/finally để luôn thử dừng receiver; tái sử dụng close trước tạo phiên/phục hồi |
| Thiếu script chỉ được phát hiện sau khi cố mở tiến trình | Kiểm tra script trước Popen; kiểm tra bộ file bắt buộc trước khởi động CLI |
| Hướng dẫn và lỗi khó đọc | Chuẩn hóa thông báo tiếng Việt; lỗi script con tiếp tục được trả mã thoát và ghi log, không coi bước đó đã đạt |

Một lượt khởi tạo lúc 09:19:13 ngày 09/11/2026 đã dừng vì UnicodeEncodeError trước khi tạo giao dịch hoặc bật receiver. Lượt này **CHƯA ĐẠT ở bước chuẩn bị**, chưa thực hiện HTTP 409 hay mất ACK. Log lỗi được giữ nguyên, bản đưa lên Git đã ẩn đường dẫn máy: [kết quả lượt lỗi](MinhChungBoSung/HoanThien_20261109_091911_9358106/MinhChung/KET_QUA_BO_SUNG.json), [trace lỗi](MinhChungBoSung/HoanThien_20261109_091911_9358106/MinhChung/terminal_bo_sung.txt).

Sau khi sửa bảng mã, các ca chưa thực hiện được chạy trên runtime mới lúc 15:46:58–15:47:07 cùng ngày, múi giờ +07:00. Không dùng lại dữ liệu của lượt lỗi.

## 3. KT-BS1 — cùng mã khác nội dung

1. Tạo một giao dịch thử số tiền 50.000 và gửi hợp lệ; cửa hàng ACKED 1, HQ có 1.
2. Gửi HTTP POST cùng mã và các trường còn lại giữ nguyên, chỉ đổi số tiền thành 50.001.
3. Receiver trả HTTP 409 và nội dung báo xung đột.
4. So sánh bản ghi HQ trước/sau: giữ nguyên 50.000, không ghi đè, không thêm bản trùng; integrity_check ok.

**ĐẠT.** [Minh chứng KT-BS1](MinhChungBoSung/HoanThien_20261109_154657_2899761/MinhChung/KT_BS1_HTTP409.json) lưu yêu cầu xung đột, mã HTTP, phản hồi và dữ liệu trước/sau.

## 4. KT-BS2 — mất ACK sau commit

Bộ thử tạo một receiver gây lỗi chỉ trong runtime: kế thừa handler TV3 hiện có, kiểm tra giao dịch đã commit bằng kết nối SQLite chỉ đọc, rồi đóng kết nối HTTP trước khi gửi ACK đầu tiên. Mã receiver ứng dụng và schema không bị sửa để tạo kết quả này.

| Mốc thực tế | Cửa hàng | HQ | Kết quả |
|---|---|---|---|
| Lần gửi đầu, ACK bị ngắt | 1 SENT, chưa ACKED | 1 bản ghi đã commit | Cửa hàng báo chưa được xác nhận và giữ dữ liệu |
| Gửi lại chính giao dịch đó | 1 ACKED | Vẫn 1 bản ghi | Receiver nhận diện DA_TON_TAI, trả ACK hợp lệ rồi cửa hàng mới cập nhật ACKED |

**ĐẠT.** Không tạo bản ghi trùng hoặc đổi nội dung HQ. [Minh chứng KT-BS2](MinhChungBoSung/HoanThien_20261109_154657_2899761/MinhChung/KT_BS2_MAT_ACK.json) có marker xác nhận điểm gây lỗi sau commit, trạng thái sau mất ACK và sau gửi lại. Kịch bản tạo receiver gây lỗi được lưu trong [mã bộ thử](KiemThu/kiem_thu_bo_sung.py).

Đây là mô phỏng ngắt phản hồi ở lớp HTTP trên localhost, không phải phép thử mất WAN thật. ACK sai mã hoặc JSON ACK sai định dạng vẫn chưa có ca riêng.

## 5. Hồi quy phần bị ảnh hưởng

| Ca | Thực hiện và kết quả thực tế |
|---|---|
| HR-01 | Socket thử giữ cổng 18000; bộ điều khiển từ chối khởi động receiver, không đóng socket giữ cổng hoặc tạo tiến trình ngoài phiên |
| HR-02 | Thiếu script được báo trước khi Popen; script con exit 7 và script khởi động exit 9 đều được báo lỗi, không báo thành công |
| HR-03 | Auto sync đồng bộ một giao dịch tới ACKED; mô phỏng lỗi sender.stop sau khi đã dừng sender, close vẫn dừng receiver; không còn hai PID của phiên |
| HR-04 | CLI thoat và EOF đều dừng hai tiến trình con; launcher PowerShell thoát 0; các subprocess được cố ý đặt PYTHONIOENCODING=cp1258 để kiểm tra UTF-8 của main |
| HR-05 | CLI thiếu auto_sync.py dừng với mã khác 0 trước khi tạo phiên hoặc dịch vụ |

Tất cả **ĐẠT** trong [kết quả JSON](MinhChungBoSung/HoanThien_20261109_154657_2899761/MinhChung/KET_QUA_BO_SUNG.json) và [Terminal thực tế](MinhChungBoSung/HoanThien_20261109_154657_2899761/MinhChung/terminal_bo_sung.txt). Cổng 18000 không còn listener sau khi bộ thử kết thúc.

Các lỗi được chủ động gây ra trong HR-01/02/03 là điều kiện thử; chúng đã được nhận biết và xử lý đúng. Không coi các lỗi mong đợi này là bước nghiệp vụ thành công.

## 6. Minh chứng, bảo toàn và tái hiện

Các file được lưu tại MinhChungBoSung/ gồm bản sao log/JSON đã ẩn đường dẫn cục bộ; CSDL, cache và các bản mã runtime không đưa vào Git. Log gốc cùng dữ liệu mới vẫn được giữ trong môi trường thử độc lập. Hai phiên giai đoạn 1/2 và nguồn Nguon/ không bị sửa.

Muốn tái hiện ở một lần được cho phép sau này, dùng [KiemThu/kiem_thu_bo_sung.py](KiemThu/kiem_thu_bo_sung.py) và truyền --runtime-root là đường dẫn mới hoàn toàn, ngoài thư mục mã nguồn. Bộ thử từ chối ghi đè runtime đã tồn tại. Mã bộ thử tự sao chép các file cần thiết, chạy các ca tuần tự, ghi minh chứng và dừng các tiến trình của nó. Lệnh mẫu phải thay đường dẫn trước khi chạy:

```powershell
$thuMucThuMoi = 'DUONG_DAN_TUYET_DOI_NGOAI_REPOSITORY\HoanThien_MOI'
python -B -u .\KiemThu\kiem_thu_bo_sung.py --runtime-root $thuMucThuMoi
```

Không mở lại hoặc chép đè vào các runtime có sẵn. Nếu một ca lỗi, bộ thử dừng ca tiếp theo, giữ log và dữ liệu để phân tích; không tự chạy lại toàn bộ.

## 7. Giới hạn còn lại

- Schema TV3 vẫn tạm thời, chưa được TV2 xác nhận.
- Chưa chứng minh Python đi qua WAN Packet Tracer hoặc WAN thực tế.
- Chưa triển khai nhiều cửa hàng/POS thực tế hoặc đánh giá tải đồng thời.
- Chưa có ca riêng cho ACK sai mã/sai JSON, CSDL mất/hỏng/sai schema, mất điện, tắt cưỡng bức Terminal hoặc nhánh kill do timeout.
- Chưa chạy lịch sao lưu tự động hoặc chuyển bản sao sang Server-Backup trong bản tích hợp.
- Đây vẫn là nhánh thử nghiệm, chưa merge vào dự án chính.

[Báo cáo tổng hợp](BAO_CAO_KIEM_THU_TICH_HOP.md) giữ nguyên số liệu hai giai đoạn trước và dẫn thêm kết quả này. Bản đã hoàn thiện đủ để TV2 tiếp nhận rà soát trong phạm vi nêu trên, chưa phải nghiệm thu toàn bộ hệ thống nhóm.
