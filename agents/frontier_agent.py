import os
import json

from items import FoodItem, NutritionEstimate
import config

_collection = None


def _get_collection():
    global _collection
    if _collection is not None:
        return _collection
    if not os.path.isdir(config.VECTORSTORE_DIR):
        return None
    import chromadb

    client = chromadb.PersistentClient(path=config.VECTORSTORE_DIR)
    try:
        _collection = client.get_collection("recipes")
    except ValueError:
        return None
    return _collection


def estimate(item: FoodItem) -> NutritionEstimate:
    collection = _get_collection()
    if collection is None:
        return NutritionEstimate(0, 0, 0, 0, source="frontier_unavailable")

    results = collection.query(query_texts=[item.name], n_results=3)
    metadatas = results.get("metadatas", [[]])[0]
    if not metadatas:
        return NutritionEstimate(0, 0, 0, 0, source="frontier_no_match")

    n = len(metadatas)
    avg = NutritionEstimate(
        calories=sum(m["calories"] for m in metadatas) / n,
        protein_g=sum(m["protein_g"] for m in metadatas) / n,
        carbs_g=sum(m["carbs_g"] for m in metadatas) / n,
        fat_g=sum(m["fat_g"] for m in metadatas) / n,
        source="frontier",
    )
    return avg


def suggest_recipes(remaining_macros: NutritionEstimate, n: int = 3) -> list[dict]:
    collection = _get_collection()
    if collection is None:
        return []

    query = (
        f"a meal with about {remaining_macros.calories:.0f} calories, "
        f"{remaining_macros.protein_g:.0f}g protein, "
        f"{remaining_macros.carbs_g:.0f}g carbs, {remaining_macros.fat_g:.0f}g fat"
    )
    results = collection.query(query_texts=[query], n_results=n)
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    return [
        {"recipe": doc, **meta} for doc, meta in zip(documents, metadatas)
    ]
