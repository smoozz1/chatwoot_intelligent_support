import logging
from datetime import datetime, timezone
from fastapi import Request, HTTPException

logger = logging.getLogger(__name__)

async def handle_webhook(request: Request, app_state):
    """
    Обработка входящего webhook от Chatwoot.
    app_state — app.state с embedder, qdrant_client, chatwoot_client, assistant
    """
    try:
        data = await request.json()
    except Exception as e:
        logger.error("Ошибка при парсинге JSON: %s", e)
        raise HTTPException(status_code=400, detail="Invalid JSON")

    if data.get('message_type') != 'incoming':
        return data  # Игнорируем исходящие сообщения

    try:
        conversation_id = data['conversation']['id']
        message = data['content']
        message_time_str = data['conversation']['messages'][0]['updated_at']
        message_time = datetime.fromisoformat(message_time_str.replace("Z", "+00:00"))

        logger.info(
            "Новое сообщение от %s, chat_id: %s, время: %s, текст: %s",
            data['sender']['name'],
            conversation_id,
            message_time,
            message
        )

        # Обращение к ассистенту
        await app_state.chatwoot_client.get_assist(conversation_id, message, message_time)
        logger.info("Ассистент обработал сообщение chat_id=%s", conversation_id)

    except Exception as e:
        logger.exception("Ошибка при обработке сообщения: %s", e)
    
    return data
