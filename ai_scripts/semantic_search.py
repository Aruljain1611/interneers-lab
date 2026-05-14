from qdrant_client import models, QdrantClient
from sentence_transformers import SentenceTransformer
import toy_products_777 

document = toy_products_777.document


encoder = SentenceTransformer("all-MiniLM-L6-v2")

client = QdrantClient(":memory:")

client.create_collection(
    collection_name="products",
    vectors_config=models.VectorParams(
        size = encoder.get_sentence_embedding_dimension(),
        distance = models.Distance.COSINE
    )
)

client.upload_points(
    collection_name="products",
    points = [
        models.PointStruct(
            id = idx, vector = encoder.encode(doc["description"]).tolist(), payload=doc
        )
        for idx, doc in enumerate(document)
    ]
)

def search_query(query : str):
    hits = client.query_points(
        collection_name="products",
        query=encoder.encode(query).tolist(),
        limit=5,
    ).points

    for hit in hits:
        print(hit.payload, "score:", hit.score)





