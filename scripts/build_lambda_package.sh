#!/bin/bash

set -e

echo "Building Lambda deployment package..."
echo ""

# Check if directories exist
for dir in managers tools ports platform_agents utils; do
    if [ ! -d "$dir" ]; then
        echo "Warning: Directory '$dir' not found, skipping..."
    fi
done

# Clean up previous build
if [ -d "lambda_build" ]; then
    echo "Cleaning up previous build..."
    rm -rf lambda_build
fi

# Create build directory
echo "Creating build directory..."
mkdir -p lambda_build

# Install dependencies to build directory
echo "Installing Python dependencies with UV..."
if [ -f "pyproject.toml" ]; then
    uv pip install --target lambda_build/ -e .
elif [ -f "requirements.txt" ]; then
    uv pip install --target lambda_build/ -r requirements.txt
else
    echo "Warning: pyproject.toml or requirements.txt not found"
fi

# Copy application code
echo "Copying application code..."
for item in managers tools ports platform_agents utils lambda_handler.py main.py; do
    if [ -e "$item" ]; then
        cp -r "$item" lambda_build/
    else
        echo "Warning: $item not found, skipping..."
    fi
done

# Create deployment package
echo "Creating deployment package zip file..."
if [ -f "lambda_deployment.zip" ]; then
    rm lambda_deployment.zip
fi

cd lambda_build
zip -r ../lambda_deployment.zip . -q
cd ..

# Verify zip was created
if [ -f "lambda_deployment.zip" ]; then
    SIZE=$(du -h lambda_deployment.zip | cut -f1)
    echo ""
    echo "Lambda deployment package created: lambda_deployment.zip"
    echo "Package size: $SIZE"
else
    echo "Error: Failed to create Lambda deployment package"
    exit 1
fi
