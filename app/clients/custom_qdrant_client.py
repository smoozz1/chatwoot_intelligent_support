from qdrant_client import AsyncQdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse
import itertools
import logging

logger = logging.getLogger(__name__)

TOP_K_ANSWERS = 3
COLLECTION_NAME = 'my_collection'


class Qdrant:
    def __init__(self, host="qdrant", port=6333, api=None, url=None):
        self._id_counter = itertools.count(1)  # генератор для уникальных ID
        self.client = AsyncQdrantClient(host=host, port=port)
        logger.info('AsyncQdrantClient клиент инициализирован')
        self.host = host
        self.port = port
        self.api = api
        self.url = url
        self.answers_number = TOP_K_ANSWERS
        self.collection_name = COLLECTION_NAME

    async def collection_init(self):
        """Создание коллекции, если она ещё не существует"""
        if not await self.client.collection_exists(self.collection_name):
            await self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(size=1024, distance=models.Distance.COSINE),
            )
            logger.info(f'Коллекция {self.collection_name} успешно создана')
            return 'created'
        logger.info(f'Коллекция {self.collection_name} уже существует')
        return 'exists'

    async def load_embeddings(self, data):
        """
        Загружает эмбеддинги в Qdrant.
        data: список словарей с ключами embedding, answer, category, subcategory
        """
        points = [
            models.PointStruct(
                id=next(self._id_counter),
                vector=record['embedding'],
                payload={
                    "answer": record['answer'],
                    "category": record.get('category', ''),
                    "subcategory": record.get('subcategory', '')
                }
            )
            for record in data
        ]

        try:
            await self.client.upsert(collection_name=self.collection_name, points=points)
            logger.info('Эмбеддинги успешно загружены в Qdrant')
        except Exception as e:
            logger.exception('Ошибка при загрузке эмбеддингов: %s', e)

    async def search_embedding(self, embedding, top_k=None):
        """Поиск топ-K похожих эмбеддингов"""
        top_k = top_k or self.answers_number
        result = {}
        try:
            search_results = await self.client.search(
                collection_name=self.collection_name,
                query_vector=embedding,
                with_payload=True,
                limit=top_k
            )
            for i, each in enumerate(search_results, 1):
                result[i] = {
                    'score': each.score,
                    'answer': each.payload.get('answer'),
                    'category': each.payload.get('category'),
                    'subcategory': each.payload.get('subcategory'),
                }
        except Exception as e:
            logger.exception('Ошибка при поиске эмбеддингов: %s', e)

        return result
