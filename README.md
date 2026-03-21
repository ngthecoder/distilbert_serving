# DistilBERT Serving with Kubernetes
Serving DistilBERT sentiment analysis API with FastAPI, Docker, and Kubernetes.

## Lessons Learned
### Model Pre-download
When using docker compose, we did not need to pre-download the image but the model was downloaded once and cached by Docker. However with Minikube, we had to pre-download the model because we cannot tolerate the pods downloading the model from HuggingFace everytime they go down. The drawback of pre-downloading is that it takes much longer to build the image but it is much more beneficial for the cluster to get the pods working as soon as old ones crash.

### Pod Resource Limiting
The inference takes so much processing power so when we have multiple pods running, we need to limit resources each pod is allowed to use otherwise the machine would run out of resources that crash the whole cluster. To avoid it, for the request resource, I set the 1 Gigabyte of memory & 200 millicore of CPU and for the limit resource, I set the 1 Gigabyte of memory & 500 millicore of CPU. The request resource indicates the guaranteed resources a pod can use and the limit resource dictates the maximum resources.

### Difference between LivenessProbe and ReadinessProbe
LivenessProbe checks if a pod is alive meaning not crashed and ReadinessProbe checks if a pod is ready to serve the application. In the last project ([movie_ticketing](https://github.com/ngthecoder/movie_ticketing)), I used /ping for LivenessProbe and /movies for Readiness because we wanted to check if the database connection is established before labeling the pod as ready. But, I used /ping for both in this project and there are 3 reasons for that. The 1st reason is that pipeline() is executed at the module level in main.py, meaning the model is fully loaded before uvicorn starts accepting any requests. So if /ping responds, the model is guaranteed to be ready. The 2nd reason is that we can only use GET request for LivenessProbe or ReadinessProbe so we cannot even use /analyze for any check. The 3rd reason is that even if we were able to use POST request for readiness, frequent /analyze request (every 15 seconds as defined in `deployment.yaml`) will surely put a strain on the compute resources.

### imagePullPolicy
Without imagePullPolicy: Never in Deployment, Kubernetes tries to pull the image from DockerHub but since we build the image locally, we should set imagePullPolicy to Never to tell Kubernetes the image is built locally.

## Tech Stack
- LLM: DistilBERT
- Backend: Python, FastAPI, uvicorn
- Infrastructure: Kubernetes

## Structure
```
distilbert_serving/
├── k8s/                 # Kubernetes manifests
|    ├── deployment.yaml # Defines deployment
|    └── service.yaml    # Defines service
├── Dockerfile           # Image build
├── main.py              # FastAPI router
└── requirements.txt
```

## Getting Started
### Run with Docker Compose
#### Requirements
- Python 3.12+
- Docker

#### Commands
```bash
docker compose up --build
```

#### Testing
```bash
curl -X POST "http://localhost:8080/analyze" \
  -H "Content-Type: application/json" \
  -d '{"text": "This is absolutely amazing!"}'
```

### Run with Minikube
#### Requirements
- Python 3.12+
- Docker
- Minikube

#### Commands
```bash
minikube start
eval $(minikube docker-env)
docker build -t distilbert_app:latest .
kubectl apply -f k8s/

# Grab the URL and run the test command below
minikube service distilbert-service --url
```

#### Testing
```bash
curl -X GET "http://<copy from the URL>/ping"

curl -X POST "http://<copy from the URL>/analyze" \
  -H "Content-Type: application/json" \
  -d '{"text": "This is absolutely amazing!"}'
```
