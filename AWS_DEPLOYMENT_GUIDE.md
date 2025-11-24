# AWS Deployment Guide - Agentic Customer Support Platform (Lambda + API Gateway)

This guide walks you through deploying the agentic customer support platform to AWS using Lambda and API Gateway with CloudFormation.

## Prerequisites

- AWS account with appropriate permissions
- AWS CLI installed and configured (`aws configure`)
- Python 3.9+
- Pip and virtual environment tools

## Architecture Overview

The deployment consists of:
- **Lambda Function** - Runs the FastAPI application (via Mangum)
- **API Gateway (HTTP API)** - Routes traffic to Lambda
- **DynamoDB Table** - Stores orders with Global Secondary Indexes
- **S3 Bucket** - Stores conversation data
- **CloudWatch Logs** - Application logging
- **IAM Roles** - Lambda execution permissions

## Step 1: Prepare Your Application

### 1.1 Update Dependencies

Add Mangum to your `pyproject.toml`:

```toml
dependencies = [
    # ... existing dependencies
    "mangum>=0.17.0",  # ASGI adapter for AWS Lambda
    "boto3>=1.26.0",
]
```

Install dependencies:

```bash
pip install -e ".[dev]"
```

### 1.2 Create Lambda Handler

Create `lambda_handler.py` in your project root:

```python
# lambda_handler.py
import os
from mangum import Mangum
from main import app

# Set environment variables for Lambda
os.environ.setdefault('ORDER_MANAGER_TYPE', 'dynamodb')
os.environ.setdefault('CONVERSATION_MANAGER_TYPE', 's3')

# Export Mangum handler for Lambda
handler = Mangum(app, lifespan="off")
```

### 1.3 Create Deployment Package Script

Create `scripts/build_lambda_package.sh`:

```bash
#!/bin/bash
set -e

# Create build directory
rm -rf lambda_build
mkdir -p lambda_build

# Install dependencies to build directory
pip install -r requirements.txt -t lambda_build/

# Copy application code
cp -r managers/ lambda_build/
cp -r tools/ lambda_build/
cp -r ports/ lambda_build/
cp -r platform_agents/ lambda_build/
cp -r utils/ lambda_build/
cp lambda_handler.py lambda_build/
cp main.py lambda_build/

# Create deployment package
cd lambda_build
zip -r ../lambda_deployment.zip .
cd ..

echo "Lambda deployment package created: lambda_deployment.zip"
```

Make it executable:

```bash
chmod +x scripts/build_lambda_package.sh
```

### 1.4 Update Environment Configuration

Create `.env.production`:

```bash
# Application
LOG_LEVEL=info

# Order Management
ORDER_MANAGER_TYPE=dynamodb
AWS_REGION=us-east-1
DYNAMODB_TABLE_NAME=orders

# Conversation Management
CONVERSATION_MANAGER_TYPE=s3
S3_BUCKET_NAME=agentic-support-conversations-prod

# Lambda specific
ENVIRONMENT=production
```

## Step 2: Set Up AWS CLI

### 2.1 Configure AWS Credentials

```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Enter default region (e.g., us-east-1)
# Enter default output format (json)
```

### 2.2 Verify Configuration

```bash
aws sts get-caller-identity
# Should return your AWS account info
```

## Step 3: Create CloudFormation Template

Create `cloudformation/stack-template.yaml`:

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Agentic Customer Support Platform on AWS with Lambda and API Gateway'

Parameters:
  EnvironmentName:
    Type: String
    Default: production
    Description: Environment name (dev, staging, production)

  LambdaMemory:
    Type: Number
    Default: 1024
    MinValue: 128
    MaxValue: 10240
    Description: Lambda memory allocation (MB)

  LambdaTimeout:
    Type: Number
    Default: 60
    MinValue: 3
    MaxValue: 900
    Description: Lambda timeout (seconds)

