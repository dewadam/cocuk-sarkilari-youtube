$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$ComfyUrl = if ($env:COMFYUI_URL) { $env:COMFYUI_URL.TrimEnd("/") } else { "http://127.0.0.1:8188" }

Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host " Cocuk Sarkilari - Yerel Uretim Sunucusu Testi" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "Depo: $Root"
Write-Host "ComfyUI: $ComfyUrl"
Write-Host ""

function Check-Command($Name, $Args = @()) {
    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $cmd) {
        Write-Host "[YOK] $Name bulunamadi" -ForegroundColor Red
        return $false
    }
    try {
        $ver = (& $Name @Args 2>&1 | Select-Object -First 1).ToString()
        Write-Host "[OK]  $Name : $ver" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "[UYARI] $Name bulundu ancak surum okunamadi" -ForegroundColor Yellow
        return $false
    }
}

$pythonOk = Check-Command "python" @("--version")
$gitOk = Check-Command "git" @("--version")
$ffmpegOk = Check-Command "ffmpeg" @("-version")
$ffprobeOk = Check-Command "ffprobe" @("-version")

Write-Host ""
Write-Host "--- NVIDIA GPU ---" -ForegroundColor Cyan
$nvidia = Get-Command "nvidia-smi" -ErrorAction SilentlyContinue
if ($nvidia) {
    & nvidia-smi --query-gpu=name,memory.total,memory.used,temperature.gpu --format=csv
} else {
    Write-Host "[UYARI] nvidia-smi PATH icinde bulunamadi. NVIDIA surucusunu kontrol edin." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "--- ComfyUI API ---" -ForegroundColor Cyan
try {
    $system = Invoke-RestMethod -Uri "$ComfyUrl/system_stats" -TimeoutSec 5
    Write-Host "[OK] ComfyUI yanit veriyor." -ForegroundColor Green
    if ($system.system) {
        Write-Host ("Python: " + $system.system.python_version)
        Write-Host ("Torch: " + $system.system.torch_version)
    }
    if ($system.devices) {
        foreach ($device in $system.devices) {
            Write-Host ("Aygit: {0} | VRAM toplam: {1} | VRAM bos: {2}" -f $device.name, $device.vram_total, $device.vram_free)
        }
    }
} catch {
    Write-Host "[YOK] ComfyUI API'ye ulasilamadi. ComfyUI acik olmali: $ComfyUrl" -ForegroundColor Red
}

Write-Host ""
Write-Host "--- Depo kontrolu ---" -ForegroundColor Cyan
$workflowDir = Join-Path $Root ".github\workflows"
if (Test-Path $workflowDir) {
    $count = (Get-ChildItem $workflowDir -Filter "*.yml" -File | Measure-Object).Count
    Write-Host "[OK] GitHub Actions is akislari: $count"
} else {
    Write-Host "[UYARI] .github\workflows klasoru bulunamadi." -ForegroundColor Yellow
}
Write-Host ""
Write-Host "Test tamamlandi. Bu script video uretmez ve herhangi bir dosyayi degistirmez."
Write-Host "Sonraki adim icin bu ekrandaki ciktinin tamamini paylasin."
