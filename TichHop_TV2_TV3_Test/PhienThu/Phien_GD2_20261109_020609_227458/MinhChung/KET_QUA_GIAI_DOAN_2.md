# Kết quả kiểm thử tích hợp giai đoạn 2

Trạng thái: **PASS**

Phiên: THU_MUC_BAN_GIAO\PhienThu\Phien_GD2_20261109_020609_227458

| Bước | Kết quả | Thực tế |
|---|---|---|
| GD2-01 | PASS | Read README, plan, source and stage 1 PASS; verified isolated source 5/5/5. |
| GD2-02 | PASS | New session seeded through read-only SQLite backup; scripts resolve DB paths from new session. |
| GD2-03 | PASS | Initial new session: store 5, ACKED 5, HQ 5, fields/counter match copied source. |
| GD2-04 | PASS | Replayed 5: 5 DA_TON_TAI ACKs; HQ remains 5, no duplicate IDs. |
| GD2-05 | PASS | TV2 backup contains 5 matching rows; integrity_check ok; immutable B5 recorded. |
| GD2-06 | PASS | Created exactly 5 more; automatic sync reaches store 10 / ACKED 10 / HQ 10. |
| GD2-07 | PASS | Auto sync and receiver stopped before restore; port 18000 free. |
| GD2-08 | PASS | HQ restored 10 -> 5; store remains byte-identical with 10 ACKED; B5 and safety backup10 preserved. |
| GD2-09 | PASS | TV2 detects exactly 5 missing ACKED; exit2; does not falsely report a match. |
| GD2-10 | PASS | TV2 gui-bu sends only the 5 missing records, 5/5 ACKs, and reconciliation passes. |
| GD2-11 | PASS | Final store10/ACKED10/HQ10; exact pre-restore data restored; no duplicates; B5 unchanged. |
| GD2-CLEANUP | PASS | All owned services stopped; port 18000 free. |

Ban đầu: cửa hàng 5, ACKED 5, trụ sở 5, thiếu 0.

Trước phục hồi: cửa hàng 10, ACKED 10, trụ sở 10, thiếu 0.

Sau phục hồi: cửa hàng 10, ACKED 10, trụ sở 5, thiếu 5.

Sau gửi bù: cửa hàng 10, ACKED 10, trụ sở 10, thiếu 0.

Lỗi: Không phát hiện lỗi chức năng trong phạm vi đã chạy.

Phiên giai đoạn 1 giữ nguyên byte: True. Không sửa mã/kiến trúc, không truy cập repository gốc hoặc TV3_TuDong_Test, không thao tác Git.
