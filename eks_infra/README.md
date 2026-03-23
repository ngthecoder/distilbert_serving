# EKS Infra for DistilBERT Serving
Terraform configuration for provisioning an EKS cluster to serve DistilBERT inference workloads on AWS.

## Architecture
- VPC with public and private subnets across 2 availability zones
- NAT Gateway for outbound internet access from private subnets
- EKS Cluster (Kubernetes 1.31)
- Managed Node Group (t3.medium × 1) deployed in private subnets
- IAM roles for EKS control plane and worker nodes

## Usage
```bash
terraform init
terraform apply
```

## Connecting to the Cluster
```bash
aws eks update-kubeconfig \
  --region us-east-1 \
  --name distilbert-serving-eks-cluster

kubectl get nodes
```

## Cost Warning
This configuration incurs approximately **$4.60/day** in AWS charges (EKS cluster + NAT Gateway + EC2). Always run `terraform destroy` when the cluster is no longer needed.

## Files
| File | Description |
|------|-------------|
| `main.tf` | Provider and Terraform configuration |
| `vpc.tf` | VPC, subnets, NAT Gateway, route tables |
| `eks.tf` | EKS cluster and managed node group |
| `iam.tf` | IAM roles and policy attachments |
| `variables.tf` | Input variables |
| `outputs.tf` | Cluster name, endpoint, and ARN |
