# Starts the PDF editor on Windows.
# On first run it creates the .venv and installs the dependencies.

$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot
$Host.UI.RawUI.WindowTitle = "PDF Editor"

$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
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

    Write-Host "Starting PDF editor. Close this window or press Ctrl+C to stop it."
    & $venvPython (Join-Path $PSScriptRoot "app.py") @args
}
catch {
    Write-Host ""
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    Read-Host "Press Enter to close"
    exit 1
}
