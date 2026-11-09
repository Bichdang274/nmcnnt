# Chi khoi dong bo dieu khien. Chua tao phien hay bat dich vu.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Push-Location -LiteralPath $PSScriptRoot
try {
    python -B -u (Join-Path $PSScriptRoot 'demo_tich_hop.py')
    if ($LASTEXITCODE -ne 0) {
        throw "Bo dieu khien dung voi ma $LASTEXITCODE"
    }
}
finally {
    Pop-Location
}
