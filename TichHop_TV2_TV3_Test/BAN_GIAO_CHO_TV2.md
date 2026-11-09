# BÀN GIAO BẢN TÍCH HỢP THỬ NGHIỆM CHO TV2

**Người phụ trách TV3:** Thành viên 3.  
**Phạm vi bàn giao:** Mã mẫu, bộ điều khiển Terminal, dữ liệu và minh chứng tích hợp thử TV2–TV3 trên localhost.  
**Trạng thái:** Đủ để TV2 tiếp nhận, rà soát và thống nhất bước tiếp theo. Chưa xác nhận tích hợp chính thức vào repository nhóm.

## 1. Nguồn và những gì được bàn giao

| Thành phần nguồn | Phiên bản cố định |
|---|---|
| TV3 | `2159cc8987e44a53e20ce4ee3bded194e8122969` |
| TV2 | `f4aeed5d29bc72e7a07e73d3c9ff1a5cb3152af8` |

- `Nguon/`: bản xuất nguyên gốc tại hai commit, phục vụ đối chiếu.
- `Script/`: chín script mẫu dùng trong môi trường thử, gồm phần TV3 và hai script TV2 đã điều chỉnh.
- `demo_tich_hop.py`, `chay_demo.ps1`: bộ điều khiển và launcher.
- `PhienThu/Phien_20261109_014617_838147`: phiên giai đoạn 1, kết thúc ở 5 ACKED và HQ 5.
- `PhienThu/Phien_GD2_20261109_020609_227458`: phiên giai đoạn 2 riêng, kết thúc ở 10 ACKED và HQ 10, kèm hai bản sao HQ.
- [Báo cáo tổng hợp](BAO_CAO_KIEM_THU_TICH_HOP.md), [hướng dẫn demo nhóm](HUONG_DAN_DEMO_NHOM.md) và tài liệu này.

[NGUON_GIT.json](NGUON_GIT.json) và Nguon/ giữ nguyên nguồn tham chiếu. MANIFEST.json và danh mục hash đã cập nhật trạng thái kiểm chứng, giữ lịch sử chuẩn bị trong các trường preparation_*. Banner, README và kế hoạch hiện phân biệt các ca đã đạt với phiên mới chưa chạy. Các log giai đoạn 1/2 giữ nguyên byte.

Các script chép trong hai phiên giống mã mẫu `Script/` tại lần rà soát lập tài liệu. Không sao chép CSDL 15 giao dịch từ repository gốc hay dùng log 45 giao dịch TV2 để lập kết quả tích hợp này.

## 2. Phần TV3 đã hoàn thành và mức kiểm chứng

| Phần TV3 | Vai trò | Kết quả trong hai phiên |
|---|---|---|
| `store_agent.py` | Lưu trước khi gửi, sinh mã có bộ đếm SQLite, quản lý trạng thái và kiểm tra ACK | Đã lưu và đồng bộ bộ 5, rồi thêm đúng 5 thành 10 |
| `hq_receiver.py` | Nhận JSON, kiểm tra dữ liệu, commit trước ACK, xử lý mã trùng | Đã nhận giao dịch mới và trả ACK cho 5 giao dịch gửi lặp |
| `auto_sync.py` | Gọi lại hàm gửi PENDING/SENT, chờ 10 giây sau mỗi lượt | Đã giữ 5 SENT khi dịch vụ tắt và tự gửi khi phục hồi |
| `kiem_tra_trung.py` | Gửi lặp, kiểm tra DA_TON_TAI và đối chiếu dữ liệu | Đã thử gửi lặp 5, HQ không tăng, trùng 0 |
| `xuat_giao_dich.py`, `sao_luu.py`, `kiem_tra_phuc_hoi.py` | CSV, sao lưu và thử phục hồi kho cửa hàng | Có trong gói; chưa chạy trong hai phiên tích hợp |

KT-BS1 đã kiểm tra HTTP 409, không ghi đè/trùng HQ. KT-BS2 đã ngắt ACK sau commit, xác nhận SENT trước gửi lại, DA_TON_TAI rồi ACKED và HQ vẫn một bản ghi. Đây là các ca riêng trên localhost, có [minh chứng bổ sung](BAO_CAO_KIEM_THU_BO_SUNG.md); việc receiver tắt trong giai đoạn 1 vẫn không thay thế phép thử mất ACK.

## 3. Phần TV2 đã tích hợp được

Hai script mới của TV2 đã dùng đúng bảng và năm trường dữ liệu của TV3:

- `doi_chieu.py`: đối chiếu cửa hàng/trụ sở, liệt kê giao dịch ACKED bị thiếu và gửi bù riêng các mã thiếu.
- `sao_luu_tru_so.py`: sao lưu SQLite trụ sở, kiểm tra toàn vẹn và khôi phục bản được chọn.

