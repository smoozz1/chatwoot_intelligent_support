import httpx
import logging
from app.utils.tunnel import get_localtunnel_url

logger = logging.getLogger(__name__)


class Chatwoot:
    def __init__(self, admin_id: int | str, api_key: str, assistant):
        self.admin_id = admin_id
        self.api_key = api_key
        self.assistant = assistant
        self.client: httpx.AsyncClient | None = None
        self.webhook_id: str | None = None
        self.public_url: str | None = None
        logger.info("Инициализация Chatwoot клиента...")

    async def close(self):
        """Закрытие HTTP клиента"""
        if self.client:
            await self.client.aclose()
            logger.info("HTTP клиент Chatwoot закрыт")

    async def init_client(self):
        """Проверка аккаунта и создание вебхука"""
        if not self.client:
            self.client = httpx.AsyncClient(timeout=10.0)

        url = f"https://app.chatwoot.com/api/v1/accounts/{self.admin_id}"
        headers = {"api_access_token": self.api_key}

        try:
            resp = await self.client.get(url, headers=headers)
            resp.raise_for_status()
            logger.info("Chatwoot клиент инициализирован")
        except httpx.HTTPError as e:
            logger.error(f"Ошибка при инициализации Chatwoot клиента: {e}")
            return

        await self.add_webhook()

    async def add_webhook(self):
        """Создание вебхука"""
        if not self.public_url:
            self.public_url = get_localtunnel_url()
            if not self.public_url:
                logger.error("Не удалось получить публичный URL туннеля")
                return

        self.webhook_url = f"{self.public_url}/webhook"
        url = f"https://app.chatwoot.com/api/v1/accounts/{self.admin_id}/webhooks"
        payload = {"url": self.webhook_url, "subscriptions": ["message_created"]}
        headers = {"api_access_token": self.api_key, "Content-Type": "application/json"}

        try:
            resp = await self.client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            self.webhook_id = resp.json()['payload']['webhook']['id']
            logger.info(f"Вебхук {self.webhook_id} создан: {self.webhook_url}")
        except httpx.HTTPError as e:
            logger.error(f"Ошибка при создании вебхука: {e}")

    async def delete_webhook(self):
        """Удаление вебхука"""
        if not self.webhook_id:
            logger.warning("Нет вебхука для удаления")
            return False

        url = f"https://app.chatwoot.com/api/v1/accounts/{self.admin_id}/webhooks/{self.webhook_id}"
        headers = {"api_access_token": self.api_key}

        try:
            logger.info(f"Удаляю вебхук {self.webhook_url}")
            resp = await self.client.delete(url, headers=headers)
            resp.raise_for_status()
            logger.info(f"Вебхук {self.webhook_url} удален")
            return True
        except httpx.HTTPError as e:
            logger.error(f"Не удалось удалить вебхук {self.webhook_url}: {e}")
            return False

    async def send_message(self, conversation_id, content: str, private: bool = True):
        """Универсальная функция отправки сообщений"""
        if not self.client:
            self.client = httpx.AsyncClient(timeout=10.0)

        url = f"https://app.chatwoot.com/api/v1/accounts/{self.admin_id}/conversations/{conversation_id}/messages"
        payload = {
            "content": content,
            "message_type": "outgoing",
            "private": private,
            "content_type": "text",
        }
        headers = {"api_access_token": self.api_key, "Content-Type": "application/json"}

        try:
            resp = await self.client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            logger.info(f"Сообщение отправлено в чат {conversation_id}")
        except httpx.HTTPError as e:
            logger.error(f"Ошибка при отправке сообщения: {e}")
            raise

    async def get_assist(self, conversation_id, message, message_time):
        """Получение помощи через ассистента"""
        if not self.assistant:
            logger.error("Assistant не передан в Chatwoot клиент")
            return
        await self.assistant.handle_message(self, conversation_id, message, message_time)