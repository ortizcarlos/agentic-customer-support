# Build Lambda Deployment Package (PowerShell)

param(
    [string]$OutputPath = "lambda_deployment.zip"
)

$ErrorActionPreference = "Stop"

Write-Host "Building Lambda deployment package..."
Write-Host ""

# Check if directories exist
$DirsToCheck = @("managers", "tools", "ports", "platform_agents", "utils")
foreach ($dir in $DirsToCheck) {
    if (-not (Test-Path $dir)) {
        Write-Host "Warning: Directory '$dir' not found, skipping..."
    }
}

# Clean up previous build
if (Test-Path "lambda_build") {
    Write-Host "Cleaning up previous build..."
    try {
        Remove-Item -Path "lambda_build" -Recurse -Force -ErrorAction Stop
    } catch {
        Write-Host "Warning: Could not remove lambda_build, trying alternative method..."
        cmd /c rmdir /s /q lambda_build
    }
}

# Create build directory
Write-Host "Creating build directory..."
New-Item -ItemType Directory -Path "lambda_build" | Out-Null

# Install dependencies to build directory
Write-Host "Installing Python dependencies..."
if (Test-Path "pyproject.toml") {
    uv pip install --target lambda_build/ -e .
} elseif (Test-Path "requirements.txt") {
    uv pip install --target lambda_build/ -r requirements.txt
} else {
    Write-Host "Warning: pyproject.toml or requirements.txt not found"
}

# Copy application code
Write-Host "Copying application code..."
$ItemsToCopy = @(
    "managers",
    "tools",
    "ports",
    "platform_agents",
    "utils",
    "lambda_handler.py",
    "main.py"
)

foreach ($item in $ItemsToCopy) {
    if (Test-Path $item) {
        if ((Get-Item $item).PSIsContainer) {
            Copy-Item -Path $item -Destination "lambda_build/$item" -Recurse -Force
        } else {
            Copy-Item -Path $item -Destination "lambda_build/$item" -Force
        }
    } else {
        Write-Host "Warning: $item not found, skipping..."
    }
}

# Create deployment package
Write-Host "Creating deployment package zip file..."
if (Test-Path $OutputPath) {
    Remove-Item -Path $OutputPath -Force
}

# Try using 7-Zip if available (handles long paths better)
$SevenZipPath = "C:\Program Files\7-Zip\7z.exe"
if (Test-Path $SevenZipPath) {
    Write-Host "Using 7-Zip for better long path support..."
    Push-Location lambda_build
    & $SevenZipPath a -r -tzip "..\$OutputPath" . | Out-Null
    Pop-Location
} else {
    # Fallback: Use PowerShell .NET compression (works around long paths by using relative paths)
    Write-Host "Using .NET compression for zip creation..."
    try {
        Add-Type -AssemblyName System.IO.Compression.FileSystem

        # Create zip from inside lambda_build directory
        $ZipPath = (Get-Item ".").FullName + "\" + $OutputPath

        # Use .NET ZipFile to create archive
        $lambda_build_path = (Get-Item "lambda_build").FullName

        # Create temp list of files and use compression
        Push-Location lambda_build
        $files = Get-ChildItem -Recurse

        # Create new zip file
        $zip = [System.IO.Compression.ZipFile]::Open($ZipPath, "Create")

        foreach ($file in $files) {
            if (-not $file.PSIsContainer) {
                $relativePath = $file.FullName.Substring($lambda_build_path.Length + 1)
                [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip, $file.FullName, $relativePath) | Out-Null
            }
        }

        $zip.Dispose()
        Pop-Location
    } catch {
        Write-Error "Failed to create archive. Please install 7-Zip: https://www.7-zip.org/"
        exit 1
    }
}

# Verify zip was created
if (Test-Path $OutputPath) {
    $ZipSize = (Get-Item $OutputPath).Length / 1MB
    Write-Host ""
    Write-Host "Lambda deployment package created: $OutputPath"
    Write-Host "Package size: $([Math]::Round($ZipSize, 2)) MB"
} else {
    Write-Error "Failed to create Lambda deployment package"
}