Kết quả thực tế giai đoạn 2:

| Mốc | Cửa hàng | ACKED | Trụ sở | ACKED thiếu tại HQ |
|---|---:|---:|---:|---:|
| Sao chép đầu phiên | 5 | 5 | 5 | 0 |
| Sau tạo thêm và đồng bộ | 10 | 10 | 10 | 0 |
| Sau phục hồi bản sao cũ | 10 | 10 | 5 | 5 |
| Sau TV2 gửi bù | 10 | 10 | 10 | 0 |

Bản sao HQ 5 có dữ liệu khớp, integrity_check ok và giữ nguyên hash sau thử. Trước phục hồi, bộ điều khiển còn tạo bản sao an toàn 10. CSDL cửa hàng không thay đổi byte trong quá trình phục hồi HQ và gửi bù. Toàn bộ phiên giai đoạn 1 giữ nguyên.

Bằng chứng: [kết quả giai đoạn 2](PhienThu/Phien_GD2_20261109_020609_227458/MinhChung/KET_QUA_GIAI_DOAN_2.json), [Terminal](PhienThu/Phien_GD2_20261109_020609_227458/MinhChung/terminal_giai_doan_2.txt) và [bảo toàn giai đoạn 1](PhienThu/Phien_GD2_20261109_020609_227458/MinhChung/BAO_TOAN_GIAI_DOAN_1.json).

## 4. Các điều chỉnh chỉ có trong bản thử

| File/thành phần | Điều chỉnh và lý do |
|---|---|
| Store agent, receiver, kiểm tra trùng và đối chiếu | Dùng `TV23_HQ_URL`/`TV23_HQ_PORT`, mặc định localhost 18000, tách khỏi cổng 8000 của dự án gốc |
| `doi_chieu.py` | Không biến thiếu file/lỗi SQL thành danh sách rỗng; 0/0 không coi là đạt; ACK gửi bù phải là object; trả mã thoát theo kết quả |
| `kiem_tra_trung.py` | Ca không đạt trả mã thoát khác 0 để bộ điều khiển nhận biết |
| `sao_luu_tru_so.py` | Bỏ lệnh xóa thử khỏi CLI; tắt tự xóa bản sao cũ để bảo toàn minh chứng |
| `kiem_tra_phuc_hoi.py` | Chọn bản sao kho bằng --file thay tên bản sao ngày cũ được viết cố định |
| Bộ điều khiển | Mỗi phiên có mã/dữ liệu/log riêng; quản lý tiến trình thuộc phiên; ngăn gửi thủ công khi auto sync đang chạy |
| Quy trình phục hồi | Dừng cả sender và receiver, sao lưu hiện trạng, phục hồi, đối chiếu, bật receiver và gửi bù; không tự bật lại sender |

`auto_sync.py`, `sao_luu.py` và `xuat_giao_dich.py` giữ nguyên byte nguồn TV3. Các điều chỉnh endpoint giữ nguyên giao thức JSON và logic PENDING/SENT/ACKED.

Ca 0/0 đã được chạy trước đó. Đợt bổ sung kiểm tra thiếu script, exit 7/9, cổng bị chiếm và lỗi dọn tiến trình. Lỗi file CSDL/sai schema, ACK sai mã/sai kiểu và các ngoại lệ khác vẫn chưa có ca riêng; không nhận tất cả nhánh đã được bao phủ.

Bản thử giữ tất cả bản sao, còn TV2 gốc có chính sách giữ bảy bản. Cần chốt lại chính sách trước khi dùng ngoài môi trường thử. Không tự áp cơ chế giữ vô hạn làm chính sách vận hành chính thức.

## 5. Nội dung cần TV2 xác nhận về schema

**Đề xuất tạm thời:** tiếp tục dùng schema TV3 trong [SCHEMA_TAM_THOI.sql](SCHEMA_TAM_THOI.sql) để giữ phần dữ liệu đã kiểm thử. Đề xuất này chưa phải quyết định cuối của nhóm.

| Nội dung | Bản thử theo TV3 | SQL tham khảo TV2 |
|---|---|---|
| File HQ | `truso.db` | `hq.db` |
| Cửa hàng/POS | `ma_cua_hang`, `ma_may` | `ma_ch`, `ma_pos` |
| Thời gian tạo | `thoi_gian` | `thoi_diem_tao` |
| Số tiền | `so_tien > 0` | `tong_tien >= 0` |
| Số mặt hàng, thời gian nhận | Chưa lưu trong bảng HQ | `so_mat_hang`, `thoi_diem_nhan` bắt buộc |
| Nhật ký nhận riêng | Log văn bản | Bảng `nhat_ky_nhan` |
| Kho cửa hàng tham chiếu trong SQL | `cuahang01.db/giao_dich` | `ch1.db/hang_doi` |

