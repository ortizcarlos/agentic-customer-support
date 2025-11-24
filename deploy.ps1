# Agentic Customer Support Platform - AWS Deploy Script (PowerShell)

param(
    [string]$Environment = "production",
    [string]$AwsRegion = "us-east-1",
    [int]$LambdaMemory = 1024,
    [int]$LambdaTimeout = 60
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Color codes
$Blue = "`e[34m"
$Green = "`e[32m"
$Yellow = "`e[33m"
$Red = "`e[31m"
$NC = "`e[0m"

# Configuration
$ProjectName = "agentic-support"
$StackName = "$ProjectName-$Environment"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "$Blue$Message$NC" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "$Green✓ $Message$NC" -ForegroundColor Green
}

function Write-Error {
    param([string]$Message)
    Write-Host "$Red✗ Error: $Message$NC" -ForegroundColor Red
    exit 1
}

function Write-Info {
    param([string]$Message)
    Write-Host "  $Message"
}

# Main script
Write-Host ""
Write-Host "$Blue============================================$NC" -ForegroundColor Cyan
Write-Host "$Blue Agentic Customer Support Platform - AWS Deploy$NC" -ForegroundColor Cyan
Write-Host "$Blue============================================$NC" -ForegroundColor Cyan
Write-Host ""

# Display configuration
Write-Host "$Yellow Configuration:$NC" -ForegroundColor Yellow
Write-Info "Environment: $Environment"
Write-Info "AWS Region: $AwsRegion"
Write-Info "Lambda Memory: $LambdaMemory MB"
Write-Info "Lambda Timeout: $LambdaTimeout seconds"
Write-Host ""

# Step 1: Verify AWS credentials
Write-Step "Step 1: Verifying AWS credentials..."
try {
    $CallerIdentity = aws sts get-caller-identity --region $AwsRegion | ConvertFrom-Json
    $AwsAccountId = $CallerIdentity.Account
    Write-Success "AWS credentials verified"
    Write-Info "Account ID: $AwsAccountId"
} catch {
    Write-Error "AWS credentials not configured or invalid. Run: aws configure"
}
Write-Host ""

# Step 2: Create S3 bucket for Lambda code if it doesn't exist
Write-Step "Step 2: Setting up S3 bucket for Lambda code..."
$LambdaCodeBucket = "$ProjectName-lambda-code-$Environment-$AwsAccountId"

try {
    $BucketExists = aws s3api head-bucket --bucket $LambdaCodeBucket --region $AwsRegion 2>$null
    Write-Success "S3 bucket already exists: $LambdaCodeBucket"
} catch {
    Write-Info "Creating S3 bucket: $LambdaCodeBucket"
    aws s3 mb "s3://$LambdaCodeBucket" --region $AwsRegion
    Write-Success "S3 bucket created"
}
Write-Host ""

# Step 3: Build Lambda deployment package
Write-Step "Step 3: Building Lambda deployment package..."

$BuildScript = "scripts\build_lambda_package.ps1"
if (-not (Test-Path $BuildScript)) {
    Write-Error "$BuildScript not found"
}

# Check if build script exists (bash version)
$BashBuildScript = "scripts/build_lambda_package.sh"
if (-not (Test-Path $BashBuildScript)) {
    Write-Error "$BashBuildScript not found"
}

# Run the build script (either PowerShell or Bash version)
if (Test-Path $BuildScript) {
    & $BuildScript
} else {
    # If only bash version exists, try to run it
    if ($IsLinux -or $IsMacOS) {
        bash $BashBuildScript
    } else {
        # On Windows, we need to use bash through WSL or Git Bash
        Write-Info "Running build script with bash..."
        bash $BashBuildScript
    }
}

if (-not (Test-Path "lambda_deployment.zip")) {
    Write-Error "lambda_deployment.zip not created"
}

Write-Success "Lambda package built successfully"
Write-Host ""

# Step 4: Upload deployment package to S3
Write-Step "Step 4: Uploading deployment package to S3..."
try {
    aws s3 cp lambda_deployment.zip "s3://$LambdaCodeBucket/lambda_deployment.zip" --region $AwsRegion
    Write-Success "Deployment package uploaded"
} catch {
    Write-Error "Failed to upload deployment package: $_"
}
Write-Host ""

# Step 5: Create CloudFormation stack
Write-Step "Step 5: Creating/Updating CloudFormation stack..."

