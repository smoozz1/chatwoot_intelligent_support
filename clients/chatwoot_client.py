import requests
import subprocess
import re
from datetime import datetime, timezone


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
        self.add_webhook()


    def add_webhook(self):
        try:
            public_url = self.get_public_url()
            self.webhook_url = f'{public_url}/webhook'
            
            url = f"https://app.chatwoot.com/api/v1/accounts/{self.admin_id}/webhooks"
            payload = {
                "url": self.webhook_url,
                "subscriptions": ["message_created"]
            }
            headers = {
                "api_access_token": self.api_key,
                "Content-Type": "application/json"
            }
            response = requests.post(url, json=payload, headers=headers)
            self.webhook_id = response.json()['payload']['webhook']['id']
            print(f'Вебхук {self.webhook_id} создан')
        except Exception as e:
            print(f'Ошибка при создании вебхука: {e}')
            
            
    def delete_webhook(self):
        url = f"https://app.chatwoot.com/api/v1/accounts/{self.admin_id}/webhooks/{self.webhook_id}"
        headers = {"api_access_token": self.api_key}
        try:
            response = requests.delete(url, headers=headers)
            print(f'Вебхук {self.webhook_url} удален')
        except Exception as e:
            print(f'Не удалось удалить вебхук {self.webhook_url}:\n{e}')
    
    
    def get_public_url(self):
        process = subprocess.Popen(
            ["lt", "--port", "8000"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        for line in process.stdout:
            match = re.search(r'https://[a-zA-Z0-9.-]+\.loca\.lt', line)
            if match:
                self.public_url = match.group(0)
                print("Публичный URL:", self.public_url)
                break
        return self.public_url
    
    
    async def get_assist(self, conversation_id, message, qdrant_client, embedder, message_time):
        embedding = embedder.get_embedding(message)
        print('Вопрос переведен в эмбеддинг')
        answer_variants = await qdrant_client.search_embedding(embedding[0])
        print('Поиск эмбеддингов в qdrant выполнен')
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
            try:
                request = requests.post(url, json=payload, headers=headers)
                utc_now = datetime.now(timezone.utc)
                answer_time = (utc_now - message_time).total_seconds()
                print(f'Предоставляю {variant} ответ, время ответа: {answer_time}')
            except Exception as e:
                print(f'Возникла ошибка при предоставлении заготовленного ответа\n{e}')