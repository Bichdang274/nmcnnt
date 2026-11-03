# Demo tích hợp Nhóm 02 – chỉ dùng thư viện chuẩn Python, không cài thêm gói nào
FROM python:3.12-slim
WORKDIR /app
COPY demo_tich_hop.py giao_dien.html README.md ./
COPY Script_TV3 ./Script_TV3
COPY Script_TV2 ./Script_TV2
COPY CauHinh ./CauHinh
ENV DEMO_HOST=0.0.0.0 PYTHONUNBUFFERED=1
EXPOSE 8765
CMD ["python", "demo_tich_hop.py", "--khong-mo"]
