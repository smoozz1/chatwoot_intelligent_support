import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import logging
from transformers import AutoTokenizer, AutoModel
import torch

logger = logging.getLogger(__name__)


# Mean Pooling - учитывает attention mask для корректного усреднения
def mean_pooling(model_output, attention_mask):
    token_embeddings = model_output[0]  # Первый элемент содержит все токен-эмбеддинги
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)


class Embedder:
    def __init__(self, embedding_model='BorisTM/bge-m3_en_ru'):
        logger.info("Загрузка модели эмбеддингов: %s", embedding_model)
        self.tokenizer = AutoTokenizer.from_pretrained(embedding_model)
        self.model = AutoModel.from_pretrained(embedding_model)
        logger.info("Модель эмбеддингов загружена и готова к работе")

    def get_embedding(self, data):
        """
        Генерация эмбеддингов для строки или списка строк
        """
        if isinstance(data, str):
            data = [data]

        logger.info("Генерация эмбеддингов для %d объектов", len(data))

        # Токенизация
        encoded_input = self.tokenizer(data, padding=True, truncation=True, return_tensors="pt")

        # Вычисление эмбеддингов
        with torch.no_grad():
            model_output = self.model(**encoded_input)

        embeddings = mean_pooling(model_output, encoded_input["attention_mask"]).tolist()
        logger.info("Эмбеддинги сгенерированы")
        return embeddings
