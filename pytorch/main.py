from transformers import AutoTokenizer, AutoModelForSequenceClassification
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import torch
import torch.nn.functional as F

app = FastAPI()

distillbert_tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased-finetuned-sst-2-english")
distillbert_model = AutoModelForSequenceClassification.from_pretrained("distilbert-base-uncased-finetuned-sst-2-english")

class AnalyzeRequest(BaseModel):
    text: str

@app.get("/ping")
def test():
    return {
        'text': "pong"
    }

@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    input_tensor = distillbert_tokenizer(req.text, return_tensors="pt")

    with torch.no_grad():
        logits = distillbert_model(**input_tensor).logits
    
    predicted_class_id = logits.argmax().item()

    output_label = distillbert_model.config.id2label[predicted_class_id]

    probs = F.softmax(logits, dim=1)

    output_score = probs[0][predicted_class_id].item()

    return {
        'label': output_label,
        'score': output_score
    }

if __name__ == "__main__":
    uvicorn.run('main:app', host='0.0.0.0', port=8080)
