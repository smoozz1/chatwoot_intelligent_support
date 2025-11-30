import httpx
import asyncio
import json

class LLMmodel:
    def __init__(self, api_key, model):
        self.api_key = api_key
        self.model = model
        
    async def handle_request(self, question, answers):
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "model": f"{self.model}",
            "messages": [
                {
                    "role": "system",
                    "content": "Ты — сотрудник службы поддержки. Твоя задача: отвечать на вопросы пользователей, используя только предоставленные подходящие ответы из базы знаний. \\n\\nАлгоритм действий:\\n1. Оцени, относится ли вопрос к теме базы знаний.\\n2. Проверяй, какой из предоставленных ответов подходит лучше всего.\\n3. Составь ясный, краткий и профессиональный ответ на основе подходящего материала.\\n4. Если вопрос не по теме или данных недостаточно — вежливо уточни у пользователя детали.\\n5. Не придумывай информацию."
                },
                {
                    "role": "user", 
                    "content": f"Вот вопрос: {question}.\nВот наиболее подходящие ответы: {answers}"
                }
            ]
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            return response
