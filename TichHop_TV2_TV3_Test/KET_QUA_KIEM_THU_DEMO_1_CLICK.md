# Kết quả kiểm thử ONE-CLICK DEMO

## Bản hoàn thiện để trình diễn — 10/11/2026

Đã hoàn thiện giao diện Terminal tiếng Việt UTF-8, tiêu đề **HỆ THỐNG GIAO DỊCH CHUỖI CỬA HÀNG**, phân biệt hai demo, giai đoạn 1/6 và 1/7, tiến độ, bảng giao dịch căn cột, màu theo khả năng console và bảng tổng kết để chụp màn hình. Màn hình chỉ có nội dung trình diễn và lý do lỗi ngắn; PID, đường dẫn đầy đủ, JSON và traceback được giữ trong `chi_tiet.txt` của runtime mới.

Ba launcher cũ được giữ; bổ sung `chay_demo_thuyet_trinh.cmd`. `.cmd` thử tối ưu cửa sổ console thường nếu host cho phép, không sửa thiết lập Terminal hệ thống. PowerShell dùng UTF-8 BOM để giữ dấu khi chạy trên Windows PowerShell 5.1. Có thể tắt màu bằng `-KhongMau`.

### Kiểm thử hồi quy bản hoàn thiện

Windows, Python 3.13.15. Bộ kiểm thử gọi launcher `.cmd` thật, điều khiển Enter qua stdin, sau đó đọc SQLite độc lập với lớp hiển thị; kiểm tra integrity, đủ mã, payload, ACKED, bản sao 5/10 và toàn bộ tiến trình đã dừng.

| Ca kiểm thử | Kết quả thực tế |
| --- | --- |
| TỰ ĐỘNG — `chay_demo_1_click.cmd` | ĐẠT, mã thoát 0: cả TV3 và TV2–TV3 đạt 10 ACKED/HQ10, không mất/trùng/lệch; tiến trình dừng bình thường |
| THUYẾT TRÌNH — `chay_demo_thuyet_trinh.cmd` | ĐẠT, mã thoát 0: đủ 13 điểm chờ; mỗi điểm có ảnh chụp trước/sau Enter không đổi; cả hai demo cuối đạt 10 ACKED/HQ10 |
| Chờ ở TV3 giai đoạn 5 | Giữ 11 giây: CH02 vẫn 5 SENT/0 ACKED, HQ5; log tăng chu kỳ auto sync, chứng minh worker tiếp tục chạy mà trạng thái vẫn ổn định |
| Chờ sau phục hồi TV2, giai đoạn 5 | Giữ 11 giây: kho vẫn 10 ACKED, HQ vẫn 5; sender/receiver tắt, chưa gửi bù sớm |
| Thoát lúc TV3 giai đoạn 5 đang chờ | ĐẠT tiêu chí an toàn: EOF khiến demo báo CHƯA ĐẠT, mã thoát 1; hai sender và receiver đều đã dừng, mã thoát 0, không cưỡng bức |
| Cổng 18000 bị chiếm | ĐẠT: demo trả mã 1 trước khi có SQLite/worker; socket ngoài phiên còn nguyên; không kill tiến trình khác |
| Cú pháp/hiển thị | Python AST và PowerShell AST hợp lệ; terminal.txt không có escape màu, PID, đường dẫn cá nhân, JSON kỹ thuật hoặc traceback |

Không chạy lại toàn bộ 22 ca nâng cao vì mã nghiệp vụ không đổi. Các ca trên tập trung vào giao diện, launcher, tạm dừng, tính đúng dữ liệu cuối và cleanup bị ảnh hưởng bởi phần điều phối.

### Minh chứng bản hoàn thiện

Đường dẫn tương đối với `TichHop_TV2_TV3_Test`:

| Nội dung | Runtime mới |
| --- | --- |
| Tổng hợp hồi quy | `runtime/KiemThuGiaoDien_20261110_191251_ef53d7ec/ket_qua_hoi_quy.json` |
| Tự động A → B | `runtime/Demo1Click_20261110_191252_279400_4811bc39/` |
| Thuyết trình A → B | `runtime/Demo1Click_20261110_191342_952881_2824181c/` |
| Thoát tại điểm chờ, thất bại đúng mong đợi | `runtime/Demo1Click_20261110_191443_122357_9472b072/` |
| Cổng bị chiếm, thất bại đúng mong đợi | `runtime/Demo1Click_20261110_191450_641771_9ee9eeae/` |
| Fingerprint bảo toàn đầu đợt hoàn thiện | `runtime/HoanThien_20261110_180936_020760/bao_toan_truoc.json` |

