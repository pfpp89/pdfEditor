# Starts the PDF editor on Windows.
# On first run it creates the .venv and installs the dependencies.
# -SetupOnly: only prepare the .venv (used by install.ps1).
# Other arguments are passed to app.py (e.g. --browser-tab).

param([switch]$SetupOnly)

$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot
$Host.UI.RawUI.WindowTitle = "PDF Editor"

$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$venvPythonw = Join-Path $PSScriptRoot ".venv\Scripts\pythonw.exe"
$marker = Join-Path $PSScriptRoot ".venv\.requirements-installed"
$requirements = Join-Path $PSScriptRoot "requirements.txt"

function Find-Python {
    if (Get-Command py -ErrorAction SilentlyContinue) { return @("py", "-3") }
    $python = Get-Command python -ErrorAction SilentlyContinue
    # Skip the Microsoft Store placeholder that only opens the Store.
    if ($python -and $python.Source -notmatch "WindowsApps") { return @($python.Source) }
    return $null
}

try {
    if (-not (Test-Path $venvPython)) {
        $py = Find-Python
        if (-not $py) {
            throw "Python 3 was not found. Install it from https://www.python.org/downloads/ and try again."
        }
        Write-Host "Creating virtual environment (first run only)..."
        $pyArgs = @($py | Select-Object -Skip 1) + @("-m", "venv", ".venv")
        & $py[0] @pyArgs
        if ($LASTEXITCODE -ne 0) { throw "Could not create the virtual environment." }
    }

    if (-not (Test-Path $marker) -or (Get-Item $requirements).LastWriteTime -gt (Get-Item $marker).LastWriteTime) {
        Write-Host "Installing dependencies..."
        & $venvPython -m pip install --disable-pip-version-check -q -r $requirements
        if ($LASTEXITCODE -ne 0) { throw "Could not install the dependencies." }
        New-Item -ItemType File -Path $marker -Force | Out-Null
    }

    if ($SetupOnly) { return }

    # pythonw has no console window; the editor stops when its window is closed.
    $appArgs = @("`"$(Join-Path $PSScriptRoot 'app.py')`"") + $args
    Start-Process -FilePath $venvPythonw -ArgumentList $appArgs -WorkingDirectory $PSScriptRoot
}
catch {
    Write-Host ""
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    Read-Host "Press Enter to close"
    exit 1
}
