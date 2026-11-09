# Nguồn và điều chỉnh trong bản thử

## Phiên bản cố định

- TV3: `2159cc8987e44a53e20ce4ee3bded194e8122969`.
- TV2: `f4aeed5d29bc72e7a07e73d3c9ff1a5cb3152af8`.
- File dưới `Nguon/` được xuất nguyên byte từ Git object. `MANIFEST.json` ghi commit, đường dẫn nguồn và SHA-256.
- Ở bước chuẩn bị môi trường ban đầu, không checkout, fetch, pull, merge, commit hay push; việc lưu lên nhánh thử nghiệm được thực hiện ở bước riêng sau đó.
- Không đưa CSDL, .pkt hoặc .git vào thư mục bàn giao. Các log giai đoạn 1/2 và bổ sung được lưu riêng làm minh chứng; không lấy log 45 giao dịch TV2 làm kết quả tích hợp.

## Điều chỉnh có chủ đích, chỉ trong bản sao

| File | Điều chỉnh |
|---|---|
| `Script/store_agent.py` | Endpoint đọc từ TV23_HQ_URL; mặc định localhost:18000. Giữ cơ chế tạo mã, SQLite transaction, PENDING/SENT/ACKED |
| `Script/hq_receiver.py` | Cổng đọc TV23_HQ_PORT, mặc định 18000; chỉ localhost. Giữ schema và xử lý ACK/409 |
| `Script/kiem_tra_trung.py` | Cùng endpoint thử; ca không đạt trả mã thoát khác 0 |
| `Script/doi_chieu.py` | Cùng endpoint thử; thiếu file/lỗi SQL không trả danh sách rỗng giả; 0-0 không coi là đạt; kiểm tra ACK là object; CLI trả mã thoát theo kết quả |
| `Script/sao_luu_tru_so.py` | Tắt tự xóa bản sao cũ; bỏ thao tác xóa thử dữ liệu khỏi CLI bản thử; giữ backup API và phục hồi |
| `Script/kiem_tra_phuc_hoi.py` | Bắt buộc --file là tên bản sao kho trong phiên, không dùng tên bản cũ hard-code |
| `demo_tich_hop.py` | Bộ điều khiển Terminal mới; quản lý một receiver và một auto sync; phiên riêng, không xóa phiên cũ; log riêng; mã thoát lỗi không coi thành công |
| `chay_demo.ps1` | Chạy bộ điều khiển tại đúng thư mục, không tự chạy thử hoặc tạo dữ liệu |

`Script/auto_sync.py`, `Script/sao_luu.py`, `Script/xuat_giao_dich.py` giữ nguyên byte nguồn TV3.
Bộ điều khiển phục hồi tắt cả hai tiến trình, sao lưu hiện trạng trước rồi mới phục hồi; không tự bật lại sender. Người thử đối chiếu và gửi bù trước khi bật lại.

Bản thử chủ động giữ mọi bản sao, khác chính sách 7 bản trong script TV2 gốc. Đây là lựa chọn bảo toàn dữ liệu thử, chưa thay chính sách vận hành chính thức.

## Tương thích và phần chưa giải quyết

- Chọn tạm schema năm trường của TV3. Cần xác nhận với TV2; chưa chuyển đổi schema SQL cũ.
- Hai script TV2 mới được thiết kế cho CH01/POS01 và cùng máy với hai CSDL; chưa hỗ trợ đối chiếu qua API giữa các máy.
- Không sửa auto_sync để gửi mọi ACKED: gửi bù sau phục hồi là thao tác riêng do TV2 thực hiện.
- Chưa có lịch sao lưu độc lập, HTTPS/xác thực, WAN thật hoặc đa cửa hàng/POS. KT-BS1 đã thử HTTP 409 và KT-BS2 đã thử mất ACK sau commit; ACK sai mã/định dạng vẫn chưa thử.
- Dừng tiến trình con trên Windows dùng terminate/wait và kill nếu timeout; chỉ nhắm tiến trình do bộ điều khiển tạo. SQLite giữ tính nguyên tử của transaction. Đã kiểm tra dừng bình thường, thoat/EOF và receiver vẫn được dừng khi sender.stop báo lỗi. Chưa thử tắt cưỡng bức hoặc nhánh kill do timeout.
- Kiểm tra chuẩn bị ban đầu chỉ đọc/parse cú pháp, đường dẫn, nguồn và hash. Các lần kiểm thử thực tế được thực hiện sau đó trong phiên riêng và có báo cáo, log đi kèm.

## Đợt hoàn thiện cuối trên nhánh tích hợp

Chỉ demo_tich_hop.py và chay_demo.ps1 thay đổi về mã ứng dụng: cập nhật tiếng Việt/banner, cố định đầu ra UTF-8, kiểm tra file bắt buộc và luôn thử dừng receiver trong finally. Launcher lưu UTF-8 BOM cho PowerShell 5. Chín script dữ liệu và schema giữ nguyên; Nguon/ không sửa. Bộ thử mới KiemThu/kiem_thu_bo_sung.py tạo dữ liệu mới và receiver ngắt ACK chỉ trong runtime.

Lượt khởi tạo đầu lỗi cp1258 được giữ; sau sửa, hai ca bổ sung và năm nhóm hồi quy ĐẠT. Tài liệu, manifest và hash cập nhật theo kết quả thật; giai đoạn 1/2 không chạy lại và không ghi đè. [Báo cáo bổ sung](BAO_CAO_KIEM_THU_BO_SUNG.md) dẫn toàn bộ minh chứng. Các trường preparation_* trong manifest giữ lịch sử trước kiểm thử, không mô tả trạng thái hiện tại.

SO_SANH_MA_NGUON.patch giữ phần so sánh Nguon/ với Script/ đã có; phần bổ sung so sánh bộ điều khiển/launcher với commit tích hợp a4c19ae và ghi bộ thử mới so với file chưa tồn tại.
