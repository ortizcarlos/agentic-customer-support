# Deployment Scripts Guide

Two deployment scripts are provided to deploy your agentic customer support platform to AWS:
- `deploy.sh` - Bash script for Linux/macOS/WSL
- `deploy.ps1` - PowerShell script for Windows/PowerShell

## Prerequisites

Both scripts require:
- AWS CLI installed and configured (`aws configure`)
- CloudFormation template at `cloudformation/stack-template.yaml`
- Build script at `scripts/build_lambda_package.sh` or `scripts/build_lambda_package.ps1`

## Bash Script (deploy.sh)

### Usage

```bash
./deploy.sh [environment] [region] [lambda-memory] [lambda-timeout]
```

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| environment | production | Environment name (dev, staging, production) |
| region | us-east-1 | AWS region |
| lambda-memory | 1024 | Lambda memory in MB (128-10240) |
| lambda-timeout | 60 | Lambda timeout in seconds (3-900) |

### Examples

```bash
# Deploy to production (all defaults)
./deploy.sh

# Deploy to staging with custom parameters
./deploy.sh staging us-west-2

# Deploy with custom memory and timeout
./deploy.sh production us-east-1 2048 90

# Deploy to development environment
./deploy.sh dev us-east-1 512 30
```

### What it Does

1. Verifies AWS credentials
2. Creates/checks S3 bucket for Lambda code
3. Builds Lambda deployment package
4. Uploads package to S3
5. Creates or updates CloudFormation stack
6. Displays deployment outputs and helpful commands

### Make Script Executable

```bash
chmod +x deploy.sh
```

## PowerShell Script (deploy.ps1)

### Usage

```powershell
.\deploy.ps1 [-Environment <string>] [-AwsRegion <string>] [-LambdaMemory <int>] [-LambdaTimeout <int>]
```

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| -Environment | production | Environment name (dev, staging, production) |
| -AwsRegion | us-east-1 | AWS region |
| -LambdaMemory | 1024 | Lambda memory in MB (128-10240) |
| -LambdaTimeout | 60 | Lambda timeout in seconds (3-900) |

### Examples

```powershell
# Deploy to production (all defaults)
.\deploy.ps1

# Deploy to staging with custom parameters
.\deploy.ps1 -Environment staging -AwsRegion us-west-2

# Deploy with custom memory and timeout
.\deploy.ps1 -Environment production -AwsRegion us-east-1 -LambdaMemory 2048 -LambdaTimeout 90

# Deploy to development environment
.\deploy.ps1 -Environment dev -LambdaMemory 512 -LambdaTimeout 30
```

### PowerShell Execution Policy

If you get an execution policy error, run:

```powershell
# For current session only
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

# Or permanently for current user
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### What it Does

1. Verifies AWS credentials
2. Creates/checks S3 bucket for Lambda code
3. Builds Lambda deployment package
4. Uploads package to S3
5. Creates or updates CloudFormation stack
6. Displays deployment outputs and helpful commands

## Build Scripts

### Bash Build Script (scripts/build_lambda_package.sh)

Automatically called by `deploy.sh`. Creates a zip file with:
- Python dependencies
- Application code (managers, tools, ports, platform_agents, utils)
- Lambda handler
- Main application file

Output: `lambda_deployment.zip`

### PowerShell Build Script (scripts/build_lambda_package.ps1)

Automatically called by `deploy.ps1`. Creates a zip file with:
- Python dependencies
- Application code (managers, tools, ports, platform_agents, utils)
- Lambda handler
- Main application file

Output: `lambda_deployment.zip`

Can also be run standalone:
```powershell
.\scripts\build_lambda_package.ps1
```

## Common Deployment Scenarios

### Initial Deployment (Production)

**Linux/macOS/WSL:**
```bash
./deploy.sh production us-east-1
```

**Windows/PowerShell:**
```powershell
.\deploy.ps1 -Environment production -AwsRegion us-east-1
```

### Staging Deployment

**Linux/macOS/WSL:**
```bash
./deploy.sh staging us-east-1 1024 60
```

**Windows/PowerShell:**
```powershell
.\deploy.ps1 -Environment staging
```

### Development Deployment (Lower Cost)

**Linux/macOS/WSL:**
```bash
./deploy.sh dev us-east-1 512 30
```

**Windows/PowerShell:**
```powershell
.\deploy.ps1 -Environment dev -LambdaMemory 512 -LambdaTimeout 30
```

### High-Traffic Deployment

**Linux/macOS/WSL:**
```bash
./deploy.sh production us-east-1 3008 120
```

**Windows/PowerShell:**
```powershell
.\deploy.ps1 -Environment production -LambdaMemory 3008 -LambdaTimeout 120
```

## Post-Deployment

After successful deployment, the scripts display:

1. **API Endpoint** - Use this to call your API
2. **Lambda Function Name** - For monitoring and updates
3. **DynamoDB Table Name** - For data inspection
4. **S3 Bucket Name** - For conversation storage

### Test Deployment

```bash
# Get API endpoint (displayed at end of deployment)
API_ENDPOINT=https://xxxxx.execute-api.us-east-1.amazonaws.com/production

