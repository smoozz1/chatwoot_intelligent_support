from qdrant_client import AsyncQdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse


TOP_K_ANSWERS = 3
COLLECTION_NAME = 'my_collection' 

class Qdrant:
    def __init__(self, host="qdrant", port=6333, api=None, url=None):
        self.id = 0
        self.client = AsyncQdrantClient(host=host, port=port)
        print('AsyncQdrantClient клиент инициализирован')
        self.host = host
        self.port = port
        self.api = api
        self.url = url
        self.answers_number = TOP_K_ANSWERS
        self.collection_name = COLLECTION_NAME


    async def collection_init(self):
        try:
            await self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(size=1024, distance=models.Distance.COSINE),
            )
            print(f'Коллекция {self.collection_name} успешно создана')
        except UnexpectedResponse as e:
            if 'already exists' in str(e):
                print(f'Коллекция {self.collection_name} уже существует, продолжаем работу...')
                return 'already exists'
            else:
                print(f'При создании коллекции произошла ошибка: {e}')


    def _next_id(self):
        self.id += 1
        return self.id
    
    
    async def load_embeddings(self, data):
        points = []
        for tuple in data:
            vector = tuple[0]
            answer = tuple[1]
            category = tuple[2]
            subcategory = tuple[3]
            points.append(models.PointStruct(id=self._next_id(), payload={"answer": answer, 'category': category, 'subcategory': subcategory}, vector=vector))
        try:
            response = await self.client.upsert(collection_name=self.collection_name, points=points)
            print('Эмбеддинги загружены в qdrant')
        except Exception as e:
            print('Ошибка при загрузке эмбеддингов', e)
    
    
    async def search_embedding(self, embedding, top_k=3):
        result = {}
        i = 0
        search_results = await self.client.search(collection_name=self.collection_name, query_vector=embedding, limit=top_k)
        for each in search_results:
            i += 1
            current_res = dict(each)
            result[i] = {
                'score': current_res['score'], 
                'answer': current_res['payload']['answer'], 
                'category': current_res['payload']['category'],
                'subcategory': current_res['payload']['subcategory'],
            }
            
        return result