import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.clients.custom_qdrant_client import Qdrant
from app.clients.chatwoot_client import Chatwoot
from app.core.embedder import Embedder
from app.scripts.init_kb import init_kb
from app.services.assistant import Assistant
from app.utils.tunnel import LocalTunnel


#Вставляем свои данные
CHATWOOT_API_KEY = 
CHATWOOT_ADMIN_ID = 

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):    
    
    async def update_webhook(new_url):
        await app.state.chatwoot_client.create_or_update_webhook(new_url)
        
    # Инициализация клиентов
    app.state.embedder = Embedder()
    
    app.state.qdrant_client = Qdrant()
    if await app.state.qdrant_client.collection_init() == 'created':
        await init_kb(app.state.qdrant_client, app.state.embedder)
    
    app.state.tunnel = LocalTunnel(on_url_change=update_webhook)
    app.state.assistant = Assistant(app.state.embedder, app.state.qdrant_client)
    app.state.chatwoot_client = Chatwoot(
        CHATWOOT_ADMIN_ID,
        CHATWOOT_API_KEY,
        app.state.tunnel,
        app.state.assistant
    )
    
    await app.state.chatwoot_client.init_client()
    await app.state.tunnel.start()
    
    logger.info("Локальный туннель запущен, все клиенты инициализированы, приложение готово к работе")
    
    yield  # Работа приложения

    # Завершение работы
    await app.state.tunnel.stop()
    await app.state.chatwoot_client.delete_webhook()
    await app.state.chatwoot_client.close()
    logger.info("Завершение работы приложения...")
