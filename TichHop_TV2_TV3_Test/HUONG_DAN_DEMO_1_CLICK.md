# Demo một lần chạy: TV3 nâng cao và TV2–TV3

Mở thư mục `TichHop_TV2_TV3_Test`. Cần Windows PowerShell và Python **3.9 trở lên** trong PATH; không cần cài thư viện Python bên ngoài. Đóng dịch vụ đang dùng cổng **18000** theo cách thông thường trước khi trình diễn.

## Nhấp đúp trên Windows

| File | Nội dung |
| --- | --- |
| `chay_demo_TV3.cmd` | Chế độ A: hai cửa hàng, ngắt/nối riêng CH02, auto sync tự gửi lại |
| `chay_demo_TV2_TV3.cmd` | Chế độ B: một cửa hàng, TV2 sao lưu → phục hồi → phát hiện thiếu → gửi bù |
| `chay_demo_1_click.cmd` | Chạy A rồi B, mỗi chế độ có phiên riêng |
| `chay_demo_thuyet_trinh.cmd` | Chạy A rồi B; xem kết quả và nhấn Enter sau mỗi giai đoạn |

Mặc định tự chạy, nghỉ 2 giây giữa các giai đoạn. Kết thúc sẽ giữ bảng tổng kết; nhấn Enter để đóng. Chế độ A thường mất khoảng 25–40 giây, B khoảng 15–30 giây, tùy máy. Nếu một chế độ lỗi, chế độ tiếp theo không chạy.

**TỰ ĐỘNG:** nhấp đúp một trong ba launcher đầu. **THUYẾT TRÌNH:** nhấp đúp `chay_demo_thuyet_trinh.cmd`; không cần nhớ lệnh. Chờ dòng `CHỜ THUYẾT TRÌNH`, đọc bảng rồi nhấn Enter. Có 6 giai đoạn TV3 và 7 giai đoạn tích hợp, kể cả điểm chờ cuối mỗi demo.

Điểm chờ chỉ được mở khi dữ liệu đã ổn định: CH01 đã ACKED hoặc sender chưa bật; CH02 đang offline phải hết PENDING và giữ SENT; khi phục hồi TV2 thì sender/receiver đã tắt. Worker nền có thể tiếp tục chạy, nhưng không còn giao dịch online có thể đổi trạng thái. Chương trình so sánh nội dung SQLite và trạng thái tiến trình trước/sau Enter; khác ngoài dự kiến sẽ báo CHƯA ĐẠT và dọn tiến trình.

Terminal hiển thị tiêu đề **HỆ THỐNG GIAO DỊCH CHUỖI CỬA HÀNG**, tên demo, giai đoạn, tiến độ và bảng căn cột. Màu dùng khi console hỗ trợ; chuyển hướng log tự bỏ màu. Khi mở `.cmd`, chương trình thử tối ưu cửa sổ console thường tới 110 cột × 36 dòng trong giới hạn màn hình. Windows Terminal, VS Code hoặc host không hỗ trợ sẽ giữ kích thước hiện tại; không sửa profile/registry hay thiết lập Terminal hệ thống.

## Chạy từ Terminal

Mở PowerShell trong `TichHop_TV2_TV3_Test`:

```powershell
# Hai lệnh dễ nhớ
.\chay_demo_1_click.ps1 -CheDo tv3
.\chay_demo_1_click.ps1 -CheDo tich-hop

# Chạy cả hai
.\chay_demo_1_click.ps1

# Nhấn Enter sau khi xem kết quả từng giai đoạn
.\chay_demo_1_click.ps1 -CheDo tv3 -TamDung

# Thuyết trình riêng tích hợp
.\chay_demo_1_click.ps1 -CheDo tich-hop -TamDung

# Tắt màu nếu Terminal hiển thị không đúng
.\chay_demo_1_click.ps1 -KhongMau

# Tùy chỉnh khoảng nghỉ và timeout mỗi lệnh/lượt chờ
.\chay_demo_1_click.ps1 -CheDo tich-hop -NghiGiay 3 -TimeoutGiay 60

# Dùng trong kiểm thử/tự động hóa: không chờ Enter ở màn hình cuối
.\chay_demo_1_click.ps1 -CheDo tv3 -KhongGiuManHinh
```

