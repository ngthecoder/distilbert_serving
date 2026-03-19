# DistilBERT Serving with Kubernetes

## Tech Stack
- LLM: DistilBERT
- Backend: Python, FastAPI, uvicorn
- Infrastructure: Kubernetes

## Structure
```
distilbert_serving/
├── k8s/                 # Kubernetes manifests
├── Dockerfile           # Multi-stage build
├── main.py              # FastAPI router
└── requirements.txt
```

## Getting Started
### Requirements
- Python 3.12+
- Docker
- Minikube

## Commands
```bash
docker built -t distilbert_serving .
docker run distilbert_serving
```