TV2 cần thống nhất với nhóm:

1. Tên file, bảng và năm trường dùng làm hợp đồng trao đổi dữ liệu.
2. Có cần số mặt hàng, thời gian nhận và bảng nhật ký nhận hay không; nếu cần, xác định nguồn dữ liệu và cách chuyển đổi, không tự gán dữ liệu chưa có.
3. Quy tắc số tiền và xử lý cùng mã khác nội dung. Nên giữ việc so sánh nội dung và phản hồi 409 của TV3, tránh bỏ qua mọi trường hợp trùng mã.
4. Cách sửa các truy vấn SQL TV2 cũ cho schema được chọn. Hai script Python mới đã tương thích schema TV3, nhưng không thể chạy nguyên truy vấn SQL cũ trên CSDL này.
5. Quyền thực hiện phục hồi, thời điểm dừng gửi và tiêu chí cho phép hoạt động lại sau đối chiếu.

## 6. Việc cần làm trước khi đưa vào repository chính

Thực hiện theo thứ tự để giữ phần đã hoàn thành:

1. TV2 đọc log và chốt schema với nhóm; ghi lại phạm vi bản tích hợp chính thức dự kiến.
2. Rà soát khác biệt giữa `Nguon/` và `Script/`, chọn các điều chỉnh cần đưa sang. Giữ bộ nguồn có phiên bản thống nhất, tránh nhiều bản receiver khác nhau trong cùng luồng.
3. Chuẩn hóa cấu hình endpoint, đường dẫn phiên và chính sách sao lưu. Quyết định có bổ sung lệnh nạp bản sao phiên vào CLI hay công cụ tái hiện hay không; hiện chức năng nạp phiên cũ chưa có trên giao diện Terminal.
4. Cập nhật README, kế hoạch, banner và metadata trạng thái cho bản chính. Những file mốc chuẩn bị trong gói này cần được giữ với ngữ cảnh lịch sử, không dùng làm kết luận kiểm thử hiện tại.
5. Giữ kết quả KT-BS1/KT-BS2 và hồi quy đã đạt; bổ sung ACK sai mã/sai định dạng, lỗi CSDL/sai schema. Nếu mở rộng phạm vi thì kiểm thử nhiều cửa hàng/POS, đồng thời và mạng thật; chỉ ghi đạt khi có minh chứng mới.
6. Thống nhất lịch sao lưu, nơi lưu bản sao ngoài máy hiện tại, số bản giữ và quy trình gửi bù sau phục hồi. Không dùng log của bộ mã khác thay kết quả của bộ mã đã chốt.
7. Kiểm tra danh sách file dự kiến đưa vào Git, giữ nguyên dữ liệu 15 giao dịch và các nhánh thành viên. Việc commit/merge chỉ thực hiện trong một công việc được nhóm cho phép riêng.

## 7. Kết luận bàn giao

Bản thử đã có kết quả đủ để TV2 kiểm tra luồng kết hợp: giữ giao dịch khi mất dịch vụ, tự gửi lại, chống trùng, sao lưu HQ, phục hồi bản cũ, phát hiện thiếu và gửi bù. Bản Git bàn giao mã, log và bản chụp JSON; CSDL được giữ tại môi trường thử độc lập và không đưa lên Git.

Chưa đủ cơ sở kết luận đã nghiệm thu toàn bộ hệ thống nhóm, đã chạy WAN thật, đã hoạt động nhiều cửa hàng hoặc mọi tình huống ACK, CSDL lỗi và vận hành dài hạn. Việc tích hợp chính thức cần TV2 xác nhận schema và hoàn thành các bước thống nhất, rà soát, kiểm thử tương ứng với phạm vi nhóm lựa chọn.

## 8. Bổ sung khi hoàn thiện lần cuối

Bộ điều khiển đã sửa banner, đầu ra UTF-8/cp1258, kiểm tra script thiếu và dùng try/finally dừng receiver khi sender.stop báo lỗi. Launcher dùng UTF-8 BOM; bộ thử và log được bổ sung trong KiemThu/ và MinhChungBoSung/. KT-BS1, KT-BS2 cùng năm nhóm hồi quy đều ĐẠT; một lượt lỗi bảng mã trước đó được giữ để đối chiếu. Không sửa chín script dữ liệu hoặc schema, không đổi Nguon/ hay các phiên đã kiểm chứng. Xem [báo cáo bổ sung](BAO_CAO_KIEM_THU_BO_SUNG.md).
