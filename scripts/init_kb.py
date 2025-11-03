import sys
import os
import pandas as pd
import warnings 


warnings.simplefilter("ignore", UserWarning)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


from  clients.custom_qdrant_client import Qdrant
from core.embedder import Embedder


def init_kb(qdrant_client, embedder):
    
    df = pd.read_excel('./data/knowledge_base.xlsx')
    questions = df['Пример вопроса'].to_list()
    answers = df['Шаблонный ответ'].to_list()
    category = df['Основная категория'].to_list()
    subcategory = df['Подкатегория'].to_list()
    print('Вопросы с ответами получены, перевожу вопросы в эмбеддинги...')
    
    try:
        embeddings = embedder.get_embedding(questions)
        data = zip(embeddings, answers, category, subcategory)
        qdrant_client.load_embeddings(data)
        print('База знаний инициализирована')
    except Exception as e:
        print('Возникла ошибка')
        print(str(e))