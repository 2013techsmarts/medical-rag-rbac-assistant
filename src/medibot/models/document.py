from pydantic import BaseModel


class ChunkMetadata(BaseModel):
    source_document: str

    collection: str

    access_roles: list[str]

    section_title: str

    chunk_type: str