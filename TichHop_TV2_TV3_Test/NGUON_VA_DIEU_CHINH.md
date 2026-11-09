# Nguồn và điều chỉnh trong bản thử

## Phiên bản cố định

- TV3: `2159cc8987e44a53e20ce4ee3bded194e8122969`.
- TV2: `f4aeed5d29bc72e7a07e73d3c9ff1a5cb3152af8`.
- File dưới `Nguon/` được xuất nguyên byte từ Git object. `MANIFEST.json` ghi commit, đường dẫn nguồn và SHA-256.
- Không checkout, fetch, pull, merge, commit hay push để chuẩn bị thư mục này.
- Không chứa CSDL, .pkt, log kiểm thử cũ hoặc .git.

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
- Chưa có lịch sao lưu độc lập, HTTPS/xác thực, WAN thật, đa cửa hàng/POS hoặc thử lỗi ACK/409.
- Dừng tiến trình con trên Windows dùng terminate/wait và kill nếu timeout; chỉ nhắm tiến trình do bộ điều khiển tạo. SQLite giữ tính nguyên tử của transaction. Đây mới là thiết kế, chưa được kiểm thử vận hành.
- Kiểm tra chuẩn bị chỉ đọc/parse cú pháp, đường dẫn, nguồn và hash. Không import/chạy ứng dụng, tạo CSDL hoặc lấy kết quả kiểm thử.
