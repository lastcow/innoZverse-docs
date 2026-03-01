# AWS Core Services

## Compute

```bash
# EC2 — Virtual Machines
aws ec2 describe-instances --region us-east-1
aws ec2 run-instances \
  --image-id ami-0abcdef1234567890 \
  --instance-type t3.micro \
  --key-name my-key-pair \
  --security-group-ids sg-12345678

# Lambda — Serverless Functions
aws lambda invoke \
  --function-name my-function \
  --payload '{"key": "value"}' \
  output.json
```

## Storage

```bash
# S3 — Object Storage
aws s3 ls                               # List buckets
aws s3 ls s3://my-bucket/              # List objects
aws s3 cp file.txt s3://my-bucket/     # Upload
aws s3 sync /local/ s3://my-bucket/    # Sync directory
aws s3 presign s3://my-bucket/file.txt --expires-in 3600  # Presigned URL
```

## Databases

| Service | Type | Use Case |
|---------|------|----------|
| RDS | Relational (MySQL, PostgreSQL, etc.) | Traditional apps |
| DynamoDB | NoSQL | High-scale, low-latency |
| ElastiCache | In-memory (Redis/Memcached) | Caching |
| Aurora | Cloud-native relational | High-performance MySQL/PostgreSQL |

## Networking

```bash
# VPC — Virtual Private Cloud
# Create isolated network with public/private subnets

# Key components:
# - VPC: Your private network (e.g., 10.0.0.0/16)
# - Subnets: Subdivisions (public: 10.0.1.0/24, private: 10.0.2.0/24)
# - Internet Gateway: Connect to internet
# - NAT Gateway: Private subnet internet access
# - Security Groups: Instance-level firewall
# - NACLs: Subnet-level firewall
```

## IAM — Identity & Access Management

```bash
# Create user
aws iam create-user --user-name alice

# Attach policy
aws iam attach-user-policy \
  --user-name alice \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess

# Create access keys
aws iam create-access-key --user-name alice
```
