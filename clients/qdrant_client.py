from qdrant_client import QdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse

collection_name = 'collection'


class Qdrant:
    def __init__(self, host="localhost", port=6333, api=None, url=None):
        self.id = 0
        global client
        client = QdrantClient(host=host, port=port)
        self.host = host
        self.port = port
        self.api = api
        self.url = url
        try:
            client.create_collection(collection_name=collection_name, vectors_config=models.VectorParams(size=1024, distance=models.Distance.COSINE))
            print(f'Коллекция {collection_name} успешно создана')
        except UnexpectedResponse as e:
            if 'already exists' in str(e):
                print(f'Коллекция {collection_name} уже существует, продолжаем работу...')
            else:
                raise e
    
    
    def _next_id(self):
        self.__class__.id += 1
        return self.__class__.id
    
    
    def load_embeddings(self, data):
        points = []
        for tuple in data:
            answer = tuple[1]
            vector = tuple[0]
            points.append(models.PointStruct(id=self._next_id(), payload={"answer": answer}, vector=vector))
            
        
        client.upsert(collection_name=collection_name, points=points)
        print('Эмбеддинги загружены в qdrant')
    
    
    def search_embedding(self, embedding):
        client.search(
        collection_name=collection_name,
        query_vector=embedding,
        limit=3
    )

