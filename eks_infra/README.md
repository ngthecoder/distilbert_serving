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
# Run this once
terraform init

terraform apply

aws eks update-kubeconfig \
  --region us-east-1 \
  --name distilbert-serving-eks-cluster

aws eks create-access-entry \
  --cluster-name distilbert-serving-eks-cluster \
  --principal-arn $(aws sts get-caller-identity --query Arn --output text) \
  --region us-east-1

aws eks associate-access-policy \
  --cluster-name distilbert-serving-eks-cluster \
  --principal-arn $(aws sts get-caller-identity --query Arn --output text) \
  --policy-arn arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy \
  --access-scope type=cluster \
  --region us-east-1

aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  <account id>.dkr.ecr.us-east-1.amazonaws.com

# Execute the following in the roor directory
docker build -t distilbert-serving .

docker tag distilbert-serving:latest \
  <account id>.dkr.ecr.us-east-1.amazonaws.com/distilbert-serving-ecr-repo:latest

docker push \
  <account id>.dkr.ecr.us-east-1.amazonaws.com/distilbert-serving-ecr-repo:latest

kubectl apply -f k8s/

kubectl get nodes

kubectl get pods

kubectl get service distilbert-service

curl -X POST \
  http://<elb url>.us-east-1.elb.amazonaws.com:8080/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "This movie was absolutely fantastic!"}
```

## Teardown
```bash
# 1. Delete Kubernetes resources first (removes ELB)
kubectl delete -f k8s/

# 2. Destroy infrastructure
terraform destroy
```
Skipping step 1 will cause VPC deletion to fail due to ELB dependency.

## Change in Deployment for AWS
### `deployment.yaml`
Before:
```yaml
image: distilbert_api:latest
imagePullPolicy: Never
```

After:
```yaml
image: <account id>.dkr.ecr.us-east-1.amazonaws.com/distilbert-serving-ecr-repo:latest
imagePullPolicy: Always
```

When developing locally, we wanted the cluster to use the image built locally so we set `Never` for imagePullPolicy and used the image `distilbert_api:latest`. However, when working with AWS, we need to set imagePullPolicy `Always` because we want to use the image from AWS ECR and specified the image on ECR `<account id>.dkr.ecr.us-east-1.amazonaws.com/distilbert-serving-ecr-repo:latest`

### `service.yaml`
Before:
```yaml
type: NodePort
```

After:
```yaml
type: LoadBalancer
```

`NodePort` exposes worker node's IP and port to outside and in local development, we are able to use it in combination with the IP obtained by `minikube ip` command. However, with AWS, nodes could go down and the nodes' IPs are too unstable for production so with the use of `LoadBalancer`, we can tell AWS to create an elastic load balancer (ELB) and this adds additional layer in front of nodes so even if nodes go down and new nodes are assigned new IPs + ports, we can simply hit the ELB's URL which handles traffic for us under the hood.

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
| `ecr.tf` | ECR and ECR policy |
