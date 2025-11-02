import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import warnings
warnings.simplefilter("ignore", UserWarning)


from  clients.qdrant_client import Qdrant
import pandas as pd


df = pd.read_excel('./data/knowledge_base.xlsx')
questions = df['Пример вопроса'].to_list()
answers = df['Шаблонный ответ'].to_list()
print('Данные прочитаны')



data = zip(embeddings, answers)

client = Qdrant()

client.load_embeddings(data)
