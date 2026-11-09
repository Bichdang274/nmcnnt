-- TAM THOI: schema TV3, can TV2 xac nhan; chi tham khao, chua chay.
CREATE TABLE IF NOT EXISTS giao_dich (
                ma_gd TEXT PRIMARY KEY NOT NULL,
                ma_cua_hang TEXT NOT NULL,
                ma_may TEXT NOT NULL,
                thoi_gian TEXT NOT NULL,
                so_tien INTEGER NOT NULL CHECK (so_tien > 0)
            );
