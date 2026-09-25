<#
Movie Match developer tasks (Windows / PowerShell).

    .\tasks.ps1 doctor      check that the required tools are installed
    .\tasks.ps1 install     install API and web dependencies
    .\tasks.ps1 dev-api     run the API with reload
    .\tasks.ps1 dev-web     run the web dev server
    .\tasks.ps1 lint        lint both projects
    .\tasks.ps1 test        THE PHASE GATE - lint, typecheck, build, tests
    .\tasks.ps1 migrate     apply database migrations

`test` is what the phase prompts mean by "run the gate". It stops at the first
failing command, so a green run means every step passed.
#>

param(
  [Parameter(Position = 0)]
  [ValidateSet('doctor', 'install', 'dev-api', 'dev-web', 'lint', 'test', 'migrate', 'help')]
  [string]$Task = 'help'
)

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$api = Join-Path $root 'services\api'
$web = Join-Path $root 'apps\web'
$python = Join-Path $api '.venv\Scripts\python.exe'

function Invoke-Step {
  param([string]$Name, [string]$Directory, [scriptblock]$Action)
  Write-Host ""
  Write-Host "=== $Name ===" -ForegroundColor Cyan
  Push-Location $Directory
  try {
    & $Action
    if ($LASTEXITCODE -ne 0) { throw "$Name failed with exit code $LASTEXITCODE" }
  }
  finally { Pop-Location }
}

function Find-SystemPython {
  # The interpreter used to build the virtualenv. Needs 3.12 or newer. Returns a full path.
  # Never runs `py`, and skips anything under WindowsApps: on Windows those are aliases for
  # the Python install manager, which can start downloading a Python when invoked.
  $candidates = @()
  foreach ($v in '312', '313') {
    $candidates += Join-Path $env:LOCALAPPDATA "Programs\Python\Python$v\python.exe"
    $candidates += Join-Path $env:ProgramFiles "Python$v\python.exe"
  }
  foreach ($name in 'python', 'python3') {
    $candidates += @(Get-Command $name -CommandType Application -All -ErrorAction SilentlyContinue |
      ForEach-Object { $_.Source })
  }
  foreach ($exe in $candidates) {
    if (-not $exe -or $exe -like '*\WindowsApps\*' -or -not (Test-Path $exe)) { continue }
    $probe = 'import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)'
    & $exe -c $probe 2>$null
    if ($LASTEXITCODE -eq 0) { return $exe }
  }
  return $null
}

function Assert-Venv {
  if (-not (Test-Path $python)) {
    throw "No virtualenv at $python. Run: .\tasks.ps1 install"
  }
}

switch ($Task) {
  'doctor' {
    Write-Host "`
=== tool check ===" -ForegroundColor Cyan
    $ok = $true

    $sysPython = Find-SystemPython
    if ($sysPython) {
      $version = (& $sysPython --version) 2>&1
      Write-Host "  ok       python: $version  ($sysPython)"
    }
    else {
      Write-Host "  MISSING  Python 3.12+ - install from python.org, tick 'Add python.exe to PATH'" -ForegroundColor Yellow
      $ok = $false
    }

    if (Get-Command node -ErrorAction SilentlyContinue) {
      # Parsed here rather than with `node -p`: PowerShell 5.1 strips inner quotes from native args.
      $nodeMajor = [int]((node --version).TrimStart('v').Split('.')[0])
      if ($nodeMajor -ge 20) { Write-Host "  ok       node: $(node --version)" }
      else { Write-Host "  OLD      node: $(node --version) - need 20 or newer" -ForegroundColor Yellow; $ok = $false }
    }
    else {
      Write-Host "  MISSING  Node 20+ - install the LTS build from nodejs.org" -ForegroundColor Yellow
      $ok = $false
    }

    if (Get-Command npm -ErrorAction SilentlyContinue) { Write-Host "  ok       npm: $(npm --version)" }
    else { Write-Host "  MISSING  npm (ships with Node)" -ForegroundColor Yellow; $ok = $false }

    if (Get-Command git -ErrorAction SilentlyContinue) { Write-Host "  ok       git: $(git --version)" }
    else { Write-Host "  MISSING  git" -ForegroundColor Yellow; $ok = $false }

    if (Test-Path $python) { Write-Host "  ok       virtualenv: $python" }
    else { Write-Host "  note     no virtualenv yet - run: tasks install" }

    Write-Host ""
    if ($ok) { Write-Host "All required tools present." -ForegroundColor Green }
    else {
      Write-Host "Install what is marked MISSING, open a new terminal, then run: tasks doctor" -ForegroundColor Yellow
      exit 1
    }
  }

  'install' {
    $sysPython = Find-SystemPython
    if (-not $sysPython) { throw "Python 3.12+ not found. Run: tasks doctor" }
    Invoke-Step 'create virtualenv' $api { & $sysPython -m venv .venv }
    Invoke-Step 'upgrade pip' $api { & $python -m pip install --upgrade pip }
    Invoke-Step 'install api deps' $api { & $python -m pip install -e ".[dev]" }
    Invoke-Step 'install web deps' $web { npm install }
    Write-Host "`nDone. Copy the .env.example files to .env and fill them in." -ForegroundColor Green
  }

  'dev-api' {
    Assert-Venv
    Invoke-Step 'api' $api { & $python -m uvicorn app.main:app --reload }
  }

  'dev-web' {
    Invoke-Step 'web' $web { npm run dev }
  }

  'lint' {
    Assert-Venv
    Invoke-Step 'ruff check' $api { & $python -m ruff check . }
    Invoke-Step 'ruff format' $api { & $python -m ruff format --check . }
    Invoke-Step 'eslint' $web { npm run lint }
  }

  'migrate' {
    Assert-Venv
    Invoke-Step 'alembic upgrade head' $api { & $python -m alembic upgrade head }
  }

  'test' {
    Assert-Venv
    Invoke-Step 'ruff check' $api { & $python -m ruff check . }
    Invoke-Step 'ruff format --check' $api { & $python -m ruff format --check . }
    Invoke-Step 'pytest' $api { & $python -m pytest -q }
    Invoke-Step 'eslint' $web { npm run lint }
    Invoke-Step 'typecheck' $web { npm run typecheck }
    Invoke-Step 'build' $web { npm run build }
    Invoke-Step 'vitest' $web { npm test }
    Write-Host "`nGATE PASSED - every command exited 0." -ForegroundColor Green
  }

  default {
    Get-Help $PSCommandPath -Detailed
  }
}
