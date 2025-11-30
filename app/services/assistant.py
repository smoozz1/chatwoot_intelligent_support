import logging
from datetime import datetime, timezone
import httpx

logger = logging.getLogger(__name__)

class Assistant:
    def __init__(self, embedder, qdrant_client, llm_client):
        self.embedder = embedder
        self.qdrant_client = qdrant_client
        self.llm_client = llm_client

    async def handle_message(self, chatwoot_client, conversation_id, message, message_time):
        """Поиск ответов и отправка через Chatwoot"""
        embedding = self.embedder.get_embedding(message)
        logger.info("Вопрос переведен в эмбеддинг")

        answer_variants = await self.qdrant_client.search_embedding(embedding[0])
        logger.info("Поиск эмбеддингов в Qdrant выполнен")

        answers = []
        for i, variant_data in answer_variants.items():
            content = f"""
Точность ответа: {variant_data['score'] * 100:.1f}%
Категория: {variant_data['category']}, {variant_data['subcategory']}
{variant_data['answer']}
            """
            answers.append(content)
        try:
            resp = await self.llm_client.handle_request(message, answers)
            resp.raise_for_status()
            
            llm_answer = resp.json()["choices"][0]["message"]["content"]
        
            await chatwoot_client.send_message(conversation_id, llm_answer, private=False)
            answer_time = (datetime.now(timezone.utc) - message_time).total_seconds()
            logger.info(f"Предоставляю ответ от LLM, время ответа: {answer_time:.2f} сек")
        
        except httpx.ReadTimeout:
            logger.error(f"Запрос к LLM превысил таймаут")
            await chatwoot_client.send_message(
                conversation_id,
                "Произошла ошибка при подготовке ответа. Попробуйте повторить запрос позже.",
                private=False
            )
        
        except httpx.HTTPError as e:
            logger.error(f"HTTP ошибка при обращении к LLM: {str(e)}")
            await chatwoot_client.send_message(
                conversation_id,
                "Произошла ошибка при подготовке ответа. Попробуйте повторить запрос позже.",
                private=False
            )
            
        except Exception as e:
            logger.error(f"Ошибка при обработке ответа LLM или отправке в Chatwoot: {str(e)}")
            await chatwoot_client.send_message(
                conversation_id,
                "Не удалось обработать ответ. Попробуйте повторить запрос позже.",
                private=False
            )