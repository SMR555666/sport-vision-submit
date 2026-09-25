# ═══════════════════════════════════════════════════════════════════════
# 把 D 盘的训练集 / 基础镜像链接到仓库的 work\ 下，避免复制 28GB。
#
#   PowerShell -ExecutionPolicy Bypass -File tools\link_data.ps1
#
# 用目录联接（Junction）而不是复制，所以：
#   · 不占额外磁盘
#   · 两个任务的训练数据仍在 D:\mCloudDownload 原地，云盘/下载器继续管它们
#   · work\ 整体已在 .gitignore 里，git 不会误收这 28GB
#
# 用完想解除链接（不会删原数据）：
#   Remove-Item work\data\pp_train_data    # Junction 删链接，不删目标
# ═══════════════════════════════════════════════════════════════════════
$ErrorActionPreference = "Stop"

$Repo    = Split-Path -Parent $PSScriptRoot          # 仓库根
$SrcRoot = "D:\mCloudDownload\乒乓球多视角落点检测"   # D 盘资源根（如搬过位置请改这里）

$work = Join-Path $Repo "work"
$data = Join-Path $work "data"
New-Item -ItemType Directory -Path $data -Force | Out-Null

# 注意：D 盘这套资源是「双层嵌套」结构，真正的数据在内层同名目录里
$links = @(
    @{ Name = "pp_train_data"; Target = Join-Path $SrcRoot "pp_train_data\pp_train_data" },
    @{ Name = "bb_train_data"; Target = Join-Path $SrcRoot "bb_train_data\bb_train_data" },
    @{ Name = "sport-base_v1"; Target = Join-Path $SrcRoot "sport-base_v1" }
)

foreach ($l in $links) {
    $link   = Join-Path $data $l.Name
    $target = $l.Target

    if (-not (Test-Path -LiteralPath $target)) {
        Write-Warning "找不到目标，跳过：$target"
        continue
    }
    if (Test-Path -LiteralPath $link) {
        Write-Host "已存在，跳过：$link"
        continue
    }
    New-Item -ItemType Junction -Path $link -Target $target | Out-Null
    Write-Host "已链接 $link  ->  $target"
}

Write-Host ""
Write-Host "=== work\data 现状 ==="
Get-ChildItem -LiteralPath $data -Force |
    Select-Object Mode, Name, @{n = 'Target'; e = { $_.Target } } | Format-Table -AutoSize

Write-Host "训练集体积（链接，不占额外空间）："
foreach ($n in @("pp_train_data", "bb_train_data")) {
    $p = Join-Path $data $n
    if (Test-Path -LiteralPath $p) {
        $s = (Get-ChildItem -LiteralPath $p -Recurse -File -ErrorAction SilentlyContinue |
              Measure-Object -Property Length -Sum).Sum
        Write-Host ("  {0,-16} {1,10:N1} MB" -f $n, ($s / 1MB))
    }
}