Resources:
  # S3 Bucket for Conversations
  ConversationsBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub 'agentic-support-conversations-${EnvironmentName}-${AWS::AccountId}'
      VersioningConfiguration:
        Status: Enabled
      PublicAccessBlockConfiguration:
        BlockPublicAcls: true
        BlockPublicPolicy: true
        IgnorePublicAcls: true
        RestrictPublicBuckets: true
      LifecycleConfiguration:
        Rules:
          - Id: DeleteOldVersions
            NoncurrentVersionExpirationInDays: 90
          - Id: TransitionToIA
            Transitions:
              - TransitionInDays: 30
                StorageClass: STANDARD_IA
      Tags:
        - Key: Environment
          Value: !Ref EnvironmentName
        - Key: Application
          Value: agentic-customer-support

  # DynamoDB Table for Orders
  OrdersTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: !Sub 'orders-${EnvironmentName}'
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - AttributeName: order_id
          AttributeType: S
        - AttributeName: customer_id
          AttributeType: S
        - AttributeName: customer_name
          AttributeType: S
        - AttributeName: status
          AttributeType: S
        - AttributeName: created_at
          AttributeType: S
      KeySchema:
        - AttributeName: order_id
          KeyType: HASH
      GlobalSecondaryIndexes:
        - IndexName: customer_id_index
          KeySchema:
            - AttributeName: customer_id
              KeyType: HASH
            - AttributeName: created_at
              KeyType: RANGE
          Projection:
            ProjectionType: ALL
        - IndexName: customer_name_index
          KeySchema:
            - AttributeName: customer_name
              KeyType: HASH
            - AttributeName: created_at
              KeyType: RANGE
          Projection:
            ProjectionType: ALL
        - IndexName: status_index
          KeySchema:
            - AttributeName: status
              KeyType: HASH
            - AttributeName: created_at
              KeyType: RANGE
          Projection:
            ProjectionType: ALL
      Tags:
        - Key: Environment
          Value: !Ref EnvironmentName
        - Key: Application
          Value: agentic-customer-support

  # CloudWatch Log Group for Lambda
  LambdaLogGroup:
    Type: AWS::Logs::LogGroup
    Properties:
      LogGroupName: !Sub '/aws/lambda/agentic-support-${EnvironmentName}'
      RetentionInDays: 30

  # IAM Role for Lambda Execution
  LambdaExecutionRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: lambda.amazonaws.com
            Action: 'sts:AssumeRole'
      ManagedPolicyArns:
        - 'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
      Policies:
        - PolicyName: DynamoDBAccess
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - 'dynamodb:GetItem'
                  - 'dynamodb:PutItem'
                  - 'dynamodb:UpdateItem'
                  - 'dynamodb:DeleteItem'
                  - 'dynamodb:Query'
                  - 'dynamodb:Scan'
                Resource:
                  - !GetAtt OrdersTable.Arn
                  - !Sub '${OrdersTable.Arn}/index/*'
        - PolicyName: S3ConversationsAccess
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - 's3:GetObject'
                  - 's3:PutObject'
                  - 's3:DeleteObject'
                  - 's3:ListBucket'
                Resource:
                  - !GetAtt ConversationsBucket.Arn
                  - !Sub '${ConversationsBucket.Arn}/*'

  # Lambda Function
  ApiFunction:
    Type: AWS::Lambda::Function
    Properties:
      FunctionName: !Sub 'agentic-support-${EnvironmentName}'
      Runtime: python3.9
      Handler: lambda_handler.handler
      Role: !GetAtt LambdaExecutionRole.Arn
      Timeout: !Ref LambdaTimeout
      MemorySize: !Ref LambdaMemory
      Code:
        S3Bucket: !Ref LambdaCodeBucket
        S3Key: !Ref LambdaCodeKey
      Environment:
        Variables:
          ORDER_MANAGER_TYPE: dynamodb
          DYNAMODB_TABLE_NAME: !Ref OrdersTable
          CONVERSATION_MANAGER_TYPE: s3
          S3_BUCKET_NAME: !Ref ConversationsBucket
          AWS_REGION: !Ref 'AWS::Region'
          ENVIRONMENT: !Ref EnvironmentName
      LoggingConfig:
        LogGroup: !Ref LambdaLogGroup
      Tags:
        - Key: Environment
          Value: !Ref EnvironmentName

  # Lambda Version (for API Gateway integration)
  ApiFunctionVersion:
    Type: AWS::Lambda::Version
    Properties:
      FunctionName: !Ref ApiFunction
      Description: !Sub 'Version deployed at ${AWS::StackName}'

  # Lambda Permission for API Gateway
  ApiGatewayInvokePermission:
    Type: AWS::Lambda::Permission
    Properties:
      FunctionName: !Ref ApiFunction
      Action: 'lambda:InvokeFunction'
      Principal: apigateway.amazonaws.com
      SourceArn: !Sub 'arn:aws:execute-api:${AWS::Region}:${AWS::AccountId}:${ApiGateway}/*/*'

  # API Gateway (HTTP API)
  ApiGateway:
    Type: AWS::ApiGatewayV2::Api
    Properties:
      Name: !Sub 'agentic-support-${EnvironmentName}'
      ProtocolType: HTTP
      Description: API Gateway for Agentic Customer Support Platform
      CorsConfiguration:
        AllowCredentials: false
        AllowHeaders:
          - '*'
        AllowMethods:
          - GET
          - POST
          - PUT
          - DELETE
          - OPTIONS
        AllowOrigins:
          - '*'
      Tags:
        Environment: !Ref EnvironmentName

  # API Gateway Integration
  ApiIntegration:
    Type: AWS::ApiGatewayV2::Integration
    Properties:
      ApiId: !Ref ApiGateway
      IntegrationType: AWS_PROXY
      IntegrationUri: !Sub
        - 'arn:aws:apigatewayv2:${AWS::Region}::lambda:path/2015-03-31/functions/${LambdaArn}/invocations'
        - LambdaArn: !GetAtt ApiFunction.Arn
      PayloadFormatVersion: '2.0'

  # Default Route (catch all)
  DefaultRoute:
    Type: AWS::ApiGatewayV2::Route
    DependsOn: ApiIntegration
    Properties:
      ApiId: !Ref ApiGateway
      RouteKey: '$default'
      Target: !Sub 'integrations/${ApiIntegration}'

  # API Stage
  ApiStage:
    Type: AWS::ApiGatewayV2::Stage
    Properties:
      ApiId: !Ref ApiGateway
      StageName: !Ref EnvironmentName
      AutoDeploy: true
      AccessLogSettings:
        DestinationArn: !GetAtt ApiLogGroup.Arn
        Format: '{ "requestId":"$context.requestId", "ip": "$context.identity.sourceIp", "requestTime":"$context.requestTime", "httpMethod":"$context.httpMethod", "resourcePath":"$context.resourcePath", "status":"$context.status", "protocol":"$context.protocol", "responseLength":"$context.responseLength" }'
      DefaultRouteSettings:
        ThrottleSettings:
          RateLimit: 2000
          BurstLimit: 4000

  # CloudWatch Log Group for API Gateway
  ApiLogGroup:
    Type: AWS::Logs::LogGroup
    Properties:
      LogGroupName: !Sub '/aws/apigateway/agentic-support-${EnvironmentName}'
      RetentionInDays: 30

  # CloudWatch Alarm for Lambda Errors
  LambdaErrorAlarm:
    Type: AWS::CloudWatch::Alarm
    Properties:
      AlarmName: !Sub 'agentic-support-lambda-errors-${EnvironmentName}'
      AlarmDescription: Alert on Lambda function errors
      MetricName: Errors
      Namespace: AWS/Lambda
      Statistic: Sum
      Period: 300
      EvaluationPeriods: 1
      Threshold: 5
      ComparisonOperator: GreaterThanOrEqualToThreshold
      Dimensions:
        - Name: FunctionName
          Value: !Ref ApiFunction

  # S3 Bucket for Lambda Code
  LambdaCodeBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub 'agentic-support-lambda-code-${EnvironmentName}-${AWS::AccountId}'
      PublicAccessBlockConfiguration:
        BlockPublicAcls: true
        BlockPublicPolicy: true
        IgnorePublicAcls: true
        RestrictPublicBuckets: true
      VersioningConfiguration:
        Status: Enabled
      Tags:
        - Key: Environment
          Value: !Ref EnvironmentName

