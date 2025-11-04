import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.clients.custom_qdrant_client import Qdrant
from app.clients.chatwoot_client import Chatwoot
from app.core.embedder import Embedder
from app.scripts.init_kb import init_kb
from app.services.assistant import Assistant
from app.private_stuff import CHATWOOT_ADMIN_ID, CHATWOOT_API_KEY

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Инициализация клиентов
    app.state.embedder = Embedder()
    app.state.qdrant_client = Qdrant()
    app.state.assistant = Assistant(app.state.embedder, app.state.qdrant_client)
    app.state.chatwoot_client = Chatwoot(
        CHATWOOT_ADMIN_ID,
        CHATWOOT_API_KEY,
        app.state.assistant
    )

    # Инициализация Chatwoot и базы знаний
    await app.state.chatwoot_client.init_client()

    if await app.state.qdrant_client.collection_init() == 'created':
        await init_kb(app.state.qdrant_client, app.state.embedder)

    logger.info("Все клиенты инициализированы, приложение готово к работе")
    
    yield  # Работа приложения

    # Завершение работы
    await app.state.chatwoot_client.delete_webhook()
    await app.state.chatwoot_client.close()
    logger.info("Завершение работы приложения...")
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.clients.custom_qdrant_client import Qdrant
from app.clients.chatwoot_client import Chatwoot
from app.core.embedder import Embedder
from app.scripts.init_kb import init_kb
from app.services.assistant import Assistant
from app.private_stuff import CHATWOOT_ADMIN_ID, CHATWOOT_API_KEY

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Инициализация клиентов
    app.state.embedder = Embedder()
    app.state.qdrant_client = Qdrant()
    app.state.assistant = Assistant(app.state.embedder, app.state.qdrant_client)
    app.state.chatwoot_client = Chatwoot(
        CHATWOOT_ADMIN_ID,
        CHATWOOT_API_KEY,
        app.state.assistant
    )

    # Инициализация Chatwoot и базы знаний
    await app.state.chatwoot_client.init_client()

    if await app.state.qdrant_client.collection_init() == 'created':
        await init_kb(app.state.qdrant_client, app.state.embedder)

    logger.info("Все клиенты инициализированы, приложение готово к работе")
    
    yield  # Работа приложения

    # Завершение работы
    await app.state.chatwoot_client.delete_webhook()
    await app.state.chatwoot_client.close()
    logger.info("Завершение работы приложения...")
