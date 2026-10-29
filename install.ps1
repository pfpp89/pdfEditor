# Installs or uninstalls PDF Editor for the current Windows user.
#
#   install.cmd                        install: prepare the .venv, create Desktop and
#                                      Start menu shortcuts (double-click)
#   install.cmd -Name "Editor de PDF"  install with another shortcut name
#   uninstall.cmd                      uninstall (double-click) = install.cmd -Uninstall:
#                                      remove the shortcuts and the editor's data in
#                                      %LOCALAPPDATA%\PdfEditor; the folder itself is
#                                      then deleted by hand
#
# The shortcuts created are recorded in .installed-shortcuts.txt so that the
# uninstall finds them whatever name was used.

param(
    [string]$Name = "PDF Editor",
    [switch]$Uninstall
)

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$Host.UI.RawUI.WindowTitle = "PDF Editor setup"

$record = Join-Path $root ".installed-shortcuts.txt"
$dataDir = Join-Path $env:LOCALAPPDATA "PdfEditor"
$shortcuts = @(
    (Join-Path ([Environment]::GetFolderPath("Desktop")) "$Name.lnk"),
    (Join-Path ([Environment]::GetFolderPath("Programs")) "$Name.lnk")
)

function Test-EditorRunning {
    $instance = Join-Path $dataDir "instance.json"
    if (-not (Test-Path -LiteralPath $instance)) { return $false }
    try {
        $procId = (Get-Content -LiteralPath $instance -Raw | ConvertFrom-Json).pid
        $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
        return [bool]($proc -and $proc.ProcessName -like "python*")
    }
    catch { return $false }
}

function Uninstall-Editor {
    if (Test-EditorRunning) {
        throw "PDF Editor is still open. Close its window, wait a few seconds, then run the uninstall again."
    }

    $all = @($shortcuts)
    if (Test-Path -LiteralPath $record) { $all += Get-Content -LiteralPath $record }
    foreach ($lnk in ($all | Where-Object { $_ } | Sort-Object -Unique)) {
        if (Test-Path -LiteralPath $lnk) {
            Remove-Item -LiteralPath $lnk
            Write-Host "Removed shortcut $lnk"
        }
    }
    if (Test-Path -LiteralPath $record) { Remove-Item -LiteralPath $record }

    if (Test-Path -LiteralPath $dataDir) {
        Remove-Item -LiteralPath $dataDir -Recurse -Force
        Write-Host "Removed data folder $dataDir"
    }

    Write-Host ""
    Write-Host "PDF Editor has been uninstalled." -ForegroundColor Green
    Write-Host "To finish, delete this folder:"
    Write-Host "    $root"
    Write-Host "(Python itself is still installed; remove it from Settings > Apps if no longer needed.)"
}

function Install-Editor {
    $global:LASTEXITCODE = 0
    & (Join-Path $root "startPdfEditor.ps1") -SetupOnly
    if (-not $? -or $LASTEXITCODE -ne 0) { throw "Setup failed." }

    $pythonw = Join-Path $root ".venv\Scripts\pythonw.exe"
    if (-not (Test-Path -LiteralPath $pythonw)) { throw "Setup did not create $pythonw" }

    $shell = New-Object -ComObject WScript.Shell
    foreach ($lnk in $shortcuts) {
        $s = $shell.CreateShortcut($lnk)
        $s.TargetPath = $pythonw
        $s.Arguments = "`"$(Join-Path $root 'app.py')`""
        $s.WorkingDirectory = $root
        $s.IconLocation = "$(Join-Path $root 'static\icon.ico'),0"
        $s.Description = "Open, reorder and delete PDF pages"
        $s.Save()
        Write-Host "Created $lnk"
    }

    $known = @()
    if (Test-Path -LiteralPath $record) { $known = @(Get-Content -LiteralPath $record) }
    ($known + $shortcuts) | Where-Object { $_ } | Sort-Object -Unique | Set-Content -LiteralPath $record -Encoding UTF8

    Write-Host ""
    Write-Host "Done. Start PDF Editor with the '$Name' icon on the Desktop or in the Start menu." -ForegroundColor Green
}

try {
    if ($Uninstall) { Uninstall-Editor } else { Install-Editor }
}
catch {
    Write-Host ""
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    Read-Host "Press Enter to close"
    exit 1
}
Read-Host "Press Enter to close"
