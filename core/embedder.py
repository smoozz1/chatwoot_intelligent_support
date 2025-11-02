from transformers import AutoTokenizer, AutoModel
import torch


# Mean Pooling - Take attention mask into account for correct averaging
def mean_pooling(model_output, attention_mask):
    token_embeddings = model_output[0]  # First element of model_output contains all token embeddings
    input_mask_expanded = (attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float())
    return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)


class Embedder:
    def __init__(self, embedding_model='BorisTM/bge-m3_en_ru'):
        # Load model from HuggingFace Hub
        self.tokenizer = AutoTokenizer.from_pretrained(embedding_model)
        self.model = AutoModel.from_pretrained(embedding_model)

    def get_embedding(self, data):
        # Tokenize sentences
        encoded_input = self.tokenizer(data, padding=True, truncation=True, return_tensors="pt")
        # Compute token embeddings
        with torch.no_grad():
            model_output = self.model(**encoded_input)
        # Perform pooling. In this case, mean pooling.
        return mean_pooling(model_output, encoded_input["attention_mask"]).tolist()