Outputs:
  ApiEndpoint:
    Description: API Gateway HTTP API Endpoint
    Value: !Sub 'https://${ApiGateway}.execute-api.${AWS::Region}.amazonaws.com/${EnvironmentName}'
    Export:
      Name: !Sub 'agentic-support-api-endpoint-${EnvironmentName}'

  ConversationsBucketName:
    Description: S3 Bucket for Conversations
    Value: !Ref ConversationsBucket
    Export:
      Name: !Sub 'agentic-support-conversations-bucket-${EnvironmentName}'

  OrdersTableName:
    Description: DynamoDB Orders Table Name
    Value: !Ref OrdersTable
    Export:
      Name: !Sub 'agentic-support-orders-table-${EnvironmentName}'

  LambdaFunctionName:
    Description: Lambda Function Name
    Value: !Ref ApiFunction
    Export:
      Name: !Sub 'agentic-support-lambda-${EnvironmentName}'

  LambdaLogGroup:
    Description: CloudWatch Log Group for Lambda
    Value: !Ref LambdaLogGroup
    Export:
      Name: !Sub 'agentic-support-lambda-logs-${EnvironmentName}'

  LambdaCodeBucket:
    Description: S3 Bucket for Lambda Code
    Value: !Ref LambdaCodeBucket
    Export:
      Name: !Sub 'agentic-support-lambda-code-bucket-${EnvironmentName}'
