from qdrant_client.models import (
    Distance,
    VectorParams,
    SparseVectorParams
)

from medibot.vectorstore.qdrant import (
    get_qdrant_client
)

COLLECTION_NAME = "medibot"


client = get_qdrant_client()

if client.collection_exists(COLLECTION_NAME):
    print("Collection exists")
    exit(0)

client.create_collection(
    collection_name=COLLECTION_NAME,

    vectors_config={
        "dense": VectorParams(
            size=1024,
            distance=Distance.COSINE
        )
    },

    sparse_vectors_config={
        "sparse": SparseVectorParams()
    }
)

client.create_payload_index(
    collection_name=COLLECTION_NAME,
    field_name="collection",
    field_schema="keyword"
)

client.create_payload_index(
    collection_name=COLLECTION_NAME,
    field_name="access_roles",
    field_schema="keyword"
)

client.create_payload_index(
    collection_name=COLLECTION_NAME,
    field_name="section_title",
    field_schema="text"
)
print("Collection created")