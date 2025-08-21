# Rogue Install Script for Windows (PowerShell)
# This script downloads and installs the latest release of Rogue

param(
    [string]$InstallDir = "$env:USERPROFILE\rogue",
    [switch]$SkipPathUpdate,
    [switch]$Force,
    [string]$Version = "",
    [switch]$Help
)

# Function to show usage
function Show-Usage {
    Write-Host @"
Usage: .\install.ps1 [OPTIONS]

Options:
    -InstallDir DIR        Installation directory (default: ~\rogue)
    -SkipPathUpdate        Skip PATH update
    -Force                 Force installation even if directory exists
    -Version VER           Install specific version (e.g., v1.0.0, 1.0.0, or 'latest')
    -Help                  Show this help message

Examples:
    .\install.ps1                          # Install to ~\rogue
    .\install.ps1 -InstallDir C:\rogue     # Install to C:\rogue
    .\install.ps1 -SkipPathUpdate          # Install without updating PATH
    .\install.ps1 -Force                   # Force installation
    .\install.ps1 -Version 1.0.0           # Install version v1.0.0
    .\install.ps1 -Version v2.1.0          # Install version v2.1.0
    .\install.ps1 -Version latest          # Install latest version (explicit)

"@
}

# Function to detect architecture
function Get-Architecture {
    if ([Environment]::Is64BitOperatingSystem) {
        return "amd64"
    } else {
        return "386"
    }
}

# Function to download release
function Get-Release {
    param([string]$TempDir, [string]$Version)
    
    try {
        $repo = "qualifire-dev/rogue-private"
        $releaseInfo = $null
        $downloadUrl = $null
        
        # Set version to latest if not specified
        if ([string]::IsNullOrEmpty($Version) -or $Version -eq "latest") {
            $Version = "latest"
        } else {
            # Ensure version has 'v' prefix
            if (-not $Version.StartsWith("v")) {
                $Version = "v$Version"
            }
        }
        
        # Fetch release information
        if ($Version -eq "latest") {
            Write-Host "[INFO] Fetching latest release information..." -ForegroundColor Blue
            $apiUrl = "https://api.github.com/repos/$repo/releases/latest"
        } else {
            Write-Host "[INFO] Fetching release information for version $Version..." -ForegroundColor Blue
            $apiUrl = "https://api.github.com/repos/$repo/releases/tags/$Version"
        }
        $releaseInfo = Invoke-RestMethod -Uri $apiUrl -Method Get
        
        # Extract download URL
        $downloadUrl = $releaseInfo.assets[0].browser_download_url
        
        if ([string]::IsNullOrEmpty($downloadUrl)) {
            throw "Failed to parse release information for $Version"
        }
        
        # For latest version, also extract and update the tag name
        if ($Version -eq "latest") {
            $tagName = $releaseInfo.tag_name
            
            if (-not [string]::IsNullOrEmpty($tagName)) {
                $Version = $tagName
                Write-Host "[INFO] Latest release: $Version" -ForegroundColor Blue
            } else {
                Write-Host "[WARNING] Could not parse tag name from latest release, continuing with 'latest'" -ForegroundColor Yellow
                Write-Host "[INFO] Latest release: latest" -ForegroundColor Blue
            }
        } else {
            Write-Host "[INFO] Found release: $Version" -ForegroundColor Blue
        }
        
        Write-Host "[INFO] Downloading release archive..." -ForegroundColor Blue
        
        $archiveName = "rogue-release-${Version}.zip"
        $archivePath = Join-Path $TempDir $archiveName
        
        Invoke-WebRequest -Uri $downloadUrl -OutFile $archivePath
        
        Write-Host "[SUCCESS] Downloaded release archive: $archiveName" -ForegroundColor Green
        return $archivePath
    }
    catch {
        Write-Host "[ERROR] Failed to download release: $($_.Exception.Message)" -ForegroundColor Red
        throw
    }
}

