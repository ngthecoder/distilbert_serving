from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

distillbert_tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased-finetuned-sst-2-english")
distillbert_model = AutoModelForSequenceClassification.from_pretrained("distilbert-base-uncased-finetuned-sst-2-english")

def convert():
    example_input = distillbert_tokenizer("I love my mom and this world is full of love!", return_tensors="pt")

    input_names=["input_ids", "attention_mask"]

    output_names=["logits"]

    dynamic_axes = {
        "input_ids": {1: "sequence_length"},
        "attention_mask": {1: "sequence_length"}
    }

    onnx_program = torch.onnx.export(
        distillbert_model,
        args=(example_input["input_ids"], example_input["attention_mask"]),
        f="./distillbert_model.onnx",
        input_names=input_names,
        output_names=output_names,
        dynamic_axes=dynamic_axes
    )

if __name__ == "__main__":
    convert()
