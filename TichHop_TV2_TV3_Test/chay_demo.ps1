# Mở bộ điều khiển; chưa tạo phiên, giao dịch hoặc bật dịch vụ.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = $OutputEncoding
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw 'Không tìm thấy Python. Cần cài Python 3 và thêm vào PATH.'
}
Push-Location -LiteralPath $PSScriptRoot
try {
    python -B -u (Join-Path $PSScriptRoot 'demo_tich_hop.py')
    if ($LASTEXITCODE -ne 0) {
        throw "Bộ điều khiển chưa hoàn tất, mã thoát $LASTEXITCODE. Xem thông báo phía trên."
    }
}
finally {
    Pop-Location
}
