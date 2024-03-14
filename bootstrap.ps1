<#
.SYNOPSIS
    Installs required packages and initializes python virtual environment.
.PARAMETER pythonPath
    Path to python installation on windows.
.PARAMETER pwshPath
    Path to PowerShell 7 installation on windows.
.EXAMPLE
    .\bootstrap.ps1 -pythonPath 'C:\Python312' [-pwshPath 'C:\Program Files\PowerShell\7\pwsh.exe']
#>
param(
    $pythonPath = "C:\Python312\python.exe",
    $pwshPath = "C:\Program Files\PowerShell\7\pwsh.exe"
)

##########
# Python
##########
$DESIRED_PYTHON_VERSION = "3.12.0"

if (!(Test-Path -Path $pythonPath)) {
    Write-Host "Installing Python. This may take some time. Please wait."

    $url = "https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe"
    $dest = "python-3.12.0-amd64.exe"

    if (Test-Path -Path $dest) {
        Write-Host "File '$dest' already exists. No download needed."
    }
    else {
        Write-Host "Downloading '$dest'..."
        Invoke-WebRequest -Uri $url -OutFile $dest
    }

    Start-Process $dest -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1 TargetDir=C:\Python311" -Wait
    Write-Host "Python installed successfully."
}
else {
    Write-Host "Python is already installed at $pythonPath."
}

##########
# PowerShell 7
##########

if (!(Test-Path -Path $pwshPath)) {
    Write-Host "Installing Powershell 7. This may take some time. Please wait."

    $url = "https://github.com/PowerShell/PowerShell/releases/download/v7.4.0/PowerShell-7.4.0-win-x86.msi"
    $dest = "PowerShell-7.4.0-win-x86.msi"

    if (Test-Path -Path $dest) {
        Write-Host "File '$dest' already exists. No download needed."
    }
    else {
        Write-Host "Downloading '$dest'..."
        Invoke-WebRequest -Uri $url -OutFile $dest
    }

    Start-Process "msiexec.exe" -ArgumentList "/i $dest /qn /norestart"  -Wait
    Write-Host "PowerShell 7 installed successfully."
}
else {
    Write-Host "PowerShell 7 is already installed at $pwshPath."
}

# Reload path
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

# Init environment
& .\.venv\init.ps1

# Activate environment
& .\.venv\activate.ps1