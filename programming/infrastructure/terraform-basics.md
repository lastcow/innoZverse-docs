# Terraform Basics

Terraform is an Infrastructure as Code (IaC) tool that lets you define cloud resources in declarative configuration files.

## Core Commands

```bash
terraform init          # Initialize (download providers)
terraform plan          # Preview changes
terraform apply         # Apply changes
terraform destroy       # Destroy all resources
terraform fmt           # Format code
terraform validate      # Validate configuration
terraform show          # Show current state
```

## Basic AWS Example

```hcl
# main.tf
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Variables
variable "aws_region" {
  default = "us-east-1"
}

# EC2 Instance
resource "aws_instance" "web" {
  ami           = "ami-0abcdef1234567890"
  instance_type = "t3.micro"

  tags = {
    Name        = "web-server"
    Environment = "production"
  }
}

# S3 Bucket
resource "aws_s3_bucket" "assets" {
  bucket = "my-app-assets-${random_id.suffix.hex}"
}

resource "random_id" "suffix" {
  byte_length = 4
}

# Outputs
output "instance_ip" {
  value = aws_instance.web.public_ip
}
```

## State Management

```bash
# Remote state (recommended)
terraform {
  backend "s3" {
    bucket = "my-terraform-state"
    key    = "prod/terraform.tfstate"
    region = "us-east-1"
  }
}

# State commands
terraform state list        # List resources
terraform state show aws_instance.web
terraform import aws_instance.web i-1234567890  # Import existing resource
```
