param(
  [string]$ZipPath = ""
)

$ErrorActionPreference = "Stop"
$dest = "C:\Users\aziz\Desktop\sk1-hmi\tools\editors\usart-hmi"

$candidates = @()
if ($ZipPath) { $candidates += $ZipPath }
$candidates += @(
  "E:\Downloads\USARTHMIsetup_latest.zip",
  "$env:USERPROFILE\Desktop\USARTHMIsetup_latest.zip",
  "C:\Users\aziz\Desktop\sk1-hmi\tools\editors\USARTHMIsetup_latest.zip"
)

$zip = $candidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
if (-not $zip) {
  Write-Host "USART HMI zip nao encontrado."
  Write-Host "Baixe de http://wiki.tjc1688.com/download/usart_hmi.html"
  Write-Host "Salve o zip completo (~55MB+) e rode:"
  Write-Host "  .\tools\install_usart_hmi.ps1 -ZipPath 'CAMINHO\USARTHMIsetup_latest.zip'"
  exit 1
}

$len = (Get-Item -LiteralPath $zip).Length
Write-Host "Usando $zip ($len bytes)"
if ($len -lt 40MB) {
  Write-Host "AVISO: arquivo parece incompleto (esperado ~55MB). Re-baixe se a extracao falhar."
}

if (Test-Path $dest) { Remove-Item $dest -Recurse -Force }
New-Item -ItemType Directory -Path $dest -Force | Out-Null
Expand-Archive -LiteralPath $zip -DestinationPath $dest -Force

$setup = Get-ChildItem $dest -Recurse -Include *.exe | Where-Object { $_.Name -match 'setup|USART|HMI' } | Select-Object -First 1
if (-not $setup) {
  Write-Host "Extraido, mas nao achei setup.exe. Conteudo:"
  Get-ChildItem $dest -Recurse | Select-Object -First 30 FullName
  exit 2
}

Write-Host "Iniciando instalador: $($setup.FullName)"
Start-Process -FilePath $setup.FullName -Wait
Write-Host "Pronto. Abra USART HMI e siga hmi/BUILD.md"
