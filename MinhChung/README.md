# Danh mục minh chứng TV3

Bộ kết quả chính: ngày 01/11/2026. Log gốc được giữ nguyên nội dung, thời gian và mã hóa.

| Nội dung | Minh chứng | Kết quả |
|---|---|---|
| KT2 – tạo khi dịch vụ dừng | [KT2_PENDING_20261101.txt](KT2_PENDING_20261101.txt) | 5 mới PENDING; tổng 15 |
| KT2 – thử gửi thất bại | [KT2_GUI_LOI_20261101.txt](KT2_GUI_LOI_20261101.txt) | 5 SENT còn lưu; lỗi kết nối 10061 |
| KT3 – trước gửi lại | [KT3_TRUOC_GUI_20261101.txt](KT3_TRUOC_GUI_20261101.txt) | Trụ sở 10 |
| KT3 – gửi lại | [KT3_GUI_LAI_20261101.txt](KT3_GUI_LAI_20261101.txt) | 5 giao dịch được ACK |
| KT3 – đối chiếu | [KT3_SAU_GUI_20261101.txt](KT3_SAU_GUI_20261101.txt) | Hai bên 15, khớp True, 15 ACKED |
| KT3-b – gửi lặp | [KT3b_GUI_LAP_20261101.txt](KT3b_GUI_LAP_20261101.txt) | 15 ACK hợp lệ, trụ sở vẫn 15, mã trùng 0 |
| V2 – mất WAN: ping | [PT_V2_KT2_mat_WAN.png](PT_V2_KT2_mat_WAN.png) | LAN còn hoạt động, HQ không tới được |
| V2 – mất WAN: HTTP | [PT_V2_KT2_HTTP_mat_WAN.png](PT_V2_KT2_HTTP_mat_WAN.png) | Request Timeout |
| V2 – phục hồi: HTTP | [PT_V2_KT3_HTTP_phuc_hoi.png](PT_V2_KT3_HTTP_phuc_hoi.png) | Mở lại trang HQ |
| Xuất CSV ngày 26/10 | [xuat_giao_dich.txt](xuat_giao_dich.txt) | 10 giao dịch ở thời điểm xuất |
| Sao lưu ngày 26/10 | [sao_luu.txt](sao_luu.txt) | 10 giao dịch, integrity ok |
| Phục hồi ngày 26/10 | [kiem_tra_phuc_hoi.txt](kiem_tra_phuc_hoi.txt) | 10 giao dịch, 1 bộ đếm, khớp bản sao |

## Lịch sử không dùng thay cho lần kiểm thử chính

- [Log 24/10](LichSu/20261024): cùng loại kịch bản nhưng dữ liệu ở thời điểm khác (10 giao dịch).
- [Ảnh bản TV1 ngày 27/10](LichSu/TV1_20261027): ping, HTTP, OSPF ban đầu trên TV1. Không đổi tên để coi là ảnh V2.
- Hai ảnh HTTP TV1 và V2 phục hồi có trang web giống nhau, nhưng khác lần kiểm thử. Không phải bản sao byte giống hệt.
- Không có ảnh ping phục hồi V2 riêng trong gói; báo cáo dùng HTTP phục hồi thực có.
- Packet Tracer chứng minh kết nối mạng. Script Python trên localhost chứng minh lưu/gửi/ACK/chống trùng. Không dùng ping hay trang web để kết luận đồng bộ CSDL.
