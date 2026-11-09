# Ket qua tich hop giai doan 1

Trang thai: **PASS**

| Ca | Ket qua | Thuc te |
|---|---|---|
| GD1-BOOT | PASS | Controller started; no data/service created automatically. |
| GD1-SESSION | PASS | New isolated session and empty store. |
| GD1-EMPTY | PASS | Empty 0/0 rejected with exit code 2 as expected. |
| GD1-STOP | PASS | Owned receiver stopped; port 18000 released. |
| GD1-CREATE | PASS | Created exactly 5 PENDING; HQ remains 0. |
| GD1-OFFLINE | PASS | 5 SENT retained; HQ 0; all 5 automatic failures logged. |
| GD1-RECOVER | PASS | Same auto-sync process recovered 5 transactions without manual sending. |
| GD1-COMPARE | PASS | Store=5, ACKED=5, HQ=5; all five fields match; no duplicate IDs. |
| GD1-CLEANUP | PASS | Controller exited 0; owned children stopped; port 18000 free. |

Loi: Khong phat hien loi trong pham vi da thu.

Giu nguyen DB va log cua phien. Khong thu sao luu, phuc hoi, gui bu, gui lap hay 10 GD.
Khong truy cap/chay nmcnnt hoac TV3_TuDong_Test.
