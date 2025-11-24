#!/bin/bash

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="agentic-support"
ENVIRONMENT="${1:-production}"
AWS_REGION="${2:-us-east-1}"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
LAMBDA_MEMORY="${3:-1024}"
LAMBDA_TIMEOUT="${4:-60}"

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}Agentic Customer Support Platform - AWS Deploy${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""
echo -e "${YELLOW}Configuration:${NC}"
echo "  Environment: $ENVIRONMENT"
echo "  AWS Region: $AWS_REGION"
echo "  AWS Account ID: $AWS_ACCOUNT_ID"
echo "  Lambda Memory: $LAMBDA_MEMORY MB"
echo "  Lambda Timeout: $LAMBDA_TIMEOUT seconds"
echo ""

# Step 1: Verify AWS credentials
echo -e "${BLUE}Step 1: Verifying AWS credentials...${NC}"
if ! aws sts get-caller-identity &>/dev/null; then
    echo -e "${RED}Error: AWS credentials not configured${NC}"
    echo "Run: aws configure"
    exit 1
fi
echo -e "${GREEN}✓ AWS credentials verified${NC}"
echo ""

# Step 2: Create S3 bucket for Lambda code if it doesn't exist
LAMBDA_CODE_BUCKET="${PROJECT_NAME}-lambda-code-${ENVIRONMENT}-${AWS_ACCOUNT_ID}"
echo -e "${BLUE}Step 2: Setting up S3 bucket for Lambda code...${NC}"
if aws s3 ls "s3://${LAMBDA_CODE_BUCKET}" 2>&1 | grep -q 'NoSuchBucket'; then
    echo "Creating S3 bucket: $LAMBDA_CODE_BUCKET"
    aws s3 mb "s3://${LAMBDA_CODE_BUCKET}" --region "$AWS_REGION"
    echo -e "${GREEN}✓ S3 bucket created${NC}"
else
    echo -e "${GREEN}✓ S3 bucket already exists${NC}"
fi
echo ""

# Step 3: Build Lambda deployment package
echo -e "${BLUE}Step 3: Building Lambda deployment package...${NC}"
if [ ! -f "scripts/build_lambda_package.sh" ]; then
    echo -e "${RED}Error: scripts/build_lambda_package.sh not found${NC}"
    exit 1
fi

chmod +x scripts/build_lambda_package.sh
./scripts/build_lambda_package.sh

if [ ! -f "lambda_deployment.zip" ]; then
    echo -e "${RED}Error: lambda_deployment.zip not created${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Lambda package built successfully${NC}"
echo ""

# Step 4: Upload deployment package to S3
echo -e "${BLUE}Step 4: Uploading deployment package to S3...${NC}"
aws s3 cp lambda_deployment.zip "s3://${LAMBDA_CODE_BUCKET}/lambda_deployment.zip" \
    --region "$AWS_REGION"
echo -e "${GREEN}✓ Deployment package uploaded${NC}"
echo ""

# Step 5: Create CloudFormation stack
echo -e "${BLUE}Step 5: Creating/Updating CloudFormation stack...${NC}"
STACK_NAME="${PROJECT_NAME}-${ENVIRONMENT}"

# Check if stack exists
if aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" &>/dev/null; then

    echo "Stack exists, updating..."
    CHANGE_SET_NAME="${PROJECT_NAME}-changeset-$(date +%s)"

    aws cloudformation create-change-set \
        --stack-name "$STACK_NAME" \
        --change-set-name "$CHANGE_SET_NAME" \
        --template-body file://cloudformation/stack-template.yaml \
        --parameters \
            ParameterKey=EnvironmentName,ParameterValue="$ENVIRONMENT" \
            ParameterKey=LambdaMemory,ParameterValue="$LAMBDA_MEMORY" \
            ParameterKey=LambdaTimeout,ParameterValue="$LAMBDA_TIMEOUT" \
            ParameterKey=LambdaCodeBucket,ParameterValue="$LAMBDA_CODE_BUCKET" \
            ParameterKey=LambdaCodeKey,ParameterValue="lambda_deployment.zip" \
        --capabilities CAPABILITY_IAM \
        --region "$AWS_REGION"

    echo "Waiting for change set to be created..."
    sleep 10

    # Check if change set has changes
    CHANGES=$(aws cloudformation describe-change-set \
        --stack-name "$STACK_NAME" \
        --change-set-name "$CHANGE_SET_NAME" \
        --region "$AWS_REGION" \
        --query 'Changes' \
        --output text)

    if [ -z "$CHANGES" ]; then
        echo -e "${YELLOW}No changes detected, deleting change set${NC}"
        aws cloudformation delete-change-set \
            --stack-name "$STACK_NAME" \
            --change-set-name "$CHANGE_SET_NAME" \
            --region "$AWS_REGION"
    else
        echo "Executing change set..."
        aws cloudformation execute-change-set \
            --stack-name "$STACK_NAME" \
            --change-set-name "$CHANGE_SET_NAME" \
            --region "$AWS_REGION"

        echo "Waiting for stack update to complete..."
        aws cloudformation wait stack-update-complete \
            --stack-name "$STACK_NAME" \
            --region "$AWS_REGION"
        echo -e "${GREEN}✓ Stack updated successfully${NC}"
    fi
else
    echo "Creating new stack..."
    aws cloudformation create-stack \
        --stack-name "$STACK_NAME" \
        --template-body file://cloudformation/stack-template.yaml \
        --parameters \
            ParameterKey=EnvironmentName,ParameterValue="$ENVIRONMENT" \
            ParameterKey=LambdaMemory,ParameterValue="$LAMBDA_MEMORY" \
            ParameterKey=LambdaTimeout,ParameterValue="$LAMBDA_TIMEOUT" \
            ParameterKey=LambdaCodeBucket,ParameterValue="$LAMBDA_CODE_BUCKET" \
            ParameterKey=LambdaCodeKey,ParameterValue="lambda_deployment.zip" \
        --capabilities CAPABILITY_IAM \
        --region "$AWS_REGION"

    echo "Waiting for stack creation to complete..."
    aws cloudformation wait stack-create-complete \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION"
    echo -e "${GREEN}✓ Stack created successfully${NC}"
fi
echo ""

# Step 6: Get stack outputs
echo -e "${BLUE}Step 6: Retrieving stack outputs...${NC}"
OUTPUTS=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --query 'Stacks[0].Outputs')

