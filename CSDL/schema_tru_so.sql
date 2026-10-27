-- CSDL trung tâm (trụ sở) – DuLieu/hq.db – TV2 thiết kế
-- Khóa chính ma_gd chặn ghi trùng: gửi lại cùng một giao dịch chỉ bị bỏ qua (INSERT OR IGNORE)
CREATE TABLE IF NOT EXISTS giao_dich (
    ma_gd           TEXT PRIMARY KEY,           -- CHxx-POSyy-yyyymmdd-nnnnnn
    ma_ch           TEXT NOT NULL,              -- CH01, CH02, CH03
    ma_pos          TEXT NOT NULL,              -- POS01 .. POS05
    thoi_diem_tao   TEXT NOT NULL,              -- giờ máy POS tạo giao dịch
    tong_tien       INTEGER NOT NULL CHECK (tong_tien >= 0),
    so_mat_hang     INTEGER NOT NULL CHECK (so_mat_hang > 0),
    thoi_diem_nhan  TEXT NOT NULL               -- giờ trụ sở ghi nhận lần đầu
);
-- Nhật ký mọi lần nhận (kể cả bản trùng) để chứng minh chống trùng
CREATE TABLE IF NOT EXISTS nhat_ky_nhan (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    ma_gd      TEXT NOT NULL,
    thoi_diem  TEXT NOT NULL,
    ket_qua    TEXT NOT NULL CHECK (ket_qua IN ('MOI', 'TRUNG'))
);
