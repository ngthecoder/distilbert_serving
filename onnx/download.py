from transformers import AutoTokenizer, AutoConfig

def download():
    AutoTokenizer.from_pretrained("distilbert-base-uncased-finetuned-sst-2-english")
    AutoConfig.from_pretrained("distilbert-base-uncased-finetuned-sst-2-english")

if __name__ == "__main__":
    download()