# Function to extract and install files
function Install-Release {
    param(
        [string]$ArchivePath,
        [string]$InstallDir,
        [string]$Platform
    )
    
    Write-Host "[INFO] Extracting release archive..." -ForegroundColor Blue
    
    # Create temporary extraction directory
    $tempExtractDir = New-TemporaryFile | ForEach-Object { Remove-Item $_; New-Item -ItemType Directory -Path $_ }
    
    try {
        # Extract the archive
        Expand-Archive -Path $ArchivePath -DestinationPath $tempExtractDir -Force
        
        # Find Python wheel
        $wheelFile = Get-ChildItem -Path $tempExtractDir -Filter "rogue-*.whl" | Select-Object -First 1
        
        if (-not $wheelFile) {
            throw "No Python wheel found in release"
        }
        
        Write-Host "[INFO] Found Python wheel: $($wheelFile.Name)" -ForegroundColor Blue
        
        # Find appropriate binary for the platform
        $binaryPattern = "rogue-*${Platform}*"
        $binaryFile = Get-ChildItem -Path $tempExtractDir -Filter $binaryPattern | Select-Object -First 1
        
        if (-not $binaryFile) {
            Write-Host "[WARNING] No binary found for platform $Platform" -ForegroundColor Yellow
            Write-Host "[INFO] Available files:" -ForegroundColor Blue
            Get-ChildItem -Path $tempExtractDir -Filter "rogue-*" | ForEach-Object { $_.Name }
        } else {
            Write-Host "[INFO] Found binary: $($binaryFile.Name)" -ForegroundColor Blue
        }
        
        # Create installation directory
        New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
        
        # Store the wheel file for uvx usage
        if ($wheelFile) {
            Write-Host "[INFO] Setting up Python wheel for uvx..." -ForegroundColor Blue
            
            $wheelDest = Join-Path $InstallDir "rogue.whl"
            Copy-Item -Path $wheelFile.FullName -Destination $wheelDest -Force
            
            # Create wrapper script for rogue command
            $wrapperScript = Join-Path $InstallDir "rogue.ps1"
            $wrapperContent = @"
# Rogue wrapper script that uses uvx to run the wheel
param(`$args)
uvx "`$PSScriptRoot\rogue.whl" @args
"@
            Set-Content -Path $wrapperScript -Value $wrapperContent
            
            Write-Host "[SUCCESS] Python wheel setup completed - use 'rogue' command" -ForegroundColor Green
        }
        
        # Install binary
        if ($binaryFile) {
            Write-Host "[INFO] Installing binary..." -ForegroundColor Blue
            
            $binaryName = "rogue-tui.exe"
            $binaryDest = Join-Path $InstallDir $binaryName
            
            Copy-Item -Path $binaryFile.FullName -Destination $binaryDest -Force
            
            Write-Host "[SUCCESS] Binary installed as $binaryName" -ForegroundColor Green
        }
        
        Write-Host "[SUCCESS] Installation completed successfully!" -ForegroundColor Green
    }
    finally {
        # Clean up
        Remove-Item -Path $tempExtractDir -Recurse -Force
    }
}

# Function to update PATH
function Update-Path {
    param([string]$InstallDir)
    
    if ($SkipPathUpdate) {
        Write-Host "[INFO] Skipping PATH update as requested" -ForegroundColor Blue
        return
    }
    
    Write-Host "[INFO] Updating PATH..." -ForegroundColor Blue
    
    try {
        $currentPath = [Environment]::GetEnvironmentVariable("PATH", "User")
        
        if ($currentPath -like "*$InstallDir*") {
            Write-Host "[INFO] PATH already contains $InstallDir" -ForegroundColor Blue
            return
        }
        
        $newPath = "$InstallDir;$currentPath"
        [Environment]::SetEnvironmentVariable("PATH", $newPath, "User")
        
        Write-Host "[SUCCESS] Added $InstallDir to PATH" -ForegroundColor Green
        Write-Host "[WARNING] Please restart your terminal or run 'refreshenv' to apply changes" -ForegroundColor Yellow
    }
    catch {
        Write-Host "[WARNING] Failed to update PATH: $($_.Exception.Message)" -ForegroundColor Yellow
        Write-Host "[INFO] Please manually add $InstallDir to your PATH" -ForegroundColor Blue
    }
}

# Main function
function Main {
    if ($Help) {
        Show-Usage
        return
    }
    
    # Handle version parameter
    if ($Version -eq "latest") {
        $Version = ""
    }
    
    Write-Host "Rogue Installer" -ForegroundColor Blue
    Write-Host "========================" -ForegroundColor Blue
    Write-Host ""
    
    # Check if installation directory already exists
    if ((Test-Path $InstallDir) -and (-not $Force)) {
        Write-Host "[ERROR] Installation directory $InstallDir already exists" -ForegroundColor Red
        Write-Host "[INFO] Use -Force to overwrite, or specify a different directory with -InstallDir" -ForegroundColor Blue
        exit 1
    }
    
    # Detect platform
    $arch = Get-Architecture
    $platform = "windows-$arch"
    Write-Host "[INFO] Detected platform: $platform" -ForegroundColor Blue
    
    # Create temporary directory
    $tempDir = New-TemporaryFile | ForEach-Object { Remove-Item $_; New-Item -ItemType Directory -Path $_ }
    
    try {
        # Download release
        $archivePath = Get-Release -TempDir $tempDir -Version $Version
        
        # Extract and install files
        Install-Release -ArchivePath $archivePath -InstallDir $InstallDir -Platform $platform
        
        # Update PATH
        Update-Path -InstallDir $InstallDir
        
        # Final instructions
        Write-Host ""
        Write-Host "[SUCCESS] Installation completed!" -ForegroundColor Green
        Write-Host "[INFO] Installation directory: $InstallDir" -ForegroundColor Blue
        Write-Host ""
        Write-Host "[INFO] Available commands:" -ForegroundColor Blue
        
        $pythonScript = Join-Path $InstallDir "rogue.ps1"
        $binaryFile = Join-Path $InstallDir "rogue-tui.exe"
        
        if (Test-Path $pythonScript) {
            Write-Host "  rogue - Python-based rogue agent evaluator (runs with uvx)" -ForegroundColor White
        }
        if (Test-Path $binaryFile) {
            Write-Host "  rogue-tui - Terminal UI for rogue agent evaluator" -ForegroundColor White
        }
        
        Write-Host ""
        Write-Host "[INFO] To use rogue commands, restart your terminal or run 'refreshenv'" -ForegroundColor Blue
    }
    catch {
        Write-Host "[ERROR] Installation failed: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
    finally {
        # Clean up
        if (Test-Path $tempDir) {
            Remove-Item -Path $tempDir -Recurse -Force
        }
    }
}

# Run main function
Main
