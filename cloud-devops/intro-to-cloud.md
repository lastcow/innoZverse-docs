# Introduction to Cloud Computing

## The Three Service Models

| Model | You Manage | Provider Manages | Examples |
|-------|-----------|-----------------|---------|
| IaaS | OS, Apps, Data | Hardware, Network | AWS EC2, Azure VM |
| PaaS | Apps, Data | Everything else | Heroku, App Engine |
| SaaS | Nothing | Everything | Gmail, Salesforce |

## Major Cloud Providers

- **AWS** — Market leader, 200+ services
- **Azure** — Best for Microsoft/enterprise
- **GCP** — Best for AI/ML, Kubernetes

## Core AWS Services

```bash
# EC2 — Virtual machines
aws ec2 describe-instances
aws ec2 run-instances --image-id ami-xxx --instance-type t2.micro

# S3 — Object storage
aws s3 ls
aws s3 cp file.txt s3://my-bucket/

# RDS — Managed databases
# Lambda — Serverless functions
# VPC — Virtual networking
```
