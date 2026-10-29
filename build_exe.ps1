# Builds dist\PdfEditor.exe: a single file containing Python, the libraries and the
# UI, to send to computers without Python. Run build_exe.cmd (double-click).
#
#   build_exe.cmd             run the tests, then build
#   build_exe.cmd -SkipTests  build only

param([switch]$SkipTests)

$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot
$Host.UI.RawUI.WindowTitle = "Build PdfEditor.exe"
$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

try {
    $global:LASTEXITCODE = 0
    & (Join-Path $PSScriptRoot "startPdfEditor.ps1") -SetupOnly
    if (-not $? -or $LASTEXITCODE -ne 0) { throw "Setting up .venv failed." }

    Write-Host "Installing build tools..."
    & $python -m pip install --disable-pip-version-check -q -r requirements-dev.txt
    if ($LASTEXITCODE -ne 0) { throw "Could not install requirements-dev.txt." }

    if (-not $SkipTests) {
        Write-Host "Running tests..."
        & $python -m pytest -q
        if ($LASTEXITCODE -ne 0) { throw "Tests failed: not building." }
    }

    & $python tools\write_version_info.py build\version_info.txt
    if ($LASTEXITCODE -ne 0) { throw "Could not write the version info." }

    Write-Host "Building (this takes a minute or two)..."
    # Absolute paths: with --specpath, PyInstaller resolves relative ones from build\.
    $static = Join-Path $PSScriptRoot "static"
    & $python -m PyInstaller --noconfirm --clean --log-level WARN `
        --onefile --windowed --name PdfEditor `
        --icon (Join-Path $static "icon.ico") `
        --version-file (Join-Path $PSScriptRoot "build\version_info.txt") `
        --add-data "$static;static" `
        --exclude-module pytest `
        --exclude-module pymupdf.layout --exclude-module pymupdf4llm `
        --exclude-module onnxruntime --exclude-module numpy --exclude-module networkx `
        --specpath build --workpath build\work --distpath dist `
        app.py
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed." }

    $exe = Get-Item "dist\PdfEditor.exe"
    Write-Host ""
    Write-Host ("Built {0} ({1:N0} MB)" -f $exe.FullName, ($exe.Length / 1MB)) -ForegroundColor Green
}
catch {
    Write-Host ""
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    Read-Host "Press Enter to close"
    exit 1
}
Read-Host "Press Enter to close"