try {
    # Check if stack exists
    $StackStatus = aws cloudformation describe-stacks --stack-name $StackName --region $AwsRegion 2>$null

    if ($StackStatus) {
        Write-Info "Stack exists, updating..."
        $ChangeSetName = "$ProjectName-changeset-$(Get-Random -Maximum 999999)"

        aws cloudformation create-change-set `
            --stack-name $StackName `
            --change-set-name $ChangeSetName `
            --template-body file://cloudformation/stack-template.yaml `
            --parameters `
                ParameterKey=EnvironmentName,ParameterValue=$Environment `
                ParameterKey=LambdaMemory,ParameterValue=$LambdaMemory `
                ParameterKey=LambdaTimeout,ParameterValue=$LambdaTimeout `
                ParameterKey=LambdaCodeBucket,ParameterValue=$LambdaCodeBucket `
                ParameterKey=LambdaCodeKey,ParameterValue="lambda_deployment.zip" `
            --capabilities CAPABILITY_IAM `
            --region $AwsRegion

        Write-Info "Waiting for change set to be created..."
        Start-Sleep -Seconds 10

        # Check if change set has changes
        $ChangeSetInfo = aws cloudformation describe-change-set `
            --stack-name $StackName `
            --change-set-name $ChangeSetName `
            --region $AwsRegion | ConvertFrom-Json

        if ($ChangeSetInfo.Changes.Count -eq 0) {
            Write-Host "$Yellow No changes detected, deleting change set$NC" -ForegroundColor Yellow
            aws cloudformation delete-change-set `
                --stack-name $StackName `
                --change-set-name $ChangeSetName `
                --region $AwsRegion
        } else {
            Write-Info "Executing change set..."
            aws cloudformation execute-change-set `
                --stack-name $StackName `
                --change-set-name $ChangeSetName `
                --region $AwsRegion

            Write-Info "Waiting for stack update to complete..."
            aws cloudformation wait stack-update-complete `
                --stack-name $StackName `
                --region $AwsRegion
            Write-Success "Stack updated successfully"
        }
    } else {
        throw "Stack does not exist (will be created)"
    }
} catch {
    # Stack doesn't exist, create it
    Write-Info "Creating new stack..."
    aws cloudformation create-stack `
        --stack-name $StackName `
        --template-body file://cloudformation/stack-template.yaml `
        --parameters `
            ParameterKey=EnvironmentName,ParameterValue=$Environment `
            ParameterKey=LambdaMemory,ParameterValue=$LambdaMemory `
            ParameterKey=LambdaTimeout,ParameterValue=$LambdaTimeout `
            ParameterKey=LambdaCodeBucket,ParameterValue=$LambdaCodeBucket `
            ParameterKey=LambdaCodeKey,ParameterValue="lambda_deployment.zip" `
        --capabilities CAPABILITY_IAM `
        --region $AwsRegion

    Write-Info "Waiting for stack creation to complete..."
    aws cloudformation wait stack-create-complete `
        --stack-name $StackName `
        --region $AwsRegion
    Write-Success "Stack created successfully"
}
Write-Host ""

# Step 6: Get stack outputs
Write-Step "Step 6: Retrieving stack outputs..."

$StackOutputs = aws cloudformation describe-stacks `
    --stack-name $StackName `
    --region $AwsRegion | ConvertFrom-Json

$Outputs = $StackOutputs.Stacks[0].Outputs

$ApiEndpoint = ($Outputs | Where-Object { $_.OutputKey -eq "ApiEndpoint" }).OutputValue
$LambdaFunction = ($Outputs | Where-Object { $_.OutputKey -eq "LambdaFunctionName" }).OutputValue
$OrdersTable = ($Outputs | Where-Object { $_.OutputKey -eq "OrdersTableName" }).OutputValue
$ConversationsBucket = ($Outputs | Where-Object { $_.OutputKey -eq "ConversationsBucketName" }).OutputValue

Write-Host ""
Write-Host "$Green============================================$NC" -ForegroundColor Green
Write-Host "$Green Deployment Successful!$NC" -ForegroundColor Green
Write-Host "$Green============================================$NC" -ForegroundColor Green
Write-Host ""

Write-Host "$Yellow Stack Information:$NC" -ForegroundColor Yellow
Write-Info "Stack Name: $StackName"
Write-Info "Region: $AwsRegion"
Write-Host ""

Write-Host "$Yellow Deployed Resources:$NC" -ForegroundColor Yellow
Write-Info "API Endpoint: $ApiEndpoint"
Write-Info "Lambda Function: $LambdaFunction"
Write-Info "Orders Table: $OrdersTable"
Write-Info "Conversations Bucket: $ConversationsBucket"
Write-Host ""

Write-Host "$Yellow Quick Commands:$NC" -ForegroundColor Yellow
Write-Host ""
Write-Info "Test API health:"
Write-Info "  curl $ApiEndpoint/health"
Write-Host ""

Write-Info "View Lambda logs:"
Write-Info "  aws logs tail /aws/lambda/$LambdaFunction --follow --region $AwsRegion"
Write-Host ""

Write-Info "View API Gateway logs:"
Write-Info "  aws logs tail /aws/apigateway/$ProjectName-$Environment --follow --region $AwsRegion"
Write-Host ""

Write-Info "Update Lambda function:"
Write-Info "  ./scripts/build_lambda_package.ps1"
Write-Info "  aws s3 cp lambda_deployment.zip s3://$LambdaCodeBucket/"
Write-Info "  aws lambda update-function-code --function-name $LambdaFunction --s3-bucket $LambdaCodeBucket --s3-key lambda_deployment.zip --region $AwsRegion"
Write-Host ""

Write-Info "Delete stack:"
Write-Info "  aws cloudformation delete-stack --stack-name $StackName --region $AwsRegion"
Write-Host ""
