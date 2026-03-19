# DistilBERT Serving with Kubernetes
Serving DistilBERT sentiment analysis API with FastAPI and Docker.

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

### Commands
```bash
docker compose up --build
```

### Teseting
```bash
curl -X POST "http://localhost:8080/analyze" \
  -H "Content-Type: application/json" \
  -d '{"text": "This is absolutely amazing!"}'
```