# Test health endpoint
curl $API_ENDPOINT/health

# Test API endpoint
curl -X GET $API_ENDPOINT/orders
```

### View Logs

**Lambda Logs:**
```bash
aws logs tail /aws/lambda/agentic-support-production --follow --region us-east-1
```

**API Gateway Logs:**
```bash
aws logs tail /aws/apigateway/agentic-support-production --follow --region us-east-1
```

### Update Deployment

After making code changes:

**Linux/macOS/WSL:**
```bash
# Run the deployment script again (detects existing stack)
./deploy.sh production us-east-1

# OR manually update:
./scripts/build_lambda_package.sh
aws s3 cp lambda_deployment.zip s3://agentic-support-lambda-code-production-YOUR_ACCOUNT_ID/
aws lambda update-function-code \
  --function-name agentic-support-production \
  --s3-bucket agentic-support-lambda-code-production-YOUR_ACCOUNT_ID \
  --s3-key lambda_deployment.zip \
  --region us-east-1
```

**Windows/PowerShell:**
```powershell
# Run the deployment script again (detects existing stack)
.\deploy.ps1 -Environment production

# OR manually update:
.\scripts\build_lambda_package.ps1
aws s3 cp lambda_deployment.zip s3://agentic-support-lambda-code-production-YOUR_ACCOUNT_ID/
aws lambda update-function-code `
  --function-name agentic-support-production `
  --s3-bucket agentic-support-lambda-code-production-YOUR_ACCOUNT_ID `
  --s3-key lambda_deployment.zip `
  --region us-east-1
```

### Delete Deployment

To remove the entire stack:

**Bash:**
```bash
aws cloudformation delete-stack --stack-name agentic-support-production --region us-east-1
```

**PowerShell:**
```powershell
aws cloudformation delete-stack --stack-name agentic-support-production --region us-east-1
```

Then empty and delete the S3 buckets:

```bash
# Empty Lambda code bucket
aws s3 rm s3://agentic-support-lambda-code-production-YOUR_ACCOUNT_ID --recursive

# Empty conversations bucket (CloudFormation will handle deletion)
aws s3 rm s3://agentic-support-conversations-production-YOUR_ACCOUNT_ID --recursive
```

## Troubleshooting

### AWS Credentials Not Found

**Error:** "Error: AWS credentials not configured"

**Solution:** Configure AWS CLI
```bash
aws configure
# Enter:
# - AWS Access Key ID
# - AWS Secret Access Key
# - Default region (e.g., us-east-1)
# - Default output format (json)
```

### S3 Bucket Already Exists

Scripts automatically detect and reuse existing buckets. No action needed.

### Stack Update Failed

Check CloudFormation events:
```bash
aws cloudformation describe-stack-events --stack-name agentic-support-production
```

### Lambda Build Package Failed

**Bash:**
```bash
./scripts/build_lambda_package.sh
```

**PowerShell:**
```powershell
.\scripts\build_lambda_package.ps1
```

Check for missing files or dependencies.

### Lambda Function Errors After Deployment

Check logs:
```bash
aws logs tail /aws/lambda/agentic-support-production --follow
```

### API Gateway Not Responding

Check API Gateway logs:
```bash
aws logs tail /aws/apigateway/agentic-support-production --follow
```

Verify Lambda function:
```bash
aws lambda get-function --function-name agentic-support-production
```

## Environment Variables

Both scripts automatically set these Lambda environment variables:

- `ORDER_MANAGER_TYPE=dynamodb`
- `DYNAMODB_TABLE_NAME=orders-{environment}`
- `CONVERSATION_MANAGER_TYPE=s3`
- `S3_BUCKET_NAME=agentic-support-conversations-{environment}-{account-id}`
- `AWS_REGION={specified-region}`
- `ENVIRONMENT={environment}`

These are configured in the CloudFormation template and passed to the Lambda function.

## Performance Tips

### Lambda Memory

Higher memory = faster CPU and better network performance:
- **512 MB** - Good for low-traffic, dev/test
- **1024 MB** - Balanced, recommended default
- **2048 MB** - High-traffic, faster cold starts
- **3008 MB** - Maximum practical for cost efficiency

### Lambda Timeout

Adjust based on API response times:
- **30 seconds** - For quick APIs
- **60 seconds** - Default, suitable for most cases
- **120+ seconds** - For long-running operations

### Cost Optimization

Use lower settings for development:
```bash
./deploy.sh dev us-east-1 512 30
```

Use higher settings for production if needed:
```bash
./deploy.sh production us-east-1 2048 120
```

## Next Steps

1. Deploy application: `./deploy.sh` or `.\deploy.ps1`
2. Test endpoints with provided API endpoint
3. Monitor with CloudWatch logs
4. Update code and redeploy as needed
5. Set up CI/CD for automated deployments (optional)
