# DỮ LIỆU KHÔNG ĐÓNG GÓI

ZIP phục vụ rà soát mã và minh chứng, không chứa CSDL SQLite. Các file dưới đây vẫn ở môi trường gốc và không bị sửa/xóa khi đóng gói.

| File đã loại | Minh chứng thay thế trong gói |
|---|---|
| PhienThu/Phien_20261109_014617_838147/DuLieu/cuahang01.db | [Kết quả và bản chụp](PhienThu/Phien_20261109_014617_838147/MinhChung/KET_QUA_GIAI_DOAN_1.json) |
| PhienThu/Phien_20261109_014617_838147/DuLieu/truso.db | [Kết quả và bản chụp](PhienThu/Phien_20261109_014617_838147/MinhChung/KET_QUA_GIAI_DOAN_1.json) |
| PhienThu/Phien_GD2_20261109_020609_227458/DuLieu/cuahang01.db | [Kết quả và bản chụp](PhienThu/Phien_GD2_20261109_020609_227458/MinhChung/KET_QUA_GIAI_DOAN_2.json) |
| PhienThu/Phien_GD2_20261109_020609_227458/DuLieu/SaoLuuTruSo/truso_20261109_020610_619085.db | [Kết quả và bản chụp](PhienThu/Phien_GD2_20261109_020609_227458/MinhChung/KET_QUA_GIAI_DOAN_2.json) |
| PhienThu/Phien_GD2_20261109_020609_227458/DuLieu/SaoLuuTruSo/truso_20261109_020611_690229.db | [Kết quả và bản chụp](PhienThu/Phien_GD2_20261109_020609_227458/MinhChung/KET_QUA_GIAI_DOAN_2.json) |
| PhienThu/Phien_GD2_20261109_020609_227458/DuLieu/truso.db | [Kết quả và bản chụp](PhienThu/Phien_GD2_20261109_020609_227458/MinhChung/KET_QUA_GIAI_DOAN_2.json) |

Bản sao 5 giao dịch được kiểm tra trong giai đoạn 2 có integrity_check ok, sau thử vẫn giữ nguyên hash. Dữ liệu này được chứng minh bằng JSON/log; file .db không có trong ZIP để mở trực tiếp.

[Xem bảng số liệu và danh mục minh chứng](BAO_CAO_KIEM_THU_TICH_HOP.md).

Mười tám bản mã trong hai thư mục phiên đã được kiểm tra giống hệt Script/ chung và được lược bỏ. Xem ánh xạ trong DANH_MUC_GOI.json. Các phiên đóng gói chỉ dùng để đọc kết quả; tạo phiên mới nếu trình diễn vào một lần được cho phép sau này.
