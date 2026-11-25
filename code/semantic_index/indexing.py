from collections.abc import Iterable, Sequence
from typing import Any

from qdrant_client import models

from semantic_index.embedding import EmbeddingModel, collection_name_for_model


def index_public_items(
    model: EmbeddingModel,
    items: Sequence[Any] | Iterable[Any],
    client: Any = None,
    batch_size: int = 256,
) -> int:
    """Index public items into a Qdrant collection named for the given model and revision."""
    iterator = items.iterator(chunk_size=batch_size) if hasattr(items, "iterator") else iter(items)
    try:
        first_item = next(iterator)
    except StopIteration:
        return 0

    from semantic_index import create_collection, get_qdrant_client

    qdrant_client = client if client is not None else get_qdrant_client()
    collection_name = collection_name_for_model(model)

    create_collection(
        client=qdrant_client,
        collection_name=collection_name,
        vector_size=model.dimension,
        distance=models.Distance.COSINE,
    )

    total_indexed = 0
    batch = [first_item]

    def _flush_batch(current_batch: list[Any]) -> int:
        descriptions = [getattr(it, "description", "") for it in current_batch]
        vectors = model.embed_passages(descriptions)

        points = []
        for it, vec in zip(current_batch, vectors, strict=True):
            normalized_unit = getattr(it, "unit_normalized", "") or ""

            pub_date = getattr(it, "published_on", None)
            if hasattr(pub_date, "isoformat"):
                pub_date_str = pub_date.isoformat()
            elif pub_date:
                pub_date_str = str(pub_date)[:10]
            else:
                pub_date_str = ""

            payload = {
                "unit": normalized_unit,
                "state": getattr(it, "state", ""),
                "published_on": pub_date_str,
                "item_kind": getattr(it, "item_kind", ""),
                "modality": int(getattr(it, "modality", 0) or 0),
            }
            points.append(
                models.PointStruct(
                    id=int(it.pk),
                    vector=vec,
                    payload=payload,
                )
            )

        qdrant_client.upsert(
            collection_name=collection_name,
            points=points,
        )
        return len(points)

    for it in iterator:
        batch.append(it)
        if len(batch) >= batch_size:
            total_indexed += _flush_batch(batch)
            batch.clear()

    if batch:
        total_indexed += _flush_batch(batch)
        batch.clear()

    return total_indexed
