import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
import uvicorn
from clients.custom_qdrant_client import Qdrant
from clients.chatwoot_client import Chatwoot

from core.embedder import Embedder
from scripts.init_kb import init_kb
from private_stuff import CHATWOOT_ADMIN_ID, CHATWOOT_API_KEY

app = FastAPI()
qdrant_client = Qdrant()
chatwoot_client = Chatwoot(CHATWOOT_ADMIN_ID, CHATWOOT_API_KEY)
embedder = Embedder()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_kb(app.state.qdrant_client, embedder)
    yield


@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
        if data['private'] == True or data['conversation']['messages'][0]['sender_type'] != 'Contact': # or data['content_type'] == 'input_email' or 
            return
        chat_id = data['conversation']['id']
        message = data['conversation']['messages'][0]['content']
        print(f'''
==================================================
Получено новое сообщение от {data['sender']['name']} в {data['conversation']['messages'][0]['updated_at']}
Номер чата: {chat_id}
Содержание: {message}
==================================================
        ''')
        try:
            chatwoot_client.get_assist(chat_id, message, qdrant_client, embedder)
        except Exception as e:
            print(str(e))
    except Exception as e:
        data = None
    return data
        
        
if __name__=='__main__':
    uvicorn.run(app="app.main:app", reload=True, host='127.0.0.1', port=8000) #lt --port 8000
