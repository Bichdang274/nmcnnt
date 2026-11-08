
# Chuyen ve thu muc goc du an
Set-Location $PSScriptRoot

# Tao thu muc luu minh chung neu chua co
New-Item -ItemType Directory -Force -Path ".\MinhChung\TuDong" | Out-Null

# Chay dong bo tu dong va luu log
python -u .\Script\auto_sync.py 2>&1 |
    Tee-Object -FilePath ".\MinhChung\TuDong\auto_sync_log.txt" -Append