```

## Step 4: Build Lambda Deployment Package

### 4.1 Install Python Dependencies

```bash
pip install -r requirements.txt
pip install mangum boto3
```

### 4.2 Run Build Script

```bash
./scripts/build_lambda_package.sh
```

This creates `lambda_deployment.zip` containing all dependencies and application code.

## Step 5: Upload Code to S3

### 5.1 Create S3 Bucket for Lambda Code

```bash
aws s3 mb s3://agentic-support-lambda-code-production-<YOUR_ACCOUNT_ID>
```

### 5.2 Upload Deployment Package

```bash
aws s3 cp lambda_deployment.zip \
  s3://agentic-support-lambda-code-production-<YOUR_ACCOUNT_ID>/
```

Note the S3 bucket name and key for the next step.

## Step 6: Deploy with CloudFormation

### 6.1 Update Template Parameters

Update the CloudFormation template to reference your Lambda code S3 bucket:

Add these parameters to the template:

```yaml
Parameters:
  LambdaCodeBucket:
    Type: String
    Description: S3 bucket containing Lambda deployment package

  LambdaCodeKey:
    Type: String
    Default: lambda_deployment.zip
    Description: S3 key for Lambda deployment package
```

### 6.2 Create Stack

```bash
aws cloudformation create-stack \
  --stack-name agentic-support-prod \
  --template-body file://cloudformation/stack-template.yaml \
  --parameters \
    ParameterKey=EnvironmentName,ParameterValue=production \
    ParameterKey=LambdaMemory,ParameterValue=1024 \
    ParameterKey=LambdaTimeout,ParameterValue=60 \
    ParameterKey=LambdaCodeBucket,ParameterValue=agentic-support-lambda-code-production-<YOUR_ACCOUNT_ID> \
    ParameterKey=LambdaCodeKey,ParameterValue=lambda_deployment.zip \
  --capabilities CAPABILITY_IAM \
  --region us-east-1
```

### 6.3 Monitor Stack Creation

```bash
# Watch stack creation
aws cloudformation wait stack-create-complete \
  --stack-name agentic-support-prod \
  --region us-east-1

# Check status
aws cloudformation describe-stacks \
  --stack-name agentic-support-prod \
  --region us-east-1 \
  --query 'Stacks[0].StackStatus'
```

### 6.4 Get API Endpoint

```bash
aws cloudformation describe-stacks \
  --stack-name agentic-support-prod \
  --region us-east-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text
```

## Step 7: Verify Deployment

### 7.1 Test API Endpoint

```bash
API_URL=$(aws cloudformation describe-stacks \
  --stack-name agentic-support-prod \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text)

# Test health endpoint
curl $API_URL/health

