# Prepare Docker for ai-lab-portal e2e: inspect conflicts, stop this repo's stack, start postgres only.
param(
    [switch]$SkipDown,
    [switch]$NoPostgres
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$ProjectPorts = @(15432, 16379, 18000, 13000, 13100)

function Test-Docker {
    docker version --format "{{.Server.Version}}" 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Docker daemon is not running. Start Docker Desktop and retry."
    }
}

function Show-PortListeners {
    Write-Host "`n=== Host ports used by ai-lab-portal / e2e ===" -ForegroundColor Cyan
    foreach ($port in $ProjectPorts) {
        $listeners = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
        if ($listeners) {
            $pids = $listeners | Select-Object -ExpandProperty OwningProcess -Unique
            foreach ($pid in $pids) {
                $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
                $name = if ($proc) { $proc.ProcessName } else { "?" }
                Write-Host "  Port $port -> PID $pid ($name)"
            }
        } else {
            Write-Host "  Port $port -> free"
        }
    }
}

function Show-AllContainers {
    Write-Host "`n=== All running containers (compose project label) ===" -ForegroundColor Cyan
    docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Ports}}\t{{.Label `"com.docker.compose.project`"}}"
}

function Stop-LocalNodeE2E {
    Write-Host "`n=== Stopping stale local dev on e2e ports (not Docker) ===" -ForegroundColor Cyan
    foreach ($port in @(13100, 18000)) {
        $listeners = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
        if (-not $listeners) { continue }
        foreach ($pid in ($listeners | Select-Object -ExpandProperty OwningProcess -Unique)) {
            $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
            if ($proc -and $proc.ProcessName -match "node|python") {
                Write-Host "  Killing PID $pid ($($proc.ProcessName)) on port $port"
                Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
            }
        }
    }
}

Test-Docker
Show-AllContainers
Show-PortListeners

if (-not $SkipDown) {
    Write-Host "`n=== Stopping ai-lab-portal compose stack (this repo only) ===" -ForegroundColor Cyan
    Push-Location $RepoRoot
    docker compose down --remove-orphans
    Pop-Location
}

Stop-LocalNodeE2E
Show-PortListeners

if (-not $NoPostgres) {
    Write-Host "`n=== Starting postgres only for e2e ===" -ForegroundColor Cyan
    Push-Location $RepoRoot
    docker compose up -d postgres
    docker compose ps postgres
    Write-Host "Waiting for postgres health..."
    $deadline = (Get-Date).AddMinutes(2)
    do {
        Start-Sleep -Seconds 2
        $health = docker inspect --format "{{.State.Health.Status}}" (docker compose ps -q postgres) 2>$null
        if ($health -eq "healthy") { break }
    } while ((Get-Date) -lt $deadline)
    if ($health -ne "healthy") {
        Write-Warning "Postgres may not be healthy yet. Check: docker compose logs postgres"
    } else {
        Write-Host "Postgres is healthy on localhost:15432" -ForegroundColor Green
    }
    Pop-Location
}

Write-Host "`nDone. Run e2e from frontend: npm run test:e2e" -ForegroundColor Green
