# KAWSAY AI: ejecuta frontend + backend + DB en Docker Desktop (sin instalar Node en Windows).
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { throw 'Instala e inicia Docker Desktop primero.' }
& docker compose version
if ($LASTEXITCODE -ne 0) { throw 'Docker Compose no esta disponible.' }
& docker info *> $null
if ($LASTEXITCODE -ne 0) { throw 'Inicia Docker Desktop y vuelve a ejecutar.' }
if (-not (Test-Path '.env')) {
    $b = New-Object byte[] 32
    [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($b)
    $secret = ([BitConverter]::ToString($b)).Replace('-', '').ToLowerInvariant()
    $content = "JWT_SECRET=$secret`nAPP_ENV=development`nWEB_BIND_IP=127.0.0.1`nAI_PROVIDER=disabled`n"
    [System.IO.File]::WriteAllText((Join-Path $PSScriptRoot '.env'), $content, (New-Object System.Text.UTF8Encoding($false)))
    Write-Host 'Configuracion .env creada con JWT_SECRET aleatorio. NO compartir.' -ForegroundColor Yellow
}
& docker compose up -d --build backend teacher-web
if ($LASTEXITCODE -ne 0) { throw 'No se pudo construir o iniciar el sistema. Consulta docker compose logs.' }
Write-Host 'KAWSAY AI: http://127.0.0.1:8080' -ForegroundColor Green
Write-Host 'Pruebas basicas: py scripts/smoke_local_stack.py (o python scripts/smoke_local_stack.py)'
Write-Host 'Para crear admin: establece ADMIN_PASSWORD seguro y ejecuta docker compose exec -e ADMIN_PASSWORD backend python -m app.cli create-admin correo@ejemplo.pe "Administrador"'
