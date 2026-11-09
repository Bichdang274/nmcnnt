-- Truy vấn đối chiếu (KT3, KT3-b, BK-1) – chạy trên DuLieu/hq.db
-- Mở bằng: sqlite3 DuLieu/hq.db   hoặc   python3 Script/doi_chieu.py (chạy sẵn Q1–Q4)

-- Q1. Số bản ghi theo cửa hàng
SELECT ma_ch, COUNT(*) AS so_ban_ghi FROM giao_dich GROUP BY ma_ch ORDER BY ma_ch;

-- Q2. Mã giao dịch trùng – phải trả về RỖNG
SELECT ma_gd, COUNT(*) FROM giao_dich GROUP BY ma_gd HAVING COUNT(*) > 1;

-- Q3. Số lần trụ sở nhận bản trùng (bỏ qua nhưng vẫn ACK)
SELECT ket_qua, COUNT(*) FROM nhat_ky_nhan GROUP BY ket_qua;

-- Q4. Giao dịch cửa hàng 1 đã ACKED mà trụ sở thiếu – phải bằng 0
ATTACH DATABASE 'DuLieu/ch1.db' AS ch1;
SELECT COUNT(*) FROM ch1.hang_doi
 WHERE trang_thai = 'ACKED' AND ma_gd NOT IN (SELECT ma_gd FROM giao_dich);

-- Q5. Tổng tiền theo cửa hàng (báo cáo doanh thu tại trụ sở)
SELECT ma_ch, COUNT(*) AS so_gd, SUM(tong_tien) AS doanh_thu FROM giao_dich GROUP BY ma_ch;
