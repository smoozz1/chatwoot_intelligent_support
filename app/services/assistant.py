import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class Assistant:
    def __init__(self, embedder, qdrant_client):
        self.embedder = embedder
        self.qdrant_client = qdrant_client

    async def handle_message(self, chatwoot_client, conversation_id, message, message_time):
        """Поиск ответов и отправка через Chatwoot"""
        embedding = self.embedder.get_embedding(message)
        logger.info("Вопрос переведен в эмбеддинг")

        answer_variants = await self.qdrant_client.search_embedding(embedding[0])
        logger.info("Поиск эмбеддингов в Qdrant выполнен")

        for i, variant_data in answer_variants.items():
            content = f"""
Точность ответа: {variant_data['score'] * 100:.1f}%
Категория: {variant_data['category']}, {variant_data['subcategory']}
{variant_data['answer']}
            """
            try:
                await chatwoot_client.send_message(conversation_id, content)
                answer_time = (datetime.now(timezone.utc) - message_time).total_seconds()
                logger.info(f"Предоставляю {i} ответ, время ответа: {answer_time:.2f} сек")
            except Exception as e:
                logger.error(f"Ошибка при отправке ответа: {e}")