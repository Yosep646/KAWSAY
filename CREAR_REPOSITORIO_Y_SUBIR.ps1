# El repositorio Yosep646/KAWSAY ya existe. No se debe crear otro.
$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot 'SUBIR_A_KAWSAY.ps1')
if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
