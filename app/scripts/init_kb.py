import pandas as pd
import warnings
import logging
from pathlib import Path
import sys
from itertools import islice

# Игнорируем предупреждения от pandas
warnings.simplefilter("ignore", UserWarning)

# Настройка пути, если нужно добавить родительский каталог в sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Логгер
logger = logging.getLogger(__name__)


async def init_kb(qdrant_client, embedder, batch_size: int = 100):
    """
    Инициализация базы знаний: загрузка вопросов и ответов,
    перевод вопросов в эмбеддинги и загрузка в Qdrant.
    Обработка выполняется батчами для экономии памяти.
    """
    try:
        # Папка app
        APP_DIR = Path(__file__).resolve().parent.parent
        data_file = APP_DIR / "data" / "knowledge_base.xlsx"

        if not data_file.exists():
            logger.error("Файл базы знаний не найден: %s", data_file)
            return

        df = pd.read_excel(data_file)
        records = [
            {
                "question": q,
                "answer": a,
                "category": c,
                "subcategory": sc
            }
            for q, a, c, sc in zip(
                df['Пример вопроса'],
                df['Шаблонный ответ'],
                df['Основная категория'],
                df['Подкатегория']
            )
        ]

        logger.info("Вопросы с ответами получены, перевожу вопросы в эмбеддинги...")

        # Обработка батчами
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            questions = [r['question'] for r in batch]
            embeddings = embedder.get_embedding(questions)

            # Подготавливаем данные для Qdrant
            data_to_load = [
                {
                    "embedding": emb,
                    "answer": r["answer"],
                    "category": r["category"],
                    "subcategory": r["subcategory"]
                }
                for emb, r in zip(embeddings, batch)
            ]

            await qdrant_client.load_embeddings(data_to_load)
            logger.info(
                "Загружен батч с %d вопросами (порядок %d-%d)",
                len(batch), i + 1, i + len(batch)
            )

        logger.info("База знаний успешно загружена")

    except Exception as e:
        logger.exception("Возникла ошибка при загрузке базы знаний: %s", e)