API_ENDPOINT=$(echo "$OUTPUTS" | jq -r '.[] | select(.OutputKey=="ApiEndpoint") | .OutputValue')
LAMBDA_FUNCTION=$(echo "$OUTPUTS" | jq -r '.[] | select(.OutputKey=="LambdaFunctionName") | .OutputValue')
ORDERS_TABLE=$(echo "$OUTPUTS" | jq -r '.[] | select(.OutputKey=="OrdersTableName") | .OutputValue')
CONVERSATIONS_BUCKET=$(echo "$OUTPUTS" | jq -r '.[] | select(.OutputKey=="ConversationsBucketName") | .OutputValue')

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}Deployment Successful!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "${YELLOW}Stack Information:${NC}"
echo "  Stack Name: $STACK_NAME"
echo "  Region: $AWS_REGION"
echo ""
echo -e "${YELLOW}Deployed Resources:${NC}"
echo "  API Endpoint: $API_ENDPOINT"
echo "  Lambda Function: $LAMBDA_FUNCTION"
echo "  Orders Table: $ORDERS_TABLE"
echo "  Conversations Bucket: $CONVERSATIONS_BUCKET"
echo ""
echo -e "${YELLOW}Quick Commands:${NC}"
echo ""
echo "Test API health:"
echo "  curl $API_ENDPOINT/health"
echo ""
echo "View Lambda logs:"
echo "  aws logs tail /aws/lambda/${LAMBDA_FUNCTION} --follow --region $AWS_REGION"
echo ""
echo "View API Gateway logs:"
echo "  aws logs tail /aws/apigateway/${PROJECT_NAME}-${ENVIRONMENT} --follow --region $AWS_REGION"
echo ""
echo "Update Lambda function:"
echo "  ./scripts/build_lambda_package.sh"
echo "  aws s3 cp lambda_deployment.zip s3://${LAMBDA_CODE_BUCKET}/"
echo "  aws lambda update-function-code --function-name ${LAMBDA_FUNCTION} --s3-bucket ${LAMBDA_CODE_BUCKET} --s3-key lambda_deployment.zip --region ${AWS_REGION}"
echo ""
echo "Delete stack:"
echo "  aws cloudformation delete-stack --stack-name ${STACK_NAME} --region ${AWS_REGION}"
echo ""
