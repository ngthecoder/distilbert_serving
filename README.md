# DistilBERT Serving with Kubernetes
Serving DistilBERT sentiment analysis API with FastAPI, Docker, and Kubernetes.

## Lessons Learned
### Model Pre-download
When using docker compose, we did not need to pre-download the model but the model was downloaded once and cached by Docker. However with Minikube, we had to pre-download the model because we cannot tolerate the pods downloading the model from HuggingFace everytime they go down. The drawback of pre-downloading is that it takes much longer to build the image but it is much more beneficial for the cluster to get the pods working as soon as old ones crash.

### Pod Resource Limiting
The inference takes so much processing power so when we have multiple pods running, we need to limit resources each pod is allowed to use otherwise the machine would run out of resources that crash the whole cluster. To avoid it, for the request resource, I set the 1 Gigabyte of memory & 200 millicore of CPU and for the limit resource, I set the 1 Gigabyte of memory & 500 millicore of CPU. The request resource indicates the guaranteed resources a pod can use and the limit resource dictates the maximum resources.

### Updating Pod Resource Limiting
When the pods are idle meaning just waiting for requests, they use this much resource:
```bash
kubectl top pods

NAME                                     CPU(cores)   MEMORY(bytes)   
distilbert-deployment-6f6cc57777-4kf7k   2m           279Mi           
distilbert-deployment-6f6cc57777-ckqgd   3m           273Mi           
distilbert-deployment-6f6cc57777-nj8ml   2m           375Mi    
```

And I watched how they bump when I make frequent requests against /analyze endpoint.

I ran this command to continuously monitor the resource:
```bash
watch -n 1 kubectl top pods
```

I ran this command to make 20 /analyze requests consecutively:
```bash
for i in {1..20}; do curl -s -X POST "http://127.0.0.1:57001/analyze" -H "Content-Type: application/json" -d '{"text": "This is absolutely amazing!"}' ; done
```

The resource usage at the peak:
```bash
Every 1.0s: kubectl top pods

NAME                                     CPU(cores)   MEMORY(bytes)
distilbert-deployment-6f6cc57777-4kf7k   146m         279Mi
distilbert-deployment-6f6cc57777-ckqgd   295m         276Mi
distilbert-deployment-6f6cc57777-nj8ml   116m         375Mi
```

So when idle, each pod uses about 3 millicore of CPU and 300 Megabytes of memory and at the peak, it uses 295 millicore of CPU and 400 Megabytes of memory. I updated the resource limits in `deployment.yaml` based on this information.

Previous Resource Limit:
```yaml
resources:
    limits:
        memory: "1Gi"
        cpu: "500m"
    requests:
        memory: "1Gi"
        cpu: "200m"
```

Updated Resource Limit:
```yaml
resources:
    limits:
        memory: "500Mi"
        cpu: "500m"
    requests:
        memory: "500Mi"
        cpu: "50m"
```

