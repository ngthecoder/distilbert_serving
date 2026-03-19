from transformers import pipeline
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

app = FastAPI()

distilbert_classifier = pipeline(
    "sentiment-analysis",
    model="distilbert-base-uncased-finetuned-sst-2-english"
)

class AnalyzeRequest(BaseModel):
    text: str

@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    result = distilbert_classifier(req.text)
    return {
        'label': result[0]['label'],
        'score': result[0]['score']
    }

if __name__ == "__main__":
    uvicorn.run('main:app', host='0.0.0.0', port=8080)


curl -X POST "http://localhost:8080/analyze" \
  -H "Content-Type: application/json" \
  -d '{"text": "This is absolutely amazing!"}'