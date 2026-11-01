# Set the destination folder
$installDir = Join-Path $env:LOCALAPPDATA "BookCompanion"
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
$userEntries = @($userPath -split ";" | Where-Object { $_ })

# Create it if it doesn't exist
New-Item -ItemType Directory -Path $installDir -Force

# Copy the app files from this script's folder
Copy-Item (Join-Path $PSScriptRoot "companion.bat") $installDir
Copy-Item (Join-Path $PSScriptRoot "book-comp.py") $installDir

if ($userEntries -notcontains $installDir) {
    $updatedPath = (@($userEntries) + $installDir) -join ";"
    [Environment]::SetEnvironmentVariable("Path", $updatedPath, "User")
}

Write-Host "Files installed to $installDir"