Nếu PowerShell chặn thực thi file `.ps1`, dùng launcher `.cmd` hoặc lệnh chỉ áp dụng chính sách cho tiến trình này:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\chay_demo_1_click.ps1 -CheDo tv3
```

Có thể chạy bộ điều phối trực tiếp, không giữ màn hình cuối:

```powershell
python -B -u .\demo_1_click.py --mode tv3
python -B -u .\demo_1_click.py --mode tich-hop
python -B -u .\demo_1_click.py --mode all --pause
```

Không chạy hai demo cùng lúc vì cùng dùng cổng 18000. Mã thoát `0` nghĩa là mọi kiểm tra của các chế độ được chọn đều đạt; `1` nghĩa là chưa đạt. Lỗi tham số của Python trả mã `2`.

## Nội dung trình diễn và điều kiện ĐẠT

**A — TV3:** tạo phiên trắng; bật receiver; tạo CH01 với 5 PENDING; auto sync chuyển thành 5 ACKED/HQ5; tạo SQLite riêng CH02; bật cờ mô phỏng ngắt HTTP CH02; tạo 5 PENDING; auto sync thử gửi và giữ 5 SENT/0 ACKED, HQ vẫn 5; nối lại, chờ chính worker auto sync ở chu kỳ kế tiếp đưa CH02 lên 5 ACKED/HQ10. CH01 tiếp tục chạy trong lúc CH02 bị ngắt. Kiểm tra PID CH02 không đổi khi nối lại và số lượt auto sync tăng. Không gọi lệnh gửi thủ công trong A.

**B — TV2–TV3:** tạo phiên trắng khác, chỉ CH01; tự đồng bộ 5; tắt sender và dùng công cụ TV2 sao lưu HQ5; thêm 5, tự đồng bộ HQ10; dừng sender/receiver, sao lưu thêm HQ10 trước phục hồi; dùng TV2 phục hồi HQ5; dùng đối chiếu TV2 kiểm tra đúng danh sách 5 mã đã ACKED bị thiếu; bật receiver, gọi `gui-bu` của TV2 khi auto sync tắt. Cuối cùng phải có 10 ACKED, HQ10 và nội dung đúng như trước phục hồi. Bản sao HQ5 phải giữ nguyên SHA-256.

Bảng trạng thái đọc SQLite thật, hiển thị PENDING/SENT/ACKED và số giao dịch HQ. ĐẠT cuối yêu cầu đủ số giao dịch, khớp cả 5 trường (`ma_gd`, `ma_cua_hang`, `ma_may`, `thoi_gian`, `so_tien`), không thiếu/thừa, không trùng mã, không còn PENDING/SENT. Mốc 0/0 chỉ kiểm tra phiên mới trống, không được dùng làm bằng chứng đồng bộ thành công. HQ5 sau phục hồi ở B là tình huống thiếu dữ liệu mong đợi; bước phát hiện thiếu chỉ đạt khi xác minh đúng 5 mã.

## Log và minh chứng

Mỗi lần chạy tạo duy nhất một thư mục mới:

```text
runtime/Demo1Click_<ngày_giờ_microsecond>_<mã_ngẫu_nhiên>/
  terminal.txt                      Toàn bộ đầu ra Terminal, gồm lỗi nếu có
  chi_tiet.txt                      PID, đường dẫn, JSON, đầu ra công cụ và traceback
  kiem_tra_moi_truong.json          Python, tiến trình hiện có, cổng và lỗi kiểm tra
  tong_ket.json                     Kết luận lần chạy
  TV3/ hoặc TV2-TV3/
    ket_qua.json                   Kết quả từng giai đoạn
    tien_trinh.json                 PID, mã thoát, trạng thái đã dừng
    ma_nguon_phien.json             SHA-256 bản sao Script dùng trong phiên
    PhienThu/Phien_<ngày_giờ>/
      phien.json
      Script/                      Bản sao mã chương trình
      DuLieu/                      SQLite từng kho, trụ sở và các bản sao TV2
      MinhChung/
        *_*.json                   Ảnh chụp số liệu và từng giao dịch
        *_tam_dung_truoc.json       Dữ liệu/trạng thái tại điểm chờ
        *_tam_dung_sau.json         Thời gian chờ và xác nhận không thay đổi
        receiver_log.txt
        auto_sync_log.txt           CH01
        auto_sync_CH02_POS01.txt    CH02, chỉ ở A
        dieu_khien_log.txt
