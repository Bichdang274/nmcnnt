# BẢN TÍCH HỢP THỬ NGHIỆM TV2–TV3

Bản này được lưu riêng trên nhánh `tich-hop-tv2-tv3-test`, xuất phát từ TV3 commit `2159cc8987e44a53e20ce4ee3bded194e8122969`. Đây là bản thử để rà soát và quản lý phiên bản, chưa phải bản tích hợp chính thức của nhóm.

## Đọc tài liệu và minh chứng

Mở lần lượt:

1. [Báo cáo kiểm thử tích hợp](BAO_CAO_KIEM_THU_TICH_HOP.md).
2. [Bàn giao cho TV2](BAN_GIAO_CHO_TV2.md).
3. [Hướng dẫn demo nhóm](HUONG_DAN_DEMO_NHOM.md).

Hai giai đoạn đã kiểm thử thành công trên localhost, một CH01/POS01, cổng 18000:

- Giai đoạn 1: giữ 5 giao dịch khi receiver tắt; cùng auto sync tự gửi khi receiver hoạt động, kết thúc 5 ACKED và HQ 5.
- Giai đoạn 2: gửi lặp 5 không tăng bản ghi; sao lưu 5; đồng bộ lên 10; phục hồi HQ về 5 trong khi kho giữ 10 ACKED; phát hiện 5 thiếu và gửi bù về 10, không trùng.

Schema đang dùng là schema TV3 **tạm thời, cần TV2 xác nhận**. KT-BS1 (HTTP 409), KT-BS2 (mất ACK sau commit) và năm nhóm hồi quy bộ điều khiển đã ĐẠT; xem [báo cáo bổ sung](BAO_CAO_KIEM_THU_BO_SUNG.md). Chưa triển khai nhiều cửa hàng/POS hoặc thử WAN thực tế. Chưa chứng minh HTTP Python đi qua WAN Packet Tracer.

Việc đưa file lên nhánh Git không chạy lại các ca kiểm thử. Khi cần xem kết quả, đọc log và JSON đã có; không cần khởi động dịch vụ.

## Nội dung thư mục

- `Script/`: chín script mẫu tích hợp.
- `demo_tich_hop.py`, `chay_demo.ps1`: bộ điều khiển Terminal và launcher.
- `Nguon/`: mã gốc/SQL tham khảo theo hai commit cố định, phục vụ đối chiếu.
- `PhienThu/Phien_20261109_014617_838147/`: metadata và minh chứng giai đoạn 1.
- `PhienThu/Phien_GD2_20261109_020609_227458/`: metadata và minh chứng giai đoạn 2.
- [NGUON_GIT.json](NGUON_GIT.json), [ghi chú điều chỉnh](NGUON_VA_DIEU_CHINH.md) và [bản so sánh mã](SO_SANH_MA_NGUON.patch): nguồn và thay đổi kỹ thuật.
- [DANH_MUC_GOI.json](DANH_MUC_GOI.json): danh sách/hash file trong thư mục Git này.
- [DU_LIEU_KHONG_DONG_GOI.md](DU_LIEU_KHONG_DONG_GOI.md): giải thích các CSDL và bản mã lặp đã loại.

Thư mục Git có mã, tài liệu, bộ thử và minh chứng đã chọn; số file/hash hiện tại nằm trong DANH_MUC_GOI.json. Không chứa CSDL, cache, file tạm hoặc ZIP. Sáu file CSDL và 18 bản mã chép trong các phiên không được thêm vào. Những bản mã phiên giống bộ Script/ chung đã được kiểm tra và có ánh xạ trong danh mục.

Các file minh chứng giữ số liệu giao dịch mẫu, thời gian và kết quả thực tế. Bản đưa lên Git đã ẩn tên cá nhân và thay đường dẫn máy bằng các nhãn `THU_MUC_BAN_GIAO`, `RUNTIME_BO_SUNG`, `MA_NGUON_TICH_HOP` hoặc `THU_MUC_NGUOI_DUNG`. Những nhãn này không phải đường dẫn có thể chạy nguyên trạng.

## Nguồn và phạm vi thay đổi khi đưa lên Git

- TV3: `2159cc8987e44a53e20ce4ee3bded194e8122969`.
- TV2: `f4aeed5d29bc72e7a07e73d3c9ff1a5cb3152af8`.
- Nội dung được lấy từ bộ bàn giao đã lọc; không thêm file ZIP vào Git.
- Chín script giao dịch/đối chiếu/sao lưu và schema giữ nguyên; đợt hoàn thiện chỉ sửa bộ điều khiển, launcher và thêm bộ kiểm thử. Nguon/ giữ nguyên.
- Đợt hoàn thiện đồng bộ các tài liệu, manifest và danh mục; chi tiết tại NGUON_VA_DIEU_CHINH.md.
- Tài liệu kế thừa có nhắc ZIP mô tả nguồn bộ bàn giao; các hạn chế CSDL/mã lặp cũng áp dụng cho bản Git này.
- MANIFEST.json ghi nguồn, trạng thái kiểm chứng và hash mã hiện tại; phần preparation_* lưu lịch sử chuẩn bị. DANH_MUC_GOI.json ghi hash file trong bản Git; hash lịch sử trong log/JSON vẫn mô tả file gốc tại thời điểm thử.

## Nếu nhóm trình diễn vào một lần sau

Chỉ thực hiện khi có chủ đích chạy demo mới. Từ thư mục này:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\chay_demo.ps1
```

Lệnh mở bộ điều khiển; `phien-moi` tạo thư mục dữ liệu riêng. Hai phiên minh chứng trong Git không chứa CSDL hoặc bản mã phiên để chạy lại trực tiếp. Không dùng chúng như phiên làm việc. Tham khảo hướng dẫn demo để tạo phiên mới, dừng receiver/auto sync và giữ log.

.gitignore riêng chặn CSDL, cache, ZIP, file tạm/thông tin cấu hình riêng và các phiên chạy mới. Trong PhienThu/, chỉ hai phiên minh chứng đã chọn được theo dõi; log bổ sung đã lọc nằm tại MinhChungBoSung/. Các CSDL đã có trong lịch sử nhánh TV3 ở bên ngoài thư mục này là dữ liệu kế thừa, không phải CSDL được thêm bởi bản tích hợp.

## Hoàn thiện và kiểm thử bổ sung

Đã sửa banner cũ, lỗi bảng mã cp1258, kiểm tra file thiếu và dọn receiver khi sender.stop báo lỗi. [Báo cáo bổ sung](BAO_CAO_KIEM_THU_BO_SUNG.md) lưu cả lượt khởi tạo lỗi đã được sửa và lượt kiểm thử sau đó đạt 7/7 ca. Mở demo chỉ thông báo kết quả lịch sử; phiên demo mới vẫn chưa có dữ liệu hoặc kết quả cho đến khi được chạy và đối chiếu.
