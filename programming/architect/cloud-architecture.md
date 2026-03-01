# Cloud Architecture

## Well-Architected Framework (AWS)

### 6 Pillars

```
1. Operational Excellence    → Automate, monitor, improve
2. Security                  → Defense in depth, least privilege
3. Reliability               → Multi-AZ, auto-recovery, backups
4. Performance Efficiency    → Right-sizing, caching, CDN
5. Cost Optimization         → Reserved instances, spot, right-sizing
6. Sustainability            → Minimize environmental impact
```

## Microservices Architecture

```
                    [API Gateway]
                    /    |    \
            [Auth]  [Orders] [Products]
              |         |        |
           [Users DB] [Orders DB] [Products DB]
              |         |
           [Cache]    [Queue] → [Notifications]
```

### Service Communication

```python
# Synchronous: REST/gRPC
import httpx
response = httpx.get("http://products-service/api/products/123")

# Asynchronous: Message Queue (SQS/RabbitMQ)
import boto3
sqs = boto3.client('sqs')
sqs.send_message(
    QueueUrl='https://sqs.us-east-1.amazonaws.com/123/orders',
    MessageBody='{"order_id": 456, "status": "shipped"}'
)
```

## Serverless Architecture

```python
# AWS Lambda function
import json
import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Orders')

def lambda_handler(event, context):
    order_id = event['pathParameters']['id']

    response = table.get_item(Key={'id': order_id})
    order = response.get('Item')

    if not order:
        return {'statusCode': 404, 'body': json.dumps({'error': 'Not found'})}

    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(order)
    }
```

## Infrastructure as Code — Production Pattern

```hcl
# terraform/environments/prod/main.tf
module "vpc" {
  source = "../../modules/vpc"
  environment = "prod"
  cidr = "10.0.0.0/16"
}

module "eks" {
  source          = "../../modules/eks"
  cluster_name    = "prod-cluster"
  cluster_version = "1.29"
  vpc_id          = module.vpc.vpc_id
  subnet_ids      = module.vpc.private_subnets

  node_groups = {
    general = {
      instance_types = ["m6i.xlarge"]
      min_size       = 3
      max_size       = 20
      desired_size   = 5
    }
    spot = {
      instance_types = ["m6i.xlarge", "m6a.xlarge", "m5.xlarge"]
      capacity_type  = "SPOT"
      min_size       = 0
      max_size       = 50
      desired_size   = 10
    }
  }
}
```
