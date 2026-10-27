# KAWSAY AI: subir proyecto al repositorio ya existente Yosep646/KAWSAY
# Ejecutar desde una extraccion limpia del ZIP con Git instalado y autenticado.
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $ProjectRoot
$Repo = 'https://github.com/Yosep646/KAWSAY.git'
function Check([string]$phase) {
  if ($LASTEXITCODE -ne 0) { throw "Error en $phase (codigo $LASTEXITCODE). Comprueba red, credenciales y permisos." }
}
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw 'Necesitas Git: https://git-scm.com/downloads' }
foreach ($required in @('render.yaml','render.Dockerfile','teacher-web/package.json','backend/requirements.txt','.gitignore')) {
  if (-not (Test-Path -LiteralPath $required)) { throw "No se encontro $required; abre el directorio KAWSAY-AI descomprimido." }
}
if (Test-Path '.git') { throw 'Hay un directorio .git. Usa una extraccion limpia para no afectar otro repositorio.' }
$unsafe=@(Get-ChildItem -File -Recurse -Force | Where-Object {
  $_.Name -match '^\.env($|\.(?!example$))|^(id_rsa|id_ed25519)$|\.(sqlite|sqlite3|db|pem|p12|pfx|key)$' -or
  $_.FullName -match '[\\/](node_modules|\.venv|venv|__pycache__)[\\/]'
})
if ($unsafe.Count -gt 0) {
  $unsafe | ForEach-Object { Write-Host "Archivo sensible/no publicable: $($_.FullName)" }
  throw 'Se detectaron archivos no publicables; revisalos antes de hacer git add.'
}
& git init -b main
Check 'git init'
& git remote add origin $Repo
Check 'git remote add origin'
# Abortar ante una rama remota con commits. Nunca usar --force.
$heads = & git ls-remote --heads origin main
Check 'git ls-remote (comprueba acceso a GitHub)'
if (-not [string]::IsNullOrWhiteSpace(($heads -join "`n"))) { throw 'La rama main ya tiene commits. Se detuvo la publicacion para evitar sobrescribirla.' }
& git add --all
Check 'git add'
& git diff --cached --quiet
if ($LASTEXITCODE -eq 0) { throw 'No hay archivos para publicar.' }
& git commit -m 'Initial KAWSAY AI source and Render deployment config'
Check 'git commit'
& git push -u origin main
Check 'git push'
Write-Host "Proyecto subido correctamente: https://github.com/Yosep646/KAWSAY"