```

Màn hình chỉ in đường dẫn tương đối ngắn ở đầu/cuối. Mở thư mục đó trong `TichHop_TV2_TV3_Test` để xem log. Thông tin kỹ thuật đầy đủ nằm trong `chi_tiet.txt` và log của từng phiên. Không xóa runtime lỗi: sửa nguyên nhân rồi chạy lại để có phiên mới, giữ lịch sử lỗi làm bằng chứng. `/runtime/` được bỏ qua bởi Git; không đóng gói CSDL/log vào commit.

## Bảng cuối để chụp màn hình

Ví dụ dưới đây chỉ minh họa bố cục; số liệu khi chạy được đọc từ SQLite của phiên mới:

```text
BẢNG TỔNG KẾT TRÌNH DIỄN
NỘI DUNG                    KHO / ACKED   TRỤ SỞ     KẾT QUẢ
TV3 nâng cao                      10/10       10         ĐẠT
Tích hợp TV2–TV3                  10/10       10         ĐẠT
KẾT QUẢ CHUNG: ĐẠT
Không mất / không trùng / không lệch: ĐẠT
Tiến độ: 100% — HOÀN TẤT
```

Chụp bảng này trước khi nhấn Enter ở màn hình kết thúc. Nếu có lỗi, bảng hiển thị CHƯA ĐẠT và lý do ngắn; các bước sau lỗi có thể chưa được chạy.

## An toàn và xử lý lỗi

- **Cổng 18000 đang bị chiếm:** bộ chạy từ chối trước khi tạo giao dịch, không kill tiến trình ngoài phiên. Xem `kiem_tra_moi_truong.json`; tự dừng đúng dịch vụ của bạn rồi chạy lại. Trường hợp Windows chưa giải phóng cổng sau lần chạy trước, chờ một chút rồi thử lại.
- **Không đọc được danh sách tiến trình / Access denied:** kiểm tra quyền đọc WMI/CIM và cấu hình bảo mật Windows. Trong môi trường Codex sandbox, có thể cần cho phép chạy thử ngoài sandbox. Bộ chạy dừng an toàn nếu không hoàn tất kiểm tra môi trường; không tự bỏ qua kiểm tra.
- **Không tìm thấy Python hoặc phiên bản quá cũ:** kiểm tra `python --version` hoặc `py -3 --version`. Launcher ưu tiên `python`, nếu không có mới dùng `py -3`.
- **Timeout/CHƯA ĐẠT:** đọc lý do ngắn trên màn hình, rồi xem `chi_tiet.txt`, log sender/receiver, `ket_qua.json` và ảnh chụp `het_thoi_gian` nếu có. Timeout mặc định 45 giây mỗi lệnh/lượt chờ, có thể tăng đến 120 giây. Không báo ĐẠT từ mã thoát của công cụ nếu dữ liệu chưa khớp.
- **Dừng giữa chừng:** dùng Ctrl+C, giữ Terminal mở để bộ chạy hoàn tất dọn tiến trình. Các worker nhận yêu cầu dừng qua pipe; sender hoàn tất lượt hiện tại rồi ngắt chờ, receiver đóng socket. Nếu parent bị đóng đột ngột, EOF trên pipe yêu cầu worker dừng. Khi buộc phải terminate/kill PID do phiên tạo sau timeout, kết quả bị đánh dấu CHƯA ĐẠT. Không thể bảo đảm ghi đầy đủ tổng kết khi Windows tắt nguồn hoặc cưỡng bức kết thúc toàn bộ cây tiến trình.
- **Muốn thuyết trình chậm:** dùng `-TamDung` hoặc tăng `-NghiGiay`. Chế độ tạm dừng chủ động đợi Enter; các thao tác đồng bộ vẫn có timeout.

Ngắt HTTP ở A là cờ mô phỏng tại cửa hàng, không thay firewall hoặc tắt mạng thật. Lớp điều phối cập nhật cờ trước mỗi chu kỳ và cho phép dừng vòng chờ; hàm tạo/gửi giao dịch, xử lý receiver, schema, sao lưu, phục hồi và gửi bù đều dùng bản sao mã hiện có. B giới hạn một cửa hàng vì công cụ TV2 chưa hỗ trợ đầy đủ nhiều cửa hàng. Chương trình chỉ dùng localhost và schema trụ sở TV3 hiện có trong bản tích hợp thử nghiệm.

Đây là **bản tích hợp thử nghiệm phục vụ trình diễn**, chưa phải bản triển khai chính thức. Mô phỏng mất HTTP không chứng minh hành vi mất WAN thật, định tuyến Packet Tracer hoặc vận hành trên máy chủ thực.

`demo_tich_hop.py`, thư mục `Script` hiện có, mã tham chiếu `Nguon/`, schema, Packet Tracer, CSDL và các phiên cũ được giữ nguyên. Bản thân bộ demo không chạy lệnh Git. Mã hoàn thiện chỉ được phát hành trên nhánh `tv3-nang-cao-demo`; không merge hoặc thay đổi nhánh khác.

## Kết quả chạy thử thực tế

Kết quả cụ thể của đợt xây dựng được ghi trong `KET_QUA_KIEM_THU_DEMO_1_CLICK.md`, kèm đường dẫn tới runtime mới. Mỗi lần trình diễn sau này vẫn phải đọc kết quả của chính phiên đó.

Để chạy lại bộ hồi quy giao diện/launcher (cần cổng 18000 trống):

```powershell
python -B .\KiemThu\kiem_thu_demo_1_click.py
```

Bộ này chạy launcher `.cmd` thật ở chế độ tự động và thuyết trình, giữ hai điểm chờ quan trọng hơn 10 giây, thử thoát khi chờ và cổng bị chiếm; không chạy lại toàn bộ 22 ca nghiệp vụ nâng cao.
