import sys
import os
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
import uvicorn
from datetime import datetime, timezone

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from clients.custom_qdrant_client import Qdrant
from clients.chatwoot_client import Chatwoot
from core.embedder import Embedder
from scripts.init_kb import init_kb
from private_stuff import CHATWOOT_ADMIN_ID, CHATWOOT_API_KEY


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        app.state.qdrant_client = Qdrant()
    except Exception as e:
        print(e)
    collection = await app.state.qdrant_client.collection_init()
    
        
    app.state.chatwoot_client = Chatwoot(CHATWOOT_ADMIN_ID, CHATWOOT_API_KEY)
    app.state.embedder = Embedder()
    if collection != 'already exists':
        await init_kb(app.state.qdrant_client, app.state.embedder)
    print('Все клиенты инициализированы, приложение готово к работе')
    yield
    print('Завершение работы приложения...')
    app.state.chatwoot_client.delete_webhook()


app = FastAPI(lifespan=lifespan)


@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
        if data['message_type'] != 'incoming':
            return
        
        chat_id = data['conversation']['id']
        message = data['content']
        message_time = data['conversation']['messages'][0]['updated_at']
        print(f'''
Получено новое сообщение от {data['sender']['name']} {message_time}
Номер чата: {chat_id}
Содержание: {message}
        ''')
        message_time = datetime.fromisoformat(message_time.replace("Z", "+00:00"))
        try:
            print('Обращаюсь к ассистенту')
            await app.state.chatwoot_client.get_assist(chat_id, message, app.state.qdrant_client, app.state.embedder, message_time)
        except Exception as e:
            print(f'Ошибка при обработке сообщения {e}')
    except Exception as e:
        print(f'Ошибка при обработке запроса {e}')
        data = None
    
    return data
        
        
if __name__=='__main__':
    uvicorn.run("app.main:app", reload=True, host='127.0.0.1', port=8000)
