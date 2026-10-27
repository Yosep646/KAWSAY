$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Write-Host 'KAWSAY AI - verificacion e instalacion local' -ForegroundColor Cyan
function RunChecked([string]$program, [string[]]$arguments) {
  & $program @arguments
  if ($LASTEXITCODE -ne 0) { throw "Falló $program $($arguments -join ' ') con código $LASTEXITCODE" }
}
if (-not (Test-Path (Join-Path $root 'teacher-web/package-lock.json'))) { throw 'Coloca este script en la raíz de KAWSAY-AI, junto a teacher-web y backend.' }
$node = Get-Command node -ErrorAction SilentlyContinue
if (-not $node) { throw 'Node no está instalado. Instala Node >=24.15.0 con winget install OpenJS.NodeJS.LTS; cierra y vuelve a abrir PowerShell.' }
$nodeVersion = (& node -p 'process.versions.node').Trim()
if ([version]$nodeVersion -lt [version]'24.15.0') { throw "Node $nodeVersion incompatible. Instala Node >=24.15.0 y vuelve a abrir PowerShell (winget install OpenJS.NodeJS.LTS)." }
Write-Host "Node $nodeVersion listo" -ForegroundColor Green
Push-Location (Join-Path $root 'teacher-web')
try {
 RunChecked npm @('ci','--no-audit','--no-fund')
 RunChecked npm @('run','typecheck')
 RunChecked npm @('run','build')
 RunChecked npm @('test')
 RunChecked npm @('run','test:integration')
} finally { Pop-Location }
$py = Get-Command py -ErrorAction SilentlyContinue
if ($py) { $pythonExe = 'py'; $pythonArgs = @('-3') } elseif (Get-Command python -ErrorAction SilentlyContinue) { $pythonExe = 'python'; $pythonArgs = @() } else { throw 'Python 3 no está instalado.' }
Push-Location (Join-Path $root 'backend')
try {
 RunChecked $pythonExe ($pythonArgs + @('-m','venv','.venv'))
 $venvPython = Join-Path (Get-Location) '.venv/Scripts/python.exe'
 RunChecked $venvPython @('-m','pip','install','--upgrade','pip')
 RunChecked $venvPython @('-m','pip','install','-r','requirements.txt')
 RunChecked $venvPython @('-m','pip','install','-r','requirements-dev.txt')
 RunChecked $venvPython @('-m','pytest','-q','tests/test_auth.py','tests/test_assignments.py','tests/test_sync_reto10.py')
} finally { Pop-Location }
Push-Location (Join-Path $root 'ml')
try {
 $mlVenv = Join-Path (Get-Location) '.venv'
 RunChecked $pythonExe ($pythonArgs + @('-m','venv',$mlVenv))
 $mlPython = Join-Path $mlVenv 'Scripts/python.exe'
 RunChecked $mlPython @('-m','pip','install','-r','requirements.txt')
 if (Test-Path 'tests') { RunChecked $mlPython @('-m','pytest','-q','tests') }
} finally { Pop-Location }
if (Get-Command flutter -ErrorAction SilentlyContinue) {
 Push-Location (Join-Path $root 'mobile')
 try { RunChecked flutter @('pub','get'); RunChecked flutter @('analyze'); RunChecked flutter @('test') } finally { Pop-Location }
} else { Write-Warning 'Flutter no instalado. Instala Flutter SDK + Android SDK si vas a compilar la app móvil.' }
Write-Host 'Instalación de dependencias terminada. Revisa los resultados de las pruebas mostrados arriba.' -ForegroundColor Green
