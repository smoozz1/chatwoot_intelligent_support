import requests
from .custom_qdrant_client import Qdrant
from core.embedder import Embedder

class Chatwoot:
    def __init__(self, admin_id: int | str, api_key: str):
        self.api_key = api_key
        self.admin_id = admin_id
        try:
            url = f"https://app.chatwoot.com/api/v1/accounts/{admin_id}"
            headers = {"api_access_token": self.api_key}
            response = requests.get(url, headers=headers)
            print('Chatwoot клиент инициализирован')
        except Exception as e:
            print('Ошибка при инициализации клиента Chatwoot:\n', e)
        
        # try:
        #     url = f"https://app.chatwoot.com/api/v1/accounts/{admin_id}/webhooks"
        #     payload = {
        #         "url": "{lt_url}/webhook",
        #         "subscriptions": ["message_created"]
        #     }
        #     headers = {
        #         "api_access_token": api_key,
        #         "Content-Type": "application/json"
        #     }
        #     response = requests.post(url, json=payload, headers=headers)
        #     print('Вебхук создан')
    
    def get_assist(self, conversation_id, message, qdrant_client, embedder):
        embedding = embedder.get_embedding(message)
        answer_variants = qdrant_client.search_embedding(embedding[0])
        url = f"https://app.chatwoot.com/api/v1/accounts/{self.admin_id}/conversations/{conversation_id}/messages"
        for variant in answer_variants:
            cur = answer_variants[variant]
            payload = {
                "content": f'''
Точность ответа: {cur['score'] * 100:.1f}% 
Категория: {cur['category']}, {cur['subcategory']}
{cur['answer']}
                ''',
                "message_type": "outgoing",
                "private": True,
                "content_type": "text",
            }
            headers = {
                "api_access_token": f"{self.api_key}",
                "Content-Type": "application/json"
            }
            response = requests.post(url, json=payload, headers=headers)