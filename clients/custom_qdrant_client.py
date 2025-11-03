from qdrant_client import QdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse

collection_name = 'collection'


class Qdrant:
    def __init__(self, host="localhost", port=6333, api=None, url=None):
        self.id = 0
        try:
            self.client = QdrantClient(host=host, port=port)
            print('Qdrant клиент инициализирован')
        except Exception as e:
            print(e)
        self.host = host
        self.port = port
        self.api = api
        self.url = url
        try:
            self.client.create_collection(collection_name=collection_name, vectors_config=models.VectorParams(size=1024, distance=models.Distance.COSINE))
            print(f'Коллекция {collection_name} успешно создана')
        except UnexpectedResponse as e:
            if 'already exists' in str(e):
                print(f'Коллекция {collection_name} уже существует, продолжаем работу...')
            else:
                raise e
    
    
    def _next_id(self):
        self.id += 1
        return self.id
    
    
    def load_embeddings(self, data):
        points = []
        for tuple in data:
            vector = tuple[0]
            answer = tuple[1]
            category = tuple[2]
            subcategory = tuple[3]
            points.append(models.PointStruct(id=self._next_id(), payload={"answer": answer, 'category': category, 'subcategory': subcategory}, vector=vector))
            
        
        self.client.upsert(collection_name=collection_name, points=points)
        print('Эмбеддинги загружены в qdrant')
    
    
    def search_embedding(self, embedding):
        result = {}
        i = 0
        search_results = self.client.search(collection_name='collection', query_vector=embedding, limit=3)
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