### Difference between LivenessProbe and ReadinessProbe
LivenessProbe checks if a pod is alive meaning not crashed and ReadinessProbe checks if a pod is ready to serve the application. In the last project ([movie_ticketing](https://github.com/ngthecoder/movie_ticketing)), I used /ping for LivenessProbe and /movies for Readiness because we wanted to check if the database connection is established before labeling the pod as ready. But, I used /ping for both in this project and there are 3 reasons for that. The 1st reason is that pipeline() is executed at the module level in main.py, meaning the model is fully loaded before uvicorn starts accepting any requests. So if /ping responds, the model is guaranteed to be ready. The 2nd reason is that we can only use GET request for LivenessProbe or ReadinessProbe so we cannot even use /analyze for any check. The 3rd reason is that even if we were able to use POST request for readiness, frequent /analyze request (every 15 seconds as defined in `deployment.yaml`) will surely put a strain on the compute resources.

### imagePullPolicy
Without imagePullPolicy: Never in Deployment, Kubernetes tries to pull the image from DockerHub but since we build the image locally, we should set imagePullPolicy to Never to tell Kubernetes the image is built locally.

## Investigating the Relationship between CPU Resource Limit and Response Time
I wanted to know how strong the correlation is between the response time and CPU resource limit so I measured the response time by changing the resource limit and taking the average latency of multiple /analyze responses.

Curl Command with -w (Write-out) flag:
```bash
curl -w "\nOperation lasted: %{time_total} seconds" -X POST "http://127.0.0.1:60579/analyze" \
  -H "Content-Type: application/json" \
  -d '{"text": "This is absolutely amazing!"}'
```

### Trouble in Measuring under 100m Limit
When measuring the response time with the CPU limit of 100m, the pods were taking forever to get ready and sometimes they even fell to Not Ready from Ready. I was not sure why, since it had been working fine with 500m. But after a while, I realized that 100m of CPU limit was insufficient to load the model so the uvicorn server could not start within the Liveness/ReadinessProbe initialDelaySeconds. So in response to this, I adjusted the initialDelaySeconds from 15 seconds to 30 seconds and the pods started working again.

### 3 Replica with 5 Measurements
When resources/limit/cpu = 100m (millicore):
```
1st time: 17.989952 seconds
2nd time: 27.100116 seconds
3rd time: 22.431852 seconds
4th time: 12.798270 seconds
5th time: 19.589428 seconds
Average time: 19.9819236 seconds (python3 -c "times=[17.989952, 27.100116, 22.431852, 12.798270, 19.589428]; average=sum(times)/len(times); print(average)")
```

When resources/limit/cpu = 200m (millicore):
```
1st time: 6.325544 seconds
2nd time: 12.331928 seconds
3rd time: 2.522913 seconds
4th time: 11.090575 seconds
5th time: 2.446036 seconds
Average time: 6.9433992 seconds (python3 -c "times=[6.325544, 12.331928, 2.522913, 11.090575, 2.446036]; average=sum(times)/len(times); print(average)")
```

### 1 Replica with 5 Measurements
I noticed that the time varies significantly among those 5 times and I figured that the requests are load balanced between 3 replicas. For accurate testing, I set replicas:1 and re-tested.

When resources/limit/cpu = 100m (millicore):
```
1st time: 24.158747 seconds
2nd time: 4.755142 seconds
3rd time: 23.202797 seconds
4th time: 6.195886 seconds
5th time: 14.083801 seconds
Average time: 14.4792746 seconds (python3 -c "times=[24.158747, 4.755142, 23.202797, 6.195886, 14.083801]; average=sum(times)/len(times); print(average)")
```

When resources/limit/cpu = 200m (millicore):
```
1st time: 9.677102 seconds
2nd time: 9.325476 seconds
3rd time: 3.554495 seconds
4th time: 1.893006 seconds
5th time: 7.254398 seconds
Average time: 6.3408954 seconds (python3 -c "times=[9.677102, 9.325476, 3.554495, 1.893006, 7.254398]; average=sum(times)/len(times); print(average)")
```

When resources/limit/cpu = 300m (millicore):
```
1st time: 9.050799 seconds
2nd time: 2.586199 seconds
3rd time: 4.502776 seconds
4th time: 0.298613 seconds
5th time: 3.602089 seconds
Average time: 4.0080952 seconds (python3 -c "times=[9.050799, 2.586199, 4.502776, 0.298613, 3.602089]; average=sum(times)/len(times); print(average)")
```

When resources/limit/cpu = 400m (millicore):
```
1st time: 7.934045 seconds
2nd time: 7.821140 seconds
3rd time: 0.679779 seconds
4th time: 0.893427 seconds
5th time: 7.957631 seconds
Average time: 5.0572044 seconds (python3 -c "times=[7.934045, 7.821140, 0.679779, 0.893427, 7.957631]; average=sum(times)/len(times); print(average)")
```

When resources/limit/cpu = 500m (millicore):
```
1st time: 6.301705 seconds
2nd time: 0.284281 seconds
3rd time: 0.496677 seconds
4th time: 1.929600 seconds
5th time: 0.896461 seconds
Average time: 1.9817448 seconds (python3 -c "times=[6.301705, 0.284281, 0.496677, 1.929600, 0.896461]; average=sum(times)/len(times); print(average)")
```

### 1 Replica with 10 Measurements for 300m and 400m
The average time shows decreasing trend as I increased the limit but there is anomaly between CPU=300m and 400m. So I decided to take time 10 times instead of 5 for those two limits.

When resources/limit/cpu = 300m (millicore):
```
1st time: 6.895056 seconds
2nd time: 0.700627 seconds
3rd time: 2.877908 seconds
4th time: 3.571861 seconds
5th time: 0.866828 seconds
6th time: 1.671221 seconds
7th time: 4.475670 seconds
8th time: 1.956510 seconds
9th time: 2.258433 seconds
10th time: 1.815006 seconds
Average time: 2.708912 seconds (python3 -c "times=[6.895056, 0.700627, 2.877908, 3.571861, 0.866828, 1.671221, 4.475670, 1.956510, 2.258433, 1.815006]; average=sum(times)/len(times); print(average)")
```

When resources/limit/cpu = 400m (millicore):
```
1st time: 4.150546 seconds
2nd time: 1.329997 seconds
3rd time: 0.866239 seconds
4th time: 2.788253 seconds
5th time: 0.975224 seconds
6th time: 5.406327 seconds
7th time: 1.453371 seconds
8th time: 3.187058 seconds
9th time: 3.119381 seconds
10th time: 0.764513 seconds
Average time: 2.4040909 seconds (python3 -c "times=[4.150546, 1.329997, 0.866239, 2.788253, 0.975224, 5.406327, 1.453371, 3.187058, 3.119381, 0.764513]; average=sum(times)/len(times); print(average)")
```

### Results Table and Conclusion
| CPU Limit (Millicore) | Response Time (Seconds) |
| --------------------- | ----------------------- |
| 100 | 14.4792746 |
| 200 | 6.3408954 |
| 300 | 2.708912 |
| 400 | 2.4040909 |
| 500 | 1.9817448 |

\* For 300 and 400 Millicore, I used the average of 10 measurements while for others, I used the average of 5.

In conclusion, we can say that as the limit increases, the response time shortens. However, between 300m and 500m, the rate of change becomes smaller. 

Before explaining why the rate of change got small, we need to know about CPU throttling. With full access to CPU, a process can use CPU core for the full cycle (100 milliseconds) but with 300 millicore limit, the process can only use CPU core for 30 milliseconds and it needs to wait doing nothing for 70 milliseconds. So if the process with 300 millicore limit wants to do the same thing as it did with no limit, it requires 4 cycles (30ms of working & 70ms of waiting -> 30ms of working & 70ms of waiting -> 30ms of working & 70ms of waiting -> 10ms of working).

Once the CPU limit is high enough to complete the inference in a single or similar number of cycles, the bottleneck shifts from CPU throttling to the model's own computation time. That's why the gains become smaller beyond 300m.

## Tech Stack
- Model: DistilBERT
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
curl -X GET "http://localhost:8080/ping"

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