# Cloud Computing Concepts

## Service Models

| Model | You Manage | Cloud Manages | Examples |
|-------|-----------|---------------|---------|
| **IaaS** | OS, Runtime, App, Data | Hardware, Network, Virtualization | AWS EC2, Azure VM, GCE |
| **PaaS** | App, Data | Everything else | Heroku, App Engine, Elastic Beanstalk |
| **SaaS** | Nothing | Everything | Gmail, Salesforce, Office 365 |

## Deployment Models

- **Public Cloud** — AWS, Azure, GCP (shared infrastructure)
- **Private Cloud** — On-premises, dedicated
- **Hybrid** — Mix of public and private
- **Multi-cloud** — Multiple cloud providers

## Core Cloud Concepts

**Elasticity** — Scale resources up/down automatically based on demand
**High Availability** — Design for uptime across multiple availability zones
**Fault Tolerance** — System continues operating despite component failures
**Disaster Recovery** — RPO (Recovery Point Objective) & RTO (Recovery Time Objective)

## Pricing Models

| Model | Description | Best For |
|-------|-------------|----------|
| On-Demand | Pay by the hour/second | Unpredictable workloads |
| Reserved | 1-3 year commitment, 60-70% cheaper | Steady-state workloads |
| Spot/Preemptible | Unused capacity, 80-90% cheaper | Fault-tolerant, batch jobs |
| Savings Plans | Flexible commitment | Mixed workloads |
