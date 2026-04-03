# DistilBERT Serving with Kubernetes

Serving DistilBERT sentiment analysis API with FastAPI, Docker, and Kubernetes on AWS EKS.

## Overview

This project progressively evolves a DistilBERT inference API, each iteration exploring a different aspect of ML infrastructure.

| Directory | Description |
|-----------|-------------|
| `pipeline/` | Original implementation using HuggingFace `pipeline()` |
| `pytorch/` | Custom PyTorch implementation using `AutoTokenizer` + `AutoModelForSequenceClassification` |
| `onnx/` | ONNX Runtime implementation for optimized inference |
| `k8s/` | Kubernetes manifests for each implementation |
| `eks_infra/` | Terraform configuration for AWS EKS infrastructure |
| `load_tests/` | k6 load test scripts |
| `etc/` | Miscellaneous files (notebooks, graphs) |

## Tech Stack

- **Model**: DistilBERT (`distilbert-base-uncased-finetuned-sst-2-english`)
- **Backend**: Python, FastAPI, uvicorn
- **Inference**: PyTorch, ONNX Runtime
- **Infrastructure**: AWS EKS, ECR, Terraform
- **Monitoring**: Prometheus + Grafana (via Helm)
- **Load Testing**: k6

## Iterations

### Local Kubernetes (Minikube)
Initial deployment of DistilBERT sentiment analysis API on local Minikube cluster. Explored pod resource limiting, liveness/readiness probes, and the relationship between CPU limits and response time.

### AWS EKS
Migrated from Minikube to AWS EKS. Set up VPC with public/private subnets, NAT Gateway, ECR, and EKS cluster using Terraform.

### HPA Autoscaling
Compared HPA strategies under various load patterns. Found that warm capacity outperforms threshold tuning for spike workloads, and that HPA cannot react fast enough to absorb the initial peak.

### PyTorch vs ONNX Runtime
Benchmarked custom PyTorch inference against ONNX Runtime with short, medium, and long payloads. ONNX was 3.3x faster on short inputs, 2.1x on medium, and 1.3x on long. Cold-start first request latency dropped 95% (1.88s → 0.10s).

## Infrastructure

### AWS
- Region: `us-east-1`
- VPC CIDR: `10.0.0.0/16`
- 2 public subnets, 2 private subnets

### EKS
- Kubernetes version: `1.35`
- Node instance type: `t3.medium`
- Authentication mode: API

## Getting Started

### Prerequisites
- Terraform
- AWS CLI
- kubectl
- Docker
- Helm
- k6

### 1. Provision Infrastructure

```bash
cd eks_infra
terraform init
terraform apply
```

### 2. Configure kubectl

```bash
aws eks update-kubeconfig \
  --region us-east-1 \
  --name distilbert-serving-eks-cluster
```

### 3. Build and Push Images to ECR

```bash
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# PyTorch
docker build -t distilbert-pytorch:latest ./pytorch
docker tag distilbert-pytorch:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/distilbert-serving-ecr-repo:pytorch
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/distilbert-serving-ecr-repo:pytorch

# ONNX
docker build -t distilbert-onnx:latest ./onnx
docker tag distilbert-onnx:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/distilbert-serving-ecr-repo:onnx
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/distilbert-serving-ecr-repo:onnx
```

### 4. Deploy

```bash
# PyTorch
kubectl apply -f k8s/pytorch/

# ONNX
kubectl apply -f k8s/onnx/
```

### 5. Test

```bash
curl -X POST http://<elb-url>:8080/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "This movie was absolutely fantastic!"}'
```

### 6. Run Load Tests

```bash
k6 run load_tests/load_test_short.js
k6 run load_tests/load_test_medium.js
k6 run load_tests/load_test_long.js
```

## Cleanup

```bash
kubectl delete -f k8s/pytorch/
# or
kubectl delete -f k8s/onnx/

cd eks_infra
terraform destroy
```

> **Note**: Always delete Kubernetes resources before running `terraform destroy` to avoid VPC DependencyViolation errors caused by the LoadBalancer service.