from collections.abc import Sequence
from typing import Any

from qdrant_client import models

from semantic_index.embedding import EmbeddingModel, collection_name_for_model


def index_public_items(
    model: EmbeddingModel,
    items: Sequence[Any],
    client: Any = None,
    batch_size: int = 256,
) -> int:
    """Index public items into a Qdrant collection named for the given model and revision."""
    if not items:
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

    item_list = list(items)
    total_indexed = 0

    for i in range(0, len(item_list), batch_size):
        batch = item_list[i : i + batch_size]
        descriptions = [getattr(it, "description", "") for it in batch]
        vectors = model.embed_passages(descriptions)

        points = []
        for it, vec in zip(batch, vectors, strict=True):
            unit_raw = getattr(it, "unit", "") or ""
            norm_unit = unit_raw.strip().casefold()

            pub_date = getattr(it, "published_on", None)
            if hasattr(pub_date, "isoformat"):
                pub_date_str = pub_date.isoformat()
            elif pub_date:
                pub_date_str = str(pub_date)[:10]
            else:
                pub_date_str = ""

            payload = {
                "unit": norm_unit,
                "state": getattr(it, "state", ""),
                "published_on": pub_date_str,
                "item_kind": getattr(it, "item_kind", ""),
            }
            points.append(
                models.PointStruct(
                    id=int(it.pk),
                    vector=list(vec),
                    payload=payload,
                )
            )

        qdrant_client.upsert(collection_name=collection_name, points=points)
        total_indexed += len(points)

    return total_indexed
