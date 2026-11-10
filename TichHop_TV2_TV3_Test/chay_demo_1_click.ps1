param(
    [ValidateSet('tv3', 'tich-hop', 'all')]
    [string]$CheDo = 'all',
    [switch]$TamDung,
    [ValidateRange(0, 30)]
    [double]$NghiGiay = 2,
    [ValidateRange(15, 120)]
    [double]$TimeoutGiay = 45,
    [switch]$KhongGiuManHinh,
    [switch]$KhongMau,
    [switch]$ToiUuCuaSo
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$demoExitCode = 1
$demoOldEncoding = $env:PYTHONIOENCODING
try {
    $OutputEncoding = [System.Text.UTF8Encoding]::new($false)
    [Console]::OutputEncoding = $OutputEncoding
    $env:PYTHONIOENCODING = 'utf-8'
    # Chỉ tối ưu cửa sổ console hiện tại; không sửa profile, registry hay Terminal.
    if ($ToiUuCuaSo -and -not [Console]::IsOutputRedirected -and
        -not $env:WT_SESSION -and -not $env:TERM_PROGRAM) {
        try {
            $demoRaw = $Host.UI.RawUI
            $demoRaw.WindowTitle = 'HỆ THỐNG GIAO DỊCH CHUỖI CỬA HÀNG'
            $demoSize = $demoRaw.WindowSize
            $demoSize.Width = [Math]::Min(110, $demoRaw.MaxPhysicalWindowSize.Width)
            $demoSize.Height = [Math]::Min(36, $demoRaw.MaxPhysicalWindowSize.Height)
            $demoBuffer = $demoRaw.BufferSize
            $demoBuffer.Width = [Math]::Max($demoBuffer.Width, $demoSize.Width)
            $demoBuffer.Height = [Math]::Max($demoBuffer.Height, $demoSize.Height)
            $demoRaw.BufferSize = $demoBuffer
            $demoRaw.WindowSize = $demoSize
        }
        catch { } # Host không hỗ trợ đổi kích thước: giữ cửa sổ hiện tại.
    }
    $demoArguments = @('-B', '-u', (Join-Path $PSScriptRoot 'demo_1_click.py'),
        '--mode', $CheDo, '--delay', $NghiGiay.ToString([Globalization.CultureInfo]::InvariantCulture),
        '--timeout', $TimeoutGiay.ToString([Globalization.CultureInfo]::InvariantCulture))
    if ($TamDung) { $demoArguments += '--pause' }
    if ($KhongMau) { $demoArguments += '--no-color' }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        & python @demoArguments
    }
    elseif (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3 @demoArguments
    }
    else {
        throw 'Không tìm thấy Python. Cần Python 3.9+ và thêm vào PATH.'
    }
    $demoExitCode = $LASTEXITCODE
}
catch {
    Write-Host ('CHƯA ĐẠT: ' + $_.Exception.Message) -ForegroundColor Red
}
finally {
    $env:PYTHONIOENCODING = $demoOldEncoding
    if (-not $KhongGiuManHinh) {
        Write-Host ''
        Read-Host 'Đã kết thúc. Nhấn Enter để đóng màn hình tổng kết' | Out-Null
    }
}
exit $demoExitCode
