from backend.app.schemas.clothing import ClothingSearchQuery


def reduce_dict(left: dict, right: dict) -> dict:
    return {**left, **right}


def reduce_clothing_search_query(
    left: ClothingSearchQuery, right: ClothingSearchQuery
) -> ClothingSearchQuery:
    return ClothingSearchQuery.model_validate({**left, **right})
