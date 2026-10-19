param([Parameter(Mandatory=$true)][string]$NodePath, [int]$Runs = 9)
$ErrorActionPreference = 'Stop'
if ($Runs -lt 3 -or $Runs % 2 -eq 0) { throw 'Runs must be an odd number of at least 3' }
$runtime = (Resolve-Path -LiteralPath $NodePath).Path
$root = Split-Path -Parent $PSScriptRoot
$output = Join-Path $root 'results'
New-Item -ItemType Directory -Force $output | Out-Null
$samples = @()
foreach ($kind in @('buffer-churn', 'buffer-retained', 'heap-churn')) {
  for ($run = 0; $run -lt $Runs; $run++) {
    $order = if ($run % 2 -eq 0) { @('baseline','flag8') } else { @('flag8','baseline') }
    foreach ($variant in $order) {
      $arguments = @()
      if ($variant -eq 'flag8') { $arguments += '--scavenger-max-new-space-capacity-mb=8' }
      $arguments += @((Join-Path $PSScriptRoot 'workload.cjs'), $kind)
      $data = & $runtime @arguments | ConvertFrom-Json
      if ($LASTEXITCODE -ne 0) { throw 'Workload failed' }
      $samples += [pscustomobject]@{workload=$kind; variant=$variant; run=$run; data=$data}
    }
  }
  $middle = [int][math]::Floor($Runs / 2)
  $old = @($samples | Where-Object { $_.workload -eq $kind -and $_.variant -eq 'baseline' } | ForEach-Object { $_.data.ops } | Sort-Object)[$middle]
  $new = @($samples | Where-Object { $_.workload -eq $kind -and $_.variant -eq 'flag8' } | ForEach-Object { $_.data.ops } | Sort-Object)[$middle]
  Write-Output "$kind median change: $([math]::Round(100*($new/$old-1),2))%"
}
$samples | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $output 'windows-flag-tradeoffs.json')