Mỗi phiên chính có `terminal.txt`, `chi_tiet.txt`, `tong_ket.json`; mỗi chế độ có `ket_qua.json`, `tien_trinh.json`, bản sao mã và SQLite mới. Ảnh chụp `*_tam_dung_truoc.json`/`*_tam_dung_sau.json` lưu dữ liệu thực tế và thời gian chờ. Báo cáo hồi quy nằm trong runtime cục bộ, được loại khỏi Git.

Các lần lỗi cũng được giữ: `KiemThuGiaoDien_20261110_181427_77a7ab30` là lỗi harness tìm launcher không có tiền tố `.\`; đã sửa harness dùng đường dẫn tương đối tường minh. `KiemThuGiaoDien_20261110_181443_ef4c651e` và `Demo1Click_20261110_181444_116113_448fb8f5` bị sandbox chặn CIM/WMI trước khi tạo giao dịch; sau khi cho phép chạy ngoài sandbox, bốn ca hồi quy đều đạt. Không xóa hoặc ghi đè lần lỗi.

### Phạm vi và sẵn sàng trình diễn

Mã thay đổi chỉ ở lớp điều phối/giao diện, launcher, kiểm thử hồi quy, tài liệu và quy tắc bỏ qua `/runtime/` trong thư mục ứng dụng. Thêm `giao_dien_demo.py`, `chay_demo_thuyet_trinh.cmd`, `KiemThu/kiem_thu_demo_1_click.py`. Giữ nguyên `demo_tich_hop.py`, `Script/`, mã tham chiếu `Nguon/`, schema, Packet Tracer, CSDL, runtime và minh chứng có sẵn.

Fingerprint trước/sau bao phủ 504 file đã có: chỉ 6 file nằm trong phạm vi được yêu cầu có thay đổi; 498 file còn lại giữ nguyên SHA-256, gồm mã nghiệp vụ, nguồn tham chiếu và toàn bộ runtime/minh chứng cũ đã rà soát. Kết quả chi tiết ở `runtime/HoanThien_20261110_180936_020760/bao_toan_sau.json`.

Đã xác minh worktree và nhánh `tv3-nang-cao-demo`, commit nền `b08b52326a37e11400415b4e9285c9fdf941227a`. Phạm vi phát hành chỉ gồm file mã, launcher, tài liệu cần thiết và `.gitignore` của ứng dụng; không gồm `.db`, runtime, cache, ZIP hoặc đường dẫn cá nhân. Không merge, tạo PR, force push hoặc thay đổi nhánh khác.

**Sẵn sàng trình diễn trên Windows/local theo các luồng đã kiểm thử.** Người dùng đã xác nhận nhấp đúp bản One-Click ban đầu thành công. Bản hoàn thiện được chạy qua `.cmd` bằng tiến trình thật, chưa tự thao tác chuột GUI để kiểm tra màu, thay đổi kích thước cửa sổ và phím Enter vật lý. Nên mở thử launcher thuyết trình trên đúng màn hình trình chiếu; nếu host không hỗ trợ màu/resize, giao diện vẫn chạy ở chế độ văn bản thường.

B vẫn chỉ một cửa hàng; mô phỏng ngắt HTTP ở A không phải mất WAN thật. Đây là bản tích hợp thử nghiệm, chưa phải bản chính thức; không thay Packet Tracer hoặc chứng minh vận hành LAN/máy chủ thật. Quyền đọc CIM/WMI vẫn là điều kiện preflight. Các điểm chờ chủ động đợi Enter, còn thao tác đồng bộ có timeout.

## Hồ sơ đợt xây dựng ban đầu

Ngày 10/11/2026, giờ Việt Nam; Windows, Python 3.13.15. Kết quả dưới đây lấy từ các phiên runtime vừa chạy, không dùng minh chứng cũ.

### File đã tạo ở đợt đầu

- `demo_1_click.py`: điều phối tự động, kiểm tra dữ liệu, quản lý vòng đời tiến trình và ghi minh chứng.
- `chay_demo_1_click.ps1`: chọn `tv3`, `tich-hop`, `all`, tùy chọn tạm dừng và giữ màn hình tổng kết.
- `chay_demo_1_click.cmd`: launcher nhấp đúp, mặc định chạy cả hai.
- `chay_demo_TV3.cmd`, `chay_demo_TV2_TV3.cmd`: hai launcher chạy riêng từng chế độ.
- `HUONG_DAN_DEMO_1_CLICK.md`: hướng dẫn sử dụng, log, giới hạn và xử lý lỗi.
- `KET_QUA_KIEM_THU_DEMO_1_CLICK.md`: báo cáo này.
- Các thư mục mới trong `runtime/`: CSDL, bản sao mã, log, minh chứng và công cụ kiểm tra cục bộ của đợt thử.

### Kết quả đợt đầu

| Kiểm tra | Kết quả thực tế |
| --- | --- |
| Cú pháp Python | ĐẠT: `ast.parse`, không tạo bytecode trong mã nguồn |
| Cú pháp PowerShell | ĐẠT: PowerShell AST parser không báo lỗi |
| A chạy riêng, khoảng nghỉ mặc định 2 giây | ĐẠT: CH01 5 ACKED; CH02 lúc ngắt có 5 SENT/0 ACKED, HQ5; nối lại đạt 5 ACKED; cuối HQ10, không thiếu/thừa/lệch/trùng |
| B chạy riêng, khoảng nghỉ mặc định 2 giây | ĐẠT: sao lưu HQ5; đồng bộ HQ10; phục hồi HQ5; TV2 phát hiện đúng 5 mã `000006`–`000010`; gửi bù 5/5; cuối 10 ACKED/HQ10, payload khớp trước phục hồi |
| Luồng mặc định A → B, `-NghiGiay 0` | ĐẠT: hai phiên khác nhau; cả A và B đạt; receiver được đóng và mở lại an toàn trên cùng cổng |
| Cổng đã bị chiếm | ĐẠT: guard từ chối; socket giả lập ngoài phiên vẫn còn nguyên; không kill tiến trình khác |
| Lỗi có chủ đích sau khi bật receiver/sender | ĐẠT tiêu chí an toàn: demo báo CHƯA ĐẠT đúng mong đợi; `finally` dừng cả hai tiến trình, mã thoát 0, không dừng cưỡng bức; bind lại cổng thành công |
| Bảo toàn file có sẵn | ĐẠT: so SHA-256 của 234 file đã có trước đợt thử, không file nào thay đổi |

Các lần demo thành công trả mã thoát 0. Toàn bộ tiến trình do phiên tạo đều được `wait()` xác nhận đã kết thúc; sender/receiver đều thoát mã 0, `forced=false`. A giữ nguyên PID CH02 khi nối HTTP; log chứng minh số chu kỳ auto sync tăng từ lượt ngắt sang lượt tự gửi lại. Không gọi hàm gửi thủ công trong A. B giữ nguyên SHA-256 bản HQ5 sau phục hồi và gửi bù.

### Vị trí minh chứng đợt đầu

Các đường dẫn dưới đây tương đối với `TichHop_TV2_TV3_Test`:

| Phiên | Thư mục |
| --- | --- |
| A chạy riêng | `runtime/Demo1Click_20261110_170431_477170_68a755e2/` |
| B chạy riêng | `runtime/Demo1Click_20261110_170620_283536_a2bddc34/` |
| A và B liên tiếp | `runtime/Demo1Click_20261110_171615_103988_fa720b71/` |
| Kiểm tra bổ sung/bảo toàn | `runtime/KiemThu_20261110_170204_303526/` |

Mỗi phiên chính có `terminal.txt`, `kiem_tra_moi_truong.json`, `tong_ket.json`. Trong `TV3/` hoặc `TV2-TV3/` có `ket_qua.json`, `tien_trinh.json`, `ma_nguon_phien.json` và `PhienThu/Phien_*/MinhChung/` chứa ảnh chụp JSON đầy đủ từng giao dịch. SQLite và bản sao TV2 nằm trong `PhienThu/Phien_*/DuLieu/`.

Trong thư mục kiểm tra bổ sung:

- `bao_toan_truoc.json`, `bao_toan_sau.json`: fingerprint file cũ và kết quả không có file đổi.
- `xac_minh_cuoi.json`: đọc SQLite độc lập sau khi kết thúc cả ba lần chạy; xác nhận 4 phiên chế độ đều có 10 ACKED/HQ10, payload khớp, integrity_check OK, không trùng và tiến trình đã dừng.
- `git_status_truoc.txt`, `git_status_sau.txt`: trạng thái Git dạng porcelain với ký tự phân cách NUL.
- `kiem_tra_an_toan.py`, `kiem_tra_an_toan.json`, `kiem_tra_an_toan_terminal_UTF8.txt`: guard cổng và kiểm tra cleanup khi lỗi.
- `LoiCoChuDich_UTF8/`: phiên thất bại có chủ đích, cần đọc kết quả CHƯA ĐẠT là đúng mong đợi của ca thử này.

### Các lần bị chặn/lỗi đợt đầu đã giữ nguyên

1. `runtime/Demo1Click_20261110_170205_796879_f113d4c7/`: sandbox từ chối `Get-CimInstance` với Access denied. Bộ chạy dừng ở preflight, không tạo giao dịch hoặc bật receiver/sender. Sau khi được phép chạy ngoài sandbox, A và B chạy thành công. Bộ demo giữ điều kiện kiểm tra môi trường, không bỏ qua lỗi quyền.
2. `runtime/KiemThu_20261110_170204_303526/LoiCoChuDich/` và `kiem_tra_an_toan_terminal.txt`: lần đầu gọi lớp kiểm tra trực tiếp từ Python stdin dùng encoding console cp1258, chưa đi qua phần khởi tạo UTF-8 của `main()`, nên harness lỗi khi in tiếng Việt. Sửa đúng harness bằng `reconfigure(encoding='utf-8')` và chạy lại phần kiểm tra an toàn trong phiên mới `LoiCoChuDich_UTF8/`; kết quả đạt. Luồng launcher sản phẩm vốn khởi tạo UTF-8 và đã chạy thành công.

Không xóa hoặc ghi đè các runtime lỗi. Không có lỗi chức năng còn tồn tại trong hai kịch bản đã thử.

### Giới hạn và bảo toàn dự án ở đợt đầu

- B chỉ dùng CH01/POS01 theo giới hạn công cụ TV2 hiện có. A mô phỏng ngắt HTTP bằng cờ cửa hàng, không can thiệp mạng/firewall thật.
- Chỉ kiểm thử trên Windows và localhost:18000, với schema trụ sở TV3 sẵn có. Chưa kiểm thử qua mạng LAN hoặc máy chủ thật.
- Kiểm thử luồng nghiệp vụ thực hiện qua launcher PowerShell; chưa thao tác nhấp đúp bằng GUI hay xác nhận tương tác `-TamDung` bằng người dùng. Launcher `.cmd` gọi chung file PowerShell này.
- Cần quyền đọc danh sách tiến trình qua CIM/WMI. Sandbox có thể yêu cầu cấp phép chạy ngoài sandbox; bình thường bộ chạy không tự yêu cầu quyền Administrator.
- Các thao tác có timeout; chế độ `-TamDung` và giữ màn hình cuối chủ động đợi người thuyết trình. Không thể bảo đảm ghi tổng kết khi máy tắt nguồn hoặc cưỡng bức đóng toàn bộ cây tiến trình.

Không sửa `demo_tich_hop.py`, mã `Script/`, mã tham chiếu `Nguon/`, schema, logic giao dịch hoặc file/CSDL/phiên cũ. SHA-256 trước/sau xác nhận 234 file được theo dõi bảo toàn không đổi, gồm file tracked và dữ liệu/minh chứng cũ trong các thư mục đã rà soát. Những thay đổi Git đã có từ trước vẫn được giữ nguyên.

Ở đợt xây dựng ban đầu, mọi file mới thuộc worktree được yêu cầu và thư mục chương trình `TichHop_TV2_TV3_Test`; khi kết thúc đợt đó chưa git add, commit hoặc push. Việc phát hành bản hoàn thiện được thực hiện riêng theo yêu cầu mới, chỉ trên nhánh `tv3-nang-cao-demo`.
