# Azure Fundamentals

## Core Services vs AWS

| Category | AWS | Azure |
|----------|-----|-------|
| Compute | EC2 | Virtual Machines |
| Serverless | Lambda | Azure Functions |
| Containers | ECS/EKS | AKS |
| Object Storage | S3 | Blob Storage |
| Database | RDS | Azure SQL Database |
| CDN | CloudFront | Azure CDN |
| DNS | Route 53 | Azure DNS |

## Azure CLI

```bash
# Login
az login

# List resources
az group list
az vm list --output table

# Create resource group
az group create --name myResourceGroup --location eastus

# Create VM
az vm create \
  --resource-group myResourceGroup \
  --name myVM \
  --image Ubuntu2204 \
  --admin-username azureuser \
  --generate-ssh-keys

# Azure Blob Storage
az storage blob upload \
  --account-name mystorageaccount \
  --container-name mycontainer \
  --name myfile.txt \
  --file ./myfile.txt
```