# Test API
curl -X GET $API_URL/orders
```

### 7.2 Check Lambda Logs

```bash
aws logs tail /aws/lambda/agentic-support-production --follow
```

### 7.3 View API Gateway Logs

```bash
aws logs tail /aws/apigateway/agentic-support-production --follow
```

## Step 8: Update Application (Subsequent Deployments)

### 8.1 Rebuild Lambda Package

```bash
./scripts/build_lambda_package.sh
```

### 8.2 Upload New Package to S3

```bash
aws s3 cp lambda_deployment.zip \
  s3://agentic-support-lambda-code-production-<YOUR_ACCOUNT_ID>/
```

### 8.3 Update Lambda Function

```bash
aws lambda update-function-code \
  --function-name agentic-support-production \
  --s3-bucket agentic-support-lambda-code-production-<YOUR_ACCOUNT_ID> \
  --s3-key lambda_deployment.zip \
  --region us-east-1
```

The API Gateway will automatically use the updated function.

## Step 9: Cleanup (Optional)

### 9.1 Delete CloudFormation Stack

```bash
aws cloudformation delete-stack \
  --stack-name agentic-support-prod \
  --region us-east-1
```

### 9.2 Empty and Delete S3 Buckets

```bash
# Empty Lambda code bucket
aws s3 rm s3://agentic-support-lambda-code-production-<YOUR_ACCOUNT_ID> --recursive

# CloudFormation will delete the conversation bucket when stack is deleted
```

## Troubleshooting

### Lambda Function Errors

Check logs:
```bash
aws logs tail /aws/lambda/agentic-support-production --follow
```

Check function details:
```bash
aws lambda get-function \
  --function-name agentic-support-production \
  --region us-east-1
```

### API Gateway Issues

Test integration:
```bash
aws apigateway test-invoke-method \
  --rest-api-id <API_ID> \
  --resource-id <RESOURCE_ID> \
  --http-method GET \
  --path-with-query-string /health
```

View execution logs:
```bash
aws logs tail /aws/apigateway/agentic-support-production --follow
```

### DynamoDB Errors

Verify table exists:
```bash
aws dynamodb describe-table \
  --table-name orders-production \
  --region us-east-1
```

Check IAM permissions in Lambda execution role.

### S3 Access Issues

Verify bucket exists:
```bash
aws s3 ls s3://agentic-support-conversations-production-<YOUR_ACCOUNT_ID>/
```

Check Lambda role has S3 permissions.

## Performance Considerations

### Lambda Timeout
- Default: 60 seconds
- Adjust based on API response times
- Longer timeout = higher cost per invocation

### Lambda Memory
- Default: 1024 MB
- Higher memory = faster CPU and more network bandwidth
- Auto-scales with memory (128MB to 10GB)

### Cold Starts
- First invocation after period of inactivity takes longer
- Typical cold start: 1-5 seconds
- Consider provisioned concurrency for consistent performance

```bash
# Enable provisioned concurrency
aws lambda put-provisioned-concurrency-config \
  --function-name agentic-support-production \
  --provisioned-concurrent-executions 5 \
  --region us-east-1
```

## Cost Optimization

- Lambda: Pay per invocation + execution time
- API Gateway: $3.50 per million requests
- DynamoDB: On-demand billing (pay per request)
- S3: Pay per GB stored
- CloudWatch Logs: Pay per GB ingested

Enable AWS Cost Explorer to monitor spending.

## Monitoring

### CloudWatch Metrics

```bash
# Lambda invocations
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=agentic-support-production \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 300 \
  --statistics Sum
```

### Set Up Alarms

CloudFormation template includes error alarm. View additional metrics:
```bash
aws cloudwatch list-metrics \
  --namespace AWS/Lambda \
  --dimensions Name=FunctionName,Value=agentic-support-production
```

## Scaling

Lambda and API Gateway auto-scale automatically. No manual scaling needed.

Configure API Gateway throttling in the template (default: 2000 req/sec, 4000 burst).

## Next Steps

1. Add custom domain name using Route53 and API Gateway
2. Add authentication (API Key, OAuth, Cognito)
3. Set up CI/CD with CodePipeline for automated deployments
4. Add WAF (Web Application Firewall) to API Gateway
5. Enable VPC integration if accessing other AWS resources
6. Set up DynamoDB backups and point-in-time recovery
